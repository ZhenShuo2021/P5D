import random
import unittest
from pathlib import Path

from p5d.app_settings import EN, JP, OTHER
from p5d.categorizer import categorize_files
from p5d.synchronizer import FileSyncer
from tests.test_base import TestBase, safe_rmtree, TEST_REMOTE


class TestFilenamePathResolver(TestBase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDownTestFile()
        safe_rmtree(self.root_dir / TEST_REMOTE)

    def test_direct_sync(self):
        fn1 = [
            "ベッセルイン,tag1,notag1,tag2.jpg",
            "Never_loses,tag4,notag1,tag5.jpg",
            "70、80、90年代老音響討論交流區,notag,notag,notag.jpg",
            "幸永,notag,notag,notag.jpg",
        ]
        cat1_dir = Path(self.config_loader.get_combined_paths()["Others"]["local_path"])
        cat1_remote = Path(self.config_loader.get_combined_paths()["Others"]["remote_path"])
        cat1_dir.mkdir(parents=True, exist_ok=True)
        for filename in fn1:
            file_path = cat1_dir.parent / filename
            with open(file_path, "w") as f:
                f.write("test")

        cat2 = "BlueArchive"
        cat2_dir = Path(self.config_loader.get_combined_paths()[cat2]["local_path"])
        cat2_remote = Path(self.config_loader.get_combined_paths()[cat2]["remote_path"])
        cat2_dir.mkdir(parents=True, exist_ok=True)
        fn2 = [
            "file1,一之瀨亞絲娜(限定),NoTag1,NoTag2.jpg",
            "file2,亞絲娜,NoTag1,NoTag2.jpg",
            "file3,调月莉音,notag,notag.jpg",
        ]
        for filename in fn2:
            file_path = cat2_dir / filename
            with open(file_path, "w") as f:
                f.write("test")

        cat3 = "IdolMaster"
        cat3_dir = Path(self.config_loader.get_combined_paths()[cat3]["local_path"])
        cat3_remote = Path(self.config_loader.get_combined_paths()[cat3]["remote_path"])
        cat3_dir.mkdir(parents=True, exist_ok=True)
        child_list = self.config_loader.get_categories()[cat3]["children"]
        fn3 = [
            "file1,黛冬優子,NoTag1,NoTag2.jpg",
            "file2,NoTag1,桑山千雪,樋口円香.jpg",
            "file3,NoTag1,NoTag2,NoTag3.jpg",
        ]
        for filename in fn3:
            random_child = random.choice(child_list)
            file_dir = cat3_dir.parent / random_child
            file_dir.mkdir(parents=True, exist_ok=True)
            file_path = file_dir / filename
            with open(file_path, "w") as f:
                f.write("test")

        cat4 = "Marin"
        cat4_dir = Path(self.config_loader.get_combined_paths()[cat4]["local_path"])
        cat4_remote = Path(self.config_loader.get_combined_paths()[cat4]["remote_path"])
        cat4_dir.mkdir(parents=True, exist_ok=True)
        fn4 = [
            "file1,黛冬優子,NoTag1,NoTag2.jpg",
            "file2,NoTag1,桑山千雪,樋口円香.jpg",
            "file3,NoTag1,NoTag2,NoTag3.jpg",
        ]
        for filename in fn4:
            file_path = cat4_dir / filename
            with open(file_path, "w") as f:
                f.write("test")

        categorize_files(self.config_loader, direct_sync=True, logger=self.mock_logger)
        syncer = FileSyncer(self.config_loader, self.mock_logger, direct_sync=True)
        syncer.sync_folders(None, None)

        self.assertTrue((cat1_remote / JP / fn1[0]).exists())
        self.assertTrue((cat1_remote / EN / fn1[1]).exists())
        self.assertTrue((cat1_remote / OTHER / fn1[2]).exists())
        self.assertTrue((cat1_remote / OTHER / fn1[3]).exists())

        self.assertTrue((cat2_remote / "一之瀬アスナ" / fn2[0]).exists())
        self.assertTrue((cat2_remote / "一之瀬アスナ" / fn2[1]).exists())
        self.assertTrue((cat2_remote / "調月リオ" / fn2[2]).exists())

        self.assertTrue((cat3_remote / "黛冬優子" / fn3[0]).exists())
        self.assertTrue((cat3_remote / "桑山千雪" / fn3[1]).exists())
        self.assertTrue((cat3_remote / "其他標籤" / fn3[2]).exists())

        self.assertTrue((cat4_remote / fn4[0]).exists())
        self.assertTrue((cat4_remote / fn4[1]).exists())
        self.assertTrue((cat4_remote / fn4[2]).exists())


if __name__ == "__main__":
    unittest.main()
