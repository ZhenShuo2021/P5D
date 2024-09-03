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

from p5d import custom_logger
from p5d.app_settings import RETRIEVE_DIR, MISS_LOG, DANBOORU_SEARCH_URL


progress_lock = threading.Lock()
progress_idx = -1


def retrieve_artwork(logger, download=False) -> None:
    base_dir = Path(__file__).resolve().parents[1]
    file_path = base_dir / RETRIEVE_DIR / f"{MISS_LOG}.txt"
    output_path = Path(RETRIEVE_DIR) / f"{MISS_LOG}_retrieve.txt"

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

    results = fetch_all(pixiv_ids, danbooru, logger)
    write_results_to_file(extract_values(results), output_path)
    logger.debug(f"Retrieving result written to '{output_path}'")

    if download:
        download_dir = base_dir / RETRIEVE_DIR
        download_dir.mkdir(parents=True, exist_ok=True)
        download_urls(output_path, base_dir, logger)


def fetch_all(pixiv_ids, fetch_func, logger, slow_number=100):
    results = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_func, pixiv_id): pixiv_id for pixiv_id in pixiv_ids}
        for future in as_completed(futures):
            pixiv_id = futures[future]

            if logger.getEffectiveLevel() > logging.DEBUG:
                update_progress(len(pixiv_ids))
            try:
                if progress_idx > slow_number:
                    time.sleep(random.uniform(0, 1.2))
                data = future.result()
                if data:
                    results.update(data)
            except Exception as exc:
                logger.error(f"{pixiv_id} generated an exception: {exc}")

    # Clean terminal
    sys.stdout.write("\r")
    sys.stdout.write("\033[K")
    sys.stdout.flush()
    return results


def danbooru(pixiv_id: str) -> dict[str, Any]:
    url = DANBOORU_SEARCH_URL.format(pixiv_id)
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


def download_urls(file_path, base_dir, logger):
    with open(file_path, "r+", encoding="utf-8") as file:
        lines = file.readlines()
        file.seek(0)

        for line in lines:
            line = line.strip()
            if not line.startswith("https://"):
                file.write(line + "\n")
                continue

            try:
                response = requests.get(line)
                time.sleep(1.5)
                response.raise_for_status()

                tree = html.fromstring(response.content)
                size_element = tree.xpath('//li[@id="post-info-size"]')

                if not size_element:
                    logger.error(f"No size information found for URL: {line}")
                    file.write(line + "\n")
                    continue

                download_url = size_element[0].xpath(
                    './/a[contains(@href, "https://cdn.donmai.us/")]/@href'
                )

                if not download_url:
                    logger.error(f"No download URL found for URL: {line}")
                    file.write(line + "\n")
                    continue

                file_url = download_url[0]
                file_ext = file_url.split("/")[-1].split(".")[-1]
                file_name = "danbooru " + line.split("/")[-1] + "." + file_ext
                file_path = base_dir / RETRIEVE_DIR / file_name
                if download_file(file_url, file_path, logger):
                    # 如果下載成功，加上 "# " 前綴
                    file.write(f"# {line}\n")
                else:
                    file.write(line + "\n")

            except requests.exceptions.HTTPError as http_err:
                logger.error(f"HTTP error occurred: {http_err}")
                file.write(line + "\n")
            except Exception as err:
                logger.error(f"An error occurred: {err}")
                file.write(line + "\n")


def download_file(url, save_path, logger):
    try:
        download_with_speed_limit(url, save_path, speed_limit_kbps=1536)
        logger.info(f"File successfully downloaded: '{save_path}'")
        return True
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        return False
    except Exception as err:
        logger.error(f"An error occurred: {err}")
        return False


def download_with_speed_limit(url, save_path, speed_limit_kbps=1536):
    chunk_size = 1024  # 1 KB
    speed_limit_bps = speed_limit_kbps * 1024  # 轉換為 bytes per second

    response = requests.get(url, stream=True)
    response.raise_for_status()  # 確認請求成功

    with open(save_path, "wb") as file:
        start_time = time.time()
        downloaded = 0

        for chunk in response.iter_content(chunk_size=chunk_size):
            file.write(chunk)
            downloaded += len(chunk)

            elapsed_time = time.time() - start_time
            expected_time = downloaded / speed_limit_bps

            if elapsed_time < expected_time:
                time.sleep(expected_time - elapsed_time)


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


def update_progress(jobs):
    global progress_idx
    with progress_lock:
        progress_idx += 1
        print_progress(progress_idx, jobs)


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
