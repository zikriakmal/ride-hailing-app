# 007: Rider goes online and reports location

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 005
- **PRD flow:** 3. Rider goes online and receives a ride request

## Goal

A rider toggles online/offline. While online (or on a trip), the app sends their GPS position every 3 s and the backend stores it.

## Scope

**In:**
- `PUT /riders/me/status`, `PUT /riders/me/location` (rider only)
- Rider app `features/availability` (`availabilitySlice`): home with map of own position, online/offline toggle, location sent every 3 s while the app is foregrounded and status ≠ offline

**Out (don't build here):**
- Receiving offers (task 009)
- Background location
- Simulated movement (task 015)

## API

- `PUT /riders/me/status`
- `PUT /riders/me/location`

## Acceptance criteria

- [ ] Status `online`/`offline` → `200` `Rider` with new status; consumer token → `403`
- [ ] Going `offline` while `on_trip` → `409 INVALID_TRANSITION`
- [ ] Location PUT → `200` envelope with `data: null`; stores `last_lat`, `last_lng`, `last_location_at`; invalid coordinates → `400`
- [ ] Mobile: toggle reflects server status; going offline stops location updates
- [ ] Mobile: location sent at ~3 s intervals while online (test with fake timers)
- [ ] Unit tests added for every new/changed function, handler, slice, endpoint, schema, hook, and component
- [ ] Tests cover the cases above and pass; coverage is 100% in every touched codebase (ADR 0013), output pasted in Notes

## Notes

