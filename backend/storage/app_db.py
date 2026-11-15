import os
import sqlite3
import threading
from contextlib import contextmanager


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
    full_name     TEXT NOT NULL DEFAULT '',
    role          TEXT NOT NULL CHECK (role IN ('admin', 'employee')),
    password_hash TEXT NOT NULL,
    active        INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL,
    last_login    TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    actor     TEXT NOT NULL,
    role      TEXT NOT NULL,
    action    TEXT NOT NULL,
    target    TEXT NOT NULL DEFAULT '',
    details   TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_log (timestamp);

CREATE TABLE IF NOT EXISTS email_events (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp        TEXT NOT NULL,
    channel          TEXT NOT NULL,
    sender           TEXT NOT NULL DEFAULT '',
    subject          TEXT NOT NULL DEFAULT '',
    query            TEXT NOT NULL DEFAULT '',
    intent           TEXT NOT NULL DEFAULT 'UNKNOWN',
    route            TEXT NOT NULL,
    confidence_level TEXT NOT NULL DEFAULT '',
    top_score        REAL,
    email_sent       INTEGER NOT NULL DEFAULT 0,
    duration_ms      INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_email_time ON email_events (timestamp);

CREATE TABLE IF NOT EXISTS search_events (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp        TEXT NOT NULL,
    actor            TEXT NOT NULL DEFAULT '',
    query            TEXT NOT NULL,
    intent           TEXT NOT NULL DEFAULT 'UNKNOWN',
    route            TEXT NOT NULL DEFAULT '',
    confidence_level TEXT NOT NULL DEFAULT '',
    top_score        REAL,
    duration_ms      INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_search_time ON search_events (timestamp);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class AppDatabase:
    """
    Small SQLite database for accounts, the audit log, analytics
    events and runtime settings. One connection per operation keeps
    it safe to use from API worker threads and the scheduler thread.
    """

    def __init__(self, path=None):

        self.path = path or os.getenv(
            "APP_DB_PATH",
            os.path.join(
                os.getenv("AUTOMATION_DATA_DIR", "data/automation"),
                "app.db"
            )
        )

        directory = os.path.dirname(self.path)

        if directory:
            os.makedirs(directory, exist_ok=True)

        self._write_lock = threading.Lock()

        with self.connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript(SCHEMA)

    @contextmanager
    def connect(self):

        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row

        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def query(self, sql, params=()):

        with self.connect() as connection:
            return [dict(row) for row in connection.execute(sql, params).fetchall()]

    def execute(self, sql, params=()):

        with self._write_lock, self.connect() as connection:
            cursor = connection.execute(sql, params)
            return cursor.lastrowid

    # ========================================================
    # SETTINGS
    # ========================================================

    def get_setting(self, key, default=None):

        rows = self.query("SELECT value FROM settings WHERE key = ?", (key,))

        return rows[0]["value"] if rows else default

    def set_setting(self, key, value):

        self.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value))
        )
