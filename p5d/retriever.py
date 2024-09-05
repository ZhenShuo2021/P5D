import logging
import random
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, Any, Callable

import requests
from lxml import html

from p5d import custom_logger
from p5d.app_settings import RETRIEVE_DIR, MISS_LOG, DANBOORU_SEARCH_URL


progress_lock = threading.Lock()
progress_idx = -1


def retrieve_artwork(logger: logging.Logger, download: bool = False) -> None:
    base_dir = Path(__file__).resolve().parents[1]
    file_path = base_dir / RETRIEVE_DIR / f"{MISS_LOG}.txt"
    output_path = Path(RETRIEVE_DIR) / f"{MISS_LOG}_retrieve.txt"
    suffix = " 404 not found\n"
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            pixiv_ids = [line.rstrip(suffix) for line in file if line.endswith(suffix)]
        results = fetch_all(pixiv_ids, danbooru, logger)
        write_retrieve_results(results, output_path)
        logger.debug(f"Retrieving result written to '{output_path}'")

    except FileNotFoundError:
        logger.info(f"Artwork list file '{file_path}' not found, continue to next step")

    if download:
        download_dir = base_dir / RETRIEVE_DIR
        download_dir.mkdir(parents=True, exist_ok=True)
        danbooru_downloader(output_path, base_dir, logger)


def fetch_all(
    pixiv_ids: list[str],
    fetch_func: Callable,
    logger: logging.Logger,
    max_workers: int = 5,
) -> dict[str, str]:
    results = {}
    max_workers = 32 if max_workers > 32 else max_workers
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(fetch_func, pixiv_id, logger): pixiv_id for pixiv_id in pixiv_ids
        }
        for future in as_completed(futures):
            pixiv_id = futures[future]

            if logger.getEffectiveLevel() > logging.DEBUG:
                update_progress(len(pixiv_ids))
            try:
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


def danbooru(
    pixiv_id: str, logger: logging.Logger, retry: int = 5, sleep_time: int = 5
) -> dict[str, str]:
    url = DANBOORU_SEARCH_URL.format(pixiv_id)
    response = retry_request(url, logger, retry, sleep_time)

    if response.status_code != 200:
        return {pixiv_id: f"HTTPS connection error with code {response.status_code}"}

    return danbooru_fetcher(pixiv_id, response)


def retry_request(
    url: str, logger: logging.Logger, retries: int, sleep_time: int
) -> requests.Response:
    response = requests.Response()
    response.status_code = 500  # Default to an error status code
    try:
        for attempt in range(retries):
            response = requests.get(url, stream=True)
            # Break if success (200), go to next iteration if (429), leave if any error.
            if response.status_code == 200:
                break
            elif response.status_code == 429:
                time.sleep(sleep_time)
                logger.info(
                    f"Rate limit exceeded for {url}. Sleeping for {sleep_time}s. Attempt {attempt + 1}/{retries}."
                )
            else:
                logger.error(f"Failed fetching for {url} with code {response.status_code}")
                break
            logger.error(f"Failed to retrieve URL after {retries} attempts: '{url}'")
    except requests.RequestException as e:
        logger.error(f"Failed to retrieve '{url}': {e}")

    return response


def danbooru_fetcher(pixiv_id: str, response: requests.Response) -> dict[str, str]:
    """
    Extract the response to get the artwork status.

    This function extract the response.text to resolve the artwork status. Four types of artwork
    status is defined in this function: `No posts found`, `Hidden posts`, `Found` and `No matching`.

    :return:
    """
    fetch_result = {}
    tree = html.fromstring(response.text)

    posts_div = tree.xpath('//div[@id="posts"]')
    if not posts_div:
        fetch_result[pixiv_id] = "Error: <div id='posts'> not found"
        return fetch_result
    posts_div = posts_div[0]

    # 沒有找到posts: 搜尋<p>內容為No posts found
    if posts_div.xpath('.//p[text()="No posts found."]'):
        fetch_result[pixiv_id] = "No posts found."
    # 隱藏的posts: 搜尋<div>
    elif posts_div.xpath('.//div[@class="fineprint hidden-posts-notice"]'):
        fetch_result[pixiv_id] = "Hidden posts"
    # 找到特定的article: 搜尋<article>中id鍵值以 "post_"開頭
    else:
        articles = posts_div.xpath('.//article[starts-with(@id, "post_")]')
        if articles:
            fetch_result[pixiv_id] = [article.get("id").split("_")[1] for article in articles]
        else:
            fetch_result[pixiv_id] = "Error: No matching condition found"
    return fetch_result


def danbooru_downloader(file_path: Path, base_dir: Path, logger: logging.Logger) -> None:
    """
    Download danbooru file with given file with urls.
    """
    if not file_path.exists():
        logger.error(f"File '{file_path}' not found, stop downloading")
        return

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


def download_file(url: str, save_path: Path, logger: logging.Logger) -> bool:
    """
    Error control subfunction for download files.

    Return `True` for successful download, else `False`.
    """
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


def download_with_speed_limit(url: str, save_path: Path, speed_limit_kbps: int = 1536) -> None:
    """
    Download with speed limit function.

    Default speed limit is 1536 KBps (1.5 MBps).
    """
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


def write_retrieve_results(data: dict[str, str], filename: Path):
    base_url = "https://danbooru.donmai.us/posts/"
    with open(filename, "w", encoding="utf-8") as file:
        # Write list values first
        for key, value in data.items():
            if isinstance(value, list):
                file.write(f"# {key}\n")
                for post_id in value:
                    file.write(f"{base_url}{post_id}\n")

        # Write "no posts found" entries
        for key, value in data.items():
            if value == "No posts found.":
                file.write(f"# {key} No posts found\n")

        # Write "hidden posts" entries
        for key, value in data.items():
            if value == "Hidden posts":
                file.write(f"# {key} Hidden posts\n")

        # Write "retrieve error" entries
        for key, value in data.items():
            if not isinstance(value, list) and value not in ["No posts found.", "Hidden posts"]:
                file.write(f"# {key} retrieve error: {value}\n")


def update_progress(jobs: int) -> None:
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
