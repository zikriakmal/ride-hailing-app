# 008: Realtime connection

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 005
- **PRD flow:** 3, 4 (foundation for pushes)

## Goal

The app holds an authenticated WebSocket connection while logged in, and the backend can emit an event to any user, per `docs/api/realtime.md`.

## Scope

**In:**
- `GET /ws` with `coder/websocket` (ADR 0004); bearer token checked before upgrade; mounted outside the OpenAPI validation middleware
- `internal/realtime/hub.go`: mutex-guarded `userID → connections`; `SendToUser(userID, event, data)`; unregister on close; ping every 25 s
- Mobile `src/lib/realtime/`: connect when `authSlice` has a token, close on `auth/loggedOut`, reconnect with backoff (1 s → 30 s); parse `{ event, data }` and dispatch a `realtime/<event>` action; on every (re)connect dispatch `realtime/connected` (task 009 makes it refetch `getCurrentRide`)

**Out (don't build here):**
- Any ride events (tasks 009–012)
- Multi-instance scaling (Redis pub/sub)

## API

- none (realtime contract only)

## Acceptance criteria

- [ ] Valid token upgrades; invalid/missing token → `401` error envelope (`UNAUTHORIZED`), no upgrade
- [ ] `SendToUser` reaches every connection of that user and no other user (integration test with three clients, two of them the same user)
- [ ] Closed connections are removed from the hub; `go test -race` passes on concurrent connect/send/close
- [ ] Mobile: connects on login, closes on logout, reconnects with backoff and runs the resync callback (unit test with mocked `WebSocket` and fake timers)
- [ ] Unit tests added for every new/changed function, handler, slice, endpoint, schema, hook, and component
- [ ] Tests cover the cases above and pass; coverage is 100% in every touched codebase (ADR 0013), output pasted in Notes

## Notes

