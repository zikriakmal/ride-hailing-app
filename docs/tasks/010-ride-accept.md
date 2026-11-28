# 010: Rider accepts a ride

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 009
- **PRD flow:** 4. Rider accepts

## Goal

A rider taps Accept on an offer. The first rider wins; the consumer immediately sees who is coming; other riders' offers disappear.

## Scope

**In:**
- `POST /rides/{rideId}/accept` with a conditional update so only one accept succeeds
- Ride → `accepted`, `rider_id` set, rider → `on_trip`
- Emit `ride:updated` to consumer and rider; `ride:offer_withdrawn` (`taken`) to other offered riders
- Rider app `features/offers`: Accept button → ride screen (pickup on map, consumer name/phone)
- Consumer app `features/trip`: searching → "Rider on the way" with name, plate, model

**Out (don't build here):**
- Live rider location on consumer map (task 011)
- Arrive/start/complete (task 012)

## API

- `POST /rides/{rideId}/accept`

## Acceptance criteria

- [ ] Accept on a `requested` ride → `200` `Ride` with `rider`, status `accepted`; rider status `on_trip`
- [ ] Two concurrent accepts → exactly one `200`, the other `409 RIDE_NOT_AVAILABLE` (test fires both in parallel)
- [ ] Accept on expired/cancelled/accepted ride → `409 RIDE_NOT_AVAILABLE`; offline or on-trip rider → `409 RIDER_NOT_AVAILABLE`; consumer token → `403`
- [ ] Consumer gets `ride:updated`; other offered riders get `ride:offer_withdrawn` `taken`
- [ ] Mobile: both screens switch on accept
- [ ] Consumer sees the rider's phone while the ride is active; `phone` is `null` in history responses (privacy rule)
- [ ] Security (docs/SECURITY.md): authz matrix tests for every endpoint touched (no token → `401`, wrong role → `403`, other user's resource → `404`, suspended → `403`, owner → success); input-abuse tests (oversized body, extra fields ignored, boundary values); no sensitive fields in raw responses
- [ ] Unit tests added for every new/changed function, handler, slice, endpoint, schema, hook, and component
- [ ] Tests cover the cases above and pass; coverage is 100% in every touched codebase (ADR 0013), output pasted in Notes

## Notes

