import os
from pathlib import Path

from src import categorizer, retriever, synchronizer, viewer, option
from src.utils import file_utils, string_utils
from src.logger import LogLevel, LogManager

root = Path(__file__).resolve().parent
os.chdir(root)


def main():
    args = option.build_parser()
    print(args)

    # Initialize
    log_manager = LogManager(level=args.loglevel, status="main.py")
    logger = log_manager.get_logger()
    config_loader = file_utils.ConfigLoader()
    combined_paths = config_loader.get_combined_paths()

    if not args.no_categorize:
        logger.info("開始分類檔案...")
        log_manager.set_status
        file_categorizer = categorizer.CategorizerUI(config_loader, logger)
        file_categorizer.categorize()
        file_count = file_utils.count_files(combined_paths, "local_path")

    if not args.no_sync:
        logger.info("開始同步檔案...")
        log_dir = root / Path("data")
        file_syncer = synchronizer.FileSyncer(config_loader, log_dir, logger).sync_folders()

    if not args.no_retrieve:
        logger.info("開始尋找遺失作品...")
        retriever.retrieve_artwork()

    if not args.no_view:
        logger.info("開始統計標籤...")
        viewer.viewer_main(config_loader)

    if not args.no_categorize:
        print(f"\033[32m這次新增了\033[0m\033[32;1;4m {file_count} \033[0m\033[32m個檔案🍺\033[0m")


if __name__ == "__main__":
    main()
