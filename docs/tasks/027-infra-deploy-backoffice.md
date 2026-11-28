# 027: Deploy the back office and end-to-end staff check

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 019, 023, 024, 025, 026
- **PRD flow:** 8–12; PRD success criterion for the back office

## Goal

`https://admin.<domain>` serves the back office from a GHCR image via Docker Compose behind the host nginx, deployed by the same pipeline, and a real staff walkthrough passes.

## Scope

**In:**
- `frontend/apps/backoffice/Dockerfile` (pnpm build → `nginxinc/nginx-unprivileged:alpine`) + `nginx.conf` with SPA fallback and CSP/security headers (`docs/INFRA.md`)
- `backoffice` service in `deploy/docker-compose.prod.yml` exactly as in `docs/INFRA.md`
- `deploy/nginx/ride-hailing-admin.conf` + `snippets/ride-hailing-proxy.conf`; certbot for `admin.<domain>`; login rate limit
- CI: build the back office image in `ci.yml`; build/push/deploy/smoke it in `deploy.yml` (ADR 0012)
- Walkthrough on production (record in Notes), with one consumer phone and one rider phone

**Out (don't build here):**
- IP allow-list (optional; enable later if needed)

## API

- none

## Acceptance criteria

- [ ] `https://admin.<domain>` loads with a valid cert; response headers include the CSP, `X-Frame-Options`/`frame-ancestors`, HSTS; `/api/health` → `200` envelope
- [ ] More than 5 login attempts per minute from one IP → `429`
- [ ] Merge to `main` deploys both images with the same SHA; smoke checks both
- [ ] Walkthrough: create a support account → support finds the consumer → sees the active ride on the map → force-cancels it with a reason (both phones update) → consumer reports a problem → support replies and resolves (consumer sees it) → admin suspends the consumer (app logs out) → every step appears in the audit log
- [ ] PRD back-office success criterion ticked
- [ ] `docs/INFRA.md` matches what was built

## Notes

