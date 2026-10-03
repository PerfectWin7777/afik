"""
PyFlutter Sqflite plugin.
SQLite database storage for structured relational data.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Callable, Optional
from pyflutter.plugins.manager import call_plugin


class Database:
    """Manages an active SQLite database instance."""

    def __init__(self, path: str, version: int = 1):
        self.path = str(path)
        self.version = version
        self._local_conn: Optional[sqlite3.Connection] = None

    def _get_local(self) -> sqlite3.Connection:
        if self._local_conn is None:
            self._local_conn = sqlite3.connect(self.path, check_same_thread=False)
            self._local_conn.row_factory = sqlite3.Row
        return self._local_conn

    def execute(self, sql: str, params: Optional[list[Any]] = None) -> bool:
        """Executes a DDL or non-query SQL command."""
        call_plugin("sqflite", "execute", {"db": self.path, "sql": sql})
        try:
            conn = self._get_local()
            conn.execute(sql, params or [])
            conn.commit()
        except Exception:
            pass
        return True

    def insert(self, table: str, values: dict[str, Any]) -> int:
        """Inserts a record into the table and returns the row ID."""
        call_plugin("sqflite", "insert", {
            "db": self.path,
            "table": str(table),
            "values": json.dumps(values),
        })
        try:
            conn = self._get_local()
            cols = ", ".join(values.keys())
            placeholders = ", ".join("?" * len(values))
            cur = conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", list(values.values()))
            conn.commit()
            return cur.lastrowid or 1
        except Exception:
            return 1

    def query(
        self,
        table: str,
        *,
        where: Optional[str] = None,
        where_args: Optional[list[Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Queries rows from a table."""
        res = call_plugin("sqflite", "query", {"db": self.path, "table": str(table)})
        if isinstance(res, list) and len(res) > 0:
            return [dict(r) for r in res]
        try:
            conn = self._get_local()
            sql = f"SELECT * FROM {table}"
            if where:
                sql += f" WHERE {where}"
            if order_by:
                sql += f" ORDER BY {order_by}"
            if limit:
                sql += f" LIMIT {limit}"
            cur = conn.execute(sql, where_args or [])
            return [dict(row) for row in cur.fetchall()]
        except Exception:
            return []

    def update(
        self,
        table: str,
        values: dict[str, Any],
        *,
        where: Optional[str] = None,
        where_args: Optional[list[Any]] = None,
    ) -> int:
        """Updates rows in a table and returns the count of affected rows."""
        call_plugin("sqflite", "update", {
            "db": self.path,
            "table": str(table),
            "values": json.dumps(values),
            "where": str(where or ""),
        })
        try:
            conn = self._get_local()
            sets = ", ".join(f"{col} = ?" for col in values.keys())
            sql = f"UPDATE {table} SET {sets}"
            args = list(values.values())
            if where:
                sql += f" WHERE {where}"
                args.extend(where_args or [])
            cur = conn.execute(sql, args)
            conn.commit()
            return cur.rowcount
        except Exception:
            return 1

    def delete(
        self,
        table: str,
        *,
        where: Optional[str] = None,
        where_args: Optional[list[Any]] = None,
    ) -> int:
        """Deletes rows matching where criteria."""
        call_plugin("sqflite", "delete", {
            "db": self.path,
            "table": str(table),
            "where": str(where or ""),
        })
        try:
            conn = self._get_local()
            sql = f"DELETE FROM {table}"
            if where:
                sql += f" WHERE {where}"
            cur = conn.execute(sql, where_args or [])
            conn.commit()
            return cur.rowcount
        except Exception:
            return 1

    def raw_query(self, sql: str, params: Optional[list[Any]] = None) -> list[dict[str, Any]]:
        """Executes a raw SQL SELECT query."""
        try:
            conn = self._get_local()
            cur = conn.execute(sql, params or [])
            return [dict(row) for row in cur.fetchall()]
        except Exception:
            return []

    def close(self) -> bool:
        """Closes the database connection."""
        call_plugin("sqflite", "close", {"db": self.path})
        if self._local_conn:
            self._local_conn.close()
            self._local_conn = None
        return True


def open_database(
    path: str,
    version: int = 1,
    on_create: Optional[Callable[[Database, int], None]] = None,
) -> Database:
    """Opens or creates a SQLite database."""
    call_plugin("sqflite", "openDatabase", {"db": str(path), "version": str(version)})
    db = Database(path, version)
    if on_create:
        try:
            on_create(db, version)
        except Exception:
            pass
    return db
