import secrets
import time
from datetime import datetime, timezone

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, Response

from .config import Settings
from .ratelimit import RateLimiter
from .repository import Link, SqliteRepository
from .schemas import AnalyticsResponse, CreateLinkRequest, ErrorResponse, LinkResponse
from .service import AliasTakenError, ExpiredError, NotFoundError, ShortenerService
from .validation import ValidationError

API_PREFIX = "/api/v1"


def _to_dt(ts: int | None) -> datetime | None:
    return datetime.fromtimestamp(ts, tz=timezone.utc) if ts is not None else None


def create_app(settings: Settings | None = None, clock=None) -> FastAPI:
    settings = settings or Settings.from_env()
    repo = SqliteRepository(settings.db_path)
    service = ShortenerService(repo, settings, clock or time.time)
    limiter = RateLimiter(settings.rate_limit_per_minute)

    app = FastAPI(
        title="Sudha Gelvi URL Shortener",
        version="1.0.0",
        description="Scalable URL shortener with persistence and click analytics.",
        contact={"name": "Sudha Gelvi"},
    )
    app.state.service = service
    app.state.repo = repo

    def require_api_key(x_api_key: str | None = Header(None)) -> None:
        if settings.api_key and not (
            x_api_key and secrets.compare_digest(x_api_key, settings.api_key)
        ):
            raise HTTPException(401, "Invalid or missing API key")

    def link_out(link: Link) -> LinkResponse:
        return LinkResponse(
            code=link.code,
            short_url=f"{settings.base_url}/{link.code}",
            url=link.url,
            created_at=_to_dt(link.created_at),
            expires_at=_to_dt(link.expires_at),
            click_count=link.click_count,
        )

    @app.get("/healthz", tags=["ops"])
    def healthz():
        repo.ping()
        return {"status": "ok"}

    @app.post(
        f"{API_PREFIX}/links",
        status_code=201,
        response_model=LinkResponse,
        responses={409: {"model": ErrorResponse}, 422: {"model": ErrorResponse},
                   429: {"model": ErrorResponse}},
        tags=["links"],
        dependencies=[Depends(require_api_key)],
    )
    def create_link(body: CreateLinkRequest, request: Request):
        client = request.client.host if request.client else "unknown"
        if not limiter.allow(client):
            raise HTTPException(429, "Rate limit exceeded")
        expires = None
        if body.expires_at is not None:
            if body.expires_at.tzinfo is None:
                raise HTTPException(422, "expires_at must include a timezone")
            expires = int(body.expires_at.timestamp())
        try:
            link = service.create(body.url, body.custom_alias, expires)
        except ValidationError as exc:
            raise HTTPException(422, str(exc)) from exc
        except AliasTakenError as exc:
            raise HTTPException(409, "Alias already in use") from exc
        return link_out(link)

    @app.get(
        f"{API_PREFIX}/links/{{code}}",
        response_model=LinkResponse,
        responses={404: {"model": ErrorResponse}},
        tags=["links"],
        dependencies=[Depends(require_api_key)],
    )
    def get_link(code: str):
        try:
            return link_out(service.get(code))
        except NotFoundError as exc:
            raise HTTPException(404, "Link not found") from exc

    @app.delete(
        f"{API_PREFIX}/links/{{code}}",
        status_code=204,
        responses={404: {"model": ErrorResponse}},
        tags=["links"],
        dependencies=[Depends(require_api_key)],
    )
    def delete_link(code: str):
        try:
            service.delete(code)
        except NotFoundError as exc:
            raise HTTPException(404, "Link not found") from exc
        return Response(status_code=204)

    @app.get(
        f"{API_PREFIX}/links/{{code}}/analytics",
        response_model=AnalyticsResponse,
        responses={404: {"model": ErrorResponse}},
        tags=["analytics"],
        dependencies=[Depends(require_api_key)],
    )
    def link_analytics(code: str, days: int = Query(7, ge=1, le=365)):
        try:
            return service.analytics(code, days)
        except NotFoundError as exc:
            raise HTTPException(404, "Link not found") from exc

    @app.get(
        "/{code}",
        status_code=302,
        responses={404: {"model": ErrorResponse}, 410: {"model": ErrorResponse}},
        tags=["redirect"],
    )
    def redirect(code: str, request: Request, background: BackgroundTasks):
        try:
            url = service.resolve(code)
        except NotFoundError as exc:
            raise HTTPException(404, "Link not found") from exc
        except ExpiredError as exc:
            raise HTTPException(410, "Link has expired") from exc
        # Recorded after the response is sent so analytics never slow redirects.
        background.add_task(
            service.record_click,
            code,
            request.headers.get("referer"),
            request.headers.get("user-agent"),
        )
        return RedirectResponse(url, status_code=302)

    return app
