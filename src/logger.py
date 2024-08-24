import logging
import os
from enum import Enum


class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

class CustomFormatter(logging.Formatter):
    # 定義顏色
    GREEN = "\033[32m"      # 淺綠色
    YELLOW = "\033[33;20m"
    RED = "\033[31;20m"
    BOLD_RED = "\033[31;1m"
    GREY = "\033[37m"       # 灰色
    WHITE = "\033[97m"      # 白色
    RESET = "\033[0m"

    LOG_FORMAT = "[%(asctime)s][%(levelname)s][%(status)s] - %(message)s"
    DATE_FORMAT = "%H:%M:%S"

    def format(self, record):
        # 設定時間顏色為淺綠色
        asctime = self.GREEN + self.formatTime(record, self.DATE_FORMAT) + self.RESET

        # 根據日誌級別動態設置 levelname 的顏色並轉換為小寫
        levelname = record.levelname.lower()
        if record.levelno == logging.DEBUG:
            levelname = self.GREY + levelname + self.RESET
        elif record.levelno == logging.INFO:
            levelname = self.WHITE + levelname + self.RESET
        elif record.levelno == logging.WARNING:
            levelname = self.YELLOW + levelname + self.RESET
        elif record.levelno == logging.ERROR:
            levelname = self.RED + levelname + self.RESET
        elif record.levelno == logging.CRITICAL:
            levelname = self.BOLD_RED + levelname + self.RESET

        # 確保訊息顏色始終為白色
        message = self.WHITE + record.getMessage() + self.RESET

        # 使用自定義格式組合為日誌輸出
        log_format = f"[{asctime}][{levelname}][{record.status}] {message}"
        return log_format

class PlainFormatter(logging.Formatter):
    LOG_FORMAT = "[%(asctime)s][%(levelname)s][%(status)s] - %(message)s"
    DATE_FORMAT = "%H:%M:%S"

    def format(self, record):
        # 將 levelname 轉為小寫
        levelname = record.levelname.lower()
        formatter = logging.Formatter(self.LOG_FORMAT, datefmt=self.DATE_FORMAT)
        formatted_message = formatter.format(record)
        return formatted_message.replace(record.levelname, levelname)

class LogManager:
    def __init__(self, name="MyApp", level=LogLevel.DEBUG, status=""):
        self.logger = self.setup_logger(name, level.value, status)

    def setup_logger(self, name, level, status):
        logger = logging.getLogger(name)
        logger.setLevel(level)

        if logger.hasHandlers():
            logger.handlers.clear()

        # Console handler with color
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(CustomFormatter())
        logger.addHandler(ch)

        # File handler without color
        if not os.path.exists('./data'):
            os.makedirs('./data')
        fh = logging.FileHandler('data/pixiv.log')
        fh.setLevel(level)
        fh.setFormatter(PlainFormatter())
        logger.addHandler(fh)

        logger = logging.LoggerAdapter(logger, {"status": status})
        return logger

    def set_status(self, status):
        self.logger.extra["status"] = status

    def get_logger(self):
        return self.logger

# 測試用例
if __name__ == "__main__":
    import numpy as np
    log_manager = LogManager(name="MyApp", level=LogLevel.DEBUG, status="Program A")
    logger = log_manager.get_logger()

    logger.info("This is an info message.")
    logger.error("This is an error message.")

    # 更改狀態
    log_manager.set_status("Program B")
    logger.info(f"Info message: processing x for {np.random.random_sample()+np.random.randint(0,5):.2f}s.")
    logger.info(f"Info message: processing x for {np.random.random_sample()+np.random.randint(0,5):.2f}s.")
    logger.info(f"Info message: processing x for {np.random.random_sample()+np.random.randint(0,5):.2f}s.")
    logger.debug("Debug message")
    logger.warning("Warning message")
    logger.critical("Critical message")

log_manager = LogManager(name="MyApp", level=LogLevel.DEBUG, status="UnknownProcess")
logger = log_manager.get_logger()