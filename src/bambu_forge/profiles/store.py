from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ProfileStore:
    def __init__(self, db_path: str | Path = "profiles.db"):
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS profiles (
                name        TEXT PRIMARY KEY,
                inherits    TEXT,
                overrides   TEXT NOT NULL DEFAULT '{}',
                profile_type TEXT,
                resolved    TEXT,
                created_at  TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS filaments (
                name        TEXT PRIMARY KEY,
                properties  TEXT NOT NULL DEFAULT '{}',
                created_at  TEXT NOT NULL
            );
        """)
        self._conn.commit()

    def save_profile(
        self,
        name: str,
        base_profile: str | None = None,
        overrides: dict[str, Any] | None = None,
        profile_type: str | None = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """INSERT OR REPLACE INTO profiles
               (name, inherits, overrides, profile_type, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (name, base_profile, json.dumps(overrides or {}), profile_type, now),
        )
        self._conn.commit()

    def get_profile(self, name: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM profiles WHERE name = ?", (name,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_profile(row)

    def list_profiles(self, profile_type: str | None = None) -> list[dict[str, Any]]:
        if profile_type:
            rows = self._conn.execute(
                "SELECT * FROM profiles WHERE profile_type = ? ORDER BY name",
                (profile_type,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM profiles ORDER BY name"
            ).fetchall()
        return [self._row_to_profile(r) for r in rows]

    def delete_profile(self, name: str) -> bool:
        cur = self._conn.execute("DELETE FROM profiles WHERE name = ?", (name,))
        self._conn.commit()
        return cur.rowcount > 0

    def save_resolved(self, name: str, resolved: dict[str, Any]) -> None:
        self._conn.execute(
            "UPDATE profiles SET resolved = ? WHERE name = ?",
            (json.dumps(resolved), name),
        )
        self._conn.commit()

    def save_filament(self, name: str, properties: dict[str, Any] | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """INSERT OR REPLACE INTO filaments (name, properties, created_at)
               VALUES (?, ?, ?)""",
            (name, json.dumps(properties or {}), now),
        )
        self._conn.commit()

    def list_filaments(self, filter_text: str | None = None) -> list[dict[str, Any]]:
        if filter_text:
            rows = self._conn.execute(
                "SELECT * FROM filaments WHERE name LIKE ? ORDER BY name",
                (f"%{filter_text}%",),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM filaments ORDER BY name"
            ).fetchall()
        return [self._row_to_filament(r) for r in rows]

    def close(self):
        self._conn.close()

    @staticmethod
    def _row_to_profile(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "name": row["name"],
            "inherits": row["inherits"],
            "overrides": json.loads(row["overrides"]),
            "profile_type": row["profile_type"],
            "resolved": json.loads(row["resolved"]) if row["resolved"] else None,
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_filament(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "name": row["name"],
            "properties": json.loads(row["properties"]),
            "created_at": row["created_at"],
        }
