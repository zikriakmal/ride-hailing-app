---
name: new-adr
description: Use when choosing a stack component, library, pattern, or trade-off someone might later ask "why did we do it this way?" about. Writes a short ADR in docs/decisions/.
---

# New ADR

## When to use
- Picking a technology (database, realtime transport, maps provider, auth approach, framework)
- Choosing a pattern with real trade-offs (e.g. polling vs websockets for rider location)
- Reversing or replacing an earlier decision
- Not for: obvious or easily reversible choices (formatting, variable names)

## Steps
1. Next number: the highest `docs/decisions/NNNN-*.md` + 1, zero-padded to 4 digits (`0000` is the template).
2. Copy `docs/decisions/0000-template.md` to `NNNN-<kebab-title>.md`.
3. Fill it in. List at least two real alternatives with honest reasons for rejecting them.
4. If it replaces an older ADR, set the old one's status to `superseded by NNNN`.
5. If it's a stack choice, update the table in `docs/ARCHITECTURE.md` with the choice and a link to the ADR.

## Rules
- Keep it under about a page. Context, decision, alternatives, consequences. That's it.
- Write it at the moment of deciding, not afterwards.
- Never edit an accepted ADR's decision. Supersede it with a new one instead.

## Done when
- [ ] ADR file created, status `accepted` (or `proposed` if awaiting the user)
- [ ] `docs/ARCHITECTURE.md` updated if relevant
