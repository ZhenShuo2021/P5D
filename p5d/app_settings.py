# import os
# import sys
# from pathlib import Path

# root = Path(__file__).resolve().parent.parent
# os.chdir(root)
# sys.path.insert(0, str(root))

# System Variable Configuration
import os
import platform


def is_docker() -> bool:
    path = "/proc/self/cgroup"
    return (
        os.path.exists("/.dockerenv")
        or os.path.isfile(path)
        and any("docker" in line for line in open(path))
    )


USER_OS = platform.system()

if USER_OS == "Windows":
    FONT = "Microsoft YaHei"
elif USER_OS == "Darwin":
    # MacOS
    FONT = "NotoSansOriya"
elif is_docker():
    FONT = "Noto Sans CJK JP"
else:
    FONT = "Arial Unicode MS"


# Output directory of all files.
OUTPUT_DIR = "data"
TEMP_DIR = os.path.join(OUTPUT_DIR, ".temp")
MAPPING_EXT = ".txt"
RETRIEVE_DIR = os.path.join(OUTPUT_DIR, "retrieve")

# Retriever.py
# Source site for retrieve missing artwork
DANBOORU_URL = "https://danbooru.donmai.us/"
DANBOORU_SEARCH_URL = "https://danbooru.donmai.us/posts?tags=pixiv%3A{}&z=5"
MISS_LOG = "id"

# viewer.py
# Output file name.
STATS_FILE = "tag_stats"

# logger.py
# Extension of temp rsync log
RSYNC_TEMP_EXT = ".logfile"

# categorizer.py
# Folder name of OtherCategorizer
EN = "EN Artist"
JP = "JP Artist"
OTHER = "Other Artist"
