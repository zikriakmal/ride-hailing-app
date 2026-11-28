# CLAUDE.md

Rules for any agent working in this repo. Read this first, every session.

## Project

Ride-hailing app: a backend API plus a mobile client for consumers and riders.

## Where to look

| Need | File |
|------|------|
| What we're building and why (and what we're NOT building) | `docs/PRD.md` |
| Stack, data model, folder structure | `docs/ARCHITECTURE.md` |
| Hosting, CI/CD, deploy runbook | `docs/INFRA.md` |
| Backend ↔ mobile contract (REST) | `docs/api/openapi.yaml` |
| Realtime messages (WebSocket) | `docs/api/realtime.md` |
| Why a past choice was made | `docs/decisions/` |
| Current unit of work | `docs/tasks/NNN-*.md` (roadmap: `docs/tasks/README.md`) |
| Ideas that are out of scope for now | `docs/BACKLOG.md` |
| How to do recurring jobs (API change, new task, ADR) | `.claude/skills/` |

## Working rules

1. **One task at a time.** Work only on the task file you were pointed at (or the next `todo` task via `/next-task`). Don't start adjacent work.
2. **Scope control.** If you spot a good idea outside the current task, add one line to `docs/BACKLOG.md` and keep going. Don't build it.
3. **Contract first.** Any change to an endpoint goes into `docs/api/openapi.yaml` (or a socket event into `docs/api/realtime.md`) *before* the backend or mobile code changes. Backend and mobile must both match the spec.
4. **Respect non-goals.** If a request conflicts with a non-goal in `docs/PRD.md`, stop and ask.
5. **Record decisions.** Choosing a library, pattern, or trade-off that someone might later ask "why?" about → write a short ADR in `docs/decisions/` (copy `0000-template.md`).
6. **Keep docs true.** If you change the data model or folder layout, update `docs/ARCHITECTURE.md` in the same change. Infra or pipeline changes update `docs/INFRA.md`.
7. **Done means verified.** A task is done only when its acceptance criteria are checked off and tests pass. Show the command output; don't just claim it.
8. **Update the task file.** Set `Status:` and tick acceptance criteria as you go; add notes on anything surprising.
9. **Tests ship with the feature, coverage stays 100%.** Every task that adds or changes code adds unit tests for it in the same change. The backend and every mobile app/package must stay at 100% coverage (ADR 0013). Never lower a threshold, widen exclusions, or add an unexplained ignore comment to get there.

## Commands

<!-- TODO: fill in once the stack is chosen -->
Filled in by tasks 001 and 002. Until then they are `TBD`.

- Install: `TBD`
- Start database: `TBD` (proposed: `docker compose up -d`)
- Run backend: `TBD`
- Run mobile: `TBD`
- Test: `TBD`
- Coverage (must be 100%): `TBD` (backend: `go-test-coverage`; mobile: `pnpm -r test:coverage`)
- Lint/format: `TBD`
- Lint API spec: `npx @redocly/cli lint docs/api/openapi.yaml`
- Deploy: automatic on merge to `main` (`.github/workflows/deploy.yml`); rollback via manual run with `tag`

## Conventions

<!-- TODO: naming, error format, commit style, etc. -->
- Commits: small, one logical change, [Conventional Commits](https://www.conventionalcommits.org/): `<type>(<optional scope>): <imperative summary>`, e.g. `feat(auth): add login endpoint`.
  - Types: `feat` (new behavior), `fix` (bug fix), `hotfix` (urgent production fix, deployed right away), `docs`, `test`, `refactor`, `chore` (tooling, deps, config), `ci`, `build`.
  - Scopes: an area like `auth`, `rides`, `tickets`, `admin`, `backoffice`, `consumer-app`, `rider-app`, `infra`, `api`.
  - Breaking API change: add `!` (`feat(api)!: …`) and a `BREAKING CHANGE:` footer.
- API: camelCase fields, string (uuid) IDs, ISO 8601 UTC timestamps, money as integer IDR. Every HTTP response body is the envelope `{ status, data, errors }`; validation errors are one `errors` item per field.
- Clients write over REST; the server pushes over WebSocket `/ws` (ADR 0004).
- Backend: Gin handlers implement the generated `oapi-codegen` interface; DB access through GORM repositories; schema changes are `goose` SQL migrations (ADRs 0002, 0003).
- Terms: **consumer** = passenger (Consumer app), **rider** = motorbike driver (Rider app), **ride** = a trip, **staff** = `support`/`admin` (Back office). Don't mix them up.
- Back office: React + Vite web app `frontend/apps/backoffice` reusing `@ride/core`, same feature/atomic rules, polling instead of WebSocket (ADR 0014). Every staff write records an audit entry in the same transaction; admin-only actions need `requireAdmin` (ADR 0015).
- Mobile: two Expo apps (`frontend/apps/consumer`, `frontend/apps/rider`) sharing `@ride/ui`, `@ride/core`, `@ride/features` in a pnpm workspace (ADR 0010). Server data via RTK Query over axios, client state in RTK slices, forms with React Hook Form + zod (ADRs 0007, 0008). App-only code goes in `apps/<app>/src/features/<feature>/`; code both apps need goes up to a package. UI follows atoms → molecules → organisms → templates → pages; import features only through their `index.ts` (ADR 0009).
- Never deploy by hand-building images on the VPS; images come only from CI (ADR 0012).
- No secrets in the repo. Use `.env` (gitignored) and document variables in `.env.example`.
