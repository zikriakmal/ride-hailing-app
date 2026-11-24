# CLAUDE.md

Rules for any agent working in this repo. Read this first, every session.

## Project

Ride-hailing app POC: a backend API plus a mobile client for riders and drivers.

## Where to look

| Need | File |
|------|------|
| What we're building and why (and what we're NOT building) | `docs/PRD.md` |
| Stack, data model, folder structure | `docs/ARCHITECTURE.md` |
| Backend ↔ mobile contract | `docs/api/openapi.yaml` |
| Why a past choice was made | `docs/decisions/` |
| Current unit of work | `docs/tasks/NNN-*.md` |
| Ideas that are out of scope for now | `docs/BACKLOG.md` |
| How to do recurring jobs (API change, new task, ADR) | `.claude/skills/` |

## Working rules

1. **One task at a time.** Work only on the task file you were pointed at (or the next `todo` task via `/next-task`). Don't start adjacent work.
2. **Scope control.** If you spot a good idea outside the current task, add one line to `docs/BACKLOG.md` and keep going. Don't build it.
3. **Contract first.** Any change to an endpoint goes into `docs/api/openapi.yaml` *before* the backend or mobile code changes. Backend and mobile must both match the spec.
4. **Respect non-goals.** If a request conflicts with a non-goal in `docs/PRD.md`, stop and ask.
5. **Record decisions.** Choosing a library, pattern, or trade-off that someone might later ask "why?" about → write a short ADR in `docs/decisions/` (copy `0000-template.md`).
6. **Keep docs true.** If you change the data model or folder layout, update `docs/ARCHITECTURE.md` in the same change.
7. **Done means verified.** A task is done only when its acceptance criteria are checked off and tests pass. Show the command output; don't just claim it.
8. **Update the task file.** Set `Status:` and tick acceptance criteria as you go; add notes on anything surprising.

## Commands

<!-- TODO: fill in once the stack is chosen -->
- Install: `TBD`
- Run backend: `TBD`
- Run mobile: `TBD`
- Test: `TBD`
- Lint/format: `TBD`

## Conventions

<!-- TODO: naming, error format, commit style, etc. -->
- Commits: small, one logical change, imperative mood (`Add login endpoint`).
- No secrets in the repo. Use `.env` (gitignored) and document variables in `.env.example`.
