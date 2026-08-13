# config/logging_config.py
"""Logging a consola y fichero rotatorio."""
from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

_FMT = "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"


def configure_logging(log_dir: Path, level: str = "INFO") -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()
    fmt = logging.Formatter(_FMT)
    con = logging.StreamHandler()
    con.setFormatter(fmt)
    root.addHandler(con)
    fh = logging.handlers.RotatingFileHandler(
        log_dir / "partes-transfer.log", maxBytes=5_000_000,
        backupCount=5, encoding="utf-8",
    )
    fh.setFormatter(fmt)
    root.addHandler(fh)
    # El SDK/cliente HTTP no debe inundar el log.
    logging.getLogger("httpx").setLevel(logging.WARNING)
