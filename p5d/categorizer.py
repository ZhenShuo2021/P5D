# CategorizerInterface 作為介面，所有子類別需要實作 categorize, prepare_folders 以及 categorize_helper
# CategorizerUI 為使用者介面，使用者只需要輸入要分類的分類不需接觸底層架構。

# Todo: glob file type to conf.py
# Todo: IPTC/EXIF writer
import logging
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from p5d import custom_logger
from p5d.app_settings import OTHERS_NAME, EN, JP, OTHER
from p5d.utils import (
    ConfigLoader,
    move_all_tagged,
    traverse_dir,
    safe_move,
    is_english,
    is_japanese,
    is_empty,
)


# Do NOT change unless necessary
class CategorizerInterface(ABC):
    OTHERS_NAME = OTHERS_NAME

    def __init__(self, config_loader: ConfigLoader, logger: logging.Logger):
        """Abstract base class for categorizers.

        Args:
          config_loader: Instance of ConfigLoader to load configuration settings.
          logger: Instance of LogManager to handle logging.
        """
        self.config_loader = config_loader
        self.categories = config_loader.get_categories()
        self.combined_paths = config_loader.get_combined_paths()
        self.tag_delimiter = config_loader.get_delimiters()
        self.logger = logger

    @abstractmethod
    def categorize(self, category: str, preprocess: bool) -> None:
        """Main categorize function."""
        pass

    @abstractmethod
    def prepare_folders(self, base_path: Path, tags: Optional[dict[str, str]]) -> None:
        """Preprocessing for folders. For example, create an 'other' folder."""
        pass

    @abstractmethod
    def categorize_helper(self, base_path: Path, tags: Optional[dict[str, str]]) -> None:
        """Helper function for categorize."""
        pass


class CategorizerAdapter:
    def __init__(self, config_loader: ConfigLoader, logger: logging.Logger):
        """Factory for choosing and instantiate categorizers."""
        self.config_loader = config_loader
        self.logger = logger
        self.categorizers = {
            "series": TaggedCategorizer(config_loader, logger),
            "others": UnTaggedCategorizer(config_loader, logger),
            "custom": CustomCategorizer(config_loader, logger),
        }

    def get_categorizer(
        self, category: str, categories: dict[str, dict[str, str]]
    ) -> tuple[bool, CategorizerInterface | None]:
        # Dynamically choose the categorizer base on the key existence.
        preprocess = "children" in categories.get(category, {}) or category == "Others"
        if "children" in categories[category] or "tags" in categories[category]:
            categorizer_type = "series"
        elif category == "Others":
            categorizer_type = "others"
        elif "tags" not in categories.get(category, {}):
            categorizer_type = None
        else:
            categorizer_type = "custom"

        self.logger.debug(f"Processing category '{category}' with categorizer '{categorizer_type}'")
        return preprocess, self.categorizers.get(categorizer_type, None)  # type: ignore


class CategorizerUI:
    """UI for categorizing files."""

    def __init__(
        self,
        config_loader: ConfigLoader,
        logger: logging.Logger,
        adapter: Optional[CategorizerAdapter] = None,
    ):
        self.logger = logger
        self.config_loader = config_loader
        if not self.config_loader.config:
            self.config_loader.load_config()
        base_path_local = config_loader.get_base_paths().get("local_path", "")
        if not Path(base_path_local).exists():
            self.logger.error(f"Base path '{base_path_local}' does not exist.")
            raise FileNotFoundError(f"Base path '{base_path_local}' does not exist.")

        self.combined_paths = config_loader.get_combined_paths()
        self.categories = config_loader.get_categories()
        self.adapter = adapter if adapter is not None else CategorizerAdapter(config_loader, logger)

    def categorize(self, category: str = "") -> None:
        if not category:
            self.categorize_all()
        else:
            preprocess, categorizer = self.adapter.get_categorizer(category, self.categories)
            if not categorizer:
                self.logger.debug(f"Skip categorize category '{category}'.")
                return
            categorizer.categorize(category, preprocess)

    def categorize_all(self) -> None:
        # Tackle infinite loop in ConfigLoader
        for category in self.categories:
            self.categorize(category)


class TaggedCategorizer(CategorizerInterface):
    def categorize(self, category: str, preprocess: bool) -> None:
        base_path = Path(self.combined_paths.get(category, {}).get("local_path", ""))
        tags = self.categories.get(category).get("tags")
        if preprocess:
            self.preprocess(base_path, category)

        self.prepare_folders(base_path, tags)
        self.categorize_helper(base_path, tags)
        if self.categories.get(category).get("children"):
            for child in self.categories.get(category)["children"]:
                child_path_dst = base_path / child
                if is_empty(child_path_dst):
                    shutil.rmtree(child_path_dst)

    def prepare_folders(self, base_path: Path, tags: Optional[dict[str, str]]) -> None:
        if tags is None:
            raise ValueError("Input tag error. Should be a dict.")
        self.other_path = base_path / tags.get(self.OTHERS_NAME, "others")
        self.other_path.mkdir(parents=True, exist_ok=True)

    def categorize_helper(self, base_path: Path, tags: Optional[dict[str, str]]) -> None:
        if tags is None:
            raise ValueError("Input tag error. Should be a dict.")
        move_all_tagged(base_path, tags, self.tag_delimiter, self.logger)

    def preprocess(self, base_path: Path, category: str) -> None:
        # Move download_root/* to download/others/*
        if category == "Others":
            # The base_path of Others category is download/others/
            ext = self.config_loader.get_file_type()["type"]
            for file_path in traverse_dir(base_path.parent, recursive=False, extensions=ext):
                safe_move(str(file_path), str(base_path / file_path.name), self.logger)
        else:
            for child in self.categories.get(category)["children"]:
                child_path_src = base_path.parent / child
                child_path_dst = base_path / child
                safe_move(child_path_src, child_path_dst, self.logger)
                if is_empty(child_path_dst):
                    shutil.rmtree(child_path_dst)


class UnTaggedCategorizer(CategorizerInterface):
    EN = EN
    JP = JP
    Other = OTHER
    """Categorize files that are not in any category.

    By default, it categorizes files based on their names.
    If the key "tags" exists, the categorization method is essentially the same as in SeriesCategorizer.
    """

    def categorize(self, category: str, preprocess: bool) -> None:
        base_path = Path(self.combined_paths.get(category, {}).get("local_path", ""))

        self.prepare_folders(base_path, None)
        self.categorize_helper(base_path, None)

    def prepare_folders(self, base_path: Path, tags: Optional[dict[str, str]]) -> None:
        self.folders = {
            "EN": base_path / self.EN,
            "JP": base_path / self.JP,
            "Other": base_path / self.Other,
        }
        for folder in self.folders.values():
            if not folder.is_dir():
                folder.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Creates folder '{folder}'")

    def categorize_helper(self, base_path: Path, tags: Optional[dict[str, str]] = None) -> None:
        ext = self.config_loader.get_file_type()["type"]
        for file_path in traverse_dir(base_path.parent, recursive=False, extensions=ext):
            first_char = file_path.name[0]
            if is_english(first_char):
                folder_name = self.folders["EN"]
            elif is_japanese(first_char):
                folder_name = self.folders["JP"]
            else:
                folder_name = self.folders["Other"]
            safe_move(file_path, folder_name / file_path.name, self.logger)


class CustomCategorizer(CategorizerInterface):
    def categorize(self, category: str, preprocess: bool) -> None:
        pass

    def prepare_folders(self, base_path: Path, tags: Optional[dict[str, str]]) -> None:
        pass

    def categorize_helper(self, base_path: Path, tags: Optional[dict[str, str]]) -> None:
        pass

    def _helper_function(self) -> None:
        pass


def main():
    custom_logger.setup_logging(logging.DEBUG)
    logger = logging.getLogger(__name__)
    config_loader = ConfigLoader(logger)
    config_loader.load_config()

    # Initialize categorizer
    file_categorizer = CategorizerUI(config_loader, logger)

    # Start categorizing all categories
    file_categorizer.categorize()

    # Or categorize specified category
    # categories = list(config_loader.get_categories())
    # file_categorizer.categorize(categories[-1])   # categorize the last category


if __name__ == "__main__":
    main()
