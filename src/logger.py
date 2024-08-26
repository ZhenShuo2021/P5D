import logging
import os
from enum import Enum
LOG_FORMAT = "[%(asctime)s][%(levelname)s][%(status)s] - %(message)s"
DATE_FORMAT = "%H:%M:%S"


class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


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

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        levelname = record.levelname.lower()
        return f"[{self.GREEN}{self.formatTime(record, DATE_FORMAT)}{self.RESET}]" \
            f"[{color}{levelname}{self.RESET}]" \
            f"[{record.status}] - {record.getMessage()}"


class PlainFormatter(logging.Formatter):
    def format(self, record):
        levelname = record.levelname.lower()
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        return formatter.format(record).replace(record.levelname, levelname)


class LogManager:
    def __init__(self, name="MyApp", level=LogLevel.DEBUG, status=""):
        self.logger = self._setup_logger(name, level.value, status)

    def _setup_logger(self, name, level, status):
        logger = logging.getLogger(name)
        logger.setLevel(level)
        if logger.hasHandlers():
            logger.handlers.clear()

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(CustomFormatter())
        logger.addHandler(ch)

        # File handler
        os.makedirs('./data', exist_ok=True)
        fh = logging.FileHandler('data/system.log')
        fh.setLevel(level)
        fh.setFormatter(PlainFormatter())
        logger.addHandler(fh)
        return logging.LoggerAdapter(logger, {"status": status})

    def set_status(self, status):
        self.logger.extra["status"] = status

    def get_logger(self):
        return self.logger


if __name__ == "__main__":
    log_manager = LogManager(name="MyApp", level=LogLevel.DEBUG, status="Program A")
    logger = log_manager.get_logger()
    logger.debug("Debug message")
    logger.info("This is an info message.")
    logger.warning("Warning message")

    log_manager.set_status("Program B")
    logger.error("This is an error message.")
    logger.critical("Critical message")

