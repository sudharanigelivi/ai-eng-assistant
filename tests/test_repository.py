import threading

import pytest

from shortener.repository import DuplicateCodeError, SqliteRepository


@pytest.fixture(params=[":memory:", "file"])
def repo(request, tmp_path):
    r = SqliteRepository(":memory:" if request.param == ":memory:" else str(tmp_path / "r.db"))
    yield r
    r.close()


def test_create_get_delete(repo):
    link = repo.create_link("abc1234", "https://e.com", 100, None)
    assert repo.get_link("abc1234") == link
    assert repo.delete_link("abc1234") is True
    assert repo.get_link("abc1234") is None
    assert repo.delete_link("abc1234") is False


def test_duplicate_code(repo):
    repo.create_link("abc1234", "https://e.com", 100, None)
    with pytest.raises(DuplicateCodeError):
        repo.create_link("abc1234", "https://other.com", 100, None)


def test_sql_injection_is_inert(repo):
    evil = "x'; DROP TABLE links; --"
    repo.create_link("abc1234", "https://e.com", 1, None)
    assert repo.get_link(evil) is None
    assert repo.get_link("abc1234") is not None


def test_click_for_missing_link_is_ignored(repo):
    repo.record_click("nope", 1, "direct", "desktop")
    assert repo.analytics("nope", 0)["by_day"] == []


def test_analytics_aggregation_and_window(repo):
    repo.create_link("abc1234", "https://e.com", 0, None)
    day1, day2 = 1_700_000_000, 1_700_000_000 + 86400
    for ts, ref, dev in [(day1, "direct", "desktop"), (day1, "a.com", "mobile"),
                         (day2, "a.com", "mobile"), (day2, "a.com", "bot")]:
        repo.record_click("abc1234", ts, ref, dev)
    data = repo.analytics("abc1234", 0)
    assert [d["clicks"] for d in data["by_day"]] == [2, 2]
    assert data["top_referrers"][0] == {"name": "a.com", "clicks": 3}
    assert {d["name"]: d["clicks"] for d in data["devices"]} == {"desktop": 1, "mobile": 2, "bot": 1}
    assert repo.get_link("abc1234").click_count == 4
    assert sum(d["clicks"] for d in repo.analytics("abc1234", day2)["by_day"]) == 2


def test_delete_cascades_clicks(repo):
    repo.create_link("abc1234", "https://e.com", 0, None)
    repo.record_click("abc1234", 1, "direct", "desktop")
    repo.delete_link("abc1234")
    assert repo._conn.execute("SELECT COUNT(*) FROM clicks").fetchone()[0] == 0


def test_concurrent_clicks_do_not_lose_counts(tmp_path):
    repo = SqliteRepository(str(tmp_path / "c.db"))
    repo.create_link("abc1234", "https://e.com", 0, None)

    def worker():
        for _ in range(50):
            repo.record_click("abc1234", 1, "direct", "desktop")

    threads = [threading.Thread(target=worker) for _ in range(8)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert repo.get_link("abc1234").click_count == 400
    assert repo.analytics("abc1234", 0)["by_day"][0]["clicks"] == 400
    repo.close()


def test_ping(repo):
    assert repo.ping()
