# Ride-Hailing App

A ride-hailing service: a backend API, a **Consumer app** (passengers) and a **Rider app** (motorbike drivers), plus a **Back office** web app for staff.

> **Status:** planning. A stack is *proposed* (two Expo apps — Consumer and Rider — + Go/Gin backend + Postgres + WebSocket, hosted with Docker on an existing VPS behind its nginx and deployed by GitHub Actions; see `docs/decisions/`) and work is broken into tasks 001–027. No code yet.

## What it does (in scope)

1. Sign up / log in (consumer and rider)
2. Consumer requests a ride (pickup, destination, fare estimate)
3. Rider goes online and receives ride requests
4. Rider accepts → consumer sees the rider's location live
5. Trip starts → trip completes
6. Trip history
7. Report a problem (support tickets)
8. Back office for staff: user & rider management, ride assistance, support tickets, audit log

**Not in scope:** real payments (mocked cash), surge pricing, pooling, ratings, multi-city/i18n, push notifications, or production-grade scaling. The full list is in [`docs/PRD.md`](docs/PRD.md).

## Repository layout

```
/
├── CLAUDE.md          # rules for AI agents working in this repo
├── docs/
│   ├── PRD.md           # what we're building and why
│   ├── ARCHITECTURE.md  # stack, data model, folder structure
│   ├── INFRA.md         # hosting, CI/CD, runbook
│   ├── BACKLOG.md       # out-of-scope ideas parked for later
│   ├── api/
│   │   ├── openapi.yaml # REST contract (backend ↔ mobile)
│   │   └── realtime.md  # WebSocket messages
│   ├── decisions/       # ADRs
│   └── tasks/           # units of work (NNN-*.md) + README.md roadmap
├── backend/           # API server (not yet created)
├── frontend/           # pnpm workspace: apps/consumer, apps/rider, apps/backoffice, packages/* (not yet created)
├── deploy/            # production compose, nginx server block, backups (not yet created)
├── .github/workflows/ # CI + deploy (not yet created)
└── .claude/           # agents, commands, skills
```

## Getting started

Commands are filled in by tasks 001 (backend) and 002 (mobile):

| Action | Command |
|--------|---------|
| Install | TBD |
| Run backend | TBD |
| Run Consumer app | TBD |
| Run Rider app | TBD |
| Run Back office | TBD |
| Deploy | automatic on merge to `main` (see `docs/INFRA.md`) |
| Test | TBD |
| Lint/format | TBD |

Quick start (backend): `cp .env.example .env && docker compose up --build` → API on `http://localhost:3000`. What each service does is explained in [`docs/INFRA.md`](docs/INFRA.md#docker-compose-what-runs-where).

Configuration goes in `.env` (gitignored). Variables are documented in `.env.example`.

## How work happens here

- **Tasks:** each unit of work is a file in `docs/tasks/`; the order is in [`docs/tasks/README.md`](docs/tasks/README.md). Work on one at a time (`/next-task`).
- **Contract first:** endpoint changes go into `docs/api/openapi.yaml` before the backend or mobile code changes.
- **Decisions:** record choices people might later ask "why?" about as an ADR in `docs/decisions/` (start from `0000-template.md`).
- **Scope:** ideas that don't belong to the current task go in `docs/BACKLOG.md`.
- **Done:** a task is done only when its acceptance criteria are checked off and the tests pass.

The full working rules are in [`CLAUDE.md`](CLAUDE.md).

## Commits

Keep commits small, one logical change each, using [Conventional Commits](https://www.conventionalcommits.org/): `<type>(<scope>): <imperative summary>`.

| Type | Use for | Example |
|------|---------|---------|
| `feat` | new behavior | `feat(rides): add fare estimate endpoint` |
| `fix` | bug fix | `fix(auth): reject expired tokens on websocket` |
| `hotfix` | urgent production fix | `hotfix(api): restore health check route` |
| `docs` | documentation only | `docs(adr): record maps decision` |
| `test` | tests only | `test(rides): cover accept race` |
| `refactor` | no behavior change | `refactor(core): extract envelope parser` |
| `chore` / `ci` / `build` | tooling, pipeline, packaging | `ci: cache pnpm store` |

Never commit secrets.
