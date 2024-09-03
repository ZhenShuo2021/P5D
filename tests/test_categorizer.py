import random
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

from p5d.app_settings import EN, JP, Other
from p5d.categorizer import (
    CategorizerUI,
    CategorizerAdapter,
    TaggedCategorizer,
    UnTaggedCategorizer,
)
from tests.test_base import TestBase, safe_rmtree, TEST_LOCAL, TEST_REMOTE


class TestCategorizerAdapter(TestBase):

    @patch("p5d.categorizer.TaggedCategorizer")
    @patch("p5d.categorizer.UnTaggedCategorizer")
    @patch("p5d.categorizer.CustomCategorizer")
    def setUp(self, MockCustomCategorizer, MockUnTaggedCategorizer, MockTaggedCategorizer):
        super().setUp()
        self.config_loader.load_config()
        self.adapter = CategorizerAdapter(self.config_loader, self.mock_logger)

        self.mock_tagged_categorizer = MockTaggedCategorizer.return_value
        self.mock_untagged_categorizer = MockUnTaggedCategorizer.return_value
        self.mock_custom_categorizer = MockCustomCategorizer.return_value

    def test_initialization(self):
        # 驗證 config_loader 和 logger 是否正確設置
        # self.assertEqual(self.adapter.config_loader, self.config_loader)
        # self.assertEqual(self.adapter.logger, self.mock_logger)

        # 驗證 categorizers 字典中的各個分類器是否被正確初始化
        self.assertIn("series", self.adapter.categorizers)
        self.assertIn("others", self.adapter.categorizers)
        self.assertIn("custom", self.adapter.categorizers)

        # 確保 categorizers 字典中的每個分類器實例都是正確的
        self.assertIsInstance(
            self.adapter.categorizers["series"], self.mock_tagged_categorizer.__class__
        )
        self.assertIsInstance(
            self.adapter.categorizers["others"], self.mock_untagged_categorizer.__class__
        )
        self.assertIsInstance(
            self.adapter.categorizers["custom"], self.mock_custom_categorizer.__class__
        )

    def test_get_categorizer(self):
        category = "BlueArchive"
        categories = self.config_loader.get_categories()
        preprocess, categorizer = self.adapter.get_categorizer(category, categories)
        self.assertEqual(preprocess, False)
        self.assertIsInstance(categorizer, self.mock_tagged_categorizer.__class__)

        category = "IdolMaster"
        categories = self.config_loader.get_categories()
        preprocess, categorizer = self.adapter.get_categorizer(category, categories)
        self.assertEqual(preprocess, True)
        self.assertIsInstance(categorizer, self.mock_tagged_categorizer.__class__)

        category = "Marin"
        categories = self.config_loader.get_categories()
        preprocess, categorizer = self.adapter.get_categorizer(category, categories)
        self.assertEqual(preprocess, False)
        self.assertIsNone(categorizer)

        category = "Others"
        categories = self.config_loader.get_categories()
        preprocess, categorizer = self.adapter.get_categorizer(category, categories)
        self.assertEqual(preprocess, True)
        self.assertIsInstance(categorizer, self.mock_untagged_categorizer.__class__)


class TestCategorizerUI(TestBase):
    def setUp(self):
        super().setUp()
        self.mock_adapter = Mock(spec=CategorizerAdapter)
        self.config_loader.load_config()
        self.config_loader.update_config(self.file_base)
        self.config_loader.update_config(self.categories_path)
        self.cat1 = list(self.config_loader.get_categories())[0]

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
        ui.categorize(self.cat1)

        # 確認 factory.get_categorizer 和 categorizer.categorize 都只被呼叫一次
        self.mock_adapter.get_categorizer.assert_called_once_with(self.cat1, ui.categories)
        mock_categorizer.categorize.assert_called_once_with(self.cat1, mock_preprocess)

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
        ui.categorize(self.cat1)

        # 確認 factory.get_categorizer 和 categorizer.categorize 都只被呼叫一次
        self.mock_adapter.get_categorizer.assert_called_once_with(self.cat1, ui.categories)
        mock_categorizer.categorize.assert_called_once_with(self.cat1, mock_preprocess)

        # 檢查 CategorizerAdapter 回傳 None 的執行次數
        self.mock_adapter.get_categorizer.return_value = (False, None)
        ui = CategorizerUI(self.config_loader, self.mock_logger, self.mock_adapter)
        ui.categorize(self.cat1)

        # 回傳 None ，get_categorizer 應只執行一次（第二次），並顯示對應 logger
        self.assertEqual(
            self.mock_logger.debug.call_args_list[-1],
            call((f"Skip categorize category '{self.cat1}'.")),
        )

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


class TestTaggedCategorizer(TestBase):
    def setUp(self):
        super().setUp()
        self.config_loader.load_config()
        self.config_loader.update_config(self.file_base)
        self.config_loader.update_config(self.categories_path)
        self.categorizer = TaggedCategorizer(self.config_loader, self.mock_logger)

    def tearDown(self):
        safe_rmtree(self.root_dir / TEST_LOCAL)

    def test_categorize_child(self):
        # Files of category 1: with child
        cat1 = "IdolMaster"
        cat1_dir = Path(self.config_loader.get_combined_paths()[cat1]["local_path"])
        cat1_dir.mkdir(parents=True, exist_ok=True)
        child_list = self.config_loader.get_categories()[cat1]["children"]

        fn = [
            "file1,黛冬優子,NoTag1,NoTag2.jpg",
            "file2,NoTag1,桑山千雪,樋口円香.jpg",
            "file3,NoTag1,NoTag2,NoTag3.jpg",
        ]

        for filename in fn:
            random_child = random.choice(child_list)
            file_dir = cat1_dir.parent / random_child
            file_dir.mkdir(parents=True, exist_ok=True)
            file_path = file_dir / filename
            with open(file_path, "w") as f:
                f.write("test")
        self.categorizer.categorize(cat1, preprocess=True)

        # String is value of the given tag key.
        self.assertTrue((cat1_dir / "黛冬優子" / fn[0]).exists())
        self.assertTrue((cat1_dir / "桑山千雪" / fn[1]).exists())
        self.assertTrue((cat1_dir / "others" / fn[2]).exists())

    def test_categorize_no_child(self):
        # Files of category 2: without child
        cat2 = "BlueArchive"
        cat2_dir = Path(self.config_loader.get_combined_paths()[cat2]["local_path"])
        cat2_dir.mkdir(parents=True, exist_ok=True)

        fn = [
            "file1,一之瀨亞絲娜(限定),NoTag1,NoTag2.jpg",
            "file2,亞絲娜,NoTag1,NoTag2.jpg",
            "file3,调月莉音,notag,notag.jpg",
        ]

        for filename in fn:
            file_path = cat2_dir / filename
            with open(file_path, "w") as f:
                f.write("test")
        self.categorizer.categorize(cat2, preprocess=False)

        # String is value of the given tag key.
        self.assertTrue((cat2_dir / "一之瀬アスナ" / fn[0]).exists())
        self.assertTrue((cat2_dir / "一之瀬アスナ" / fn[1]).exists())
        self.assertTrue((cat2_dir / "調月リオ" / fn[2]).exists())

    def test_categorize_others(self):
        # Add tags to Others category
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
        cat3_dir = Path(self.config_loader.get_combined_paths()["Others"]["local_path"])
        cat3_dir.mkdir(parents=True, exist_ok=True)

        fn = [
            "file1,tag1,notag1,tag2,nice_job.jpg",
            "file2,tag4,notag1,tag5,bad_job.jpg",
            "file3,notag,notag,notag,114514.jpg",
        ]

        for filename in fn:
            file_path = cat3_dir / filename
            with open(file_path, "w") as f:
                f.write("test")
        self.categorizer.categorize("Others", preprocess=False)

        # String is value of the given tag key.
        self.assertTrue((cat3_dir / "好欸！" / fn[0]).exists())
        self.assertTrue((cat3_dir / "others" / fn[1]).exists())
        self.assertTrue((cat3_dir / "id_ed25519" / fn[2]).exists())


class TestUnTaggedCategorizer(TestBase):
    def setUp(self):
        super().setUp()
        self.config_loader.load_config()
        self.config_loader.update_config(self.file_base)
        self.config_loader.update_config(self.categories_path)
        self.categorizer = UnTaggedCategorizer(self.config_loader, self.mock_logger)
        """Setup with handcraft files"""
        self.fn = [
            "ベッセルイン,tag1,notag1,tag2.jpg",
            "Never_loses,tag4,notag1,tag5.jpg",
            "70、80、90年代老音響討論交流區,notag,notag,notag.jpg",
            "幸永,notag,notag,notag.jpg",
        ]
        self.cat1_dir = Path(self.config_loader.get_combined_paths()["Others"]["local_path"])
        self.cat1_dir.mkdir(parents=True, exist_ok=True)
        for filename in self.fn:
            file_path = self.cat1_dir.parent / filename
            with open(file_path, "w") as f:
                f.write("test")

    def tearDown(self):
        safe_rmtree(self.root_dir / TEST_LOCAL)

    def test_categorize_name_entry(self):
        """Test Others category without custom tags."""
        self.categorizer.categorize("Others", preprocess=False)

        self.assertTrue((self.cat1_dir / JP / self.fn[0]).exists())
        self.assertTrue((self.cat1_dir / EN / self.fn[1]).exists())
        self.assertTrue((self.cat1_dir / Other / self.fn[2]).exists())
        self.assertTrue((self.cat1_dir / Other / self.fn[3]).exists())


if __name__ == "__main__":
    unittest.main()
