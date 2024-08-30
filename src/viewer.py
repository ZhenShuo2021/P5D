import logging
import os
from collections import Counter

import matplotlib

matplotlib.use("agg")
import matplotlib.pyplot as plt

from src import config, custom_logger
from src.config import STATS_FILE, WORK_DIR
from src.utils.file_utils import ConfigLoader
from src.utils.string_utils import color_text, is_system, split_tags

logging.getLogger("matplotlib").setLevel(logging.CRITICAL)
logging.getLogger("matplotlib.font_manager").setLevel(logging.CRITICAL)
logging.getLogger("matplotlib.backends").setLevel(logging.CRITICAL)

plt.rcParams["font.sans-serif"] = ["Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


def read_tag_counts(file_name: str) -> Counter:
    file_name = "./" + config.OUTPUT_DIR + "/" + file_name + ".txt"
    tag_counts = Counter()
    with open(file_name, "r") as file:
        for line in file:
            tag, count = line.strip().split(":")
            tag_counts[tag] = int(count)
    return tag_counts


def plot_pie_chart(
    tag_counts: Counter,
    logger: logging.Logger,
    top_n: int = 25,
    skip: int = 2,
    output_file: str = STATS_FILE,
    dpi: int = 360,
) -> None:
    output_file = output_file + ".jpg"
    keywords_to_skip = ["users", "ブルアカ", "BlueArchive"]
    exact_match_to_skip = "閃耀色彩"

    filtered_counts = {
        tag: count
        for tag, count in tag_counts.items()
        if not (any(keyword in tag for keyword in keywords_to_skip) or tag == exact_match_to_skip)
    }

    filtered_tag_counts = Counter(filtered_counts)

    most_common = filtered_tag_counts.most_common(top_n + skip)[skip:]
    if not most_common:
        print(
            color_text(
                "標籤數量不足以製作圓餅圖（可能是目的地沒有檔案導致讀不到標籤/skip值太大）", "red"
            )
        )
        return
    tags, counts = zip(*most_common)

    plt.figure(figsize=(12, 8))
    colors = plt.cm.Paired(range(len(tags)))  # type: ignore # Use a colormap for colors
    wedges, texts, autotexts = plt.pie(  # type: ignore
        counts,
        labels=tags,
        autopct="%1.1f%%",
        startangle=90,
        colors=colors,
        wedgeprops={"edgecolor": "black"},
    )

    for text in texts:
        x, y = text.get_position()
        if y > 0.9:
            text.set_horizontalalignment("center")
            text.set_verticalalignment("bottom")

    plt.axis("equal")
    plt.savefig(f"./{config.OUTPUT_DIR}/{output_file}", dpi=dpi, format="jpg", bbox_inches="tight")
    plt.close()

    logger.debug(f"Pie plot written to '{os.getcwd()}/{config.OUTPUT_DIR}/{output_file}'")


# tag
def count_tags(
    directory: str,
    tag_delimiter: dict[str, str],
    logger: logging.Logger,
    recursive: bool = True,
    output_file: str = "tags",
) -> None:
    all_tags = []
    total_files = 0

    if recursive:
        for root, _, files in os.walk(directory):
            for filename in files:
                if not is_system(filename):
                    tags = split_tags(filename, tag_delimiter)
                    all_tags.extend(tags)
                    total_files += 1
    else:
        for filename in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, filename)) and not is_system(filename):
                tags = split_tags(filename, tag_delimiter)
                all_tags.extend(tags)
                total_files += 1

    tag_counts = Counter(all_tags)
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

    with open(f"./{config.OUTPUT_DIR}/{output_file}.txt", "w", encoding="utf-8") as f:
        f.write(f"Total files: {total_files}\n")
        for tag, count in sorted_tags:
            f.write(f"{tag}: {count}\n")

    logger.debug(f"Tag statistics written to '{os.getcwd()}/{config.OUTPUT_DIR}/{output_file}.txt'")


def viewer_main(config_loader: ConfigLoader, logger: logging.Logger, file_name: str = STATS_FILE):
    base_path = config_loader.get_base_paths()
    tag_delimiter = config_loader.get_delimiters()
    count_tags(base_path[WORK_DIR], tag_delimiter, logger, output_file=file_name)
    tag_counts = read_tag_counts(file_name)
    plot_pie_chart(tag_counts, logger, 15, skip=2)  # skip since the top tags are useless


if __name__ == "__main__":
    custom_logger.setup_logging(logging.DEBUG)
    logger = logging.getLogger(__name__)
    config_loader = ConfigLoader(logger)
    config_loader.load_config()

    viewer_main(config_loader, logger)
