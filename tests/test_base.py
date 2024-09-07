import platform
import shutil
import unittest
from pathlib import Path

from unittest.mock import MagicMock
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
        self.config_loader.load_config()
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
        self.config_loader.update_config(self.file_base)
        self.config_loader.update_config(self.categories_path)

    def tearDown(self):
        self.mock_logger.reset_mock()

    def tearDownTestFile(self):
        safe_rmtree(self.root_dir / TEST_LOCAL)


def safe_rmtree(directory: Path) -> None:
    """Delete folder if not .py file inside. Comes from deleting full project folder accidentally..."""
    if not any(file.suffix == ".py" for file in directory.glob("**/*")):
        shutil.rmtree(directory)
