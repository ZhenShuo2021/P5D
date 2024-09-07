import random
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

from p5d.app_settings import EN, JP, OTHER
from p5d.utils import safe_move, safe_rmtree
from p5d.categorizer import (
    FilenamePathResolver,
    CategoryPathResolver,
    ChildPathResolver,
    SimplePathResolver,
    ResolverAdapter,
)
from tests.test_base import TestBase, TEST_LOCAL, TEST_REMOTE


class TestResolverAdapter(TestBase):
    def setUp(self):
        super().setUp()
        self.direct_sync = True
        self.adapter = ResolverAdapter(self.config_loader, self.direct_sync, self.mock_logger)

    def test_get_resolver_child(self):
        categories = self.config_loader.get_categories()
        category_child = {}
        category_child = [k for k, v in categories.items() if "children" in v]
        category_child = category_child[0]
        resolver = self.adapter.get_resolver(category_child, categories)
        self.assertIsInstance(resolver, ChildPathResolver)
        self.mock_logger.debug.assert_called_with(
            f"Processing '{category_child}' with path resolver 'child'"
        )

    def test_get_resolver_category(self):
        categories = self.config_loader.get_categories()
        category_tags = [k for k, v in categories.items() if "tags" in v]
        category_tag = [cat for cat in category_tags if "children" not in categories[cat]][0]
        resolver = self.adapter.get_resolver(category_tag, categories)
        self.assertIsInstance(resolver, CategoryPathResolver)
        self.mock_logger.debug.assert_called_with(
            f"Processing '{category_tag}' with path resolver 'category'"
        )

    def test_get_resolver_root(self):
        categories = self.config_loader.get_categories()
        category = "Others"
        resolver = self.adapter.get_resolver(category, categories)
        self.assertIsInstance(resolver, FilenamePathResolver)
        self.mock_logger.debug.assert_called_with(
            f"Processing '{category}' with path resolver 'filename'"
        )

    def test_get_resolver_simple(self):
        categories = self.config_loader.get_categories()
        category_simple = [k for k, v in categories.items() if "tags" not in v][0]
        resolver = self.adapter.get_resolver(category_simple, categories)
        self.assertIsInstance(resolver, SimplePathResolver)
        self.mock_logger.debug.assert_called_with(
            f"Processing '{category_simple}' with path resolver 'simple'"
        )

    def test_resolver_queue_eviction(self):
        self.adapter.resolver_cache.clear()
        categories = self.config_loader.get_categories()
        cat1 = "BlueArchive"  # resolver_name = "category"
        cat2 = "IdolMaster"  # resolver_name = "child"
        cat3 = "Others"  # resolver_name = "filename"
        self.adapter.get_resolver(cat1, categories)
        self.adapter.get_resolver(cat2, categories)
        self.adapter.get_resolver(cat3, categories)

        # pop resolver_name = "category"
        self.assertNotIn("category", self.adapter.resolver_cache)


class TestFilenamePathResolver(TestBase):
    def setUp(self):
        super().setUp()
        self.resolver = FilenamePathResolver(self.config_loader, False, self.mock_logger)

    def tearDown(self):
        super().tearDownTestFile()

    def test_categorize(self):
        fn = [
            "ベッセルイン,tag1,notag1,tag2.jpg",
            "Never_loses,tag4,notag1,tag5.jpg",
            "70、80、90年代老音響討論交流區,notag,notag,notag.jpg",
            "幸永,notag,notag,notag.jpg",
        ]
        cat_dir = Path(self.config_loader.get_combined_paths()["Others"]["local_path"])
        cat_dir.mkdir(parents=True, exist_ok=True)
        for filename in fn:
            file_path = cat_dir.parent / filename
            with open(file_path, "w") as f:
                f.write("test")

        for file_src, file_dst in self.resolver.category_iter("Others"):
            safe_move(file_src, file_dst, self.mock_logger)

        self.assertTrue((cat_dir / JP / fn[0]).exists())
        self.assertTrue((cat_dir / EN / fn[1]).exists())
        self.assertTrue((cat_dir / OTHER / fn[2]).exists())
        self.assertTrue((cat_dir / OTHER / fn[3]).exists())


class TestCategoryPathResolver(TestBase):
    def setUp(self):
        super().setUp()
        self.resolver = CategoryPathResolver(self.config_loader, False, self.mock_logger)

    def tearDown(self):
        super().tearDownTestFile()

    def test_categorize(self):
        cat = "BlueArchive"
        cat_dir = Path(self.config_loader.get_combined_paths()[cat]["local_path"])
        cat_dir.mkdir(parents=True, exist_ok=True)

        fn = [
            "file1,一之瀨亞絲娜(限定),NoTag1,NoTag2.jpg",
            "file2,亞絲娜,NoTag1,NoTag2.jpg",
            "file3,调月莉音,notag,notag.jpg",
        ]

        for filename in fn:
            file_path = cat_dir / filename
            with open(file_path, "w") as f:
                f.write("test")

        for file_src, file_dst in self.resolver.category_iter(cat):
            safe_move(file_src, file_dst, self.mock_logger)

        # String is value of the given tag key.
        self.assertTrue((cat_dir / "一之瀬アスナ" / fn[0]).exists())
        self.assertTrue((cat_dir / "一之瀬アスナ" / fn[1]).exists())
        self.assertTrue((cat_dir / "調月リオ" / fn[2]).exists())


class TestChildPathResolver(TestBase):
    def setUp(self):
        super().setUp()
        self.resolver = ChildPathResolver(self.config_loader, False, self.mock_logger)

    def tearDown(self):
        super().tearDownTestFile()

    def test_categorize(self):
        # Files of category 1: with child
        cat = "IdolMaster"
        cat_dir = Path(self.config_loader.get_combined_paths()[cat]["local_path"])
        cat_dir.mkdir(parents=True, exist_ok=True)
        child_list = self.config_loader.get_categories()[cat]["children"]

        fn = [
            "file1,黛冬優子,NoTag1,NoTag2.jpg",
            "file2,NoTag1,桑山千雪,樋口円香.jpg",
            "file3,NoTag1,NoTag2,NoTag3.jpg",
        ]

        for filename in fn:
            random_child = random.choice(child_list)
            file_dir = cat_dir.parent / random_child
            file_dir.mkdir(parents=True, exist_ok=True)
            file_path = file_dir / filename
            with open(file_path, "w") as f:
                f.write("test")

        for file_src, file_dst in self.resolver.category_iter(cat):
            safe_move(file_src, file_dst, self.mock_logger)

        # String is value of the given tag key.
        self.assertTrue((cat_dir / "黛冬優子" / fn[0]).exists())
        self.assertTrue((cat_dir / "桑山千雪" / fn[1]).exists())
        self.assertTrue((cat_dir / "其他標籤" / fn[2]).exists())


class TestSimplePathResolver(TestBase):
    def setUp(self):
        super().setUp()
        self.resolver = SimplePathResolver(self.config_loader, False, self.mock_logger)

    def tearDown(self):
        super().tearDownTestFile()

    def test_categorize(self):
        cat = "Marin"
        cat_dir = Path(self.config_loader.get_combined_paths()[cat]["local_path"])
        cat_dir.mkdir(parents=True, exist_ok=True)
        fn = [
            "file1,黛冬優子,NoTag1,NoTag2.jpg",
            "file2,NoTag1,桑山千雪,樋口円香.jpg",
            "file3,NoTag1,NoTag2,NoTag3.jpg",
        ]

        for filename in fn:
            file_path = cat_dir / filename
            with open(file_path, "w") as f:
                f.write("test")

        for file_src, file_dst in self.resolver.category_iter(cat):
            safe_move(file_src, file_dst, self.mock_logger)

        self.assertTrue((cat_dir / fn[0]).exists())
        self.assertTrue((cat_dir / fn[1]).exists())
        self.assertTrue((cat_dir / fn[2]).exists())


if __name__ == "__main__":
    unittest.main()
