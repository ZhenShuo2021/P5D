import random
import shutil
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.app_settings import EN, JP, Other
from src.categorizer import (
    CategorizerUI,
    CategorizerAdapter,
    TaggedCategorizer,
    UnTaggedCategorizer,
)
from test.test_file_utils import ConfigLoaderTestBase


class TestCategorizerUI(ConfigLoaderTestBase):
    def setUp(self):
        super().setUp()
        self.mock_adapter = Mock(spec=CategorizerAdapter)

        self.test_cat1, self.test_cat2 = "category1", "category2"

    @patch("pathlib.Path.exists", return_value=True)
    def test_init_success(self, mock_exists):
        ui = CategorizerUI(self.config_loader, self.mock_logger, self.mock_adapter)
        self.assertIsInstance(ui, CategorizerUI)

    @patch("pathlib.Path.exists", return_value=False)
    def test_init_failure(self, mock_exists):
        with self.assertRaises(FileNotFoundError):
            CategorizerUI(self.config_loader, self.mock_logger, self.mock_adapter)

    @patch("pathlib.Path.exists", return_value=True)
    def test_categorize_specific(self, mock_exists):
        """檢查特定分類的執行次數"""
        # CategorizerUI 輸入 config_loader, logger, factory 參數，所以給他三個 mock
        mock_categorizer = Mock()
        mock_preprocess = Mock()
        # 接下來呼叫 factory.get_categorizer ，輸出是 (preprocess, categorizer)，也新增兩個假輸出給他
        self.mock_adapter.get_categorizer.return_value = (mock_preprocess, mock_categorizer)

        # 把第一個分類給 CategorizerUI.categorize 執行
        ui = CategorizerUI(self.config_loader, self.mock_logger, self.mock_adapter)
        ui.categorize(self.test_cat1)

        # 確認 factory.get_categorizer 和 categorizer.categorize 都只被呼叫一次
        self.mock_adapter.get_categorizer.assert_called_once_with(self.test_cat1, ui.categories)
        mock_categorizer.categorize.assert_called_once_with(self.test_cat1, mock_preprocess)

    @patch("pathlib.Path.exists", return_value=True)
    def test_categorize_skip(self, mock_exists):
        """檢查CategorizerAdapter回傳None的執行次數"""
        self.mock_adapter.get_categorizer.return_value = (False, None)
        ui = CategorizerUI(self.config_loader, self.mock_logger, self.mock_adapter)
        ui.categorize(self.test_cat1)

        self.mock_adapter.get_categorizer.assert_called_once_with(self.test_cat1, ui.categories)
        self.mock_logger.debug.assert_called_once_with("Skip categorize category 'category1'.")

    @patch("pathlib.Path.exists", return_value=True)
    def test_categorize(self, mock_exists):
        """測試 CategorizerUI 在特定條件下的行為"""
        # CategorizerUI 輸入 config_loader, logger, factory 參數，所以給他三個 mock
        mock_categorizer = Mock()
        mock_preprocess = Mock()
        # 接下來呼叫 factory.get_categorizer ，輸出是 (preprocess, categorizer)，也新增兩個假輸出給他
        self.mock_adapter.get_categorizer.return_value = (mock_preprocess, mock_categorizer)

        # 把第一個分類給 CategorizerUI.categorize 執行
        ui = CategorizerUI(self.config_loader, self.mock_logger, self.mock_adapter)
        ui.categorize(self.test_cat1)

        # 確認 factory.get_categorizer 和 categorizer.categorize 都只被呼叫一次
        self.mock_adapter.get_categorizer.assert_called_once_with(self.test_cat1, ui.categories)
        mock_categorizer.categorize.assert_called_once_with(self.test_cat1, mock_preprocess)

        # 檢查 CategorizerAdapter 回傳 None 的執行次數
        self.mock_adapter.get_categorizer.return_value = (False, None)
        ui = CategorizerUI(self.config_loader, self.mock_logger, self.mock_adapter)
        ui.categorize(self.test_cat1)

        # 回傳 None ，get_categorizer 應只執行一次（第二次），並顯示對應 logger
        self.assertEqual(self.mock_adapter.get_categorizer.call_count, 2)
        self.mock_logger.debug.assert_called_once_with("Skip categorize category 'category1'.")

    @patch("pathlib.Path.exists", return_value=True)
    def test_categorize_all(self, mock_exists):
        """檢查無輸入(categorize_all)的執行次數，應等於分類數量"""
        ui = CategorizerUI(self.config_loader, self.mock_logger, self.mock_adapter)
        mock_categorizer = Mock()
        mock_preprocess = Mock()
        self.mock_adapter.get_categorizer.return_value = (mock_preprocess, mock_categorizer)

        ui.categorize_all()

        self.assertEqual(
            self.mock_adapter.get_categorizer.call_count,
            len(self.config_loader.get_categories()),
        )
        self.assertEqual(
            mock_categorizer.categorize.call_count,
            len(self.config_loader.get_categories()),
        )

    @patch("pathlib.Path.exists", return_value=True)
    def test_categorize_all_with_empty_category(self, mock_exists):
        # 空分類應出現TypeError
        with self.assertRaises(TypeError):
            self.config_loader.config["categories"][""] = ""
            self.mock_adapter.get_categorizer.return_value = (False, None)
            ui = CategorizerUI(self.config_loader, self.mock_logger, self.mock_adapter)
            ui.categorize_all()


class TestTaggedCategorizer(ConfigLoaderTestBase):
    def setUp(self):
        """Setup with handcraft files"""
        super().setUp()
        self.categorizer = TaggedCategorizer(self.config_loader, self.mock_logger)

    def tearDown(self):
        shutil.rmtree(self.root_dir)
        # pass

    def test_categorize_child(self):
        # Files of category 1: with child
        t = "text"
        cat1_dir = Path(self.config_loader.get_combined_paths()["cat1"]["local_path"])
        cat1_dir.mkdir(parents=True, exist_ok=True)
        child_list = self.config_loader.get_categories()["cat1"]["children"]
        fn1 = "file1,tag1,notag1,tag2.jpg"
        fn2 = "file2,tag4,notag1,tag5.jpg"
        fn3 = "file3,notag,notag,notag.jpg"
        cat1 = {fn1: t, fn2: t, fn3: t}
        for filename in cat1.keys():
            random_child = random.choice(child_list)
            file_dir = cat1_dir.parent / random_child
            file_dir.mkdir(parents=True, exist_ok=True)
            file_path = file_dir / filename
            with open(file_path, "w") as f:
                f.write("test")
        self.categorizer.categorize("cat1", preprocess=True)

        self.assertTrue(
            (cat1_dir / "map1" / fn1).exists(),
            f"File {fn1} not found in 'map1' directory",
        )
        self.assertTrue(
            (cat1_dir / "others" / fn2).exists(),
            f"File {fn2} not found in 'map4' directory",
        )
        self.assertTrue(
            (cat1_dir / "others" / fn3).exists(),
            f"File {fn3} not found in 'others' directory",
        )

    def test_categorize_no_child(self):
        # Files of category 2: without child
        t = "text"
        cat2_dir = Path(self.config_loader.get_combined_paths()["cat2"]["local_path"])
        cat2_dir.mkdir(parents=True, exist_ok=True)
        fn1 = "file1,tag1,notag1,tag2.jpg"
        fn2 = "file2,tag4,notag1,tag5.jpg"
        fn3 = "file3,notag,notag,notag.jpg"
        cat2 = {fn1: t, fn2: t, fn3: t}
        for filename in cat2.keys():
            file_path = cat2_dir / filename
            with open(file_path, "w") as f:
                f.write("test")
        self.categorizer.categorize("cat2", preprocess=False)

        self.assertTrue(
            (cat2_dir / "others" / fn1).exists(),
            f"File {fn1} not found in 'map1' directory",
        )
        self.assertTrue(
            (cat2_dir / "map4" / fn2).exists(),
            f"File {fn2} not found in 'map4' directory",
        )
        self.assertTrue(
            (cat2_dir / "others" / fn3).exists(),
            f"File {fn3} not found in 'others' directory",
        )

    def test_categorize_others(self):
        t = "text"
        cat3_dir = Path(self.config_loader.get_combined_paths()["Others"]["local_path"])
        Others_tag = {
            "custom_setting": {
                "Others": {
                    "tags": {
                        "nice_job": "好欸！",
                        "114514": "id_ed25519",
                    }
                }
            }
        }
        self.config_loader.update_config(Others_tag)
        cat3_dir.mkdir(parents=True, exist_ok=True)
        fn1 = "file1,tag1,notag1,tag2,nice_job.jpg"
        fn2 = "file2,tag4,notag1,tag5,bad_job.jpg"
        fn3 = "file3,notag,notag,notag,114514.jpg"
        cat3 = {fn1: t, fn2: t, fn3: t}
        for filename in cat3.keys():
            file_path = cat3_dir / filename
            with open(file_path, "w") as f:
                f.write("test")
        self.categorizer.categorize("Others", preprocess=False)

        self.assertTrue(
            (cat3_dir / "好欸！" / fn1).exists(),
            f"File {fn1} not found in 'map1' directory",
        )
        self.assertTrue(
            (cat3_dir / "others" / fn2).exists(),
            f"File {fn2} not found in 'map4' directory",
        )
        self.assertTrue(
            (cat3_dir / "id_ed25519" / fn3).exists(),
            f"File {fn3} not found in 'others' directory",
        )


class TestUnTaggedCategorizer(ConfigLoaderTestBase):
    def setUp(self):
        """Setup with handcraft files"""
        super().setUp()
        t = "text"
        # Files of category 1: with child
        self.cat1_dir = Path(self.config_loader.get_combined_paths()["Others"]["local_path"])
        self.cat1_dir.mkdir(parents=True, exist_ok=True)
        self.fn1 = "ベッセルイン,tag1,notag1,tag2.jpg"
        self.fn2 = "Never_loses,tag4,notag1,tag5.jpg"
        self.fn3 = "70、80、90年代老音響討論交流區,notag,notag,notag.jpg"
        self.fn4 = "幸永,notag,notag,notag.jpg"
        self.cat1 = {self.fn1: t, self.fn2: t, self.fn3: t, self.fn4: t}
        for filename in self.cat1.keys():
            file_path = self.cat1_dir.parent / filename
            with open(file_path, "w") as f:
                f.write("test")

        self.categorizer = UnTaggedCategorizer(self.config_loader, self.mock_logger)

    def tearDown(self):
        shutil.rmtree(self.root_dir)
        # pass

    def test_categorize_name_entry(self):
        """Test Others category without custom tags."""
        self.categorizer.categorize("Others", preprocess=False)

        self.assertTrue(
            (self.cat1_dir / JP / self.fn1).exists(),
            f"File {self.fn1} not found in 'map1' directory",
        )
        self.assertTrue(
            (self.cat1_dir / EN / self.fn2).exists(),
            f"File {self.fn2} not found in 'map4' directory",
        )
        self.assertTrue(
            (self.cat1_dir / Other / self.fn3).exists(),
            f"File {self.fn3} not found in 'others' directory",
        )
        self.assertTrue(
            (self.cat1_dir / Other / self.fn4).exists(),
            f"File {self.fn4} not found in 'others' directory",
        )


if __name__ == "__main__":
    unittest.main()
