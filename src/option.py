import argparse


class Formatter(argparse.HelpFormatter):
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
    parser = argparse.ArgumentParser(description="P5D: Pixiv Post Processor for Powerful Pixiv Downloader",
                                     usage="%(prog)s [OPTION]... URL...",
                                     formatter_class=Formatter)

    parser.add_argument('--no-categorize', action='store_true', help='關閉分類功能')
    parser.add_argument('--no-sync', action='store_true', help='關閉同步功能')
    parser.add_argument('--no-retrieve', action='store_true', help='關閉尋找遺失作品功能')
    parser.add_argument('--no-view', action='store_true', help='關閉統計標籤功能')

    return parser.parse_args()


if __name__ == "__main__":
    args = build_parser()
    print(args)
