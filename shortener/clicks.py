from urllib.parse import urlsplit

_BOT_MARKERS = ("bot", "crawler", "spider", "slurp", "curl", "wget", "python-requests", "httpx")


def classify_device(user_agent: str | None) -> str:
    ua = (user_agent or "").lower()
    if not ua:
        return "unknown"
    if any(m in ua for m in _BOT_MARKERS):
        return "bot"
    if "ipad" in ua or "tablet" in ua:
        return "tablet"
    if "mobi" in ua or "android" in ua or "iphone" in ua:
        return "mobile"
    return "desktop"


def referrer_host(referrer: str | None) -> str:
    """Store only the referring host (privacy + bounded cardinality)."""
    if not referrer:
        return "direct"
    try:
        host = urlsplit(referrer).hostname
    except ValueError:
        return "direct"
    return (host or "direct").lower()[:255]
