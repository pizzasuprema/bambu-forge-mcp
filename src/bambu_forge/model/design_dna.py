"""Design DNA Store — SQLite persistence for design lineage and metadata."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class DesignDnaStore:
    def __init__(self, db_path: str | Path = "design_dna.db"):
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS designs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT NOT NULL,
                source_type     TEXT NOT NULL,
                source_code     TEXT NOT NULL,
                mesh_path       TEXT NOT NULL,
                bbox            TEXT NOT NULL DEFAULT '[]',
                volume          REAL NOT NULL DEFAULT 0.0,
                triangle_count  INTEGER NOT NULL DEFAULT 0,
                parent_id       INTEGER REFERENCES designs(id),
                created_at      TEXT NOT NULL
            )
        """)
        self._conn.commit()

    def save(
        self,
        name: str,
        source_type: str,
        source_code: str,
        mesh_path: str,
        bbox: Any,
        volume: float,
        triangle_count: int,
        parent_id: int | None = None,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        cur = self._conn.execute(
            """INSERT INTO designs
               (name, source_type, source_code, mesh_path, bbox, volume,
                triangle_count, parent_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                name,
                source_type,
                source_code,
                mesh_path,
                json.dumps(bbox),
                volume,
                triangle_count,
                parent_id,
                now,
            ),
        )
        self._conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def get(self, design_id: int) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM designs WHERE id = ?", (design_id,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_dict(row)

    def list_designs(self, query: str | None = None) -> list[dict[str, Any]]:
        if query:
            like = f"%{query}%"
            rows = self._conn.execute(
                """SELECT * FROM designs
                   WHERE name LIKE ? OR source_code LIKE ?
                   ORDER BY created_at DESC""",
                (like, like),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM designs ORDER BY created_at DESC"
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def close(self) -> None:
        self._conn.close()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "name": row["name"],
            "source_type": row["source_type"],
            "source_code": row["source_code"],
            "mesh_path": row["mesh_path"],
            "bbox": json.loads(row["bbox"]),
            "volume": row["volume"],
            "triangle_count": row["triangle_count"],
            "parent_id": row["parent_id"],
            "created_at": row["created_at"],
        }
