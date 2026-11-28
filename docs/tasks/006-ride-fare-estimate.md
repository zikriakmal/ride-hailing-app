# 006: Fare estimate

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 005
- **PRD flow:** 2. Consumer requests a ride

## Goal

A consumer picks pickup (defaults to current GPS) and destination (search or drop a pin) on a map and sees distance and fare within 2 s.

## Scope

**In:**
- `POST /rides/estimate` (consumer only)
- `internal/rides/fare.go`: haversine × 1.3, `max(10 000, 5 000 + 2 500 × km)` rounded up to Rp 500 (PRD rules, ADR 0005)
- Consumer app `features/ride-request` on `MapTemplate`: map, location permission prompt, pickup pin at current position (movable), destination search via `expo-location` geocoding and pin drop, address labels via reverse geocoding, estimate card

**Out (don't build here):**
- Requesting the ride (task 009)
- Route drawing, autocomplete, saved places

## API

- `POST /rides/estimate`

## Acceptance criteria

- [ ] Fare function unit-tested: 0 m → 10 000; a ~1 km trip → 10 000; a 10 km straight-line trip → `5 000 + 2 500 × 13` = 37 500; results are multiples of 500
- [ ] `POST /rides/estimate` → `200` `FareEstimate`; out-of-range coordinates → `400`; rider token → `403`
- [ ] Pickup and dropoff closer than 100 m → `400 VALIDATION_ERROR`
- [ ] Mobile: estimate appears after both points are set; denied location permission shows a message and lets the consumer set pickup manually
- [ ] Security (docs/SECURITY.md): authz matrix tests for every endpoint touched (no token → `401`, wrong role → `403`, other user's resource → `404`, suspended → `403`, owner → success); input-abuse tests (oversized body, extra fields ignored, boundary values); no sensitive fields in raw responses
- [ ] Unit tests added for every new/changed function, handler, slice, endpoint, schema, hook, and component
- [ ] Tests cover the cases above and pass; coverage is 100% in every touched codebase (ADR 0013), output pasted in Notes

## Notes

