# Infrastructure

> Where the backend runs and how code gets there. Decisions: ADR 0011 (hosting), ADR 0012 (CI/CD). Update this file in the same change that alters infra.

## Topology

```
 Consumer app ─┐                      Existing VPS (shared with other sites)
               │  HTTPS / WSS         ┌──────────────────────────────────────────────────────┐
 Rider app ────┼────────────────────> │ host nginx :443 (certbot TLS)                        │
               │  api.<domain>        │   api.<domain>   ──> 127.0.0.1:3000 (api)            │
 Back office ──┘  admin.<domain>      │   admin.<domain> ──> /api/* → 127.0.0.1:3000         │
 (staff browser)                      │                      /*     → 127.0.0.1:3001 (SPA)   │
                                      │                     │                                │
                                      │   docker (host net) ▼                                │
                                      │     api (Go) ──> host Postgres 127.0.0.1:5432        │
                                      │      ▲           (existing server; our DB `ride`)    │
                                      │      └── migrate (one-shot per deploy)               │
                                      │   backoffice (nginx:alpine, static SPA) :3001        │
                                      │ cron: pg_dump daily ──> age-encrypt ──>              │
                                      │   /var/backups/ride-hailing (0700, VPS storage only) │
                                      └──────────────────────────────────────────────────────┘

 GitHub ── push main ──> Actions: ci.yml ──> deploy.yml: build image ──> GHCR
                                                         └─ SSH ──> VPS: pull, migrate, up, smoke test
```

## Repository files (created by tasks 017–019)

```
.github/workflows/
├── ci.yml                       # lint + test: spec, backend, mobile, docker build
└── deploy.yml                   # build → push GHCR → SSH deploy → smoke test (+ manual rollback)
backend/
├── Dockerfile                   # multi-stage: golang:1.23 build → gcr.io/distroless/static:nonroot
└── .dockerignore
frontend/apps/backoffice/
├── Dockerfile                   # pnpm build → nginxinc/nginx-unprivileged:alpine serving dist/
└── nginx.conf                   # SPA fallback + CSP and security headers
deploy/
├── docker-compose.prod.yml      # api, migrate only (network_mode: host; DB is the existing host Postgres)
├── nginx/ride-hailing-api.conf  # host nginx server block for api.<domain> (installed by hand)
├── nginx/ride-hailing-admin.conf # host nginx server block for admin.<domain> (installed by hand)
├── create-db.sql                # one-time: role + database on the existing Postgres
├── .env.example                 # production variables (real file lives at /opt/ride/.env)
├── deploy.sh                    # forced SSH command for CI: validate SHA → pull → migrate → up
├── backup.sh                    # pg_dump → age encrypt → sha256 → rotate (VPS storage only)
├── backup-verify.sh             # weekly: checksum + test restore into a throwaway container
└── provision.md                 # one-time VPS setup checklist
```

## Docker Compose (what runs where)

Everything we run is described by two compose files. Read them top to bottom and you know the whole system.

| | `docker-compose.yml` (local dev, repo root) | `deploy/docker-compose.prod.yml` (VPS) |
|---|---|---|
| Postgres | `postgres` service (container) | **none**: uses the existing host Postgres |
| Back office | not in compose: `pnpm --filter backoffice dev` (Vite proxies `/api` → `localhost:3000`) | `backoffice` pulled from GHCR, `127.0.0.1:3001` |
| Migrations | `migrate` service, runs once then exits | `migrate` service, runs once per deploy |
| API | `api` built from `./backend` | `api` pulled from GHCR by tag |
| Network | Docker bridge, ports published to your machine | `network_mode: host`, binds `127.0.0.1` only |
| Start | `docker compose up --build` | `docker compose run --rm migrate && docker compose up -d api backoffice` (done by CI) |

### Local: `docker-compose.yml`

```yaml
# Local development: database + migrations + API in one command.
#   docker compose up --build        → API on http://localhost:3000
#   docker compose up postgres       → only the DB (then `go run ./cmd/api serve`)
name: ride-hailing

services:
  postgres:
    image: postgres:16                 # same major as CI; prod server is ≥ 14
    environment:
      POSTGRES_USER: ride
      POSTGRES_PASSWORD: ride          # local only; never reuse in production
      POSTGRES_DB: ride
    ports:
      - "5432:5432"                    # so `psql`, GORM tests and `go run` can reach it
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./backend/scripts/create-test-db.sql:/docker-entrypoint-initdb.d/10-test-db.sql:ro  # creates ride_test
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ride -d ride"]
      interval: 5s
      retries: 10

  migrate:
    build: ./backend                   # same image as the API
    command: ["migrate", "up"]         # goose migrations embedded in the binary
    environment:
      DATABASE_URL: postgresql://ride:ride@postgres:5432/ride?sslmode=disable
    depends_on:
      postgres:
        condition: service_healthy
    restart: "no"                      # one-shot: run, then exit 0

  api:
    build: ./backend
    command: ["serve"]
    env_file: .env                     # JWT_SECRET etc. (copy from .env.example)
    environment:
      DATABASE_URL: postgresql://ride:ride@postgres:5432/ride?sslmode=disable
      HTTP_HOST: 0.0.0.0               # reachable from phones on your Wi-Fi
      PORT: "3000"
    ports:
      - "3000:3000"
    depends_on:
      migrate:
        condition: service_completed_successfully   # API starts only after migrations succeed

volumes:
  pgdata:                              # local DB data; `docker compose down -v` wipes it
```

### Production: `deploy/docker-compose.prod.yml`

```yaml
# Production on the existing VPS. Only our Go service runs here;
# nginx and Postgres are the VPS's own (see ADR 0011).
# CI runs:  IMAGE_TAG=<sha> docker compose pull api
#           docker compose run --rm migrate
#           docker compose up -d api backoffice
name: ride-hailing

x-app: &app                            # shared settings for both services
  image: ghcr.io/<owner>/ride-hailing-api:${IMAGE_TAG:?IMAGE_TAG is required}
  env_file: /opt/ride/.env             # secrets live only on the VPS (chmod 600)
  network_mode: host                   # reach host Postgres on 127.0.0.1:5432 without opening it up
  read_only: true                      # container filesystem is immutable
  security_opt:
    - no-new-privileges:true
  cap_drop: [ALL]                      # needs no Linux capabilities
  logging:
    driver: json-file
    options: { max-size: "10m", max-file: "3" }

services:
  migrate:
    <<: *app
    command: ["migrate", "up"]
    restart: "no"                      # one-shot per deploy
    profiles: ["tools"]                # not started by `up`; run explicitly by CI

  api:
    <<: *app
    command: ["serve"]                 # HTTP_HOST=127.0.0.1, PORT=3000 from .env → only nginx can reach it
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "/app/api", "healthcheck"]   # distroless has no curl
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 10s
    deploy:
      resources:
        limits: { memory: 256m }       # shared VPS: cap our footprint

  backoffice:                          # staff web app: static files only, no secrets inside
    image: ghcr.io/<owner>/ride-hailing-backoffice:${IMAGE_TAG:?IMAGE_TAG is required}
    ports:
      - "127.0.0.1:3001:8080"          # loopback only; host nginx serves it at admin.<domain>
    read_only: true
    tmpfs: [/tmp]                      # nginx needs a writable temp dir
    security_opt:
      - no-new-privileges:true
    cap_drop: [ALL]
    restart: unless-stopped
    logging:
      driver: json-file
      options: { max-size: "10m", max-file: "3" }
    deploy:
      resources:
        limits: { memory: 64m }
```

Reading it in one breath: CI pulls the images for a commit, runs `migrate` once against the VPS's Postgres, then replaces `api` and `backoffice`. Both listen only on loopback (`3000`, `3001`); the VPS's nginx is the only thing that talks to them.

## nginx server block (reference)

```nginx
# /etc/nginx/sites-available/ride-hailing-api.conf
server {
    listen 80;
    server_name api.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;
    # ssl_certificate lines are added by: certbot --nginx -d api.example.com

    client_max_body_size 1m;
    access_log /var/log/nginx/ride-hailing-api.access.log;
    error_log  /var/log/nginx/ride-hailing-api.error.log;

    location /ws {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Authorization $http_authorization;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 3600s;   # long-lived socket; server also pings every 25 s
        proxy_send_timeout 3600s;
    }

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
    }
}
```

The backend trusts `X-Forwarded-For` only from `127.0.0.1` (Gin `SetTrustedProxies`).

### Back office: `admin.<domain>`

```nginx
# /etc/nginx/sites-available/ride-hailing-admin.conf
limit_req_zone $binary_remote_addr zone=ride_admin_login:10m rate=5r/m;

server {
    listen 80;
    server_name admin.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name admin.example.com;
    # ssl_certificate lines are added by: certbot --nginx -d admin.example.com

    # Optional: staff-only network. Uncomment and list office/VPN IPs.
    # allow 203.0.113.10;
    # deny all;

    access_log /var/log/nginx/ride-hailing-admin.access.log;
    error_log  /var/log/nginx/ride-hailing-admin.error.log;
    add_header Strict-Transport-Security "max-age=31536000" always;

    location = /api/auth/login {
        limit_req zone=ride_admin_login burst=5 nodelay;
        limit_req_status 429;
        proxy_pass http://127.0.0.1:3000/auth/login;
        include /etc/nginx/snippets/ride-hailing-proxy.conf;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:3000/;   # trailing slash strips the /api prefix
        include /etc/nginx/snippets/ride-hailing-proxy.conf;
    }

    location / {
        proxy_pass http://127.0.0.1:3001;    # static SPA; CSP etc. set by the container
        include /etc/nginx/snippets/ride-hailing-proxy.conf;
    }
}
```

`/etc/nginx/snippets/ride-hailing-proxy.conf` holds the shared `proxy_http_version 1.1`, `Host`, `X-Forwarded-For`, and `X-Forwarded-Proto` lines. The back office image's own `nginx.conf` sets `Content-Security-Policy: default-src 'self'; img-src 'self' data: https://*.tile.openstreetmap.org; connect-src 'self'; frame-ancestors 'none'`, plus `X-Content-Type-Options: nosniff` and `Referrer-Policy: no-referrer`.

## Environments

| | Local dev | Production |
|---|---|---|
| Backend | `go run ./cmd/api serve` | `api` container from GHCR, host network, on `127.0.0.1:3000` |
| Database | `docker-compose.yml` Postgres 16 on `localhost:5432` | existing host Postgres on `127.0.0.1:5432`, database `ride`, role `ride` |
| API URL for apps | `http://<laptop-LAN-IP>:3000` | `https://api.<domain>` |
| WebSocket | `ws://<laptop-LAN-IP>:3000/ws` | `wss://api.<domain>/ws` |
| Back office | `http://localhost:5173` (Vite) | `https://admin.<domain>` (API at `/api`) |
| TLS | none | host nginx + certbot |
| Secrets | `.env` (gitignored) | `/opt/ride/.env` on the VPS (`chmod 600`) |

## Production variables (`/opt/ride/.env`)

| Variable | Example | Used by |
|----------|---------|---------|
| `IMAGE_TAG` | git SHA, set by deploy | compose |
| `HTTP_HOST` | `127.0.0.1` | api (bind address; never `0.0.0.0` in production) |
| `DATABASE_URL` | `postgresql://ride:<pw>@127.0.0.1:5432/ride?sslmode=disable` | api, migrate |
| `JWT_SECRET` | `openssl rand -hex 32` | api |
| `PORT` | `3000` (change if taken; must match nginx `proxy_pass`) | api |
| `APP_ENV` | `production` | api (Gin release mode, JSON logs) |
| `BACKUP_DIR` | `/var/backups/ride-hailing` | backup.sh, backup-verify.sh |
| `BACKUP_AGE_RECIPIENTS` | `age1…owner,age1…verify` (public keys only) | backup.sh |
| `BACKUP_VERIFY_KEY_FILE` | `/home/deploy/.config/ride-backup/verify.key` (`chmod 400`) | backup-verify.sh |
| `BACKUP_MIN_FREE_PCT` | `20` | backup.sh |

GitHub: secrets `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`, `SSH_KNOWN_HOSTS`; variable `API_DOMAIN`; environment `production`.

## One-time VPS setup

Check first: free RAM (`free -m`, want ≥ 256 MB spare), free disk (≥ 10 GB), port `3000` free on loopback (`ss -ltn | grep 3000`; else set `PORT`), nginx version supports `http2`, Postgres version ≥ 14 (`psql -V`) and listening on loopback only (`ss -ltn | grep 5432` shows `127.0.0.1`, not `0.0.0.0`; if it shows `0.0.0.0`, make sure `ufw` blocks 5432).

1. DNS: `A api.<domain>` and `A admin.<domain>` → VPS IP. Check port `3001` is free too.
2. Create a `deploy` user in the `docker` group (no sudo). SSH: key-only, no root login; `fail2ban` on.
3. Install Docker Engine + Compose plugin if missing; `unattended-upgrades` on; `age` for backup encryption.
4. Firewall (`ufw`): allow 22, 80, 443 only. Our containers publish no ports (host network, loopback bind).
4b. Database (as a Postgres admin): run `deploy/create-db.sql` with a strong password:
   ```sql
   CREATE ROLE ride LOGIN PASSWORD '<long random>' NOSUPERUSER NOCREATEDB NOCREATEROLE;
   CREATE DATABASE ride OWNER ride;
   REVOKE CONNECT ON DATABASE ride FROM PUBLIC;
   GRANT CONNECT ON DATABASE ride TO ride;
   \c ride
   REVOKE CREATE ON SCHEMA public FROM PUBLIC;
   ALTER SCHEMA public OWNER TO ride;
   ```
   Confirm `pg_hba.conf` allows `ride` from `127.0.0.1/32` with `scram-sha-256` (most installs already allow local password logins; don't widen anything else).
   As `deploy`: `~/.pgpass` with `127.0.0.1:5432:ride:ride:<pw>`, `chmod 600` (used by `backup.sh`).
5. `mkdir -p /opt/ride`; copy `deploy/docker-compose.prod.yml`, `backup.sh`, `backup-verify.sh`; write `/opt/ride/.env` (`chmod 600`).
   Backup storage: if the provider offers a block volume, attach it and mount it at `/var/backups/ride-hailing` (`noexec,nosuid,nodev`); otherwise create the folder on the main disk. Then `chown deploy:deploy` and `chmod 700`.
   Keys: on **your own machine** run `age-keygen -o owner.key` and store `owner.key` in your password manager (two copies), never on the VPS. On the VPS, as `deploy`, run `age-keygen -o ~/.config/ride-backup/verify.key && chmod 400` it. Put both **public** keys in `BACKUP_AGE_RECIPIENTS`.
6. nginx (as an admin, not `deploy`): copy `deploy/nginx/ride-hailing-api.conf` to `/etc/nginx/sites-available/`, symlink into `sites-enabled/`, `nginx -t && systemctl reload nginx`, then `certbot --nginx -d api.<domain>`. Same for `ride-hailing-admin.conf` + the shared `snippets/ride-hailing-proxy.conf`, then `certbot --nginx -d admin.<domain>`.
7. `docker login ghcr.io` as `deploy` with a `read:packages` token (if the image is private).
8. Cron (as `deploy`):
   `0 2 * * * /opt/ride/backup.sh >> /var/backups/ride-hailing/backup.log 2>&1`
   `30 3 * * 0 /opt/ride/backup-verify.sh >> /var/backups/ride-hailing/backup.log 2>&1`
9. Add the deploy SSH key and host key to GitHub secrets; run `deploy.yml` manually once.
10. First admin: `cd /opt/ride && docker compose run --rm api create-admin --email you@example.com --name "Your Name"` (prompts for the password). Further staff are created in the back office.

## Deploy flow

1. PR → `ci.yml` must pass to merge.
2. Merge to `main` → `ci.yml` on `main` → `deploy.yml`:
   - build + push `ride-hailing-api:<sha>` and `ride-hailing-backoffice:<sha>` (+ `:latest`)
   - SSH `deploy@host <sha>`: the key's forced command `/opt/ride/deploy.sh` validates the SHA, then runs `IMAGE_TAG=<sha> docker compose pull api backoffice && docker compose run --rm migrate && docker compose up -d api backoffice` (no DB container to touch; the key can't do anything else, see docs/SECURITY.md)
   - smoke: `GET https://api.<domain>/health` → `200` and `GET https://admin.<domain>/` → `200` within 60 s, else redeploy previous tag and fail
3. Expected downtime per deploy: a few seconds (nginx answers `502` meanwhile); apps reconnect the WebSocket and resync. nginx is never reloaded by CI.

## Runbook

| Situation | Action |
|-----------|--------|
| Roll back | Actions → `deploy.yml` → Run workflow with `tag=<older sha>` |
| See logs | `ssh deploy@<host>` → `cd /opt/ride && docker compose logs -f api`; nginx: `/var/log/nginx/ride-hailing-api.*.log` |
| Restart | `docker compose restart api` |
| `502 Bad Gateway` | `docker compose ps` (is `api` healthy?); `PORT` matches nginx `proxy_pass`? |
| `api` can't reach DB | `systemctl status postgresql`; `psql -h 127.0.0.1 -U ride ride` as `deploy` works? `pg_hba.conf` allows `127.0.0.1/32`? |
| WebSocket drops at ~60 s | `/ws` location missing `Upgrade`/`Connection` headers or `proxy_read_timeout` |
| Restore DB | Bring `owner.key` temporarily (paste into a `chmod 600` file in `/dev/shm`, removed afterwards). `sha256sum -c <file>.sha256` → `docker compose stop api` → `age -d -i /dev/shm/owner.key <file>.dump.age \| pg_restore -h 127.0.0.1 -U ride -d ride --clean --if-exists --no-owner` → `docker compose start api` → `shred -u /dev/shm/owner.key` |
| Backup health | `cat /var/backups/ride-hailing/last-success` (should be < 26 h old); `tail /var/backups/ride-hailing/backup.log` |
| Copy a backup off the VPS (optional, monthly) | From your machine: `scp deploy@<host>:/var/backups/ride-hailing/daily/<newest>.dump.age* .` (it's encrypted; safe to keep on your laptop) |
| Disk full | `docker image prune -af --filter "until=168h"`; check backup rotation in `/var/backups/ride-hailing` |
| Cert problems | `certbot certificates`; `systemctl list-timers \| grep certbot`; `certbot renew --dry-run` |
| Locked out of the back office | On the VPS: `docker compose run --rm api create-admin …` creates a new admin (audit-logged as `staff.created` with `actor: null`) |
| Staff account compromised | Another admin disables it in the back office (token stops working at once); review its audit entries |
| Changed nginx config | always `nginx -t` before `systemctl reload nginx`; other sites share this nginx |
