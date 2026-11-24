# Ride-Hailing App

A ride-hailing service: a backend API plus a mobile client for **riders** and **drivers**.

> **Status:** early planning. The stack isn't chosen yet and no code exists. See `docs/ARCHITECTURE.md`.

## What it does (in scope)

1. Sign up / log in (rider and driver)
2. Rider requests a ride (pickup, destination, fare estimate)
3. Driver goes online and receives ride requests
4. Driver accepts → rider sees the driver's location live
5. Trip starts → trip completes
6. Trip history

**Not in scope:** real payments (mocked), surge pricing, pooling, ratings, an admin dashboard, multi-city/i18n, or production-grade scaling. The full list is in [`docs/PRD.md`](docs/PRD.md).

## Repository layout

```
/
├── CLAUDE.md          # rules for AI agents working in this repo
├── docs/
│   ├── PRD.md           # what we're building and why
│   ├── ARCHITECTURE.md  # stack, data model, folder structure
│   ├── BACKLOG.md       # out-of-scope ideas parked for later
│   ├── api/openapi.yaml # backend ↔ mobile contract
│   ├── decisions/       # ADRs
│   └── tasks/           # units of work (NNN-*.md)
├── backend/           # API server (not yet created)
├── mobile/            # rider + driver app (not yet created)
└── .claude/           # agents, commands, skills
```

## Getting started

The stack hasn't been picked yet, so these commands don't exist yet:

| Action | Command |
|--------|---------|
| Install | TBD |
| Run backend | TBD |
| Run mobile | TBD |
| Test | TBD |
| Lint/format | TBD |

Configuration goes in `.env` (gitignored). Variables are documented in `.env.example`.

## How work happens here

- **Tasks:** each unit of work is a file in `docs/tasks/`. Work on one at a time.
- **Contract first:** endpoint changes go into `docs/api/openapi.yaml` before the backend or mobile code changes.
- **Decisions:** record choices people might later ask "why?" about as an ADR in `docs/decisions/` (start from `0000-template.md`).
- **Scope:** ideas that don't belong to the current task go in `docs/BACKLOG.md`.
- **Done:** a task is done only when its acceptance criteria are checked off and the tests pass.

The full working rules are in [`CLAUDE.md`](CLAUDE.md).

## Commits

Keep commits small, one logical change each, in the imperative mood (`Add login endpoint`). Never commit secrets.
