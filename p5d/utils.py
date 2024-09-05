# Todo: Add more config check
import logging
import os
import re
import sys
import shutil
import string
from pathlib import Path
from typing import Optional, Any, Callable, Iterable
import toml

from config.config import config as user_config
from p5d.app_settings import OUTPUT_DIR
from p5d import custom_logger

HIRAGANA_START = "\u3040"
HIRAGANA_END = "\u309f"
KATAKANA_START = "\u30a0"
KATAKANA_END = "\u30ff"


class ConfigLoader:
    """
    Load and manage configuration from a file.

    :param logger: A logging instance to use for logging messages.
    :type logger: logging.Logger
    :param config_path: Path to the configuration file, defaults to "config/config.toml".
    :type config_path: str | Path, optional
    """

    def __init__(self, logger: logging.Logger, config_path: str | Path = "config/config.toml"):
        """
        Initializes the ConfigLoader with the given logger and configuration path.

        :param logger: A logging instance to use for logging messages.
        :type logger: logging.Logger
        :param config_path: Path to the configuration file, defaults to "config/config.toml".
        :type config_path: str | Path, optional
        """
        self.base_dir = Path(__file__).resolve().parents[1]
        self.log_dir = self.base_dir / OUTPUT_DIR
        self.config_path: Path = self.base_dir / config_path
        self.config = {}
        self.combined_paths: dict[str, dict[str, str]] = {}
        self.logger = logger

    def load_config(self):
        """
        Loads the configuration from the specified file and validates it.

        :raises Exception: If an error occurs while loading or validating the configuration.
        """
        if self.config_path.suffix.lower() == ".toml":
            try:
                with open(self.config_path, "r", encoding="utf-8") as file:
                    self.config = toml.load(file)
                    self.config_check()
                    self.logger.debug("Configuration loaded successfully (toml)")
            except Exception as e:
                self.logger.error(f"Failed to load configuration: {e}")
                raise
        else:
            self.config = user_config
            self.logger.debug("Configuration loaded successfully (py).")

    def config_check(self):
        """
        Checks if the configuration contains valid categories.

        This method verifies that the `categories` field in the configuration
        is populated with valid values. If any of the categories are invalid
        or missing, it logs an error message and terminates the program.

        :Raises SystemExit: Exits the program with a status code of 1 if invalid categories are found.
        """
        if not all(self.config.get("categories", [])):
            self.logger.error("TypeError: input an invalid type of category")
            sys.exit(1)

    def get_base_paths(self) -> dict[str, str]:
        """
        Retrieve the base paths for local and remote configurations.

        This method fetches the `BASE_PATHS` from the configuration and returns a dictionary
        containing the `local_path` and `remote_path`. If these paths are not specified,
        empty strings are returned.

        :return: A dictionary with `local_path` and `remote_path`.
        """
        base_paths = self.config.get("BASE_PATHS", {})
        return {
            "local_path": rf"{base_paths.get('local_path', '')}",
            "remote_path": rf"{base_paths.get('remote_path', '')}",
        }

    def get_categories(self):
        return self.config.get("categories", {})

    def get_delimiters(self):
        return self.config.get("tag_delimiter", {})

    def get_file_type(self):
        return self.config.get("file_type", {})

    def get_log_dir(self) -> Path:
        """
        Returns the initialized log directory.

        :return: A `Path` object directory.
        """
        return self.log_dir

    def get_custom(self) -> dict[str, Any]:
        """
        Retrieve the custom configuration settings.

        This method returns the value of the "custom" key from the configuration.
        If the key is not present, it returns an empty dictionary.

        :return: The custom configuration settings.
        """
        return self.config.get("custom", {})

    def get_combined_paths(self) -> dict[str, dict[str, str]]:
        """
        Retrieves the combined path for each category.

        If the path is not combined yet, execute self.combine_path to get the path.

        :returns: A dictionary with keys `local_path` and `remote_path`
        """
        if not self.combined_paths:
            self.combined_paths = self.combine_path()
        return self.combined_paths

    def combine_path(self) -> dict[str, dict[str, str]]:
        """
        Combine paths of base_paths and the categories

        Combines the `local_path` and `remote_path` for each category. 
        Used for quick access the file directory.

        :return: A two-level dictionary with the first level key is category name, \
            and the second level key is `local_path` and `remote_path`.
        """
        base_paths = self.get_base_paths()
        categories = self.get_categories()
        combined_paths = {}

        for category, data in categories.items():
            local_combined = os.path.join(base_paths["local_path"], data["local_path"])
            remote_combined = os.path.join(base_paths["remote_path"], data["remote_path"])
            combined_paths[category] = {
                "local_path": local_combined,
                "remote_path": remote_combined,
            }
        return combined_paths

    def update_config(self, options: dict[str, Any]):
        """
        Updates the configuration with the provided options.

        This method updates the `self.config` dictionary based on the given `options` dictionary.

        :Example:
        Python usage example
        args.options = {
            "local": "path/to/local",
            "remote: "path/to/remote",
            "categories": "category1, category2, category3",

            # Develope option, temporary update a dict.
            "custom_setting": {
                "Others": {
                    "tags": {
                        "nice_job": "好欸！",
                        "114514": "id_ed25519",
                    }
                }
            }
        }
        >>> config_loader.load_config()
        >>> config_loader.update_config(args.options)

        Command line input example

        - Overwrite local_path
        >>> python -m p5d -o local=/Users/leo/Pictures/downloads

        - Only process specified categories
        >>> python -m p5d -o category="Marin, IdolMaster, Others"

        - Overwrite rsync parameters. Note that the directory of rsync can not be overwrite here.
        >>> python -m p5d -o rsync="--remove-source-files -avzd"

        - Specify multiple config at once
        >>> python3 -m p5d -o local=/Users/leo/Pictures/downloads拷貝3 remote=/Users/leo/Downloads/TestInput category="Marin, IdolMaster, Others"  rsync="--remove-source-files -a"

        :param options: A dictionary of configuration options to update.
        :type options: dict[str, Any]

        :raises ValueError: If the input is not a dictionary, if an invalid key is provided,
                            or if a value for `tag_delimiter` or `file_type` is not a string.

        :raises KeyError: If a key in `options` is not valid or is missing from the configuration.
        """
        if not isinstance(options, dict):
            raise ValueError("Input must be a dictionary")

        # Define keys to write and their alias. For example, the key name should be categories, but
        # category is ok.
        base = ["local", "remote", "local_path", "remote_path"]
        cat = ["category", "categories"]
        special_key = ["custom_setting", "rsync"]
        special_key.extend(base)
        special_key.extend(cat)
        for key, value in options.items():
            if key not in self.config and key not in special_key:
                raise ValueError(f"Invalid key: {key}")

            if key in base:
                if "_path" in key:
                    key = key.replace("_path", "")
                self.config["BASE_PATHS"][f"{key}_path"] = value
                self.logger.info(f"Input option '{key}' update successfully")

            elif key in cat:
                # Preprocess input
                others_alias = ["Other", "others", "other"]
                extract_value = split_options(value)
                extract_value = [
                    "Others" if value in others_alias else value for value in extract_value
                ]

                valid_categories = set()
                for category in extract_value:
                    if category in self.config["categories"]:
                        valid_categories.add(category)
                    else:
                        self.logger.error(
                            f"Input option '{category}' not found in {self.config_path}"
                        )

                categories_to_remove = set(self.config["categories"].keys()) - valid_categories
                for category in categories_to_remove:
                    self.config["categories"].pop(category, None)
                self.logger.info(f"Input option '{key}' update successfully")

            elif key in ["tag_delimiter", "file_type"]:
                extract_value = split_options(value)
                if key == "tag_delimiter":
                    self.config[key]["front"] = extract_value[0]
                    self.config[key]["between"] = extract_value[1]
                else:
                    self.config[key] = split_options(value)
                self.logger.info(f"Input option '{key}' update successfully")

            elif key == "custom_setting":
                # Update a category (for dev)
                self.config["categories"].update(options[key])
                self.logger.info(f"Input option '{key}' update successfully")

        self.config_check()


def safe_move(src: str | Path, dst: str | Path, logger: logging.Logger) -> None:
    """
    Safely moves a file or directory from the source to the destination.
    """
    if src == dst:
        return

    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.exists():
        logger.info(f"Source '{src}' does not exist, skip this file move")
        return

    logger.debug(f"Processing source file: {src}")
    try:
        if src_path.is_file():
            if not dst_path.parent.exists():
                dst_path.parent.mkdir(parents=True)
            else:
                if dst_path.exists():
                    dst_path = generate_unique_path(dst_path)
                    logger.info(
                        f"Destination file already exists. It will be renamed to {dst_path}."
                    )
            shutil.move(str(src_path), str(dst_path))
            logger.debug(f"Successfully move file to {dst_path}.")
        elif src_path.is_dir():
            if not dst_path.parent.exists():
                dst_path.parent.mkdir(parents=True)
            else:
                if dst_path.exists():
                    logger.warning(
                        f"Destination directory '{dst_path}' already exists. It will be renamed."
                    )
                    dst_path = generate_unique_path(dst_path)
            shutil.move(str(src_path), str(dst_path))
            logger.debug(f"Successfully move folder to {dst_path}.")

    except PermissionError:
        logger.error(f"Permission denied when moving '{src}' to '{dst}'.")
    except Exception as e:
        logger.error(f"Error occurred while moving '{src}' to '{dst}': {e}")


def generate_unique_path(path: Path) -> Path:
    counter = 1
    stem = path.stem
    suffix = path.suffix if path.is_file() else ""
    parent = path.parent

    new_path = parent / f"{stem}-{counter}{suffix}"
    while new_path.exists():
        counter += 1
        new_path = parent / f"{stem}-{counter}{suffix}"

    return new_path


def traverse_dir(
    base_path: str | Path,
    file_filter: Callable[[Path], bool] = lambda _: True,
    exclude_system_files: bool = True,
    extensions: Optional[list[str]] = None,
    recursive: bool = True,
) -> Iterable[Path]:
    """
    Traverse through files in a folder and perform operations on them.

    Parameters
    ----------
    base_path
        The starting point for searching files.
    file_filter
        Function to determine if a file is valid (default is always valid).
    exclude_system_files
        Whether to skip system files (default is True).
    exclude_extensions
        List of file extensions to exclude (default is None).
    recursive
        Whether to search subdirectories recursively (default is True).

    Yields
    ------
    Path
        Files that meet all criteria.

    Examples
    --------
    >>> from pathlib import Path
    >>>
    >>> def process_file(file_path: Path):
    >>>     print(f"Processing file: {file_path}")
    >>>
    >>> # Define file filter
    >>> def is_txt_file(file_path: Path) -> bool:
    >>>     return file_path.suffix.lower() == '.txt'
    >>>
    >>> base_path = "/path/to/dir"
    >>> extensions = ["tmp", "log"]
    >>> for file_path in traverse_folder(base_path, file_filter=is_txt_file, exclude_extensions=extensions):
    >>>     process_file(file_path)
    """
    base_path = Path(base_path)
    if extensions:
        extensions = [f".{ext.lstrip('.')}" for ext in extensions]

    search_method = base_path.rglob if recursive else base_path.glob

    for file_path in search_method("*"):
        if file_path.is_file() and file_filter(file_path):
            if exclude_system_files and is_system(file_path.name):
                continue
            if extensions and file_path.suffix not in extensions:
                continue
            yield file_path


def move_all_tagged(
    base_path: Path,
    tags: dict[str, str],
    tag_delimiter: dict[str, str],
    logger: logging.Logger,
) -> None:
    """Move tagged file for all files."""
    for file_path in traverse_dir(base_path):
        file_name = file_path.stem
        file_tags = split_tags(file_name, tag_delimiter)
        target_folder = get_tagged_path(base_path, file_tags, tags)
        safe_move(file_path, target_folder / file_path.name, logger)


def get_tagged_path(base_path: Path, file_tags: list[str], target_tags: dict[str, str]) -> Path:
    """Return the target folder path based on the file tags."""
    for tag in file_tags:
        if tag in target_tags:
            target_folder = base_path / target_tags[tag]
            return target_folder
    return base_path / target_tags.get("others", "其他標籤")


def count_files(paths: dict[str, dict[str, str]], logger, work_dir: str = "remote_path") -> int:
    file_count = 0

    for _, path in paths.items():
        path = Path(path[work_dir])
        if not path.is_dir():
            logger.error(f"FileNotFoundError: '{path}' does not exist or not a directory.")
        logger.debug(f"Counting number of files of '{path}'.")

        for _ in traverse_dir(path, recursive=True):
            file_count += 1

    return file_count


## %
def is_system(file_path: str | Path) -> bool:
    """Check if the file is a common system file based on its name."""
    common_system_files = {".DS_Store", "Thumbs.db", "desktop.ini"}
    return Path(file_path).name in common_system_files


def is_empty(file_path: str | Path) -> bool:
    # Check if any entry is a file that's not a system file or a directory that is not empty
    file_path = Path(file_path)
    if not file_path.exists():
        return False
    return not any(entry.is_dir() or not is_system(entry.name) for entry in file_path.iterdir())


def is_english(character: str) -> bool:
    return character in string.ascii_letters


def is_japanese(character: str) -> bool:
    return (HIRAGANA_START <= character <= HIRAGANA_END) or (
        KATAKANA_START <= character <= KATAKANA_END
    )


def split_tags(file_name: str, tag_delimiter: dict) -> list[str]:
    front_delim = tag_delimiter.get("front", "")
    between_delim = tag_delimiter.get("between", ",")
    file_tags = file_name.split(between_delim)
    if file_tags:
        file_tags[0] = file_tags[0].split(front_delim)[-1]
    return file_tags


def split_options(value: str) -> list[str]:
    extract_value = value.split(",")
    extract_value = [value.replace(" ", "") for value in extract_value]
    return extract_value


def normalize_path(path: str | Path) -> str:
    """Convert path from Windows format to Unix format

    See https://stackoverflow.com/a/67658259/26993682
    """
    path = str(path)
    if "\\" in path:
        path = normalize_disk(path)
    return path


def normalize_disk(path_in: str) -> str:
    # r: raw string，反斜線不會被當作特殊字符處理
    # ^: 字串開始
    # (): 每個()都是一個捕獲群組
    # ([A-Z]): 捕獲一個大寫字母
    # ([A-Z]+): 捕獲任何大寫字母
    # ([a-zA-Z]+): 捕獲任何字母
    # cygdrive: cygwin 路徑格式
    # \1 引用第一個捕獲群組
    path_in = path_in.replace("\\", "/")
    path_out = re.sub(r"^([A-Z]):/", lambda m: f"/cygdrive/{m.group(1).lower()}/", path_in)
    return path_out + "/"


def color_text(text: str, color: str = "", background: str = "", style: str = "") -> str:
    """
    返回帶有 ANSI 顏色控制碼的文本。

    :param color: red, green, yellow, blue, magenta, cyan, black, white
    :param background: red, green, yellow, blue, magenta, cyan, black, white
    :param style: bold, underline, 'reverse
    :return: f-string
    """
    color_codes = {
        "black": "30",
        "red": "31",
        "green": "32",
        "yellow": "33",
        "blue": "34",
        "magenta": "35",
        "cyan": "36",
        "white": "37",
    }
    background_codes = {
        "black": "40",
        "red": "41",
        "green": "42",
        "yellow": "43",
        "blue": "44",
        "magenta": "45",
        "cyan": "46",
        "white": "47",
    }
    style_codes = {"bold": "1", "underline": "4", "reverse": "7"}

    codes = []
    if color in color_codes:
        codes.append(color_codes[color])
    if background in background_codes:
        codes.append(background_codes[background])
    if style in style_codes:
        codes.append(style_codes[style])

    start_code = "\033[" + ";".join(codes) + "m" if codes else ""
    end_code = "\033[0m" if codes else ""

    return f"{start_code}{text}{end_code}"


if __name__ == "__main__":
    custom_logger.setup_logging(logging.DEBUG)
    logger = logging.getLogger(__name__)
    config_loader = ConfigLoader(logger)
    config_loader.load_config()
    tag_delimiters = config_loader.get_delimiters()

    combined_paths = config_loader.get_combined_paths()

    for category, paths in combined_paths.items():
        print(f"{category} - Local: {paths['local_path']}, Remote: {paths['remote_path']}")

    s = r"C:\path\to\here"
    sn = normalize_path(s)
    print(s, "\n", sn)
    # safe_move(Path('struct.txt'), Path('structA.txt'))
