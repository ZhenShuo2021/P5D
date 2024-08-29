# src/__init__.py

import os
from pathlib import Path
from . import categorizer, synchronizer, retriever, viewer, option, config
from .utils import file_utils
from .custom_logger import setup_logging
import logging

def main():
    # Initialize
    args = option.build_parser()
    setup_logging(args.loglevel, args.no_archive)
    logger = logging.getLogger(__name__)
    
    config_loader = file_utils.ConfigLoader(logger)
    config_loader.load_config()
    config_loader.update_config(args.options)
    combined_paths = config_loader.get_combined_paths()

    if not args.no_categorize:
        logger.info("開始分類檔案...")
        file_categorizer = categorizer.CategorizerUI(config_loader)
        file_categorizer.categorize()

    if not args.no_sync:
        logger.info("開始同步檔案...")
        synchronizer.FileSyncer(config_loader, args.options).sync_folders()

    if not args.no_retrieve:
        logger.info("開始尋找遺失作品...")
        retriever.retrieve_artwork(logger)

    if not args.no_view:
        logger.info("開始統計標籤...")
        viewer.viewer_main(config_loader)

    if not args.no_categorize:
        file_count = file_utils.count_files(combined_paths, logger, config.WORK_DIR)
        print(f"\033[32m這次新增了\033[0m\033[32;1;4m {file_count} \033[0m\033[32m個檔案🍺\033[0m")
