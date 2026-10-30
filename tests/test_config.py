from shortener.config import Settings


def test_render_hostname_sets_public_https_base_url(monkeypatch):
    monkeypatch.delenv("SHORTENER_BASE_URL", raising=False)
    monkeypatch.delenv("RENDER_EXTERNAL_URL", raising=False)
    monkeypatch.setenv("RENDER_EXTERNAL_HOSTNAME", "short.example.onrender.com")

    assert Settings.from_env().base_url == "https://short.example.onrender.com"


def test_render_external_url_is_used(monkeypatch):
    monkeypatch.delenv("SHORTENER_BASE_URL", raising=False)
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://short.example.onrender.com")

    assert Settings.from_env().base_url == "https://short.example.onrender.com"


def test_explicit_base_url_overrides_render_hostname(monkeypatch):
    monkeypatch.setenv("SHORTENER_BASE_URL", "https://links.example.com/")
    monkeypatch.setenv("RENDER_EXTERNAL_HOSTNAME", "short.example.onrender.com")

    assert Settings.from_env().base_url == "https://links.example.com"


def test_demo_mode_is_explicitly_enabled_by_environment(monkeypatch):
    monkeypatch.setenv("SHORTENER_DEMO_MODE", "true")

    assert Settings.from_env().demo_mode is True
