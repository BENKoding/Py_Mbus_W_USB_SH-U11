from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


logger = logging.getLogger(__name__)


@dataclass
class DBConfig:
    path: str = "storage/data.sqlite"


def ensure_db(cfg: DBConfig) -> sqlite3.Connection:
    Path(cfg.path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(cfg.path, check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS measurements (
            ts REAL NOT NULL,
            unit_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            value REAL,
            PRIMARY KEY (ts, unit_id, name)
        );
        """
    )
    conn.commit()
    return conn


def insert_measurement(conn: sqlite3.Connection, ts: float, unit_id: int, name: str, value: float) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO measurements (ts, unit_id, name, value) VALUES (?, ?, ?, ?)",
        (ts, unit_id, name, value),
    )
    conn.commit()

