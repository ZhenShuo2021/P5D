# CategorizerInterface 作為介面，所有子類別需要實作 categorize, prepare_folders 以及 categorize_helper
# CategorizerUI 為使用者介面，使用者只需要輸入要分類的分類不需接觸底層架構。

# Todo: glob file type to conf.py
# Todo: IPTC/EXIF writer
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from src import app_settings, custom_logger
from src.utils.file_utils import ConfigLoader, batch_move, move_all_tagged, safe_move
from src.utils.string_utils import is_english, is_japanese, is_system


# Do NOT change unless necessary
class CategorizerInterface(ABC):
    OTHERS_NAME = app_settings.OTHERS_NAME

    def __init__(self, config_loader: ConfigLoader, logger: logging.Logger):
        """Abstract base class for categorizers.

        Args:
          config_loader: Instance of ConfigLoader to load configuration settings.
          logger: Instance of LogManager to handle logging.
        """
        self.config_loader = config_loader
        self.categorizes = config_loader.get_categories()
        self.combined_paths = config_loader.get_combined_paths()
        self.tag_delimiter = config_loader.get_delimiters()
        self.logger = logger

    @abstractmethod
    def categorize(self, category: str, preprocess: bool) -> None:
        """Main categorize function."""
        pass

    @abstractmethod
    def prepare_folders(self, base_path: Path, tags: dict[str, str]) -> None:
        """Preprocessing for folders. For example, create an 'other' folder."""
        pass

    @abstractmethod
    def categorize_helper(self, base_path: Path, tags: dict[str, str]) -> None:
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
        for category in self.categories:
            if not category:
                self.logger.critical(
                    f"Category '{category}' not found, continue to prevent infinite loop."
                )
                continue
            self.categorize(category)


class TaggedCategorizer(CategorizerInterface):
    def categorize(self, category: str, preprocess: bool) -> None:
        base_path = Path(self.combined_paths.get(category, {}).get("local_path", ""))
        tags = self.categorizes.get(category).get("tags")
        if preprocess:
            if category == "Others":
                batch_move(self.logger, base_path, child_folders=[base_path.parent])
            else:
                batch_move(
                    self.logger,
                    base_path,
                    child_folders=self.categorizes.get(category).get("children"),
                )

        self.prepare_folders(base_path, tags)
        self.categorize_helper(base_path, tags)

    def prepare_folders(self, base_path: Path, tags: dict[str, str]) -> None:
        self.other_path = base_path / tags.get(self.OTHERS_NAME, "others")
        self.other_path.mkdir(parents=True, exist_ok=True)

    def categorize_helper(self, base_path: Path, tags: dict[str, str]) -> None:
        move_all_tagged(base_path, self.other_path, tags, self.tag_delimiter, self.logger)


class UnTaggedCategorizer(CategorizerInterface):
    EN = app_settings.EN
    JP = app_settings.JP
    Other = app_settings.Other
    """Categorize files that are not in any category.

    By default, it categorizes files based on their names.
    If the key "tags" exists, the categorization method is essentially the same as in SeriesCategorizer.
    """

    def categorize(self, category: str, preprocess: bool) -> None:
        base_path = Path(self.combined_paths.get(category, {}).get("local_path", ""))
        tags = self.categorizes.get(category).get("tags")
        if preprocess:
            # For files doesn't belong to any category, preprocess is always true.
            pass

        if tags is not None:
            # Categorize files with tags if key "tags" exist.
            self.other_path = base_path / tags.get(self.OTHERS_NAME, "其他標籤")
            self.other_path.mkdir(exist_ok=True)
            move_all_tagged(
                base_path.parent, self.other_path, tags, self.tag_delimiter, self.logger
            )
        else:
            # If key "tags" not exist, categorize with categorize_helper
            self.prepare_folders(base_path, tags)
            self.categorize_helper(base_path, tags)

    def prepare_folders(self, base_path: Path, tags: dict[str, str]) -> None:
        self.folders = {
            "EN": base_path / self.EN,
            "JP": base_path / self.JP,
            "Other": base_path / self.Other,
        }
        for folder in self.folders.values():
            if not folder.is_dir():
                folder.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Creates folder '{folder}'")

    def categorize_helper(self, base_path: Path, tags: dict[str, str] | None = None) -> None:
        for file_path in base_path.parent.iterdir():
            if file_path.is_file() and not is_system(file_path.name):
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

    def prepare_folders(self, base_path: Path, tags: dict[str, str]) -> None:
        pass

    def categorize_helper(self, base_path: Path, tags: dict[str, str]) -> None:
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
