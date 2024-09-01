import re
import string
from pathlib import Path

HIRAGANA_START = "\u3040"
HIRAGANA_END = "\u309f"
KATAKANA_START = "\u30a0"
KATAKANA_END = "\u30ff"


def is_system(file_path: str | Path) -> bool:
    """Check if the file is a common system file based on its name."""
    common_system_files = {".DS_Store", "Thumbs.db", "desktop.ini"}
    return Path(file_path).name in common_system_files


def is_empty(file_path: str | Path) -> bool:
    # Check if any entry is a file that's not a system file or a directory that is not empty
    file_path = Path(file_path)
    return not any(entry.is_dir() or not is_system(entry.name) for entry in file_path.iterdir())


def is_english(character: str) -> bool:
    return character in string.ascii_letters


def is_japanese(character: str) -> bool:
    return (HIRAGANA_START <= character <= HIRAGANA_END) or (
        KATAKANA_START <= character <= KATAKANA_END
    )


def split_tags(file_name: str, tag_delimiter: dict) -> list[str]:
    front_delim = tag_delimiter.get("front", "")
    between_delim = tag_delimiter.get("between", ",")
    file_tags = file_name.split(between_delim)
    if file_tags:
        file_tags[0] = file_tags[0].split(front_delim)[-1]
    return file_tags


def normalize_path(path: str | Path) -> str:
    """Convert path from Windows format to Unix format

    See https://stackoverflow.com/a/67658259/26993682
    """
    path = str(path)
    if "\\" in path:
        path = normalize_disk(path)
    return path


def normalize_disk(path_in: str) -> str:
    # r: raw string，反斜線不會被當作特殊字符處理
    # ^: 字串開始
    # (): 每個()都是一個捕獲群組
    # ([A-Z]): 捕獲一個大寫字母
    # ([A-Z]+): 捕獲任何大寫字母
    # ([a-zA-Z]+): 捕獲任何字母
    # cygdrive: cygwin 路徑格式
    # \1 引用第一個捕獲群組
    path_in = path_in.replace("\\", "/")
    path_out = re.sub(r"^([A-Z]):/", lambda m: f"/cygdrive/{m.group(1).lower()}/", path_in)
    return path_out + "/"


def color_text(text: str, color: str = "", background: str = "", style: str = "") -> str:
    """
    返回帶有 ANSI 顏色控制碼的文本。

    :param color: red, green, yellow, blue, magenta, cyan, black, white
    :param background: red, green, yellow, blue, magenta, cyan, black, white
    :param style: bold, underline, 'reverse
    :return: f-string
    """
    color_codes = {
        "black": "30",
        "red": "31",
        "green": "32",
        "yellow": "33",
        "blue": "34",
        "magenta": "35",
        "cyan": "36",
        "white": "37",
    }
    background_codes = {
        "black": "40",
        "red": "41",
        "green": "42",
        "yellow": "43",
        "blue": "44",
        "magenta": "45",
        "cyan": "46",
        "white": "47",
    }
    style_codes = {"bold": "1", "underline": "4", "reverse": "7"}

    codes = []
    if color in color_codes:
        codes.append(color_codes[color])
    if background in background_codes:
        codes.append(background_codes[background])
    if style in style_codes:
        codes.append(style_codes[style])

    start_code = "\033[" + ";".join(codes) + "m" if codes else ""
    end_code = "\033[0m" if codes else ""

    return f"{start_code}{text}{end_code}"


if __name__ == "__main__":
    s = r"C:\path\to\here"
    sn = normalize_path(s)
    print(s, "\n", sn)
