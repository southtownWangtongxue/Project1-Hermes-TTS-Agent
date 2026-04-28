import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 常量定义
DEFAULT_LOG_DIR = Path("logs")
DEFAULT_LOG_FILE = "app.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5  # 保留5个备份

def setup_logger(name: str = "hermes", level: int = logging.INFO) -> logging.Logger:
    """配置日志系统"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        # 控制台 handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_format = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        console_handler.setFormatter(console_format)

        # 文件 handler - 添加异常处理和日志轮转
        try:
            log_dir = DEFAULT_LOG_DIR
            log_dir.mkdir(exist_ok=True)
            file_handler = RotatingFileHandler(
                log_dir / DEFAULT_LOG_FILE,
                maxBytes=MAX_LOG_SIZE,
                backupCount=BACKUP_COUNT
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(console_format)
        except (OSError, PermissionError) as e:
            print(f"Warning: Failed to initialize file logging: {e}. Using console only.", file=sys.stderr)

        # 添加 handler
        logger.addHandler(console_handler)
        if 'file_handler' in locals():
            logger.addHandler(file_handler)

    return logger
