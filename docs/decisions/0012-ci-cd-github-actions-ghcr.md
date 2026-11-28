# 0012: CI/CD with GitHub Actions, images in GHCR, deploy over SSH

- **Date:** 2026-11-28
- **Status:** proposed

## Context

Every change should be linted and tested before merge, and `main` should reach the VPS (ADR 0011) without manual steps. The Docker image must be built in CI, not on the VPS or a laptop.

## Decision

Two workflows in `.github/workflows/`:

- **`ci.yml`** on every pull request and push to `main`, jobs in parallel:
  - `spec`: `redocly lint docs/api/openapi.yaml`
  - `backend`: `go vet`, `golangci-lint`, check generated code is up to date, `go test -race ./...` with a `postgres:16` service container
  - `mobile`: `pnpm install --frozen-lockfile`, `pnpm -r lint`, `pnpm -r typecheck`, `pnpm -r test`
  - `docker`: build the backend and back office images (no push) to catch Dockerfile breaks
- **`deploy.yml`** on push to `main` (only after `ci.yml` succeeds, via `workflow_run`) and on manual `workflow_dispatch` with an optional `tag` (for rollback):
  1. `build`: `docker/build-push-action` with Buildx and GitHub Actions cache, push `ghcr.io/<owner>/ride-hailing-api:<git-sha>` and `ghcr.io/<owner>/ride-hailing-backoffice:<git-sha>` (+ `:latest`) using `GITHUB_TOKEN` (`packages: write`).
  2. `deploy` (GitHub **environment** `production`, optional required reviewer): SSH to the VPS (as the non-sudo `deploy` user) with `appleboy/ssh-action`, then `IMAGE_TAG=<sha> docker compose pull api && docker compose run --rm migrate && docker compose up -d api backoffice`. CI never touches the host nginx.
  3. `smoke`: `curl --fail https://api.<domain>/health` and `curl --fail https://admin.<domain>/` (retry for 60 s); on failure, redeploy the previous tag and fail the run.

Repository secrets: `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`, `SSH_KNOWN_HOSTS`. Variable: `API_DOMAIN`. The VPS logs in to GHCR once with a read-only token (`read:packages`) if the package is private.

## Alternatives considered

- **Build on the VPS** (`git pull && docker compose build`): no registry, but slow builds that compete with the other sites, Go toolchain on the server, and no image history to roll back to.
- **Docker Hub / ECR**: work, but GHCR needs no extra account or IAM and uses `GITHUB_TOKEN`.
- **Pull-based deploy (Watchtower)**: no SSH key in GitHub, but no ordering for migrations and no smoke test in the pipeline.
- **Self-hosted GitHub runner on the VPS**: no inbound SSH from GitHub, but runs CI code on a shared server and uses its CPU for builds.

## Consequences

- Every image is tagged by commit SHA; rollback = run `deploy.yml` with an older `tag`.
- Migrations run on every deploy before the new `api` starts; they must be backward compatible with the running version for the few seconds in between.
- Port 22 must accept GitHub runner IPs (they change), so SSH stays key-only with `fail2ban` rather than IP-restricted.
- Mobile apps are not built or published in CI (EAS Build in CI is in the backlog).
