import secrets
import string
import threading
import time
from dataclasses import dataclass
from typing import Callable

from .cache import TTLCache
from .clicks import classify_device, referrer_host
from .config import Settings
from .repository import DuplicateCodeError, Link, SqliteRepository
from .validation import ValidationError, validate_alias, validate_target_url

BASE62 = string.ascii_letters + string.digits
MAX_CODE_ATTEMPTS = 8


class NotFoundError(Exception):
    pass


class ExpiredError(Exception):
    pass


class AliasTakenError(Exception):
    pass


@dataclass(frozen=True)
class _CachedTarget:
    url: str
    expires_at: int | None


class ShortenerService:
    def __init__(
        self,
        repo: SqliteRepository,
        settings: Settings,
        clock: Callable[[], float] = time.time,
    ):
        self._repo = repo
        self._settings = settings
        self._clock = clock
        self._cache_fill_lock = threading.Lock()
        self._cache: TTLCache[_CachedTarget] = TTLCache(
            settings.cache_size, settings.cache_ttl_seconds
        )

    def _now(self) -> int:
        return int(self._clock())

    def _random_code(self) -> str:
        # Random codes need no cross-node coordination and are not enumerable.
        return "".join(secrets.choice(BASE62) for _ in range(self._settings.code_length))

    def create(self, url: str, alias: str | None = None, expires_at: int | None = None) -> Link:
        url = validate_target_url(url)
        now = self._now()
        if expires_at is not None and expires_at <= now:
            raise ValidationError("expires_at must be in the future")
        if alias is not None:
            try:
                return self._repo.create_link(validate_alias(alias), url, now, expires_at)
            except DuplicateCodeError as exc:
                raise AliasTakenError(alias) from exc
        for _ in range(MAX_CODE_ATTEMPTS):
            try:
                return self._repo.create_link(self._random_code(), url, now, expires_at)
            except DuplicateCodeError:
                continue
        raise RuntimeError("could not allocate a unique short code")

    def get(self, code: str) -> Link:
        link = self._repo.get_link(code)
        if link is None:
            raise NotFoundError(code)
        return link

    def resolve(self, code: str) -> str:
        """Return the target URL for a redirect (cache first, then the database)."""
        target = self._cache.get(code)
        if target is None:
            # Serialize cache misses with deletion so an older database read
            # cannot refill the cache after delete() invalidates the code.
            with self._cache_fill_lock:
                target = self._cache.get(code)
                if target is None:
                    link = self._repo.get_link(code)
                    if link is None:
                        raise NotFoundError(code)
                    target = _CachedTarget(link.url, link.expires_at)
                    self._cache.set(code, target)
        if target.expires_at is not None and target.expires_at <= self._now():
            raise ExpiredError(code)
        return target.url

    def delete(self, code: str) -> None:
        with self._cache_fill_lock:
            if not self._repo.delete_link(code):
                raise NotFoundError(code)
            self._cache.invalidate(code)

    def record_click(self, code: str, referrer: str | None, user_agent: str | None) -> None:
        self._repo.record_click(
            code, self._now(), referrer_host(referrer), classify_device(user_agent)
        )

    def analytics(self, code: str, days: int) -> dict:
        link = self.get(code)
        since = self._now() - days * 86400
        data = self._repo.analytics(code, since)
        return {
            "code": code,
            "total_clicks": link.click_count,
            "window_days": days,
            "clicks_in_window": sum(d["clicks"] for d in data["by_day"]),
            **data,
        }
