import logging
from pathlib import Path
from typing import Optional

_DEF_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def get_logger(name: str = __name__, level: str = "INFO", log_file: Optional[Path] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level.upper())

    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter(_DEF_FORMAT))
    logger.addHandler(ch)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter(_DEF_FORMAT))
        logger.addHandler(fh)

    return logger
