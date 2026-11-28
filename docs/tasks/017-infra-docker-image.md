# 017: Backend Docker image and production compose

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 001
- **PRD flow:** none (infra; ADR 0011)

## Goal

The backend builds into a small, non-root Docker image, and `deploy/docker-compose.prod.yml` runs api + migrate the same way the VPS will, against an existing Postgres on `127.0.0.1:5432`. The nginx server block for the host is written and validated.

## Scope

**In:**
- `backend/Dockerfile`: multi-stage (`golang:1.23` → `gcr.io/distroless/static:nonroot`), `CGO_ENABLED=0`, version/commit via `-ldflags`; `.dockerignore`
- Binary subcommands: `serve`, `migrate up` (goose embedded with `embed.FS` migrations), `healthcheck` (GET `localhost:$PORT/health`, exit 0/1)
- Root `docker-compose.yml`: add `migrate` and `api` (built from `./backend`) exactly as in `docs/INFRA.md`, so `docker compose up --build` runs the whole backend locally
- `deploy/docker-compose.prod.yml` exactly as in `docs/INFRA.md`: `api` and `migrate` only (read-only FS, `cap_drop: ALL`, `no-new-privileges`, memory limit), both `network_mode: host`; `api` binds `HTTP_HOST=127.0.0.1`; no DB service (ADR 0011); healthcheck; log rotation; `restart: unless-stopped`
- Config: `HTTP_HOST` (default `0.0.0.0` for dev, `127.0.0.1` in prod) added to `internal/config` and `.env.example`
- `deploy/create-db.sql` (role + database, least privilege, as in `docs/INFRA.md`)
- `deploy/nginx/ride-hailing-api.conf` as in `docs/INFRA.md` (HTTP→HTTPS, `/ws` upgrade headers, timeouts); `deploy/.env.example`
- Gin `SetTrustedProxies(["127.0.0.1"])` so client IPs come from `X-Forwarded-For` only via nginx
- Doc how to run the prod stack locally against the dev Postgres from `docker-compose.yml` (`curl http://127.0.0.1:3000/health`)

**Out (don't build here):**
- CI workflows (018), the VPS setup, deploy, and backups (019)

## API

- none

## Acceptance criteria

- [ ] On a clean clone, `cp .env.example .env && docker compose up --build` brings up postgres → migrate (exits 0) → api, and `curl http://localhost:3000/health` → `200`
- [ ] `docker build backend` succeeds; image runs as non-root and is < 40 MB
- [ ] `docker compose -f deploy/docker-compose.prod.yml up` locally: with the dev Postgres running, `migrate` exits 0, `api` becomes healthy, `curl http://127.0.0.1:3000/health` → `200` envelope
- [ ] The nginx config passes `nginx -t` (in an `nginx` container with a dummy cert), and a WebSocket client connects through that container to `/ws` and stays connected > 90 s
- [ ] `api` listens on `127.0.0.1` only (`ss -ltn` shows `127.0.0.1:3000`, not `0.0.0.0`)
- [ ] `create-db.sql` run against a fresh Postgres gives a `ride` role that can migrate and use `ride` but cannot connect to `postgres` or create databases
- [ ] Running `migrate` twice is a no-op the second time
- [ ] `serve`/`migrate`/`healthcheck` subcommand code has unit tests; backend coverage stays 100%
- [ ] `docs/INFRA.md` matches the files

## Notes

