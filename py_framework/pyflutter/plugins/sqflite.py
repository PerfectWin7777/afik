"""
PyFlutter Sqflite plugin.
SQLite database storage for structured relational data.
"""

from __future__ import annotations

import re
import sqlite3
from typing import Any, Callable, Optional
from pyflutter.plugins.manager import call_plugin


_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?$")


def _ident(name: str) -> str:
    """Validates a table/column name before it is interpolated into SQL."""
    name = str(name)
    if not _IDENTIFIER.match(name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return name


class Database:
    """Manages an active SQLite database instance.

    SQLite runs in-process through Python's sqlite3 module, which is the single
    source of truth. Errors are raised (never replaced by fake row ids).
    """

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
        conn = self._get_local()
        conn.execute(sql, params or [])
        conn.commit()
        return True

    def insert(self, table: str, values: dict[str, Any]) -> int:
        """Inserts a record into the table and returns the row ID."""
        conn = self._get_local()
        cols = ", ".join(_ident(c) for c in values.keys())
        placeholders = ", ".join("?" * len(values))
        cur = conn.execute(
            f"INSERT INTO {_ident(table)} ({cols}) VALUES ({placeholders})", list(values.values())
        )
        conn.commit()
        return cur.lastrowid

    def query(
        self,
        table: str,
        *,
        where: Optional[str] = None,
        where_args: Optional[list[Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Queries rows from a table. `where` / `order_by` are SQL fragments written by
        the developer: pass user input through `where_args` placeholders only."""
        conn = self._get_local()
        sql = f"SELECT * FROM {_ident(table)}"
        if where:
            sql += f" WHERE {where}"
        if order_by:
            sql += f" ORDER BY {order_by}"
        if limit is not None:
            sql += f" LIMIT {int(limit)}"
        cur = conn.execute(sql, where_args or [])
        return [dict(row) for row in cur.fetchall()]

    def update(
        self,
        table: str,
        values: dict[str, Any],
        *,
        where: Optional[str] = None,
        where_args: Optional[list[Any]] = None,
    ) -> int:
        """Updates rows in a table and returns the count of affected rows."""
        conn = self._get_local()
        sets = ", ".join(f"{_ident(col)} = ?" for col in values.keys())
        sql = f"UPDATE {_ident(table)} SET {sets}"
        args = list(values.values())
        if where:
            sql += f" WHERE {where}"
            args.extend(where_args or [])
        cur = conn.execute(sql, args)
        conn.commit()
        return cur.rowcount

    def delete(
        self,
        table: str,
        *,
        where: Optional[str] = None,
        where_args: Optional[list[Any]] = None,
    ) -> int:
        """Deletes rows matching where criteria."""
        conn = self._get_local()
        sql = f"DELETE FROM {_ident(table)}"
        if where:
            sql += f" WHERE {where}"
        cur = conn.execute(sql, where_args or [])
        conn.commit()
        return cur.rowcount

    def raw_query(self, sql: str, params: Optional[list[Any]] = None) -> list[dict[str, Any]]:
        """Executes a raw SQL SELECT query."""
        conn = self._get_local()
        cur = conn.execute(sql, params or [])
        return [dict(row) for row in cur.fetchall()]

    def close(self) -> bool:
        """Closes the database connection."""
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
    db = Database(path, version)
    db._get_local()
    if on_create:
        on_create(db, version)
    return db
