# CategorizerInterface 作為介面，所有子類別需要實作 categorize, prepare_folders 以及 categorize_helper
# CategorizerUI 為使用者介面，使用者只需要輸入要分類的分類不需接觸底層架構。

# Todo: glob file type to conf.py
# Todo: IPTC/EXIF writer
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple, Dict, Optional

from logger import LogLevel, LogManager
from utils.file_utils import ConfigLoader, safe_move, batch_move, move_all_tagged
from utils.string_utils import is_system, is_english, is_japanese


# Do NOT change unless necessary
class CategorizerInterface(ABC):
    others_name = "others"
    EN = "EN Artist"
    JP = "JP Artist"
    Other = "Other Artist"

    def __init__(self, config_loader: ConfigLoader, logger: LogManager):
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
        """ Main categorize function. """
        pass

    @abstractmethod
    def prepare_folders(self, base_path: Path, tags: Dict[str, str]) -> None:
        """ Preprocessing for folders. For example, create an 'other' folder. """
        pass

    @abstractmethod
    def categorize_helper(self, base_path: Path, tags: Dict[str, str]) -> None:
        """ Helper function for categorize. """
        pass


class CategorizerFactory:
    def __init__(self, config_loader: ConfigLoader, logger: LogManager):
        """ Factory for choosing and instantiate categorizers. """
        self.config_loader = config_loader
        self.logger = logger
        self.categorizers = {
            "series": SeriesCategorizer(config_loader, logger),
            "others": OthersCategorizer(config_loader, logger),
            "custom": CustomCategorizer(config_loader, logger)
        }

    def get_categorizer(self, category: str, categories: Dict[str, str]) -> Tuple[bool, Optional[CategorizerInterface]]:
        # Dynamically choose the categorizer base on the key existence.
        preprocess = "children" in categories.get(category, {}) or category == "Others"
        if "children" in categories[category] or "tags" in categories[category]:
            categorizer_type = "series"
        elif category == "Others":
            categorizer_type = "others"
        elif "tags" not in categories[category]:
            categorizer_type = None
        else:
            categorizer_type = "custom"
        
        self.logger.debug(f"Processing category '{category}' with categorizer '{categorizer_type}'")
        return preprocess, self.categorizers.get(categorizer_type)


class CategorizerUI:
    def __init__(self, config_loader: ConfigLoader, logger: LogManager, factory: CategorizerFactory=None):
        """ UI for categorizing files. """
        self.logger = logger
        base_path = config_loader.get_base_paths()
        base_path_local = base_path.get("local_path")
        if not Path(base_path_local).exists():
            self.logger.error(f"Base path '{base_path_local}' does not exist.")
            raise FileNotFoundError(f"Base path '{base_path_local}' does not exist.")
        
        self.config_loader = config_loader
        self.combined_paths = config_loader.get_combined_paths()
        self.categories = config_loader.get_categories()
        self.factory = factory or CategorizerFactory(config_loader, logger)
         
    def categorize(self, category: str="") -> None:
        if not category:
            self.categorize_all()
        else:
            preprocess, categorizer = self.factory.get_categorizer(category, self.categories)
            if not categorizer:
                self.logger.debug(f"Skip categorize category '{category}'.")
                return
            categorizer.categorize(category, preprocess)
    
    def categorize_all(self) -> None:
        for category in self.categories:
            if not category:
                self.logger.critical(
                    f"Category '{category}' not found, continue to prevent infinite loop.")
                continue
            self.categorize(category)

        

class SeriesCategorizer(CategorizerInterface):
    def categorize(self, category: str, preprocess: bool) -> None:
        base_path = Path(self.combined_paths.get(category).get("local_path"))
        tags = self.categorizes.get(category).get("tags")
        if preprocess:
            batch_move(base_path, self.categorizes.get(category).get("children"))

        self.prepare_folders(base_path, tags)
        self.categorize_helper(base_path, tags)

    def prepare_folders(self, base_path: Path, tags: Dict[str, str]) -> None:
        self.other_path = base_path / tags.get(self.others_name, "others")
        self.other_path.mkdir(parents=True, exist_ok=True)

    def categorize_helper(self, base_path: Path, tags: Dict[str, str]) -> None:
        move_all_tagged(base_path, self.other_path, tags, self.tag_delimiter)


class OthersCategorizer(CategorizerInterface):
    """Categorize files that are not in any category.

    By default, it categorizes files based on their names.
    If the key "tags" exists, the categorization method is essentially the same as in SeriesCategorizer.
    """
    def categorize(self, category: str, preprocess: bool) -> None:
        base_path = Path(self.combined_paths.get(category).get("local_path"))
        tags = self.categorizes.get(category).get("tags")
        if preprocess:
            # For files doesn't belong to any category, preprocess is always true.
            pass
 
        if tags != None:
            # Categorize files with tags if key "tags" exist.
            self.other_path = base_path / tags.get(self.others_name, "others")
            self.other_path.mkdir(exist_ok=True)
            move_all_tagged(base_path.parent, self.other_path, tags, self.tag_delimiter)
        else:
            # If key "tags" not exist, categorize with categorize_helper
            self.prepare_folders(base_path, tags)
            self.categorize_helper(base_path, tags)
 
    def prepare_folders(self, base_path: Path, tags: Dict[str, str]) -> None:
        self.folders = {
            "EN": base_path / self.EN,
            "JP": base_path / self.JP,
            "Other": base_path / self.Other
        }
        for folder in self.folders.values():
            if not folder.is_dir():
                folder.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Creates folder '{folder}'")

    def categorize_helper(self, base_path: Path, tags: Dict[str, str] | None=None) -> None:
        for file_path in base_path.parent.iterdir():
            if file_path.is_file() and not is_system(file_path.name):
                first_char = file_path.name[0]
                if is_english(first_char):
                    folder_name = self.folders["EN"]
                elif is_japanese(first_char):
                    folder_name = self.folders["JP"]
                else:
                    folder_name = self.folders["Other"]
                safe_move(file_path, folder_name / file_path.name)


class CustomCategorizer(CategorizerInterface):
    def categorize(self, category: str, preprocess: bool) -> None:
        pass
    
    def prepare_folders(self, base_path: Path, tags: Dict[str, str]) -> None:
        pass

    def categorize_helper(self, base_path: Path, other_path:Path, tags: Dict[str, str]) -> None:
        pass

    def _helper_function(self) -> None:
        pass


def main():
    log_manager = LogManager(level=LogLevel.DEBUG, status="categorizer.py")
    logger = log_manager.get_logger()

    config_loader = ConfigLoader('config/config.toml')
    
    # Initialize categorizer
    file_categorizer = CategorizerUI(config_loader, logger)
    
    # Start categorizing all categories
    file_categorizer.categorize()
    
    # Or categorize specified category
    # categories = list(config_loader.get_categories())
    # file_categorizer.categorize(categories[-1])   # categorize the last category


if __name__ == "__main__":
    main()
