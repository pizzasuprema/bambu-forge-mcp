from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class PrintHistoryStore:
    def __init__(self, db_path: str | Path = "history.db"):
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS print_history (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                design_name         TEXT NOT NULL,
                design_id           INTEGER,
                profile_name        TEXT,
                printer_model       TEXT,
                filament_type       TEXT,
                filament_grams      REAL,
                print_time_minutes  INTEGER,
                outcome             TEXT NOT NULL,
                quality_grade       TEXT,
                failure_mode        TEXT,
                settings_json       TEXT,
                notes               TEXT,
                created_at          TEXT NOT NULL
            );
        """)
        self._conn.commit()

    def log_print(
        self,
        design_name: str,
        profile_name: str,
        printer_model: str,
        filament_type: str,
        filament_grams: float,
        print_time_minutes: int,
        outcome: str,
        quality_grade: str | None = None,
        failure_mode: str | None = None,
        settings: dict[str, Any] | None = None,
        notes: str | None = None,
        design_id: int | None = None,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        cur = self._conn.execute(
            """INSERT INTO print_history
               (design_name, design_id, profile_name, printer_model,
                filament_type, filament_grams, print_time_minutes,
                outcome, quality_grade, failure_mode, settings_json, notes, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                design_name, design_id, profile_name, printer_model,
                filament_type, filament_grams, print_time_minutes,
                outcome, quality_grade, failure_mode,
                json.dumps(settings) if settings else None,
                notes, now,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def list_history(
        self,
        limit: int = 50,
        outcome: str | None = None,
        filament_type: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if outcome:
            clauses.append("outcome = ?")
            params.append(outcome)
        if filament_type:
            clauses.append("filament_type = ?")
            params.append(filament_type)

        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        rows = self._conn.execute(
            f"SELECT * FROM print_history{where} ORDER BY created_at DESC LIMIT ?",
            params,
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_insights(self, printer_model: str | None = None) -> dict[str, Any]:
        where = ""
        params: list[Any] = []
        if printer_model:
            where = " WHERE printer_model = ?"
            params = [printer_model]

        row = self._conn.execute(
            f"SELECT COUNT(*) as total, "
            f"SUM(CASE WHEN outcome='success' THEN 1 ELSE 0 END) as successes, "
            f"AVG(print_time_minutes) as avg_time, "
            f"SUM(filament_grams) as total_filament "
            f"FROM print_history{where}",
            params,
        ).fetchone()

        total = row["total"] or 0
        successes = row["successes"] or 0

        filament_rows = self._conn.execute(
            f"SELECT filament_type, COUNT(*) as cnt FROM print_history{where} "
            f"GROUP BY filament_type ORDER BY cnt DESC LIMIT 1",
            params,
        ).fetchall()

        if printer_model:
            failure_rows = self._conn.execute(
                "SELECT failure_mode, COUNT(*) as cnt FROM print_history "
                "WHERE printer_model = ? AND failure_mode IS NOT NULL "
                "GROUP BY failure_mode ORDER BY cnt DESC LIMIT 1",
                [printer_model],
            ).fetchall()
        else:
            failure_rows = self._conn.execute(
                "SELECT failure_mode, COUNT(*) as cnt FROM print_history "
                "WHERE failure_mode IS NOT NULL "
                "GROUP BY failure_mode ORDER BY cnt DESC LIMIT 1",
            ).fetchall()

        return {
            "total_prints": total,
            "success_rate": round(successes / total, 4) if total else 0.0,
            "avg_print_time": round(row["avg_time"], 2) if row["avg_time"] else 0.0,
            "total_filament_grams": round(row["total_filament"], 2) if row["total_filament"] else 0.0,
            "most_used_filament": filament_rows[0]["filament_type"] if filament_rows else None,
            "most_common_failure_mode": failure_rows[0]["failure_mode"] if failure_rows else None,
        }

    def get_profile_success_rate(self, profile_name: str) -> dict[str, Any]:
        row = self._conn.execute(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN outcome='success' THEN 1 ELSE 0 END) as successes "
            "FROM print_history WHERE profile_name = ?",
            (profile_name,),
        ).fetchone()

        total = row["total"] or 0
        successes = row["successes"] or 0

        return {
            "profile_name": profile_name,
            "total_prints": total,
            "success_rate": round(successes / total, 4) if total else 0.0,
        }

    def close(self):
        self._conn.close()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        d = dict(row)
        if d.get("settings_json"):
            d["settings"] = json.loads(d["settings_json"])
        else:
            d["settings"] = None
        del d["settings_json"]
        return d
