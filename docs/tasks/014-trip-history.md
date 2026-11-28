# 014: Trip history

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 012
- **PRD flow:** 6. Trip history

## Goal

Consumers and riders see a list of their past rides, newest first, and can scroll back through older ones.

## Scope

**In:**
- `GET /rides` with `limit` + opaque `cursor` (keyset on `requested_at, id`)
- Consumer sees `completed`, `cancelled`, `expired`; rider sees `completed` and `cancelled` rides they were assigned
- `listRides` endpoint in `@ride/core` with cursor pagination merged in RTK Query; `RideHistoryList` + `HistoryScreen` in `@ride/features/history`; each app adds a History tab re-exporting it; row shows date, pickup → dropoff, fare, other party's name, status; infinite scroll; empty state

**Out (don't build here):**
- Ride detail screen, receipts, filters, search

## API

- `GET /rides`

## Acceptance criteria

- [ ] Returns only the caller's rides in the statuses above, newest first; active rides excluded
- [ ] Pagination: 25 rides with `limit=10` → pages of 10, 10, 5, last `nextCursor: null`; no duplicates or gaps
- [ ] Invalid `limit` (0, 51) or garbage `cursor` → `400`
- [ ] Mobile: list renders, loads more on scroll, shows empty state
- [ ] History items have `consumer.phone` / `rider.phone` = `null` (counterpart phones only during active rides)
- [ ] Security (docs/SECURITY.md): authz matrix tests for every endpoint touched (no token → `401`, wrong role → `403`, other user's resource → `404`, suspended → `403`, owner → success); input-abuse tests (oversized body, extra fields ignored, boundary values); no sensitive fields in raw responses
- [ ] Unit tests added for every new/changed function, handler, slice, endpoint, schema, hook, and component
- [ ] Tests cover the cases above and pass; coverage is 100% in every touched codebase (ADR 0013), output pasted in Notes

## Notes

