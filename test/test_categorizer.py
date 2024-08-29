import unittest
from unittest.mock import Mock, patch, MagicMock

from src.categorizer import CategorizerUI, CategorizerFactory
from test.test_utils_file_utils import ConfigLoaderTestBase

class TestCategorizerUI(ConfigLoaderTestBase):
    def setUp(self):
        super().setUp()
        self.mock_factory = Mock(spec=CategorizerFactory)
        
        self.test_cat1, self.test_cat2 = "category1", "category2"
        self.config_loader.get_base_paths = Mock(return_value={"local_path": "/mock/path"})
        self.config_loader.get_combined_paths = Mock(return_value={"path1": "/mock/path1", "path2": "/mock/path2"})
        self.config_loader.get_categories = Mock(return_value={self.test_cat1, self.test_cat2})

    @patch('pathlib.Path.exists', return_value=True)
    def test_init_success(self, mock_exists):
        ui = CategorizerUI(self.config_loader, self.mock_factory)
        self.assertIsInstance(ui, CategorizerUI)

    @patch('pathlib.Path.exists', return_value=False)
    def test_init_failure(self, mock_exists):
        with self.assertRaises(FileNotFoundError):
            CategorizerUI(self.config_loader, self.mock_factory)

    @patch('pathlib.Path.exists', return_value=True)
    def test_categorize_specific(self, mock_exists):
        """ 檢查特定分類的執行次數 """
        # CategorizerUI 輸入 config_loader, logger, factory 參數，所以給他三個 mock
        mock_categorizer = Mock()
        mock_preprocess = Mock()
        # 接下來呼叫 factory.get_categorizer ，輸出是 (preprocess, categorizer)，也新增兩個假輸出給他
        self.mock_factory.get_categorizer.return_value = (mock_preprocess, mock_categorizer)

        # 把第一個分類給 CategorizerUI.categorize 執行
        ui = CategorizerUI(self.config_loader, self.mock_factory)
        ui.categorize(self.test_cat1)

        # 確認 factory.get_categorizer 和 categorizer.categorize 都只被呼叫一次
        self.mock_factory.get_categorizer.assert_called_once_with(self.test_cat1, ui.categories)
        mock_categorizer.categorize.assert_called_once_with(self.test_cat1, mock_preprocess)

    @patch('pathlib.Path.exists', return_value=True)
    def test_categorize_skip(self, mock_exists):
        """ 檢查CategorizerFactory回傳None的執行次數 """
        self.mock_factory.get_categorizer.return_value = (False, None)
        ui = CategorizerUI(self.config_loader, self.mock_factory)
        ui.categorize(self.test_cat1)

        self.mock_factory.get_categorizer.assert_called_once_with(self.test_cat1, ui.categories)
        self.mock_logger.debug.assert_called_once_with("Skip categorize category 'category1'.")

    @patch('pathlib.Path.exists', return_value=True)
    def test_categorize_all(self, mock_exists):
        """ 檢查無輸入(categorize_all)的執行次數，應等於分類數量 """
        ui = CategorizerUI(self.config_loader, self.mock_factory)
        mock_categorizer = Mock()
        mock_preprocess = Mock()
        self.mock_factory.get_categorizer.return_value = (mock_preprocess, mock_categorizer)

        ui.categorize_all()

        self.assertEqual(self.mock_factory.get_categorizer.call_count, len(self.config_loader.get_categories.return_value))
        self.assertEqual(mock_categorizer.categorize.call_count, len(self.config_loader.get_categories.return_value))

    @patch('pathlib.Path.exists', return_value=True)
    def test_categorize_all_with_empty_category(self, mock_exists):
        
        self.config_loader.get_categories.return_value = {self.test_cat1, "", self.test_cat2}
        self.mock_factory.get_categorizer.return_value = (False, None)
        ui = CategorizerUI(self.config_loader, self.mock_factory)
        ui.categorize_all()

        self.mock_logger.critical.assert_called_once()

if __name__ == '__main__':
    unittest.main()