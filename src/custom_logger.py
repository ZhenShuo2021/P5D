import logging
import os

from src.config import OUTPUT_DIR


class CustomFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[38;5;248m",
        logging.INFO: "\033[37m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[31;1m"
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
            return f"[{self.GREEN}{self.formatTime(record, '%H:%M:%S')}{self.RESET}]" \
                f"[{color}{levelname}{self.RESET}] - {record.getMessage()}"
        else:
            # Convert levelname to lowercase for file logs
            levelname = record.levelname.lower()
            return f"[{self.formatTime(record, '%H:%M:%S')}][{levelname}] - {record.getMessage()}"


def setup_logging(level):
    # Clear any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Create formatters
    color_formatter = CustomFormatter(use_color=True)
    plain_formatter = CustomFormatter(use_color=False)

    # Create handlers
    console_handler = logging.StreamHandler()
    os.makedirs(f'./{OUTPUT_DIR}', exist_ok=True)
    file_handler = logging.FileHandler(f"./{OUTPUT_DIR}/system.log")

    # Set formatters
    console_handler.setFormatter(color_formatter)
    file_handler.setFormatter(plain_formatter)

    # Add handlers to the root logger
    logging.getLogger().addHandler(console_handler)
    logging.getLogger().addHandler(file_handler)
    logging.getLogger().setLevel(logging.DEBUG)
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
