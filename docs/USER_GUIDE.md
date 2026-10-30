# User Guide

This guide explains the public URL-shortener demo, local setup, API behavior, API-key handling, and the requirement planner.

## Hosted demo

The test service is available at:

- **Shortener form:** https://ai-eng-assistant-shortener-test.onrender.com/
- **Interactive API docs:** https://ai-eng-assistant-shortener-test.onrender.com/docs
- **Health check:** https://ai-eng-assistant-shortener-test.onrender.com/healthz

The root page is a browser form modeled on the reference demo. No API key is needed to create a demo link.

### Create a link in the form

1. Open the shortener form.
2. Paste an `http://` or `https://` address into **Drop Link**.
3. Optionally enter a **Short Name**. Aliases must contain 4–32 letters, digits, hyphens, or underscores. For example, `demo-link` is valid.
4. Select **Create Short Link**.
5. Copy the URL shown in **Shortened URL** and share it. Opening it redirects to the original target.

A successful response creates a 302 redirect. The form shows validation, alias-conflict, and rate-limit errors inline.

> **Test-service data is temporary.** The free test deployment stores its SQLite database under `/tmp`; links can disappear after a restart, redeploy, or service maintenance. The free service may also spin down while idle. Don’t use it for sensitive, valuable, or permanent links.

## API key and access rules

The test service has a generated `SHORTENER_API_KEY`, but demo visitors do not need it to create links. The key protects link metadata, analytics, and deletion. Keep it secret; do not put it in screenshots, public examples, browser JavaScript, or shared documents.

To view or rotate the test key, open the test service in Render, select **Environment**, then use the reveal/copy action for `SHORTENER_API_KEY`. If the key is exposed, rotate it in Render and redeploy.

| Operation | Test demo (`SHORTENER_DEMO_MODE=true`) | Default / production (`SHORTENER_DEMO_MODE=false`) |
|---|---|---|
| Open `/` and follow redirects | Public | Public |
| Create a link (`POST /api/v1/links`) | Public, rate-limited | Requires `X-API-Key` when `SHORTENER_API_KEY` is configured |
| Read metadata | Requires `X-API-Key` when configured | Requires `X-API-Key` when configured |
| Read analytics | Requires `X-API-Key` when configured | Requires `X-API-Key` when configured |
| Delete a link | Requires `X-API-Key` when configured | Requires `X-API-Key` when configured |
| Health check and API docs | Public | Public |

If no `SHORTENER_API_KEY` is configured, management endpoints are unauthenticated. Configure one for any publicly reachable non-demo deployment.

## API examples

### Create a random code

The public test demo allows this request without an API key:

```http
POST /api/v1/links
Content-Type: application/json

{"url":"https://example.com/a/long/page"}
```

The JSON response contains `code`, `short_url`, `url`, `created_at`, `expires_at`, and `click_count`. Use the returned `short_url`; codes are random, so don’t guess one in advance.

### Create a custom alias

```json
{"url":"https://example.com/a/long/page","custom_alias":"demo-link"}
```

Aliases must be 4–32 ASCII letters, digits, hyphens, or underscores. Aliases such as `api`, `healthz`, `docs`, `redoc`, `openapi.json`, and `static` are reserved. An already-used alias returns HTTP 409.

### Command-line example

On PowerShell, this creates a public test link without sending an API key:

```powershell
$body = @{ url = 'https://example.com/a/long/page' } | ConvertTo-Json
$result = Invoke-RestMethod -Uri 'https://ai-eng-assistant-shortener-test.onrender.com/api/v1/links' -Method Post -ContentType 'application/json' -Body $body
$result.short_url
```

For metadata, analytics, or deletion on the test service, add the key as an `X-API-Key` header. Keep the key in a local environment variable; do not commit it or paste it into a public terminal recording.

### API routes

| Method and path | Purpose | Typical responses |
|---|---|---|
| `GET /` | Demo form (in demo mode); otherwise a basic API landing page | 200 |
| `POST /api/v1/links` | Create a random or custom link | 201, 401, 409, 422, 429 |
| `GET /api/v1/links/{code}` | Read link metadata | 200, 401, 404 |
| `DELETE /api/v1/links/{code}` | Delete a link | 204, 401, 404 |
| `GET /api/v1/links/{code}/analytics?days=7` | Read analytics for 1–365 days | 200, 401, 404, 422 |
| `GET /{code}` | Redirect to the target | 302, 404, 410 |
| `GET /healthz` | Liveness check | 200 |
| `GET /docs` | Interactive OpenAPI docs | 200 |

A 410 response means the link expired. `expires_at` must be a future, timezone-aware ISO-8601 timestamp. The create rate limiter returns 429 when the configured per-client limit is exceeded.

## Security and privacy behavior

- Only HTTP and HTTPS target URLs are accepted. Embedded credentials, whitespace/control characters, overly long URLs, and literal localhost/private IP targets are rejected.
- The service does not fetch target URLs; it sends a 302 redirect to the browser. The URL checks do not resolve DNS names to detect private addresses.
- Click analytics store the referrer host and a coarse device class, not IP addresses or full referrer paths/queries.
- Click recording is performed after the redirect response. A process crash can therefore lose an analytics event.
- The test demo is intentionally public and rate-limited. Don’t submit private URLs or confidential information.

## Run locally

Use Python 3.10 or newer (the project is routinely tested with Python 3.12):

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

Run the URL shortener:

```powershell
uvicorn shortener.api:create_app --factory --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000/docs`. To display the browser form locally, set `SHORTENER_DEMO_MODE=true` before starting the server. In PowerShell:

```powershell
$env:SHORTENER_DEMO_MODE = 'true'
$env:SHORTENER_BASE_URL = 'http://127.0.0.1:8000'
uvicorn shortener.api:create_app --factory --host 127.0.0.1 --port 8000
```

The default local database file is `shortener.db`. Set `SHORTENER_DB_PATH` to choose another path. To run with management endpoints protected, set `SHORTENER_API_KEY` and leave demo mode disabled.

## Run the requirement planner

The planner accepts a requirement and emits a structured Markdown plan by default:

```powershell
python -m planner "Build a scalable URL shortener service with APIs, persistence, and analytics."
python -m planner --file examples/ambiguous.txt --format json
```

The planner covers greenfield, brownfield, and ambiguous requests. Its classification and plan generation use deterministic rules and curated templates; it does not call an LLM. Generated AI prompts are suggestions for engineer-directed work, not evidence that an external model ran those tasks.

## Tests and coverage

Install development dependencies as above, then run:

```powershell
python -m pytest --cov --cov-report=term-missing
```

Verified result in this repository: **111 passed, 96% total line coverage**. Tests use an injected clock for expiry and analytics, and cover URL validation, API authentication, rate limiting, persistence, redirects, analytics aggregation, planner scenarios, and the cache/delete concurrency regression.

## Deployment environments

- **Test demo:** [render.test.yaml](../render.test.yaml). Free plan, no persistent disk, demo creation enabled, 10 creates per minute per client. Data is ephemeral.
- **Production Blueprint:** [render.yaml](../render.yaml). Paid service plan and persistent disk; the Blueprint is configuration, not proof that a production service has been provisioned. Review current Render charges and ensure billing is set up before creating it. Keep demo mode disabled in production.

For deployment details and operational constraints, see [DEPLOYMENT.md](DEPLOYMENT.md). For system design, see [ARCHITECTURE.md](ARCHITECTURE.md). For assignment rationale and validation, see [../ENGINEERING_SUMMARY.md](../ENGINEERING_SUMMARY.md).
