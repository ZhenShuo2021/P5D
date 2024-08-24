
# Todo: get_tags in ConfigLoader
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List

import toml

from utils.string_utils import is_system, is_empty, split_tags
from logger import LogLevel, LogManager, logger
log_manager = LogManager(level=LogLevel.INFO, status="file_utils.py")
logger = log_manager.get_logger()


def safe_move(src: str | Path, dst: str | Path) -> None:
    if src == dst:
        return

    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.exists():
        logger.error(f"Source '{src}' does not exist.")
        raise FileNotFoundError(f"Source '{src}' does not exist.")

    logger.debug(f"Processing source file: {src}")
    try:
        if src_path.is_file():
            if dst_path.exists():
                dst_path = generate_unique_path(dst_path)
                logger.info(f"Destination file already exists. It will be renamed to {dst_path}.")
            shutil.move(str(src_path), str(dst_path))
            logger.debug(f"Successfully move file to {dst_path.parent}.")
        elif src_path.is_dir():
            if dst_path.exists():
                logger.warning(f"Destination directory '{dst_path}' already exists. It will be renamed.")
                dst_path = generate_unique_path(dst_path)
            shutil.move(str(src_path), str(dst_path))
            logger.debug(f"Successfully move folder to {dst_path.parent}.")

    except PermissionError:
        logger.error(f"Permission denied when moving '{src}' to '{dst}'.")
    except Exception as e:
        logger.error(f"Error occurred while moving '{src}' to '{dst}': {e}")


def safe_move_dir(src_folder: Path, dst_folder: Path) -> None:
    """Move the files in first level of src_folder to the dst_folder"""
    for file_path in src_folder.iterdir():
        if file_path.is_file() and not is_system(file_path.name):
            safe_move(file_path, dst_folder / file_path.name)


def batch_move(parent_folder: Path, child_folders: List[str] = []) -> None:
    """Move all files in "child_folders" to "parent_folder". 

    By default, the child and the parent folders are in the same level:
        ├── parent
        ├── child_A
        ├── child_B
        └── child_C
    If child_folders is an existing dir, directory move it to the parent folder.
    """
    parent_folder.mkdir(exist_ok=True)
    base_folder = parent_folder.parent

    if isinstance(child_folders, list):
        for child_name in child_folders:
            child_path = base_folder / child_name
            if child_path.is_dir():
                safe_move_dir(child_path, parent_folder)
                if is_empty(child_path):
                    shutil.rmtree(str(child_path))
                    logger.info(f"Deleting empty child folder '{child_path}'.")
                else:
                    logger.debug(f"'{child_path}' is not empty; deleting process canceled.")
            else:
                logger.debug(f"Child folder {child_path} not exist.")
    
    elif isinstance(child_folders, Path) and child_folders.is_dir():
        safe_move_dir(base_folder, parent_folder)


def move_tagged(base_path: Path, other_path: Path, file_path: Path, file_tags: List[str], tags: Dict[str, str]) -> None:
    """Move tagged file for a single file. Search the first file tag in tags and move it to target_folder.

    base_path: File destination. In configuration: BASE_PATHS / CATEGORIES.BlueArchive.remote
    other_path: File destination for which is not in any tag.
    file_path: File source.
    file_tags: Tags extract from file name.
    tags: Special tags for file name. In configuration: CATEGORIES.BlueArchive.tags
    """
    target_folder = get_tagged_path(base_path, file_tags, tags)
    if target_folder:
        safe_move(file_path, target_folder / file_path.name)
    else:
        safe_move(file_path, other_path / file_path.name)


def get_tagged_path(base_path: Path, file_tags: List[str], tags: Dict[str, str]) -> Path:
    """ Return the target folder path based on the file tags. """
    for tag in file_tags:
        if tag in tags:
            target_folder = Path(base_path) / tags[tag]
            target_folder.mkdir(parents=True, exist_ok=True)
            return target_folder
    return None

def move_all_tagged(base_path: Path, other_path: Path, tags: Dict[str, str], tag_delimiter: dict) -> None:
    """Move tagged file for all files."""
    for file_path in base_path.rglob('*'):
        if file_path.is_file() and not is_system(file_path.name):
            file_name = file_path.stem
            file_tags = split_tags(file_name, tag_delimiter)
            move_tagged(base_path, other_path, file_path, file_tags, tags)


def generate_unique_path(path: Path) -> Path:
    counter = 1
    stem = path.stem
    suffix = path.suffix if path.is_file() else ''
    parent = path.parent

    new_path = parent / f"{stem}-{counter}{suffix}"
    while new_path.exists():
        counter += 1
        new_path = parent / f"{stem}-{counter}{suffix}"

    return new_path


def count_files(paths: Dict[str, Path], dir: str="remote_path") -> Dict[str, int]:
    file_count = 0
    for _, path in paths.items():
        path = Path(path[dir])
        if not path.is_dir():
            logger.error(f"FileNotFoundError: {path} does not exist or not a directory.")
        
        for file_path in path.rglob('*'):
            if file_path.is_file() and not is_system(file_path):
                file_count += 1

        logger.debug(f"Accumulate '{file_count}' files until '{path}'.")
    return file_count


class ConfigLoader:
    def __init__(self, config_path='config/config.toml'):
        self.config_path = Path(__file__).parent.parent.parent / Path(config_path)
        self.load_config()
        self.combined_paths = self.combine_path()

    def load_config(self):
        try:
            with open(self.config_path, 'r') as file:
                self.config = (toml.load(file))
                logger.debug("Configuration loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise

    def get_base_paths(self):
        return self.config.get('BASE_PATHS', {})

    def get_categories(self):
        return self.config.get('categories', {})

    def get_delimiters(self):
        return self.config.get('tag_delimiter', {})
    
    def get_combined_paths(self):
        return self.combined_paths
    
    def get_file_type(self):
        return self.file_type

    def combine_path(self):
        base_paths = self.get_base_paths()
        categories = self.get_categories()
        combined_paths = {}
        # combined_paths = dict.fromkeys(["local", "remote"], dict())

        for category, data in categories.items():
            local_combined = os.path.join(base_paths['local_path'], data['local_path'])
            remote_combined = os.path.join(base_paths['remote_path'], data['remote_path'])
            combined_paths[category] = {
                'local_path': local_combined,
                'remote_path': remote_combined,
            }
        return combined_paths



if __name__ == "__main__":
    config_loader = ConfigLoader()
    config_loader.load_config()
    tag_delimiters = config_loader.get_delimiters()

    combined_paths = config_loader.get_combined_paths()
    
    for category, paths in combined_paths.items():
        print(f"{category} - Local: {paths['local_path']}, Remote: {paths['remote_path']}")

    # safe_move(Path('struct.txt'), Path('structA.txt'))
