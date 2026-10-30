import pytest
from fastapi.testclient import TestClient

from shortener.api import create_app
from shortener.config import Settings


class FakeClock:
    def __init__(self, now: float = 1_700_000_000):
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def make_client(tmp_path, clock):
    clients = []

    def _make(**overrides):
        settings = Settings(
            db_path=str(tmp_path / "t.db"), base_url="http://sho.rt",
            rate_limit_per_minute=overrides.pop("rate_limit_per_minute", 0),
            demo_mode=overrides.pop("demo_mode", False), **overrides
        )
        client = TestClient(create_app(settings, clock=clock), follow_redirects=False)
        clients.append(client)
        return client

    yield _make
    for c in clients:
        c.app.state.repo.close()


@pytest.fixture
def client(make_client):
    return make_client()
