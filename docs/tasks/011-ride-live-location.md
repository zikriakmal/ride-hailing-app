# 011: Consumer sees rider location live

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 010
- **PRD flow:** 4. Consumer sees rider location live

## Goal

From accept until the trip ends, the consumer's map shows the rider's marker moving, updated at least every 3 s.

## Scope

**In:**
- On `PUT /riders/me/location` while the rider's ride is `accepted`/`arrived`/`in_progress`, emit `rider:location` to the consumer
- `Ride.rider.location` filled from the rider's last location in REST responses while active
- `@ride/features/trip-map` `TripMap` organism (pickup, dropoff, rider marker), used by the Consumer app `features/trip` screen with `rideLive` slice; marker moves on each event; initial position from `GET /rides/current`

**Out (don't build here):**
- Route line, ETA
- Smoothing/animation beyond moving the marker

## API

- none new (behavior on `PUT /riders/me/location`; `Ride.rider.location` already in spec)

## Acceptance criteria

- [ ] Rider location PUT during an active ride → consumer receives `rider:location` with matching coords; no event to anyone when the rider has no active ride
- [ ] `GET /rides/current` for the consumer includes `rider.location`; completed rides in history have `rider.location: null`
- [ ] Mobile: marker position updates on each event (component test)
- [ ] Security (docs/SECURITY.md): authz matrix tests for every endpoint touched (no token → `401`, wrong role → `403`, other user's resource → `404`, suspended → `403`, owner → success); input-abuse tests (oversized body, extra fields ignored, boundary values); no sensitive fields in raw responses
- [ ] Unit tests added for every new/changed function, handler, slice, endpoint, schema, hook, and component
- [ ] Tests cover the cases above and pass; coverage is 100% in every touched codebase (ADR 0013), output pasted in Notes

## Notes

