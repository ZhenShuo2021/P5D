# ClassifierInterface 作為介面，所有子類別需要實作 categorize, prepare_folders 以及 categorize_helper
# CategorizerUI 為使用者介面，使用者只需要輸入要分類的分類不需接觸底層架構。

# Todo: glob file type to conf.py
# Todo: IPTC/EXIF writer
import logging
import os
from abc import ABC, abstractmethod
from collections import deque
from logging import Logger
from pathlib import Path
from typing import Optional, Type, Iterator

from p5d import custom_logger
from p5d.app_settings import EN, JP, OTHER, TEMP_DIR
from p5d.utils import (
    ConfigLoader,
    traverse_dir,
    get_tagged_path,
    safe_rmtree,
    split_tags,
    safe_move,
    normalize_path,
    is_english,
    is_japanese,
    is_empty,
)


# Do NOT change unless necessary
class PathResolver:
    def __init__(self, config_loader: ConfigLoader, direct_sync: bool, logger: Logger):
        self.config_loader = config_loader
        self.categories = config_loader.get_categories()
        self.combined_paths = config_loader.get_combined_paths()
        self.tag_delimiter = config_loader.get_delimiters()
        self.direct_sync = direct_sync
        self.dst_base_type = "remote_path" if self.direct_sync else "local_path"
        self.logger = logger

    @abstractmethod
    def get_destination(self, category: str, file_path: Path) -> Path:
        pass

    @abstractmethod
    def category_iter(self, category: str) -> Iterator[tuple[Path, Path]]:
        """
        An iterator iterates all base_path for a category.

        Yields source and destination paths for each file within the specified category.

        Args:
            category:
                The processing category for categorize.

        Returns:
            iterator (Iterator[tuple[Path, Path]]):
                An iterator of tuples where each tuple contains:
                - The source file path (Path): The source path of file to be processed.
                - The destination file path (Path): The destination path of file to be processed.
        """
        pass

    def get_config(self, category: str) -> tuple[Path, dict[str, str]]:
        base_path = Path(self.combined_paths[category]["local_path"])
        user_tags = self.categories[category].get("tags", "")
        return base_path, user_tags


class FilenamePathResolver(PathResolver):
    def get_destination(self, category: str, file_path: Path) -> Path:
        base_path = Path(self.combined_paths[category][self.dst_base_type])
        first_char = file_path.name[0]
        if is_english(first_char):
            folder_name = EN
        elif is_japanese(first_char):
            folder_name = JP
        else:
            folder_name = OTHER
        return base_path / folder_name / file_path.name

    def category_iter(self, category: str) -> Iterator[tuple[Path, Path]]:
        base_path, _ = self.get_config(category)
        for file_src in traverse_dir(base_path.parent):
            file_dst = self.get_destination(category, file_src)
            yield file_src, file_dst


class CategoryPathResolver(PathResolver):
    def get_destination(self, category: str, file_path: Path) -> Path:
        user_tags = self.categories[category].get("tags", "")
        base_path = Path(self.combined_paths[category][self.dst_base_type])
        file_tags = split_tags(str(file_path), self.tag_delimiter)
        return get_tagged_path(base_path, file_tags, user_tags) / file_path.name

    def category_iter(self, category: str) -> Iterator[tuple[Path, Path]]:
        base_path, _ = self.get_config(category)
        if category == "Others":
            base_path = base_path.parent
        for file_src in traverse_dir(base_path):
            file_dst = self.get_destination(category, file_src)
            yield file_src, file_dst


class ChildPathResolver(PathResolver):
    def get_destinations(self, category: str, file_path: Path) -> Path:
        user_tags = self.categories[category].get("tags", "")
        base_path = Path(self.combined_paths[category][self.dst_base_type])
        file_tags = split_tags(str(file_path), self.tag_delimiter)
        return get_tagged_path(base_path, file_tags, user_tags) / file_path.name

    def category_iter(self, category: str) -> Iterator[tuple[Path, Path]]:
        base_path, _ = self.get_config(category)
        child_paths = [
            base_path.parent / child for child in self.categories[category]["children"]
        ]
        for child_path in child_paths:
            for file_src in traverse_dir(child_path):
                destinations = self.get_destinations(category, file_src)
                yield file_src, destinations
            safe_rmtree(child_path)


class SimplePathResolver(PathResolver):
    def get_destinations(self, category: str, file_path: Path) -> Path:
        base_path = Path(self.combined_paths[category][self.dst_base_type])
        if self.direct_sync:
            file_dst = base_path / file_path.name
        else:
            file_dst = file_path

        return file_dst

    def category_iter(self, category: str) -> Iterator[tuple[Path, Path]]:
        base_path = Path(self.combined_paths[category]["local_path"])
        for file_src in traverse_dir(base_path):
            yield file_src, self.get_destinations(category, file_src)


class ResolverAdapter:
    def __init__(self, config_loader: ConfigLoader, direct_sync: bool, logger: Logger):
        self.config_loader = config_loader
        self.direct_sync = direct_sync
        self.logger = logger
        self.resolver_classes: dict[str, Type[PathResolver]] = {
            "category": CategoryPathResolver,
            "child": ChildPathResolver,
            "filename": FilenamePathResolver,
            "simple": SimplePathResolver,
        }
        self.resolver_queue = deque(maxlen=2)
        self.resolver_cache: dict[str, PathResolver] = {}

    def get_resolver(
        self, category: str, categories: dict[str, dict[str, str]]
    ) -> PathResolver:
        if "children" in categories[category]:
            resolver_name = "child"
        elif "tags" in categories[category]:
            resolver_name = "category"
        elif category == "Others":
            resolver_name = "filename"
        else:
            resolver_name = "simple"

        self.logger.debug(
            f"Processing '{category}' with path resolver '{resolver_name}'"
        )

        if resolver_name in self.resolver_cache:
            return self.resolver_cache[resolver_name]

        new_resolver = self.resolver_classes[resolver_name](
            self.config_loader, self.direct_sync, self.logger
        )

        if len(self.resolver_queue) == self.resolver_queue.maxlen:
            oldest_resolver_name = self.resolver_queue.popleft()
            del self.resolver_cache[oldest_resolver_name]

        self.resolver_queue.append(resolver_name)
        self.resolver_cache[resolver_name] = new_resolver
        return new_resolver


def categorize_files(config_loader: ConfigLoader, direct_sync: bool, logger: Logger):
    categories = config_loader.get_categories()
    adapter = ResolverAdapter(config_loader, direct_sync, logger)
    mapping_file = {}
    for category in categories:
        path_resolver = adapter.get_resolver(category, categories)
        for file_src, file_dst in path_resolver.category_iter(category):
            if direct_sync:
                mapping_file = add_to_sync(
                    mapping_file, str(file_src), str(file_dst.parent)
                )
            else:
                safe_move(file_src, file_dst, logger)

    if direct_sync:
        temp_dir_abs = Path(config_loader.base_dir) / TEMP_DIR
        temp_dir_abs.mkdir(exist_ok=True, parents=True)
        write_mapping(mapping_file, str(temp_dir_abs / "mapping.txt"))


def add_to_sync(
    sync_map: dict[str, list[str]], file_path: str, destination: str
) -> dict[str, list[str]]:
    if destination not in sync_map:
        sync_map[destination] = []
    sync_map[destination].append(file_path)
    return sync_map


def write_mapping(mapping: dict[str, list[str]], file_path: str) -> None:
    with open(file_path, "w", encoding="utf-8") as f:
        for file_dst, file_srcs in mapping.items():
            f.write(f"[key]{file_dst}\n")
            for file_src in file_srcs:
                f.write(f"[value]{normalize_path(file_src).rstrip("/")}\n")


def main():
    custom_logger.setup_logging(logging.DEBUG)
    logger = logging.getLogger(__name__)
    config_loader = ConfigLoader(logger)
    config_loader.load_config()

    categorize_files(config_loader, False, logger)
    # Initialize categorizer
    # file_categorizer = CategorizerUI(config_loader, logger)

    # # Start categorizing all categories
    # file_categorizer.categorize()

    # Or categorize specified category
    # categories = list(config_loader.get_categories())
    # file_categorizer.categorize(categories[-1])   # categorize the last category


if __name__ == "__main__":
    main()
