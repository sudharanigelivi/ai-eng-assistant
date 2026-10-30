import threading

import pytest

from shortener.config import Settings
from shortener.repository import DuplicateCodeError, SqliteRepository
from shortener.service import AliasTakenError, NotFoundError, ShortenerService
from shortener.validation import ValidationError


def make_service(code_length=7):
    repo = SqliteRepository(":memory:")
    return ShortenerService(repo, Settings(code_length=code_length), clock=lambda: 1000), repo


def test_collision_retry_then_success(monkeypatch):
    svc, _ = make_service()
    codes = iter(["aaaaaaa", "aaaaaaa", "bbbbbbb"])
    monkeypatch.setattr(svc, "_random_code", lambda: next(codes))
    assert svc.create("https://e.com").code == "aaaaaaa"
    assert svc.create("https://e.com").code == "bbbbbbb"  # second attempt collided, retried


def test_collision_exhaustion_raises(monkeypatch):
    svc, _ = make_service()
    monkeypatch.setattr(svc, "_random_code", lambda: "aaaaaaa")
    svc.create("https://e.com")
    with pytest.raises(RuntimeError):
        svc.create("https://e.com")


def test_alias_taken():
    svc, _ = make_service()
    svc.create("https://e.com", alias="abcd")
    with pytest.raises(AliasTakenError):
        svc.create("https://e.com", alias="abcd")


def test_expiry_must_be_future():
    svc, _ = make_service()
    with pytest.raises(ValidationError):
        svc.create("https://e.com", expires_at=1000)


def test_resolve_uses_cache(monkeypatch):
    svc, repo = make_service()
    code = svc.create("https://e.com").code
    svc.resolve(code)
    monkeypatch.setattr(repo, "get_link", lambda c: pytest.fail("cache miss"))
    assert svc.resolve(code) == "https://e.com"


def test_delete_cannot_be_followed_by_stale_cache_fill(monkeypatch):
    svc, repo = make_service()
    code = svc.create("https://e.com").code
    original_get = repo.get_link
    original_invalidate = svc._cache.invalidate
    lookup_started = threading.Event()
    continue_lookup = threading.Event()
    invalidated = threading.Event()

    def blocked_get(link_code):
        link = original_get(link_code)
        lookup_started.set()
        assert continue_lookup.wait(timeout=2)
        return link

    def observed_invalidate(link_code):
        original_invalidate(link_code)
        invalidated.set()

    monkeypatch.setattr(repo, "get_link", blocked_get)
    monkeypatch.setattr(svc._cache, "invalidate", observed_invalidate)
    resolved = []
    resolver = threading.Thread(target=lambda: resolved.append(svc.resolve(code)))
    deleter = threading.Thread(target=lambda: svc.delete(code))

    resolver.start()
    assert lookup_started.wait(timeout=1)
    deleter.start()
    invalidated.wait(timeout=0.1)
    continue_lookup.set()
    resolver.join(timeout=2)
    deleter.join(timeout=2)

    assert not resolver.is_alive() and not deleter.is_alive()
    assert resolved == ["https://e.com"]
    with pytest.raises(NotFoundError):
        svc.resolve(code)


def test_code_length_setting():
    svc, _ = make_service(code_length=10)
    assert len(svc.create("https://e.com").code) == 10
