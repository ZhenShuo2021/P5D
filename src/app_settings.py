# import os
# import sys
# from pathlib import Path

# root = Path(__file__).resolve().parent.parent
# os.chdir(root)
# sys.path.insert(0, str(root))

# System Variable Configuration

import platform

USER_OS = platform.system()

if USER_OS == "Windows":
    FONT = "Microsoft YaHei"
elif USER_OS == "Darwin":
    # MacOS
    FONT = "Arial Unicode MS"
else:
    FONT = "Arial Unicode MS"


# Output directory of all files.
OUTPUT_DIR = "data"

# Retriever.py
# Source site for retrieve missing artwork
SOURCE_URL = "https://danbooru.donmai.us/posts?tags=pixiv%3A{}&z=5"
MISS_LOG = "pixiv"

# viewer.py
# Output file name.
STATS_FILE = "tag_stats"
# Working directory of statistic info. Also used in main.py. Option: [local_path, remote_path].
WORK_DIR = "local_path"

# logger.py
# Extension of temp rsync log
LOG_TEMP_EXT = ".logfile"

# categorizer.py
# Key name in config.toml of others
OTHERS_NAME = "others"
# Folder name of OtherCategorizer
EN = "EN Artist"
JP = "JP Artist"
Other = "Other Artist"
