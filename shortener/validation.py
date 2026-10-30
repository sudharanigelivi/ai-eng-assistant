import ipaddress
import re
from urllib.parse import urlsplit

MAX_URL_LENGTH = 2048
ALIAS_RE = re.compile(r"^[A-Za-z0-9_-]{4,32}$")
RESERVED_ALIASES = {"api", "healthz", "docs", "redoc", "openapi.json", "static"}
BLOCKED_HOSTS = {"localhost", "localhost.localdomain"}


class ValidationError(ValueError):
    pass


def validate_target_url(url: str) -> str:
    """Return the normalised URL or raise ValidationError.

    Only absolute http(s) URLs are accepted. Credentials and literal
    loopback/private hosts are rejected so the service cannot be used to
    redirect users to internal addresses.
    """
    url = url.strip()
    if not url or len(url) > MAX_URL_LENGTH:
        raise ValidationError(f"URL must be 1-{MAX_URL_LENGTH} characters")
    if any(ord(c) < 32 or c.isspace() for c in url):
        raise ValidationError("URL must not contain whitespace or control characters")
    try:
        parts = urlsplit(url)
        host = parts.hostname
        parts.port  # noqa: B018 - raises ValueError on an invalid port
    except ValueError as exc:
        raise ValidationError("URL is malformed") from exc
    if parts.scheme not in ("http", "https"):
        raise ValidationError("Only http and https URLs are allowed")
    if not host:
        raise ValidationError("URL must include a host")
    if parts.username or parts.password:
        raise ValidationError("URLs with embedded credentials are not allowed")
    if _is_internal_host(host):
        raise ValidationError("Internal or private hosts are not allowed")
    return url


def _is_internal_host(host: str) -> bool:
    host = host.lower().rstrip(".")
    if host in BLOCKED_HOSTS or host.endswith(".localhost"):
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return not ip.is_global


def validate_alias(alias: str) -> str:
    if not ALIAS_RE.match(alias):
        raise ValidationError("Alias must be 4-32 chars of letters, digits, '-' or '_'")
    if alias.lower() in RESERVED_ALIASES:
        raise ValidationError("Alias is reserved")
    return alias
