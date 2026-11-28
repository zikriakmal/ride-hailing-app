# 0002: Backend in Go with Gin, run locally

- **Date:** 2026-11-28
- **Status:** proposed

## Context

The backend serves a REST API plus realtime pushes to two phones, must match `docs/api/openapi.yaml` exactly, and must be easy to test. Many concurrent long-lived connections (riders, consumers) and timers (60 s expiry) are core to the domain. It is deployed as a single container on one VM (ADR 0011).

## Decision

Go 1.23 with **Gin** as the HTTP framework.

- `oapi-codegen` (`gin-server` + `strict-server`) generates request/response types and a server interface from the spec; handlers implement that interface, so the compiler catches drift.
- `oapi-codegen/gin-middleware` (`OapiRequestValidator`, built on `kin-openapi`) validates every request against the spec at runtime, with a custom error handler that writes the `{ status, data, errors }` envelope. `kin-openapi` also validates responses in tests.
- Gin's own binding/validator tags are **not** used for API input; the spec is the single source of validation rules.
- Gin's default logger and recovery are replaced with a `log/slog` request logger and a recovery handler that returns the envelope (`500 INTERNAL_ERROR`).
- Generated Go code is committed so `go build` works without a generate step.
- One binary with subcommands: `serve`, `migrate` (goose embedded), `healthcheck` (for the distroless image). Hosting and CI/CD: ADRs 0011, 0012.

## Alternatives considered

- **Standard `net/http`** (Go 1.22 routing): no dependency, but we'd write our own middleware chaining, route groups, and context helpers that Gin already has.
- **Echo / chi**: comparable; Gin has the largest ecosystem and team familiarity.
- **Node.js + Fastify**: shares TypeScript with the app, but the spec already gives both sides generated types.

## Consequences

- Two languages in the repo (Go backend, TypeScript mobile). The OpenAPI spec is the only shared source of types.
- Route groups make the split easy: public (`/health`, `/auth/*`), authenticated API (validator + auth middleware), and `/ws` (auth only, no spec validator).
- Goroutines and `time.AfterFunc` make dispatch and expiry simple; shared state (WebSocket hub) needs a mutex.
- Tests call `router.ServeHTTP` with `httptest.NewRecorder`, no open port.
- Run Gin in `release` mode outside development to silence debug route output.
