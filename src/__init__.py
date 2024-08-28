# src/__init__.py

import os
from pathlib import Path
from . import categorizer, synchronizer, retriever, viewer, option, config
from .utils import file_utils
from .custom_logger import setup_logging
import logging

def main():
    root = Path(__file__).resolve().parent.parent
    os.chdir(root)

    args = option.build_parser()
    
    # Initialize
    setup_logging(args.loglevel)
    logger = logging.getLogger("P5D")
    config_loader = file_utils.ConfigLoader()
    config_loader.load_config()
    combined_paths = config_loader.get_combined_paths()

    if not args.no_categorize:
        logger.info("開始分類檔案...")
        file_categorizer = categorizer.CategorizerUI(config_loader)
        file_categorizer.categorize()
        file_count = file_utils.count_files(combined_paths, config.WORK_DIR)

    if not args.no_sync:
        logger.info("開始同步檔案...")
        log_dir = root / Path(config.OUTPUT_DIR)
        synchronizer.FileSyncer(config_loader, log_dir).sync_folders()

    if not args.no_retrieve:
        logger.info("開始尋找遺失作品...")
        retriever.retrieve_artwork()

    if not args.no_view:
        logger.info("開始統計標籤...")
        viewer.viewer_main(config_loader)

    if not args.no_categorize:
        print(f"\033[32m這次新增了\033[0m\033[32;1;4m {file_count} \033[0m\033[32m個檔案🍺\033[0m")
