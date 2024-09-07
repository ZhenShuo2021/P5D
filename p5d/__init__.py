# p5d/__init__.py

import logging

from p5d import categorizer, option, retriever, synchronizer, viewer
from p5d.custom_logger import setup_logging
import p5d.utils


def main():
    # Initialize
    args = option.build_parser()
    setup_logging(args.loglevel, args.no_archive)
    logger = logging.getLogger(__name__)

    config_loader = p5d.utils.ConfigLoader(logger)
    config_loader.load_config()
    config_loader.update_config(args.options)
    combined_paths = config_loader.get_combined_paths()

    if not args.no_categorize:
        logger.info("開始分類檔案...")
        categorizer.categorize_files(config_loader, args.direct_sync, logger)

    if not args.no_sync:
        logger.info("開始同步檔案...")
        synchronizer.FileSyncer(config_loader, logger, args.direct_sync, args.options).sync_folders(
            None, None
        )

    if not args.no_retrieve:
        logger.info("開始尋找遺失作品...")
        retriever.retrieve_artwork(logger, args.download)

    if not args.no_view:
        logger.info("開始統計標籤...")
        viewer.viewer_main(config_loader, logger, config_loader.get_stats_dir())

    if not args.no_categorize:
        stats_dir = config_loader.get_stats_dir()
        file_count = p5d.utils.count_files(combined_paths, logger, stats_dir)
        happy_msg = "這次新增了" if stats_dir == "local_path" else "遠端資料夾總共有"
        print(f"\033[32m{happy_msg}\033[0m\033[32;1;4m {file_count} \033[0m\033[32m個檔案🍺\033[0m")
