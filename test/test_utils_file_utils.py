import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open

from src.utils.file_utils import ConfigLoader

class ConfigLoaderTestBase(unittest.TestCase):
    def setUp(self):
        self.mock_logger = Mock()
        self.config_loader = ConfigLoader(self.mock_logger)
        self.config_loader.config = {
            'BASE_PATHS': {'local_path': '/local', 'remote_path': '/remote'},
            'categories': {
                'cat1': {'local_path': 'cat1_local', 'remote_path': 'cat1_remote'},
                'cat2': {'local_path': 'cat2_local', 'remote_path': 'cat2_remote'}
            },
            'tag_delimiter': {'front': "{}_", 'between': ','},
            'file_type': ['a', 'b', 'c']
        }

    def tearDown(self):
        pass

class TestConfigLoader(ConfigLoaderTestBase):
    def test_init(self):
        self.assertIsInstance(self.config_loader.base_dir, str)
        self.assertIsInstance(self.config_loader.log_dir, Path)
        self.assertTrue(self.config_loader.config_path.endswith('config/config.toml'))
        self.assertEqual(self.config_loader.combined_paths, {})
        self.assertEqual(self.config_loader.logger, self.mock_logger)

    @patch('builtins.open', new_callable=mock_open, read_data='[TEST]\nkey = "value"')
    @patch('toml.load')
    def test_load_config(self, mock_toml_load, mock_file):
        mock_toml_load.return_value = {'TEST': {'key': 'value'}}
        self.config_loader.load_config()
        mock_toml_load.assert_called_once()
        self.assertEqual(self.config_loader.config, {'TEST': {'key': 'value'}})
        self.mock_logger.debug.assert_called_once_with("Configuration loaded successfully.")

    def test_get_base_paths(self):
        self.assertEqual(self.config_loader.get_base_paths(), {'local_path': '/local', 'remote_path': '/remote'})

    def test_get_categories(self):
        expected = {
            'cat1': {'local_path': 'cat1_local', 'remote_path': 'cat1_remote'},
            'cat2': {'local_path': 'cat2_local', 'remote_path': 'cat2_remote'}
        }
        self.assertEqual(self.config_loader.get_categories(), expected)

    def test_get_delimiters(self):
        self.assertEqual(self.config_loader.get_delimiters(), {'front': "{}_", 'between': ','})

    def test_get_file_type(self):
        self.assertEqual(self.config_loader.get_file_type(), ['a', 'b', 'c'])

    def test_get_combined_paths_empty(self):
        self.config_loader.combined_paths = {}
        with patch.object(self.config_loader, 'combine_path') as mock_combine:
            mock_combine.return_value = {'test': 'path'}
            result = self.config_loader.get_combined_paths()
        self.assertEqual(result, {'test': 'path'})
        mock_combine.assert_called_once()

    def test_get_combined_paths_non_empty(self):
        self.config_loader.combined_paths = {'test': 'path'}
        result = self.config_loader.get_combined_paths()
        self.assertEqual(result, {'test': 'path'})

    def test_combine_path(self):
        expected = {
            'cat1': {'local_path': '/local/cat1_local', 'remote_path': '/remote/cat1_remote'},
            'cat2': {'local_path': '/local/cat2_local', 'remote_path': '/remote/cat2_remote'}
        }
        self.assertEqual(self.config_loader.combine_path(), expected)

    def test_update_config_valid(self):
        options = {'local': '/new', 'category': 'cat1,cat2'}
        self.config_loader.update_config(options)
        self.assertEqual(self.config_loader.config['BASE_PATHS']['local_path'], '/new')
        self.assertIn('cat1', self.config_loader.config['categories'])
        self.assertIn('cat2', self.config_loader.config['categories'])

    def test_update_config_invalid_key(self):
        with self.assertRaises(ValueError):
            self.config_loader.update_config({'invalid_key': 'value'})

    def test_update_config_invalid_type(self):
        with self.assertRaises(ValueError):
            self.config_loader.update_config('not a dict')

    def test_update_config_tag_delimiter(self):
        self.config_loader.update_config({'tag_delimiter': 'new'})
        self.assertEqual(self.config_loader.config['tag_delimiter'], 'new')

    def test_update_config_file_type(self):
        self.config_loader.update_config({'file_type': 'new'})
        self.assertEqual(self.config_loader.config['file_type'], 'new')


if __name__ == '__main__':
    unittest.main()