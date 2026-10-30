# AI-Assisted Software Engineering Prototype

**Author:** Sudha Gelvi. Seed demo links with `python -m shortener.seed` (aliases `sudha-gelvi`, `sudha-docs`, `sudha-py`).

Two deliverables in one repo, built around the principle **AI assists the engineer; the engineer owns execution and quality.**

1. **`shortener/`**: the mandatory use case. A scalable URL shortener service (FastAPI + SQLite) with APIs, persistence and click analytics.
2. **`planner/`**: the "requirement in, structured output out" prototype. It turns a free-text requirement into a task breakdown with dependencies and parallel waves, ambiguities and assumptions, per-task AI prompts (what AI does vs. what the engineer owns), validation steps, risks and trade-offs.

> **Honesty note:** the planner is deterministic (keyword rules plus curated templates). It makes **no LLM call**. It generates prompts you paste into Copilot or ChatGPT, and it never claims AI output is correct. Classification is a heuristic and may be wrong, so the engineer reviews it.

## Quick start

```bash
git clone -b initial-import https://github.com/sudharanigelivi/ai-eng-assistant.git
cd ai-eng-assistant
docker compose up --build        # then open http://localhost:8000/docs
```

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Run the planner

```bash
python -m planner "Build a scalable URL shortener service with APIs, persistence, and analytics."
python -m planner --file examples/ambiguous.txt --format json
echo "Fix the bug in the existing checkout service" | python -m planner
uvicorn planner.api:app --port 8001      # POST /api/v1/analyze?format=json|md
```

Sample inputs and generated outputs are in [`examples/`](examples) for greenfield, brownfield and ambiguous scenarios.

## Run the URL shortener

```bash
uvicorn shortener.api:create_app --factory --port 8000
# or: docker build -t shortener . && docker run -p 8000:8000 -v shortener-data:/data shortener

curl -X POST localhost:8000/api/v1/links -H 'content-type: application/json' \
  -d '{"url":"https://example.com/long/path","custom_alias":"demo-1","expires_at":"2030-01-01T00:00:00Z"}'
curl -i localhost:8000/demo-1                       # 302 redirect
curl localhost:8000/api/v1/links/demo-1/analytics?days=7
curl -X DELETE localhost:8000/api/v1/links/demo-1   # 204
```

| Endpoint | Purpose |
|---|---|
| `POST /api/v1/links` | Create (201). 409 alias taken, 422 invalid, 429 rate limited |
| `GET /api/v1/links/{code}` | Link metadata |
| `DELETE /api/v1/links/{code}` | Delete (204) |
| `GET /api/v1/links/{code}/analytics?days=1..365` | Totals, per-day, top referrers, devices |
| `GET /{code}` | 302 redirect, 404 unknown, 410 expired |
| `GET /healthz` | Liveness |

Full contract: [`docs/openapi.json`](docs/openapi.json), or `/docs` when running.

Configuration (env vars): `SHORTENER_DB_PATH`, `SHORTENER_BASE_URL`, `SHORTENER_API_KEY` (if set, `/api/v1/*` requires an `X-API-Key` header), `SHORTENER_CODE_LENGTH`, `SHORTENER_CACHE_SIZE`, `SHORTENER_CACHE_TTL`, `SHORTENER_RATE_LIMIT` (creates per minute per IP, 0 disables).

## Deploy to Render

The [`render.yaml`](render.yaml) Blueprint configures the paid persistent deployment; [`render.test.yaml`](render.test.yaml) configures a free, ephemeral demo deployment with keyless, rate-limited link creation and a browser form at `/`. Management endpoints remain API-key protected. See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) before applying either Blueprint.

## Testing

```bash
pytest --cov --cov-report=term-missing   # 111 tests, 96% line coverage
```

Approach: unit tests (validation, cache, rate limiter, repository, click classification), service and API tests through FastAPI's `TestClient` with an injected fake clock (expiry and analytics are deterministic), and planner tests (classification, dependency/cycle checks, CLI, API). A concurrency regression test verifies deletion cannot be followed by a stale cache fill. An end-to-end manual check with uvicorn and curl was also run (create, redirect, analytics).

Not covered: load or concurrency testing at scale, multi-process behaviour, and real-browser or real-network redirect behaviour. No performance numbers are claimed.

## Docs

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): design, AI integration, trade-offs, scaling path
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md): Render Blueprint deployment and operational notes
- [`docs/VALIDATION_AND_RISKS.md`](docs/VALIDATION_AND_RISKS.md): AI validation checklist, risks, known limitations
- [`docs/SCENARIOS.md`](docs/SCENARIOS.md): greenfield, brownfield and ambiguous walkthroughs
- [`ENGINEERING_SUMMARY.md`](ENGINEERING_SUMMARY.md): assignment outcome, implementation rationale, validation results, risks and assumptions
