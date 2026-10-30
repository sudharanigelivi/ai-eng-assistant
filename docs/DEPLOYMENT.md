# Production deployment: Render

The repository includes a Render Blueprint in [render.yaml](../render.yaml) for deploying the URL-shortener API as a Docker web service.

## Test environment

Use [render.test.yaml](../render.test.yaml) when creating a test deployment. In Render's Blueprint setup, select this file as the Blueprint path instead of `render.yaml`; this avoids creating the paid production service at the same time.

The test Blueprint uses Render's free web-service plan, a generated management API key, and `/tmp/shortener-test.db`. It intentionally has no persistent disk: data can disappear on restart or redeploy, and the free service may spin down when idle. The root page has a public demo form; link creation is rate-limited and requires no key. The API key remains required for metadata, analytics, and deletion endpoints. Use test data only. Verify `/`, `/healthz`, `/docs`, public link creation, and a redirect before considering production.

The test service is currently deployed at [https://ai-eng-assistant-shortener-test.onrender.com/](https://ai-eng-assistant-shortener-test.onrender.com/). Its generated management key is available in the service's **Environment** settings as `SHORTENER_API_KEY`; do not share that value.

## Before provisioning

- Push this repository to a Git provider that Render can access.
- Review Render's current pricing for the `0.5c-512mb` web service and its 1 GB persistent disk. The Blueprint selects these resources because SQLite must persist across deploys and restarts; provisioning may incur charges.
- This is a single-instance prototype. Do not scale it horizontally: SQLite, the cache and the rate limiter are local to one instance.

## Deploy

1. In Render, choose **New → Blueprint** and connect the repository branch containing this Blueprint.
2. Review the proposed service, plan, disk and generated environment values before applying it.
3. Wait for the first deployment to complete. Render's `PORT` environment variable is honored by the Docker command, and `/healthz` is used as the health check.
4. Open the service's `https://…onrender.com` address. The app derives its public short-link base URL from Render's `RENDER_EXTERNAL_HOSTNAME`; an explicit `SHORTENER_BASE_URL` overrides it.
5. Retrieve the generated `SHORTENER_API_KEY` from the service's environment settings and store it securely. Use it as `X-API-Key` for management endpoints (`/api/v1/*`). Do not commit the key or put it in client-side code. Redirects and `/healthz` remain public.
6. Verify `/healthz` returns `{"status":"ok"}` and `/docs` loads. Create a link using the authenticated API, confirm its returned `short_url` uses the public host, and test the redirect. Delete the test link afterward.

## Operational notes

- SQLite is stored at `/data/shortener.db` on the persistent disk. The application does not implement database backup/export or click-event retention; treat provider disk snapshots as recovery support, not an application-level backup workflow.
- Render disk-backed services have a short interruption during deploys and cannot be scaled to multiple instances. This is consistent with the prototype's single-process SQLite design.
- The API key is a shared management credential, not per-user authentication. Rotate it from Render's environment settings if exposed.
- The app uses a process-local rate limiter and cache. Keep one instance unless persistence and shared coordination are upgraded.
- No production load test or availability guarantee has been performed. Treat the deployment as a hosted prototype, not a production SLO commitment.

The test Blueprint has been applied and its service is live. The production Blueprint remains configuration only until it is applied in an authenticated Render account with the required billing information. A public production URL is assigned by Render after that deployment succeeds.
