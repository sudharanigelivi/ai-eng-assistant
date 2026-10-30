import pytest

from shortener.clicks import classify_device, referrer_host


@pytest.mark.parametrize("ua,expected", [
    (None, "unknown"), ("", "unknown"),
    ("Googlebot/2.1", "bot"), ("curl/8.0", "bot"),
    ("Mozilla/5.0 (iPad; CPU OS 16)", "tablet"),
    ("Mozilla/5.0 (iPhone; CPU iPhone OS 16) Mobile", "mobile"),
    ("Mozilla/5.0 (Linux; Android 13)", "mobile"),
    ("Mozilla/5.0 (X11; Linux x86_64) Firefox/120", "desktop"),
])
def test_classify_device(ua, expected):
    assert classify_device(ua) == expected


@pytest.mark.parametrize("ref,expected", [
    (None, "direct"), ("", "direct"), ("not a url", "direct"),
    ("https://News.Example.com/path?q=secret", "news.example.com"),
    ("http://[bad", "direct"),
])
def test_referrer_host_strips_path_and_query(ref, expected):
    assert referrer_host(ref) == expected
