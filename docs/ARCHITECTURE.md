# Architecture overview

```
Requirement ──► planner (rules + templates) ──► Plan: tasks, waves, prompts, risks, trade-offs
                                                   │  engineer reviews, uses prompts with an AI assistant,
                                                   ▼  validates every output
                                         shortener service
Client ─► FastAPI ─► LinkService ─► TTL/LRU cache ─► SQLite repository (links, clicks)
                        │                                  ▲
                        └─ BackgroundTask: record click ───┘
```

## Shortener

| Component | Responsibility |
|---|---|
| `api.py` | Routes, optional API key, per-IP rate limit on create, 302 redirect, background click recording |
| `service.py` | Create, resolve, expire, delete and analytics rules; read-through cache |
| `repository.py` | SQLite schema and queries; one connection behind an RLock; WAL, foreign keys, `clicks(code, ts)` index |
| `validation.py` | http(s)-only URLs, no credentials or control characters, max 2048 chars, SSRF guard (localhost and non-global IPs rejected), alias rules and reserved names |
| `cache.py`, `ratelimit.py`, `clicks.py` | TTL/LRU cache, token bucket, referrer-host and device classification |

Key decisions:

- **Codes:** random 7-char base62 from `secrets` (about 3.5e12 space), UNIQUE constraint plus bounded retry on collision. Not sequential, so not enumerable.
- **302, not 301:** a cached 301 would hide clicks and make delete or expiry ineffective.
- **Async click recording:** the redirect is not blocked by analytics writes. The cost is that a crash can lose a click.
- **Privacy:** only referrer host and device class are stored, never IP or full referrer paths.
- **Testability:** `create_app(settings, clock)` takes an injectable clock.

## Trade-offs

| Decision | Chosen | Alternative | Why |
|---|---|---|---|
| Storage | SQLite | PostgreSQL | Zero-ops, runnable anywhere, schema ports directly |
| Cache | In-process TTL/LRU | Redis | Simple; per-node, so staleness is bounded by TTL and delete invalidates locally only |
| Analytics | Raw events in table | Pre-aggregated counters | Flexible queries; grows linearly, so needs retention or rollups at scale |
| Code generation | Random | Counter + base62 | Not guessable; needs collision handling |
| Planner | Deterministic rules | LLM call | Reproducible, offline, testable; less flexible than an LLM |

## Scaling path (not implemented)

PostgreSQL with a read replica, Redis for shared cache and rate limiting, a queue (Kafka, SQS) for click events with batch aggregation into daily rollups, a CDN or edge cache for hot redirects, and horizontal app replicas behind a load balancer.

## How AI is integrated

The planner assigns each task an `AIAssist` record: a ready-to-paste **prompt**, what **AI does** (draft, scaffold, suggest edge cases) and what the **engineer owns** (decisions, security-sensitive logic, final review, running the tests). The engineer decides which suggestions to accept. See [VALIDATION_AND_RISKS.md](VALIDATION_AND_RISKS.md).
