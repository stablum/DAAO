from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys


LOGGER_NAME = "daao"
LOG_DIRECTORY_ENV = "DAAO_LOG_DIR"


def default_log_path() -> Path:
    """Return the platform-appropriate persistent DAAO log path."""
    configured_directory = os.environ.get(LOG_DIRECTORY_ENV)
    if configured_directory:
        return Path(configured_directory).expanduser() / "daao.log"

    if sys.platform == "win32":
        base_directory = Path(
            os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
        )
    else:
        base_directory = Path(
            os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")
        )
    return base_directory / "DAAO" / "logs" / "daao.log"


def configure_logging(log_path: Path | None = None) -> Path:
    """Configure a size-limited diagnostic log and return its path."""
    path = log_path or default_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    for existing_handler in tuple(logger.handlers):
        if getattr(existing_handler, "_daao_file_handler", False):
            return path

    handler = RotatingFileHandler(
        path,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler._daao_file_handler = True  # type: ignore[attr-defined]
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s [%(threadName)s] %(message)s"
        )
    )
    logger.addHandler(handler)
    return path
