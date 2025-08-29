from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(level: str = "INFO", log_path: str = "logs/app.log", max_bytes: int = 1_048_576, backup_count: int = 3) -> None:
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # Rotating file handler
    fh = RotatingFileHandler(log_path, maxBytes=max_bytes, backupCount=backup_count)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    logging.getLogger(__name__).debug("Logging initialized (level=%s, path=%s)", level, os.path.abspath(log_path))

