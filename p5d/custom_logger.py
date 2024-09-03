# Do NOT import utils/file_utils
import logging
import os

from p5d.app_settings import OUTPUT_DIR


class CustomFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[38;5;248m",
        logging.INFO: "\033[37m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[31;1m",
    }
    GREEN = "\033[32m"
    RESET = "\033[0m"

    def __init__(self, use_color=True):
        super().__init__()
        self.use_color = use_color

    def format(self, record):
        if self.use_color:
            color = self.COLORS.get(record.levelno, self.RESET)
            levelname = record.levelname.lower()
            return (
                f"[{self.GREEN}{self.formatTime(record, '%H:%M:%S')}{self.RESET}]"
                f"[{color}{levelname}{self.RESET}] - {record.getMessage()}"
            )
        else:
            # Convert levelname to lowercase for file logs
            levelname = record.levelname.lower()
            return f"[{self.formatTime(record, '%H:%M:%S')}][{levelname}] - {record.getMessage()}"


def setup_logging(level, no_archive=False):
    """
    level: [logging.LOGLEVEL]
    args: [bool], no_archive
    """
    # Clear any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Create formatters
    color_formatter = CustomFormatter(use_color=True)
    plain_formatter = CustomFormatter(use_color=False)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(color_formatter)
    logging.getLogger().addHandler(console_handler)

    # File handler
    if not no_archive:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        file_handler = logging.FileHandler(os.path.join(OUTPUT_DIR, "p5d.log"), encoding="utf-8")
        file_handler.setFormatter(plain_formatter)
        logging.getLogger().addHandler(file_handler)

    # Set log level
    logging.getLogger().setLevel(level)


if __name__ == "__main__":
    # Set up logging
    setup_logging(logging.DEBUG)

    # Create a logger
    logger = logging.getLogger(__name__)

    # Log messages to test the configuration
    logger.debug("Debug message")
    logger.info("This is an info message.")
    logger.warning("Warning message")
    logger.error("This is an error message.")
    logger.critical("Critical message")
