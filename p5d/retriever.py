import logging
import random
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, Any

import requests
from lxml import html

from p5d import app_settings, custom_logger


progress_lock = threading.Lock()
progress_idx = 0


def retrieve_artwork(logger) -> None:
    base_dir = Path(__file__).resolve().parent
    file_path = base_dir.parent / app_settings.OUTPUT_DIR / f"{app_settings.MISS_LOG}.txt"
    output_path = f"./{app_settings.OUTPUT_DIR}/{app_settings.MISS_LOG}_retrieve.txt"

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            file_lines = file.readlines()
    except FileNotFoundError:
        logger.info(f"Artwork list file '{file_path}' not found, continue to next step")
        return

    pixiv_ids = []
    for line in file_lines:
        if line.endswith(" 404 not found\n"):
            pixiv_ids.append(line.rstrip(" 404 not found\n"))
        elif not line.strip():
            continue

    results = fetch_all(pixiv_ids, danbooru)
    write_results_to_file(extract_values(results), output_path)
    logger.debug(f"Retrieving result written to '{output_path}'")


def fetch_all(pixiv_ids, fetch_func, slow_number=150):
    results = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_func, pixiv_id): pixiv_id for pixiv_id in pixiv_ids}
        for future in as_completed(futures):
            pixiv_id = futures[future]
            try:
                if len(pixiv_ids) > slow_number:
                    time.sleep(random.uniform(0, 1.5))
                data = future.result()
                if data:
                    results.update(data)
            except Exception as exc:
                print(f"{pixiv_id} generated an exception: {exc}")
    return results


def danbooru(pixiv_id: str) -> dict[str, Any]:
    url = app_settings.DANBOORU_SEARCH_URL.format(pixiv_id)
    result = {}

    try:
        response = requests.get(url)
        if response.status_code != 200:
            result[pixiv_id] = f"Error: HTTP {response.status_code}"
            return result
        result = danbooru_helper(pixiv_id, response)

    except requests.RequestException as e:
        result[pixiv_id] = f"Error: {str(e)}"
    return result


def danbooru_helper(pixiv_id: str, response: requests.Response):
    danbooru_result = {}
    tree = html.fromstring(response.text)

    posts_div = tree.xpath('//div[@id="posts"]')
    if not posts_div:
        danbooru_result[pixiv_id] = "Error: <div id='posts'> not found"
        return danbooru_result
    posts_div = posts_div[0]

    # 沒有找到posts: 搜尋<p>內容為No posts found
    if posts_div.xpath('.//p[text()="No posts found."]'):
        danbooru_result[pixiv_id] = "No posts found."
    # 隱藏的posts: 搜尋<div>
    elif posts_div.xpath('.//div[@class="fineprint hidden-posts-notice"]'):
        danbooru_result[pixiv_id] = "Hidden posts"
    # 找到特定的article: 搜尋<article>中id鍵值以 "post_"開頭
    else:
        articles = posts_div.xpath('.//article[starts-with(@id, "post_")]')
        if articles:
            danbooru_result[pixiv_id] = [article.get("id").split("_")[1] for article in articles]
        else:
            danbooru_result[pixiv_id] = "Error: No matching condition found"
    return danbooru_result


def extract_values(data):
    result = {"posts found": {}, "no posts found": [], "posts hidden": [], "posts error": {}}

    for key, value in data.items():
        if isinstance(value, list):
            result["posts found"][key] = value  # 儲存鍵和對應的值
        elif value == "No posts found.":
            result["no posts found"].append(key)  # 只記錄鍵
        elif value == "Hidden posts":
            result["posts hidden"].append(key)  # 只記錄鍵
        else:
            result["posts error"][key] = value
    return result


def write_results_to_file(data, filename):
    base_url = "https://danbooru.donmai.us/posts/"
    with open(filename, "w") as file:
        for key, values in data["posts found"].items():
            file.write(f"# {key}\n")  # 輸出 pixiv id
            for post_id in values:
                file.write(f"{base_url}{post_id}\n")

        for post_id in data["posts hidden"]:
            file.write(f"# {post_id} Hidden posts\n")

        for post_id in data["no posts found"]:
            file.write(f"# {post_id} No posts found\n")

        for key, values in data["posts error"].items():
            file.write(f"# {key} retrieve error: {values}\n")  # 輸出 pixiv id


def print_progress(idx: int, total_urls: int, width: int = 50) -> None:
    sys.stdout.write("\r" + " " * (width + 20) + "\r")
    progress = (idx + 1) / total_urls
    filled_length = int(width * progress)
    bar = "#" * filled_length + "-" * (width - filled_length)

    sys.stdout.write(f"[{bar}] {idx + 1}/{total_urls}")
    sys.stdout.flush()


if __name__ == "__main__":
    custom_logger.setup_logging(logging.DEBUG)
    logger = logging.getLogger(__name__)

    retrieve_artwork(logger)
