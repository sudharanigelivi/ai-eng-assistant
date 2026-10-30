import pytest

from shortener.config import Settings
from shortener.repository import DuplicateCodeError, SqliteRepository
from shortener.service import AliasTakenError, ShortenerService
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


def test_code_length_setting():
    svc, _ = make_service(code_length=10)
    assert len(svc.create("https://e.com").code) == 10
