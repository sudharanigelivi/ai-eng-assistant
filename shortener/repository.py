import sqlite3
import threading
from dataclasses import dataclass

SCHEMA = """
CREATE TABLE IF NOT EXISTS links (
    code        TEXT PRIMARY KEY,
    url         TEXT NOT NULL,
    created_at  INTEGER NOT NULL,
    expires_at  INTEGER,
    click_count INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS clicks (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    code     TEXT NOT NULL REFERENCES links(code) ON DELETE CASCADE,
    ts       INTEGER NOT NULL,
    referrer TEXT NOT NULL,
    device   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_clicks_code_ts ON clicks(code, ts);
"""


class DuplicateCodeError(Exception):
    pass


@dataclass(frozen=True)
class Link:
    code: str
    url: str
    created_at: int
    expires_at: int | None
    click_count: int


class SqliteRepository:
    """Persistence for links and click events.

    A single connection guarded by a lock keeps the implementation simple and
    works for both file and in-memory databases. Swap this class for a
    Postgres-backed one (same interface) to scale writes horizontally.
    """

    def __init__(self, path: str):
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        with self._lock:
            self._conn.execute("PRAGMA foreign_keys = ON")
            if path != ":memory:":
                self._conn.execute("PRAGMA journal_mode = WAL")
            self._conn.executescript(SCHEMA)

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def ping(self) -> bool:
        with self._lock:
            self._conn.execute("SELECT 1")
        return True

    def create_link(self, code: str, url: str, created_at: int, expires_at: int | None) -> Link:
        with self._lock:
            try:
                with self._conn:
                    self._conn.execute(
                        "INSERT INTO links (code, url, created_at, expires_at) VALUES (?, ?, ?, ?)",
                        (code, url, created_at, expires_at),
                    )
            except sqlite3.IntegrityError as exc:
                raise DuplicateCodeError(code) from exc
        return Link(code, url, created_at, expires_at, 0)

    def get_link(self, code: str) -> Link | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT code, url, created_at, expires_at, click_count FROM links WHERE code = ?",
                (code,),
            ).fetchone()
        return Link(**dict(row)) if row else None

    def delete_link(self, code: str) -> bool:
        with self._lock, self._conn:
            return self._conn.execute("DELETE FROM links WHERE code = ?", (code,)).rowcount > 0

    def record_click(self, code: str, ts: int, referrer: str, device: str) -> None:
        with self._lock, self._conn:
            updated = self._conn.execute(
                "UPDATE links SET click_count = click_count + 1 WHERE code = ?", (code,)
            ).rowcount
            if updated:
                self._conn.execute(
                    "INSERT INTO clicks (code, ts, referrer, device) VALUES (?, ?, ?, ?)",
                    (code, ts, referrer, device),
                )

    def analytics(self, code: str, since_ts: int, top_n: int = 10) -> dict:
        with self._lock:
            q = self._conn.execute
            by_day = q(
                "SELECT strftime('%Y-%m-%d', ts, 'unixepoch') AS day, COUNT(*) AS clicks "
                "FROM clicks WHERE code = ? AND ts >= ? GROUP BY day ORDER BY day",
                (code, since_ts),
            ).fetchall()
            referrers = q(
                "SELECT referrer AS name, COUNT(*) AS clicks FROM clicks "
                "WHERE code = ? AND ts >= ? GROUP BY referrer ORDER BY clicks DESC, name LIMIT ?",
                (code, since_ts, top_n),
            ).fetchall()
            devices = q(
                "SELECT device AS name, COUNT(*) AS clicks FROM clicks "
                "WHERE code = ? AND ts >= ? GROUP BY device ORDER BY clicks DESC, name",
                (code, since_ts),
            ).fetchall()
        return {
            "by_day": [dict(r) for r in by_day],
            "top_referrers": [dict(r) for r in referrers],
            "devices": [dict(r) for r in devices],
        }
