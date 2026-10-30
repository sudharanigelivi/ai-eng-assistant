import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    db_path: str = "shortener.db"
    base_url: str = "http://localhost:8000"
    api_key: str | None = None  # when set, /api/v1 requires X-API-Key
    code_length: int = 7
    cache_size: int = 10_000
    cache_ttl_seconds: int = 60
    rate_limit_per_minute: int = 60  # create-link calls per client; 0 disables

    @classmethod
    def from_env(cls) -> "Settings":
        env = os.environ
        return cls(
            db_path=env.get("SHORTENER_DB_PATH", cls.db_path),
            base_url=env.get("SHORTENER_BASE_URL", cls.base_url).rstrip("/"),
            api_key=env.get("SHORTENER_API_KEY") or None,
            code_length=int(env.get("SHORTENER_CODE_LENGTH", cls.code_length)),
            cache_size=int(env.get("SHORTENER_CACHE_SIZE", cls.cache_size)),
            cache_ttl_seconds=int(env.get("SHORTENER_CACHE_TTL", cls.cache_ttl_seconds)),
            rate_limit_per_minute=int(
                env.get("SHORTENER_RATE_LIMIT", cls.rate_limit_per_minute)
            ),
        )
