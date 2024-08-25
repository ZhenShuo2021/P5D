import os
from pathlib import Path

from src import categorizer
from src import retriever
from src import synchronizer
from src import viewer
from src.utils import file_utils, string_utils
from src.logger import LogLevel, LogManager

root = Path(__file__).resolve().parent
os.chdir(root)


def main():
    # Initialize
    log_manager = LogManager(level=LogLevel.DEBUG, status="main.py")
    logger = log_manager.get_logger()
    config_loader = file_utils.ConfigLoader()
    combined_paths = config_loader.get_combined_paths()
    
    logger.info("開始分類檔案...")
    file_categorizer = categorizer.CategorizerUI(config_loader, logger)
    file_categorizer.categorize() 
    # Or categorize specific category
    # categories = list(config_loader.get_categories())
    # file_categorizer.categorize(categories[1])   # categorize the last category
    file_count = file_utils.count_files(combined_paths, "local_path")

    logger.info("開始同步檔案...")
    log_dir = root / Path("data")
    file_syncer = synchronizer.FileSyncer(config_loader, log_dir, logger).sync_folders()
    # Or sync specific category
    # file_syncer = synchronizer.FileSyncer(config_loader, log_dir, logger)
    # file_syncer.sync_folders(combined_paths["IdolMaster"]["local_path"], combined_paths["IdolMaster"]["remote_path"])
    # synchronizer.LogMerger(log_dir).merge_logs()
    
    logger.info("開始尋找遺失作品...")
    retriever.retrieve_artwork()

    logger.info("開始統計標籤...")
    viewer.viewer_main(config_loader)

    print(f"\033[32m這次新增了\033[0m\033[32;1;4m {file_count} \033[0m\033[32m個檔案🍺\033[0m")

if __name__ == "__main__":
    main()
