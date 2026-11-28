# 018: CI pipeline (GitHub Actions)

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 001, 002, 017
- **PRD flow:** none (infra; ADR 0012)

## Goal

Every pull request and push to `main` runs spec lint, backend lint + tests, mobile lint + typecheck + tests, and a Docker build. Red CI blocks the merge.

## Scope

**In:**
- `.github/workflows/ci.yml` with parallel jobs `spec`, `backend` (Postgres 16 service container, `go test -race` with coverage, `go-test-coverage` 100% gate, `golangci-lint`, generated-code-up-to-date check), `mobile` (pnpm cache, `--frozen-lockfile`, `pnpm -r test:coverage` 100% gate), `docker` (Buildx build, no push, GHA cache)
- `concurrency` group to cancel superseded runs on the same branch
- Minimal `permissions: contents: read`
- Branch protection on `main` requiring `ci` checks (documented in `docs/INFRA.md`; set by hand)
- CI badge in `README.md`

**Out (don't build here):**
- Image push and deploy (019)
- Mobile EAS builds

## API

- none

## Acceptance criteria

- [ ] A PR that breaks a Go test, a mobile test, the spec, or the Dockerfile fails the matching job (each proved once on a throwaway branch)
- [ ] A PR that drops coverage below 100% in any codebase fails CI; coverage reports are uploaded as artifacts
- [ ] A clean PR passes all four jobs; a warm-cache run finishes in < 10 min
- [ ] Workflow uses pinned action versions (`@v4` or SHA) and no secrets
- [ ] `docs/INFRA.md` and `README.md` updated

## Notes

