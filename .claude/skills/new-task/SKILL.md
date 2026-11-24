---
name: new-task
description: Use when creating a new task file in docs/tasks/, e.g. breaking down a PRD flow or promoting a BACKLOG item. Produces one small, testable task.
---

# New task

## When to use
- Breaking a PRD flow into implementable units
- Promoting a `docs/BACKLOG.md` item that's now in scope
- Not for: ideas that aren't in scope yet (add those to `docs/BACKLOG.md` instead)

## Steps
1. Check `docs/PRD.md`. If the work hits a non-goal, stop and ask.
2. Find the next number: the highest `docs/tasks/NNN-*.md` + 1, zero-padded to 3 digits.
3. Name it `NNN-<area>-<short-verb-noun>.md` (e.g. `002-auth-signup.md`, `003-ride-request.md`).
4. Copy [template.md](template.md) and fill in every section.
5. If the task touches the API, list the affected endpoints. The spec change happens during the task (see the `api-contract-change` skill).
6. If you moved the item out of `docs/BACKLOG.md`, delete it there.

## Rules
- One task should take roughly one focused session. If it's bigger, split it.
- Every acceptance criterion must be checkable by a test or a concrete manual step.
- Make the "Out" list explicit. It's how scope stays controlled.

## Done when
- [ ] File created with all sections filled in
- [ ] `Depends on` lists real task numbers (or `none`)
