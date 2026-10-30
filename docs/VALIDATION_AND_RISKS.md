# Validation, risks and limitations

## Validating AI-assisted output (engineer checklist)

1. **Read every line** before accepting; AI code is a draft, not a result.
2. **Run it**: tests, linter, the server. Don't trust "it should work".
3. **Test the edges AI skips**: expiry boundaries, collisions, invalid and hostile input, empty and huge values.
4. **Security review** of anything touching input, URLs, auth or storage (here: SSRF, open redirect, injection, enumeration).
5. **Check claims**: library APIs, versions and performance statements are verified against docs or by running them.
6. **Compare with requirements**: each requirement maps to a test.

## Defects found while validating this project

- The test run initially collected nothing: `tests/conftest.py` couldn't import `shortener` because the project root wasn't on `sys.path`. Fixed with `pythonpath = ["."]` in `pyproject.toml`.
- One analytics test asserted that a tied referrer count would come first. Ordering for ties is alphabetical, so the test was wrong, not the code. The test now asserts membership.

## Risks

| Kind | Risk | Mitigation |
|---|---|---|
| Functional | Short-code collisions | UNIQUE constraint and bounded retry; tested |
| Functional | Expired or deleted links still served from cache | Expiry rechecked on every hit; delete invalidates cache |
| Design | SQLite is single-node | Documented; schema ports to PostgreSQL |
| Design | Per-node cache and rate limit | Documented; Redis in scaling path |
| Design | Unbounded click table growth | Rollups and retention (not implemented) |
| AI | Plausible but wrong or insecure code | Review checklist, tests, SSRF guard written and tested by the engineer |
| AI | Hallucinated APIs | Run code, pin versions |
| AI | Over-trusting generated plans | Planner states assumptions; engineer confirms with stakeholders |

## Known limitations

- Single node: SQLite, in-memory cache and rate limiter are per process (run one worker).
- Clicks are recorded after the response; a crash can drop events.
- Auth is only an optional shared API key; no per-user ownership of links.
- The SSRF guard checks literal hosts and IPs only; it does **not** resolve DNS, so a hostname that resolves to a private IP is not blocked. Redirects are never followed by the server, which limits the impact.
- The planner is rule-based; classification is heuristic and domain templates exist only for the URL-shortener use case plus generic ones.
- No load testing performed; no performance figures are claimed.
