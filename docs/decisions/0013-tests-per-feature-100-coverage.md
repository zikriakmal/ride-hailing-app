# 0013: Unit tests with every feature, 100% coverage enforced

- **Date:** 2026-11-28
- **Status:** proposed

## Context

Features are built one task at a time, often by an agent. Without a hard rule, tests lag behind code and gaps pile up. We want every task to leave each codebase fully tested, and CI to reject anything that isn't.

## Decision

- **Every task that adds or changes code adds unit tests in the same change**: each new function, handler, service, repository, slice, RTK Query endpoint, zod schema, hook, and component gets at least one test for the happy path and one per error/branch.
- **Coverage must be 100%** for each codebase after every task. It is measured over all tests (unit + integration + contract) and enforced locally and in CI:

| Codebase | Tool | Gate |
|----------|------|------|
| `backend` | `go test -race -coverpkg=./... -coverprofile=coverage.out ./...` + [`go-test-coverage`](https://github.com/vladopajic/go-test-coverage) (`backend/.testcoverage.yml`) | 100% total, per package, per file (statements) |
| `frontend/apps/consumer`, `frontend/apps/rider`, `frontend/packages/ui`, `frontend/packages/core`, `frontend/packages/features` | Jest `--coverage` with `coverageThreshold.global` | 100% statements, branches, functions, lines (each workspace separately) |
| `frontend/apps/backoffice` | Vitest `--coverage` (v8) with `thresholds: 100` | 100% statements, branches, functions, lines |

- **Excluded from measurement** (the only allowed list; adding to it needs an ADR update):
  - Generated code: `backend/internal/api/*.gen.go`, `frontend/packages/core/src/api/generated/**`
  - Process wiring: `backend/cmd/api/main.go` (kept to calling `run()`; `run()` itself is tested)
  - Test helpers: `backend/internal/testutil/**`, `**/test-utils/**`
  - Config and declaration files: `app.config.ts`, `vite.config.ts`, `*.d.ts`, `babel/metro/jest/vitest` configs; the back office `main.tsx` (renders the root only)
  - Barrel files that only re-export: `**/index.ts`, and expo-router route files that only re-export a screen (`app/**` except `_layout.tsx`)
- **No ignore comments** (`/* istanbul ignore */`, `// coverage-ignore`) without a one-line reason next to it; the reviewer rejects unexplained ones.
- **Not counted**: the manual two-device run (task 016) and infra scripts (`deploy/*.sh`), which are checked by their task's acceptance criteria instead.

## Alternatives considered

- **80–90% threshold**: the usual compromise, but "which 10% is fine to skip?" gets decided ad hoc each task, and gaps compound.
- **Coverage reported, not enforced**: easy to ignore.
- **Diff coverage only (new lines 100%)**: fairer to legacy code, but we have no legacy code; total 100% is simpler to check.

## Consequences

- Each task takes longer; tests are part of "done", not a follow-up.
- Code must be written to be testable: injectable clock, DB, HTTP client, and WebSocket; no logic in `main.go` or route files.
- 100% coverage proves every line ran, not that behavior is right; acceptance-criteria tests still matter.
- Go measures statements only (no branch coverage); Go branches are covered by table-driven tests per acceptance criterion.
- Defensive branches that can't be reached must be removed or made reachable through a test double, not ignored.
