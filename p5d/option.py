import argparse
import logging


class Formatter(argparse.RawTextHelpFormatter):
    """Custom HelpFormatter class to customize help output"""

    def __init__(self, prog):
        super().__init__(prog, max_help_position=30)

    def _format_action_invocation(self, action, join=", ".join):
        opts = action.option_strings
        if action.metavar:
            opts = opts.copy()
            opts[-1] += " " + action.metavar
        return join(opts)


def build_parser():
    options_help = "其他選項\nrsync: rsync 參數\nlocal: local_path 路徑\nremote: remote_path 路徑\ncategory: 處理指定分類"
    parser = argparse.ArgumentParser(
        description="P5D: Pixiv Post Processor for Powerful Pixiv Downloader",
        usage="%(prog)s [OPTION]... URL...",
        formatter_class=Formatter,
    )

    parser.add_argument("--no-categorize", action="store_true", help="關閉分類功能")
    parser.add_argument("--no-sync", action="store_true", help="關閉同步功能")
    parser.add_argument("--no-retrieve", action="store_true", help="關閉尋找遺失作品功能")
    parser.add_argument("--no-view", action="store_true", help="關閉統計標籤功能")
    parser.add_argument("--no-archive", action="store_true", help="關閉日誌功能")
    parser.add_argument("--download", action="store_true", help="尋回遺失作品後自動下載")
    parser.add_argument("--direct_sync", action="store_true", help="直接映射到遠端目錄")

    parser.add_argument(
        "-q", "--quiet", dest="loglevel", action="store_const", const=logging.ERROR, help="安靜模式"
    )
    parser.add_argument(
        "--stats_dir",
        type=str,
        default="local_path",
        choices=["local_path", "remote_path", "local", "remote"],
        help="統計檔案的工作目錄",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        action="store_const",
        const=logging.DEBUG,
        help="偵錯模式",
    )
    parser.add_argument(
        "-o",
        "--options",
        dest="options",
        metavar="key=value",
        nargs="+",
        type=parse_key_value,
        help=options_help,
    )

    parser.set_defaults(loglevel=logging.INFO)
    args = parser.parse_args()

    # Convert list[tuple[str, str]] to dict[str, str]
    args.options = dict(args.options) if args.options else {}

    if args.direct_sync:
        args.no_categorize = False
        args.stats_dir = "remote_path"
    if args.stats_dir == "local":
        args.stats_dir = "local_path"
    args.options.update({"stats_dir": args.stats_dir})
    return args


def parse_key_value(kv_pair):
    key, value = kv_pair.split("=", 1)
    return key.strip(), value.strip()


if __name__ == "__main__":
    args = build_parser()
    print(args.options)
