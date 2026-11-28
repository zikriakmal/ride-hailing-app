# 0011: Host on the existing VPS: its nginx, its Postgres, our app in Docker

- **Date:** 2026-11-28
- **Status:** proposed

## Context

The two-device demo should work from anywhere, not only on the laptop's Wi-Fi, so the backend needs a public HTTPS/WSS endpoint. We already have a VPS that runs **nginx on the host** (serving other sites, TLS via certbot) and a **PostgreSQL server on the host at `127.0.0.1:5432`**. Production-grade scaling and HA are non-goals (PRD). The backend is one Go service with an in-memory WebSocket hub (ADR 0004), so it must run as a single instance.

## Decision

Deploy onto the **existing VPS**, reusing its nginx and its Postgres. Our services ship as **Docker Compose** (`deploy/docker-compose.prod.yml`, written out with comments in `docs/INFRA.md`), so the whole deployment reads in one file:

| Service | Image | Network | Notes |
|---------|-------|---------|-------|
| `api` | `ghcr.io/<owner>/ride-hailing-api:<sha>` | `network_mode: host`, listens on `127.0.0.1:${PORT:-3000}` (`HTTP_HOST=127.0.0.1`) | Go binary (`api serve`), healthcheck `api healthcheck` |
| `migrate` | same image | `network_mode: host` | One-shot `api migrate up` (goose embedded), run before `api` on each deploy |
| `backoffice` | `ghcr.io/<owner>/ride-hailing-backoffice:<sha>` | bridge, `127.0.0.1:3001:8080` | `nginx:alpine` (unprivileged) serving the built SPA with security headers (ADR 0014) |

- **Database**: the existing host Postgres. We add one database `ride` owned by one role `ride` (`LOGIN`, no `SUPERUSER`/`CREATEDB`/`CREATEROLE`), `REVOKE CONNECT ON DATABASE ride FROM PUBLIC`, `REVOKE CREATE ON SCHEMA public FROM PUBLIC`, and a strong password. `DATABASE_URL=postgresql://ride:<pw>@127.0.0.1:5432/ride?sslmode=disable` (loopback only). The `ride` role cannot see other databases on the server. Minimum server version: PostgreSQL 14 (we develop on 16; no 15+/16-only features).
- **Why host networking**: the containers reach `127.0.0.1:5432` directly. We don't have to change the shared server's `listen_addresses` or `pg_hba.conf` to accept Docker bridge traffic, and Postgres stays loopback-only.

- **nginx (host)**: a second server block `deploy/nginx/ride-hailing-admin.conf` for `admin.<domain>`: `/api/` → `127.0.0.1:3000/` (prefix stripped), `/` → `127.0.0.1:3001`, login rate limit, optional IP allow-list.
- **nginx (host)**: new server block `deploy/nginx/ride-hailing-api.conf` for `api.<domain>` → `proxy_pass http://127.0.0.1:3000`, with WebSocket upgrade headers on `/ws`, `proxy_read_timeout 3600s`, `client_max_body_size 1m`, and HTTP → HTTPS redirect. Installed once by hand into `/etc/nginx/sites-available/` and enabled with `nginx -t && systemctl reload nginx`. CI never edits nginx.
- **TLS**: `certbot --nginx -d api.<domain>`, renewed by the certbot timer already on the VPS.
- **Ports**: with host networking nothing is published through Docker (so nothing bypasses `ufw`); `api` binds to `127.0.0.1` itself. `PORT` is configurable in case 3000 is already taken on the VPS.
- **Backups (on VPS storage only, no bucket)**:
  - Daily at 02:00 a host cron job (`deploy/backup.sh`, as user `deploy`) runs the **host's** `pg_dump -Fc ride` (same version as the server; password from `~/.pgpass`, `chmod 600`). It covers our `ride` database only. The other databases on the server are not ours to back up. then encrypts the dump with [`age`](https://github.com/FiloSottile/age) to a **public key** (`BACKUP_AGE_RECIPIENT`). The private key is **never stored on the VPS**; the owner keeps it offline (password manager) and brings it only to restore.
  - Stored in `/var/backups/ride-hailing/` (dir `0700`, files `0600`, owner `deploy`, `umask 077`), on a separate block volume if the provider offers one, otherwise the main disk.
  - Each file has a `.sha256` next to it; retention 7 daily + 4 weekly + 3 monthly.
  - The script refuses to run when free disk is below 20%, and writes a status line to `backup.log` plus a `last-success` timestamp file.
  - Weekly `deploy/backup-verify.sh` checks the checksum and that the encrypted file is a valid `age` file, then restores the newest dump into a throwaway container matching the server's major version (`postgres:<major>`, `--network none`) and compares row counts with production. The verify step uses a separate **verify key** pair whose private key lives on the VPS (`chmod 400`), and dumps are encrypted to **both** recipients. The owner's key stays the only off-VPS key. Simpler alternative: verify only checksums and run the restore test by hand monthly (task 019 picks one).
- **Secrets**: `/opt/ride/.env` on the VPS (`chmod 600`), created by hand; never in the repo or the image.
- **Logs**: Docker `json-file` driver with rotation (`max-size: 10m`, `max-file: 3`); nginx access/error logs for `api.<domain>` in their own files.
- Local development still uses `docker-compose.yml` (Postgres only) and `go run`.

## Alternatives considered

- **Caddy in a container**: automatic TLS and a 5-line config, but nginx already owns ports 80/443 on this VPS; running both means one proxying to the other for no gain.
- **nginx in a container**: keeps everything in compose, but clashes with the host nginx on 80/443.
- **New dedicated VM (AWS EC2)**: clean isolation, but costs money we don't need to spend while the existing VPS has room.
- **Postgres container in our compose**: isolated and version-pinned, but the VPS already runs Postgres on 5432; a second server wastes RAM and needs another port. Rejected.
- **Bridge networking + `host.docker.internal`**: keeps container network isolation, but requires the shared Postgres to listen on the Docker bridge and trust its subnet in `pg_hba.conf`. Rejected: changes a server other apps depend on.
- **Managed DB**: backups and patching handled for us, but costs extra; the DB-on-VPS choice was requested. In the backlog.
- **Off-site bucket (S3 / R2 / B2) for backups**: survives losing the VPS, but was ruled out; manual off-VPS copies are the fallback (see Consequences).
- **Unencrypted dumps with tight file permissions**: simpler, but anyone with root or a leaked file reads all user data, including the other sites' admins on this shared VPS.

## Consequences

- We share the VPS with other sites: a bad nginx edit can take them down, so always `nginx -t` before reload, and keep our config in its own file.
- CPU/RAM are shared; check free memory before go-live (`api` needs roughly 50–150 MB; our DB adds little to the existing server).
- We don't own the Postgres server: its upgrades, tuning, and restarts are shared with other apps. Before upgrading it, check our migrations and backups still work.
- Host networking gives the containers access to every loopback service on the VPS; acceptable because they run our own image as non-root, but nothing third-party should run with it.
- One VPS is a single point of failure; a deploy drops WebSocket connections for a few seconds (clients reconnect and resync; ADR 0004). Acceptable per non-goals.
- Restarting `api` loses in-memory expiry timers; the startup sweep (task 009) expires overdue rides.
- nginx returns `502` while `api` restarts; the smoke test waits for recovery.
- Mobile apps use `EXPO_PUBLIC_API_URL=https://api.<domain>`; realtime becomes `wss://api.<domain>/ws`.
- Needs an `A` record for `api.<domain>` pointing at the VPS IP.
- **Backups share the VPS's fate**: disk failure, provider outage, or account loss destroys the database *and* its backups. Mitigations: a separate block volume if available, the provider's snapshot feature if it exists, and an occasional manual copy of the newest encrypted dump to the owner's machine (`scp`, documented in the runbook). Accepted risk for a demo.
- Losing the owner's `age` private key makes the dumps unrecoverable by anyone but the verify key (if used); keep two offline copies of it.
