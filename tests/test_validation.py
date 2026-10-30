import pytest

from shortener.validation import ValidationError, validate_alias, validate_target_url


@pytest.mark.parametrize("url", [
    "https://example.com", "http://example.com/a/b?q=1#x", "https://sub.example.co.uk:8443/p",
    "https://93.184.216.34/x",
])
def test_valid_urls(url):
    assert validate_target_url(url) == url


@pytest.mark.parametrize("url", [
    "", "   ", "ftp://example.com", "javascript:alert(1)", "data:text/html,hi", "//example.com",
    "https://", "https://user:pw@example.com", "https://example.com/a b",
    "http://localhost/admin", "http://app.localhost/", "http://127.0.0.1/", "http://10.0.0.5/",
    "http://192.168.1.1/", "http://169.254.169.254/latest/meta-data", "http://[::1]/",
    "https://example.com:99999/", "https://example.com/" + "a" * 2100, "https://exa\nmple.com",
])
def test_invalid_urls(url):
    with pytest.raises(ValidationError):
        validate_target_url(url)


def test_url_is_stripped():
    assert validate_target_url("  https://example.com  ") == "https://example.com"


@pytest.mark.parametrize("alias", ["abcd", "My_Link-1", "a" * 32])
def test_valid_alias(alias):
    assert validate_alias(alias) == alias


@pytest.mark.parametrize("alias", ["abc", "a" * 33, "has space", "dot.dot", "api", "API", "docs", "ünï"])
def test_invalid_alias(alias):
    with pytest.raises(ValidationError):
        validate_alias(alias)
