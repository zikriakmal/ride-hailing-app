# 001: Backend scaffold

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** none
- **PRD flow:** none (foundation)

## Goal

A developer can clone the repo, start Postgres and the backend with documented commands, hit `GET /health`, and run an (initially tiny) test suite and linter.

## Scope

**In:**
- `backend/` Go module per the layout in `docs/ARCHITECTURE.md` (Go + Gin, ADR 0002)
- `docker-compose.yml` with the `postgres` service from `docs/INFRA.md` (api and migrate services are added in task 017), plus `backend/scripts/create-test-db.sql` creating `ride_test` on first start; first `goose` migration creating `User`, `Rider`, `Ride` from the data model; matching GORM models in `internal/model` (ADR 0003)
- `internal/config` reading env vars; fail fast if a required one is missing
- `.env.example` kept in sync
- Response helpers that write the `{ status, data, errors }` envelope for success and errors; validation middleware maps each failure to one `VALIDATION_ERROR` item with `field`; panic recovery → `500 INTERNAL_ERROR`
- `GET /health`
- `oapi-codegen` generating `internal/api/api.gen.go` from the spec (`gin-server` + strict server); `OapiRequestValidator` middleware with an error handler that writes the envelope
- Gin router with route groups (public / authenticated / `/ws`), slog logger and envelope-writing recovery replacing Gin's defaults
- `internal/testutil`: test DB setup + a helper that validates a response against `docs/api/openapi.yaml`
- Coverage gate: `go-test-coverage` with `backend/.testcoverage.yml` (100% total/package/file, exclusions from ADR 0013); `main.go` only calls a tested `run()`
- `gofmt` + `go vet` + `golangci-lint`; spec lint (`npx @redocly/cli lint docs/api/openapi.yaml`)
- A `Makefile` (or documented commands) for `generate`, `migrate`, `run`, `test`, `lint`
- Fill in the Commands section of `CLAUDE.md` and `README.md`

**Out (don't build here):**
- Any auth or ride endpoints
- WebSocket `/ws` (task 008)
- CI pipelines

## API

- `GET /health`

## Acceptance criteria

- [ ] `docker compose up -d` + documented install/run commands start the backend; `GET /health` → `200 {"status":200,"data":{"status":"ok"},"errors":null}`
- [ ] `goose up` creates `User`, `Rider`, `Ride` tables matching `docs/ARCHITECTURE.md`; a test checks the GORM models against the migrated schema
- [ ] Missing a required env var → backend exits on startup with a message naming the variable
- [ ] Unknown route → `404` envelope with `NOT_FOUND`; a panicking handler → `500` envelope with `INTERNAL_ERROR`, no stack trace in the body; envelope `status` always equals the HTTP status
- [ ] Request with two invalid fields → `400` envelope with two `VALIDATION_ERROR` items, each with its `field` (one test)
- [ ] Contract-test helper fails a test when a response doesn't match the spec (proved by one test)
- [ ] Generated code is up to date: running `generate` produces no diff
- [ ] Spec lint, `golangci-lint`, and `go test -race ./...` all pass; commands are in `CLAUDE.md`
- [ ] Coverage command reports 100% and fails when an untested function is added (proved once, then removed)

## Notes

