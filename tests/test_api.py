import concurrent.futures
from datetime import datetime, timedelta, timezone

from shortener.service import BASE62


def create(client, **body):
    body.setdefault("url", "https://example.com/some/long/path")
    return client.post("/api/v1/links", json=body)


def test_create_and_redirect(client):
    r = create(client)
    assert r.status_code == 201
    body = r.json()
    assert len(body["code"]) == 7 and set(body["code"]) <= set(BASE62)
    assert body["short_url"] == f"http://sho.rt/{body['code']}"
    assert body["click_count"] == 0
    redirect = client.get(f"/{body['code']}")
    assert redirect.status_code == 302
    assert redirect.headers["location"] == "https://example.com/some/long/path"


def test_codes_are_unique(client):
    codes = {create(client).json()["code"] for _ in range(50)}
    assert len(codes) == 50


def test_custom_alias_and_conflict(client):
    assert create(client, custom_alias="my-link").json()["code"] == "my-link"
    assert create(client, custom_alias="my-link").status_code == 409
    assert client.get("/my-link").status_code == 302


def test_invalid_inputs_return_422(client):
    assert create(client, url="javascript:alert(1)").status_code == 422
    assert create(client, url="http://127.0.0.1/").status_code == 422
    assert create(client, custom_alias="api").status_code == 422
    assert create(client, custom_alias="x").status_code == 422
    assert client.post("/api/v1/links", json={}).status_code == 422
    assert client.post("/api/v1/links", content="not json").status_code == 422


def test_expiry(client, clock):
    exp = datetime.fromtimestamp(clock.now, tz=timezone.utc) + timedelta(hours=1)
    code = create(client, expires_at=exp.isoformat()).json()["code"]
    assert client.get(f"/{code}").status_code == 302
    clock.advance(3599)
    assert client.get(f"/{code}").status_code == 302
    clock.advance(1)
    assert client.get(f"/{code}").status_code == 410


def test_expiry_validation(client, clock):
    past = datetime.fromtimestamp(clock.now - 10, tz=timezone.utc).isoformat()
    assert create(client, expires_at=past).status_code == 422
    assert create(client, expires_at="2099-01-01T00:00:00").status_code == 422  # naive


def test_unknown_code_404(client):
    assert client.get("/nope123").status_code == 404
    assert client.get("/api/v1/links/nope123").status_code == 404
    assert client.get("/api/v1/links/nope123/analytics").status_code == 404
    assert client.delete("/api/v1/links/nope123").status_code == 404


def test_get_link(client):
    code = create(client).json()["code"]
    r = client.get(f"/api/v1/links/{code}")
    assert r.status_code == 200 and r.json()["code"] == code


def test_delete_invalidates_cache(client):
    code = create(client).json()["code"]
    assert client.get(f"/{code}").status_code == 302  # warms cache
    assert client.delete(f"/api/v1/links/{code}").status_code == 204
    assert client.get(f"/{code}").status_code == 404


def test_analytics_flow(client, clock):
    code = create(client).json()["code"]
    h = {"referer": "https://news.example.org/story?id=1", "user-agent": "Mozilla/5.0 iPhone Mobile"}
    client.get(f"/{code}", headers=h)
    client.get(f"/{code}", headers=h)
    client.get(f"/{code}", headers={"user-agent": "Mozilla/5.0 X11 Linux"})
    clock.advance(86400)
    client.get(f"/{code}", headers={"user-agent": "Googlebot/2.1"})

    a = client.get(f"/api/v1/links/{code}/analytics?days=7").json()
    assert a["total_clicks"] == 4 and a["clicks_in_window"] == 4
    assert [d["clicks"] for d in a["by_day"]] == [3, 1]
    assert {"name": "news.example.org", "clicks": 2} in a["top_referrers"]
    assert {d["name"]: d["clicks"] for d in a["devices"]} == {"mobile": 2, "desktop": 1, "bot": 1}
    assert "story" not in str(a)  # path/query never stored
    assert client.get(f"/api/v1/links/{code}").json()["click_count"] == 4


def test_failed_redirects_are_not_counted(client):
    client.get("/missing1")
    code = create(client).json()["code"]
    assert client.get(f"/api/v1/links/{code}").json()["click_count"] == 0


def test_analytics_days_bounds(client):
    code = create(client).json()["code"]
    assert client.get(f"/api/v1/links/{code}/analytics?days=0").status_code == 422
    assert client.get(f"/api/v1/links/{code}/analytics?days=366").status_code == 422


def test_analytics_window_excludes_old_clicks(client, clock):
    code = create(client).json()["code"]
    client.get(f"/{code}")
    clock.advance(10 * 86400)
    a = client.get(f"/api/v1/links/{code}/analytics?days=7").json()
    assert a["total_clicks"] == 1 and a["clicks_in_window"] == 0


def test_rate_limit(make_client):
    c = make_client(rate_limit_per_minute=3)
    assert [create(c).status_code for _ in range(4)] == [201, 201, 201, 429]


def test_api_key_protects_management_not_redirect(make_client):
    c = make_client(api_key="s3cret")
    assert create(c).status_code == 401
    assert c.post("/api/v1/links", json={"url": "https://e.com"},
                  headers={"x-api-key": "wrong"}).status_code == 401
    ok = c.post("/api/v1/links", json={"url": "https://e.com"}, headers={"x-api-key": "s3cret"})
    assert ok.status_code == 201
    code = ok.json()["code"]
    assert c.get(f"/{code}").status_code == 302
    assert c.get(f"/api/v1/links/{code}/analytics").status_code == 401


def test_healthz_and_openapi(client):
    assert client.get("/healthz").json() == {"status": "ok"}
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/links" in paths and "/api/v1/links/{code}/analytics" in paths


def test_concurrent_redirects_count_every_click(client):
    code = create(client).json()["code"]
    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        results = list(pool.map(lambda _: client.get(f"/{code}").status_code, range(40)))
    assert set(results) == {302}
    assert client.get(f"/api/v1/links/{code}").json()["click_count"] == 40


def test_data_persists_across_restart(tmp_path, clock):
    from fastapi.testclient import TestClient

    from shortener.api import create_app
    from shortener.config import Settings

    s = Settings(db_path=str(tmp_path / "p.db"), rate_limit_per_minute=0)
    app1 = create_app(s, clock=clock)
    code = TestClient(app1).post("/api/v1/links", json={"url": "https://e.com"}).json()["code"]
    app1.state.repo.close()
    app2 = create_app(s, clock=clock)
    r = TestClient(app2, follow_redirects=False).get(f"/{code}")
    assert r.status_code == 302
    app2.state.repo.close()
