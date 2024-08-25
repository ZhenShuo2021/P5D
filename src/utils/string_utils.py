from pathlib import Path
import string

HIRAGANA_START = '\u3040'
HIRAGANA_END = '\u309f'
KATAKANA_START = '\u30a0'
KATAKANA_END = '\u30ff'


def is_system(file_path: str) -> bool:
    """Check if the file is a common system file based on its name."""
    common_system_files = {'.DS_Store', 'Thumbs.db', 'desktop.ini'}
    return Path(file_path).name in common_system_files

def is_empty(file_path: Path) -> bool:
    # Check if any entry is a file that's not a system file or a directory that is not empty
    return not any(
        entry.is_dir() or not is_system(entry.name)
        for entry in file_path.iterdir()
    )

def is_english(character: str) -> bool:
    return character in string.ascii_letters

def is_japanese(character: str) -> bool:
    return (HIRAGANA_START <= character <= HIRAGANA_END) or (KATAKANA_START <= character <= KATAKANA_END)

def split_tags(file_name: str, tag_delimiter: dict) -> list[str]:
    front_delim = tag_delimiter.get('front', '')
    between_delim = tag_delimiter.get('between', ',')
    file_tags = file_name.split(between_delim)
    if file_tags:
        file_tags[0] = file_tags[0].split(front_delim)[-1]
    return file_tags

def color_text(text: str, color: str=None, background: str=None, style:str =None) -> str:
    """
    返回帶有 ANSI 顏色控制碼的文本。
    
    :param color: red, green, yellow, blue, magenta, cyan, black, white
    :param background: red, green, yellow, blue, magenta, cyan, black, white
    :param style: bold, underline, 'reverse
    :return: f-string
    """
    color_codes = {
        'black': '30', 'red': '31', 'green': '32', 'yellow': '33',
        'blue': '34', 'magenta': '35', 'cyan': '36', 'white': '37'
    }
    background_codes = {
        'black': '40', 'red': '41', 'green': '42', 'yellow': '43',
        'blue': '44', 'magenta': '45', 'cyan': '46', 'white': '47'
    }
    style_codes = {
        'bold': '1', 'underline': '4', 'reverse': '7'
    }

    codes = []
    if color in color_codes:
        codes.append(color_codes[color])
    if background in background_codes:
        codes.append(background_codes[background])
    if style in style_codes:
        codes.append(style_codes[style])

    start_code = '\033[' + ';'.join(codes) + 'm' if codes else ''
    end_code = '\033[0m' if codes else ''

    return f'{start_code}{text}{end_code}'

