import os
import platform
import shutil
import unittest
from pathlib import Path

from unittest.mock import MagicMock, patch
from p5d.utils import ConfigLoader

USER_OS = platform.system()

FONT = "Microsoft YaHei" if USER_OS == "Windows" else "Arial Unicode MS"
CONFIG_FILE = "test_config.toml"
TEST_LOCAL = "test_local"
TEST_REMOTE = "test_remote"


class TestBase(unittest.TestCase):
    def setUp(self):
        self.mock_logger = MagicMock()
        self.config_path = Path(__file__).resolve().parent / CONFIG_FILE
        self.config_loader = ConfigLoader(self.mock_logger, self.config_path)
        # Variable file paths for different OSs.
        self.file_base = {
            "local_path": str(Path(__file__).resolve().parents[1] / TEST_LOCAL),
            "remote_path": str(Path(__file__).resolve().parents[1] / TEST_REMOTE),
        }
        self.categories_path = {}
        if USER_OS == "Windows":
            self.categories_path = {
                "custom_setting": {
                    "Marin": {
                        "local_path": "喜多川海夢",
                        "remote_path": "others\喜多川海夢",
                    },
                    "Others": {
                        "local_path": "others",
                        "remote_path": "others\雜圖",
                    },
                },
            }
        # ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓
        # DANGEROUS! RMTREE
        self.root_dir = Path(__file__).resolve().parents[1]
        # DANGEROUS! RMTREE
        # ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑

    def tearDown(self):
        self.mock_logger.reset_mock()


def safe_rmtree(directory: Path) -> None:
    """Delete folder if not .py file inside. Comes from deleting full project folder accidentally..."""
    if not any(file.suffix == ".py" for file in directory.rglob("*.py")):
        shutil.rmtree(directory)
    #     print(f"Deleted directory: {directory}")
    # else:
    #     print(f"Directory {directory} contains .py files and was not deleted.")
