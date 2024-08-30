import concurrent.futures
import logging
import os
import sys
import threading

import requests
from bs4 import BeautifulSoup

from src import config, custom_logger
from src.utils.string_utils import color_text

logger = logging.getLogger(__name__)

progress_lock = threading.Lock()
progress_idx = 0


def retrieve_artwork() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "../", config.OUTPUT_DIR, f"{config.MISS_LOG}.html")
    html_content = read_html(file_path)
    urls = extract_urls(html_content)
    # print(f"遺失作品數量：{len(urls)}")

    found_posts, not_found_posts, take_down_posts = process_urls(config.SOURCE_URL, urls)
    output_path = f"./{config.OUTPUT_DIR}/{config.MISS_LOG}_retrieve.txt"
    export_txt(output_path, found_posts, not_found_posts, take_down_posts)
    logger.debug(f"Retrieving result written to '{output_path}'")


def print_progress(idx: int, total_urls: int, width: int = 50) -> None:
    sys.stdout.write("\r" + " " * (width + 20) + "\r")
    progress = (idx + 1) / total_urls
    filled_length = int(width * progress)
    bar = "#" * filled_length + "-" * (width - filled_length)

    sys.stdout.write(f"[{bar}] {idx + 1}/{total_urls}")
    sys.stdout.flush()


def read_html(filename: str) -> str:
    with open(filename, "r", encoding="utf-8") as file:
        return file.read()


def extract_urls(html_content: str) -> list[str]:
    soup = BeautifulSoup(html_content, "html.parser")
    href_tags = soup.find_all(href=True)
    return [tag["href"].rsplit("/", 1)[-1] for tag in href_tags]


def fetch_url(base_url: str, url_suffix: str) -> tuple[str | None, str | None, str | None]:
    search_url = base_url.format(url_suffix)
    try:
        response = requests.get(search_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        no_posts_found = soup.find("p", string="No posts found.")
        take_down = soup.find("div", class_="fineprint hidden-posts-notice")

        if no_posts_found:
            return url_suffix, None, None
        elif take_down:
            return None, url_suffix, None
        else:
            return None, None, search_url
    except requests.RequestException as e:
        print(f"Error fetching {search_url}: {e}")
        return None, None, None


def process_urls(
    base_url: str, urls: list[str], max_threads: int = 5
) -> tuple[list[str], list[str], list[str]]:
    found_posts = []
    not_found_posts = []
    take_down_posts = []
    total_urls = len(urls)

    def update_progress():
        global progress_idx
        with progress_lock:
            progress_idx += 1
            print_progress(progress_idx, total_urls)

    with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
        futures = {
            executor.submit(fetch_url, base_url, url_suffix): idx
            for idx, url_suffix in enumerate(urls)
        }
        for future in concurrent.futures.as_completed(futures):
            no_posts_found, take_down, found = future.result()

            if logger.getEffectiveLevel() > logging.DEBUG:
                update_progress()
            if no_posts_found:
                not_found_posts.append(f"# {no_posts_found} No posts found")
            if take_down:
                take_down_posts.append(f"# {take_down} Removed because of a takedown request")
            if found:
                found_posts.append(found)

    sys.stdout.write("\r")
    sys.stdout.write("\033[K")
    sys.stdout.flush()
    return found_posts, not_found_posts, take_down_posts


def export_txt(
    filename: str, found_posts: list[str], not_found_posts: list[str], take_down_posts: list[str]
) -> None:
    with open(filename, "w", encoding="utf-8") as file:
        for result in found_posts:
            file.write(result + "\n")
        for result in take_down_posts:
            file.write(result + "\n")
        for result in not_found_posts:
            file.write(result + "\n")


if __name__ == "__main__":
    custom_logger.setup_logging(logging.DEBUG)

    retrieve_artwork()
