import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch, call

from tests.test_base import TestBase, TEST_LOCAL, TEST_REMOTE


class TestConfigLoader(TestBase):
    def setUp(self):
        super().setUp()

    @patch("builtins.open", new_callable=mock_open, read_data='[TEST]\nkey = "value"')
    @patch("toml.load")
    def test_load_config(self, mock_toml_load, mock_file):
        mock_toml_load.return_value = {"TEST": {"key": "value"}}
        self.config_loader.load_config()
        mock_toml_load.assert_called_once()
        self.assertEqual(self.config_loader.config, {"TEST": {"key": "value"}})

    def test_load_debug(self):
        expected_calls = [call("Configuration loaded successfully")]

        self.mock_logger.debug.assert_has_calls(expected_calls)
        self.assertEqual(self.mock_logger.debug.call_count, 1)

    def test_get_base_paths(self):
        self.assertEqual(
            self.config_loader.get_base_paths(), self.config_loader.config["BASE_PATHS"]
        )

    def test_get_categories(self):
        self.assertEqual(
            self.config_loader.get_categories(), self.config_loader.config["categories"]
        )

    def test_get_delimiters(self):
        self.assertEqual(
            self.config_loader.get_delimiters(), self.config_loader.config["tag_delimiter"]
        )

    def test_get_file_type(self):
        self.assertEqual(self.config_loader.get_file_type(), {"type": ["jpg", "png", "webm"]})

    def test_combine_path(self):
        expected = {
            "BlueArchive": {
                "local_path": str(self.root_dir / Path(TEST_LOCAL) / "ブルーアーカイブ"),
                "remote_path": str(self.root_dir / Path(TEST_REMOTE) / "BlueArchive"),
            },
            "IdolMaster": {
                "local_path": str(self.root_dir / Path(TEST_LOCAL) / "IdolMaster"),
                "remote_path": str(self.root_dir / Path(TEST_REMOTE) / "IdolMaster"),
            },
            "Marin": {
                "local_path": str(self.root_dir / Path(TEST_LOCAL) / "喜多川海夢"),
                "remote_path": str(self.root_dir / Path(TEST_REMOTE) / "others" / "喜多川海夢"),
            },
            "Others": {
                "local_path": str(self.root_dir / Path(TEST_LOCAL) / "others"),
                "remote_path": str(self.root_dir / Path(TEST_REMOTE) / "others" / "雜圖"),
            },
        }
        self.assertEqual(self.config_loader.combine_path(), expected)

    def test_update_config_valid(self):
        options = {"local": "/new", "category": "Others, IdolMaster"}
        self.config_loader.update_config(options)
        self.assertEqual(self.config_loader.config["BASE_PATHS"]["local_path"], "/new")
        self.assertIn("IdolMaster", self.config_loader.config["categories"])
        self.assertIn("Others", self.config_loader.config["categories"])
        self.assertNotIn("Marin", self.config_loader.config["categories"])
        self.assertNotIn("BlueArchive", self.config_loader.config["categories"])

    def test_update_config_invalid_key(self):
        with self.assertRaises(ValueError):
            self.config_loader.update_config({"invalid_key": "value"})

    def test_update_config_invalid_type(self):
        with self.assertRaises(ValueError):
            self.config_loader.update_config("not a dict")  # type: ignore

    def test_update_config_tag_delimiter(self):
        self.config_loader.update_config({"tag_delimiter": "new1, new2 "})
        self.assertEqual(
            self.config_loader.config["tag_delimiter"], {"front": "new1", "between": "new2"}
        )

    def test_update_config_file_type(self):
        self.config_loader.update_config({"file_type": "new1, new2, new3"})
        self.assertEqual(self.config_loader.config["file_type"], ["new1", "new2", "new3"])


if __name__ == "__main__":
    unittest.main()
