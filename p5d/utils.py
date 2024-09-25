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

from p5d.app_settings import OUTPUT_DIR, RSYNC_TEMP_EXT, is_docker
from p5d import custom_logger

HIRAGANA_START = "\u3040"
HIRAGANA_END = "\u309f"
KATAKANA_START = "\u30a0"
KATAKANA_END = "\u30ff"


class ConfigLoader:
    """
    Load and manage configuration from a file.

    Args:
        logger (logging.Logger): A logging instance to use for logging messages.
        config_path (str | Path, optional): Path to the configuration file, defaults to "config/config.toml".
    """

    def __init__(self, logger: logging.Logger, config_path: str | Path = "config/config.toml"):
        """
        Initializes the ConfigLoader with the given logger and configuration path.

        Args:
            logger (logging.Logger): A logging instance to use for logging messages.
            config_path (str | Path, optional): Path to the configuration file, defaults to "config/config.toml".
        """
        self.base_dir = Path(__file__).resolve().parents[1]
        self.config_path: Path = self.base_dir / config_path
        self.config = {}
        self.combined_paths: dict[str, dict[str, str]] = {}
        self.logger = logger

    def load_config(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as file:
                self.config = toml.load(file)
                self.config_check()
                self.logger.debug("Configuration loaded successfully")
            if is_docker():
                self.config["BASE_PATHS"]["local_path"] = "/mnt/local_path"
                self.config["BASE_PATHS"]["remote_path"] = "/mnt/remote_path"
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise

    def config_check(self):
        """
        Checks if the configuration contains valid categories.

        Raises:
            SystemExit: Exits the program with a status code of 1 if invalid categories are found.
        """
        if not all(self.config.get("categories", [])):
            self.logger.error("TypeError: input an invalid type of category")
            sys.exit(1)

    def get_base_paths(self) -> dict[str, str]:
        """
        Return the base paths for local and remote configurations.

        Returns:
            BASE_PATHS: A dictionary with `local_path` and `remote_path`.
        """
        return self.config.get("BASE_PATHS", {})

    def get_categories(self) -> dict[str, dict]:
        return self.config.get("categories", {})

    def get_delimiters(self) -> dict[str, str]:
        return self.config.get("tag_delimiter", {})

    def get_file_type(self) -> dict[str, list[str]]:
        return self.config.get("file_type", {})

    def get_stats_dir(self) -> str:
        return self.config.get("stats_dir", "")

    def get_output_dir(self) -> Path:
        return self.base_dir / OUTPUT_DIR

    def get_custom(self) -> dict[str, Any]:
        """
        Get the custom configuration settings.

        Returns:
            dict: The custom configuration settings.
        """
        return self.config.get("custom", {})

    def get_combined_paths(self) -> dict[str, dict[str, str]]:
        """
        Get the combined path for each category.

        If the path is not combined yet, execute self.combine_path to get the path.

        Returns:
            combined_paths: A dictionary with keys `local_path` and `remote_path`
        """
        if not self.combined_paths:
            self.combined_paths = self.combine_path()
        return self.combined_paths

    def combine_path(self) -> dict[str, dict[str, str]]:
        """
        Combine paths of base_paths and the categories

        Combines the `local_path` and `remote_path` for each category.
        Used for quick access the file directory.

        Returns:
            combined_paths: A two-level dictionary.
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

        Example:
            ### Python usage example:
            >>> args.options = {
                    "local": "path/to/local",
                    "remote": "path/to/remote",
                    "categories": "category1, category2, category3",
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

            ### Command line input examples:

            Overwrite local_path:
            $ python -m p5d -o local=/Users/leo/Pictures/downloads

            Only process specified categories:
            $ python -m p5d -o category="Marin, IdolMaster, Others"

            Overwrite rsync parameters:
            $ python -m p5d -o rsync="--remove-source-files -avzd"

            Specify multiple configs at once:
            $ python3 -m p5d -o local=/Users/leo/Pictures/downloads remote=/Users/leo/Downloads/TestInput category="Marin, IdolMaster, Others" rsync="--remove-source-files -a"

        Args:
            options (dict[str, Any]): A dictionary of configuration options to update.

        Raises:
            ValueError: If the input is not a dictionary, if an invalid key is provided,
                or if a value for `tag_delimiter` or `file_type` is not a string.
            KeyError: If a key in `options` is not valid or is missing from the configuration.
        """

        if not isinstance(options, dict):
            raise ValueError("Input must be a dictionary")

        # Define keys to write and their alias. For example, the key name should be categories, but
        # category is ok.
        base = ["local", "remote", "local_path", "remote_path"]
        cat = ["category", "categories"]
        special_key = ["custom_setting", "rsync", "stats_dir"]
        special_key.extend(base)
        special_key.extend(cat)
        for key, value in options.items():
            if key not in self.config and key not in special_key:
                raise ValueError(f"Invalid key: {key}")

            if key in base:
                if "_path" in key:
                    key = key.replace("_path", "")
                self.config["BASE_PATHS"][f"{key}_path"] = value
                self.logger.info(f"Successfully update input option '{key}'")

            elif key in cat:
                # Preprocess input
                others_alias = ["Other", "others", "other"]
                extract_value = extract_opt(value)
                extract_value = [
                    "Others" if value in others_alias else value for value in extract_value
                ]

                valid_categories = set()
                for category in extract_value:
                    if category in self.config["categories"]:
                        valid_categories.add(category)
                    else:
                        self.logger.error(
                            f"Successfully update input option '{category}' not found in {self.config_path}"
                        )

                categories_to_remove = set(self.config["categories"].keys()) - valid_categories
                for category in categories_to_remove:
                    self.config["categories"].pop(category, None)
                self.logger.info(f"Successfully update input option '{key}'")

            elif key in ["tag_delimiter", "file_type"]:
                extract_value = extract_opt(value)
                if key == "tag_delimiter":
                    self.config[key]["front"] = extract_value[0]
                    self.config[key]["between"] = extract_value[1]
                else:
                    self.config[key] = extract_opt(value)
                self.logger.info(f"Successfully update input option '{key}'")

            elif key == "custom_setting":
                # Update a category (for dev)
                self.config["categories"].update(options[key])
                self.logger.info(f"Successfully update input option '{key}'")

            elif key == "rsync":
                pass

            elif key == "stats_dir":
                self.config[key] = options[key]

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


def safe_rmtree(directory: Path) -> None:
    """Delete folder if not .py file inside. Comes from deleting full project folder accidentally..."""
    if not directory.exists():
        return
    if not any(file.suffix == ".py" or not is_system(file) for file in directory.glob("**/*")):
        shutil.rmtree(directory)


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
    recursive: bool = False,
    file_filter: Callable[[Path], bool] = lambda _: True,
    extensions: Optional[list[str]] = None,
    exclude_system_files: bool = True,
) -> Iterable[Path]:
    """
    Traverse through files in a folder and perform operations on them.

    Args:
        base_path (str or Path):
            The starting point for searching files.
        file_filter (Callable[[Path], bool], optional):
            Function to determine if a file is valid. Default is a function that always returns True.
        exclude_system_files (bool, optional):
            Whether to skip system files. Default is True.
        exclude_extensions (list of str, optional):
            List of file extensions to exclude. Default is None.
        recursive (bool, optional):
            Whether to search subdirectories recursively. Default is False.

    Yields:
        Path:
            Files that meet all criteria.

    Examples:
        >>> from pathlib import Path
        >>>
        >>> def process_file(file_path: Path):
        >>>     print(f"Processing file: {file_path}")
        >>>
        >>> def is_txt_file(file_path: Path) -> bool:
        >>>     return file_path.suffix.lower() == '.txt'
        >>>
        >>> base_path = Path("/path/to/dir")
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


def get_tagged_path(category_base: Path, file_tags: list[str], target_tags: dict[str, str]) -> Path:
    """Return the target folder path based on the file tags."""
    for tag in file_tags:
        if tag in target_tags:
            target_folder = category_base / target_tags[tag]
            return target_folder
    return category_base / target_tags.get("others", "其他標籤")


def count_files(paths: dict[str, dict[str, str]], logger, stats_dir: str = "remote_path") -> int:
    file_count = 0

    for _, path in paths.items():
        path = Path(path[stats_dir])
        if not path.is_dir():
            logger.error(f"FileNotFoundError: '{path}' does not exist or not a directory.")
        logger.debug(f"Counting number of files of '{path}'.")

        for _ in traverse_dir(path, recursive=True):
            file_count += 1

    return file_count


class LogMerger:
    def __init__(self, temp_dir: Path, logger: logging.Logger):
        self.temp_dir = temp_dir
        self.logger = logger

    def merge_logs(self) -> None:
        system_log_file = self.temp_dir.parent / "p5d.log"
        rsync_log_files = [f for f in os.listdir(self.temp_dir) if f.endswith(RSYNC_TEMP_EXT)]

        if not rsync_log_files:
            self.logger.debug("No rsync log files found in the directory.")
            return

        system_log_content = self._merge_system(system_log_file)
        rsync_log_content = self._merge_rsync(rsync_log_files)
        merged_content = system_log_content + rsync_log_content

        with open(system_log_file, "w", encoding="utf-8") as output:
            output.write(merged_content)

        self.logger.debug(f"System log and rsync logs have been merged into '{system_log_file}'")

    def _merge_rsync(self, log_files: list[str]) -> str:
        merged_content = ""
        delimiter = "=" * 20
        for log_file in log_files:
            file_path = self.temp_dir / log_file
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                merged_content += f"\n{delimiter}[{log_file}]{delimiter}\n{content}"
            os.remove(file_path)
        return merged_content

    def _merge_system(self, system_log_path: Path) -> str:
        if not system_log_path.exists():
            self.logger.debug(f"System log file '{system_log_path}' not found.")
            return ""

        with open(system_log_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.logger.debug(f"System log '{system_log_path}' has been read successfully.")
        return content


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


def extract_opt(opt_str: str) -> list[str]:
    if not opt_str:
        return []
    if opt_str.startswith("-"):
        return re.split(r"\s+", opt_str.strip())
    else:
        opt_list = opt_str.split(",")
        opt_list = [value.replace(" ", "") for value in opt_list]
    return opt_list


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
