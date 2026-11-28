# 009: Request a ride and dispatch offers

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 006, 007, 008
- **PRD flow:** 2. Consumer requests a ride; 3. Rider receives a ride request

## Goal

A consumer confirms the estimate and requests a ride. Every online rider within 3 km gets the offer within 5 s. If nobody accepts in 60 s the ride expires and the consumer can try again.

## Scope

**In:**
- `POST /rides`, `GET /rides/current` (`data: null` when none), `GET /rides/{rideId}`
- Fare recomputed server-side; `409 ACTIVE_RIDE_EXISTS` if the consumer has an active ride
- Dispatch: riders with `status = online` and `last_location_at` ≤ 30 s old within 3 km → `ride:offered`
- Expiry after 60 s → status `expired`, `ride:updated` to consumer, `ride:offer_withdrawn` (`expired`) to offered riders. Expiry must survive nothing fancier than a single running server; on startup, expire any overdue `requested` rides.
- Consumer app: "Request ride" button → searching screen with countdown; expired → "No riders found, try again"
- Rider app: offer card (pickup, dropoff, distance, fare, countdown); disappears on `ride:offer_withdrawn`
- Mobile: Consumer app `features/ride-request` (request endpoint, searching screen); Rider app `features/offers` (`offersSlice` fed by `ride:offered` / `ride:offer_withdrawn`); in both apps `realtime/connected` refetches `getCurrentRide` and `ride:updated` patches its cache

**Out (don't build here):**
- Accepting (task 010), cancelling (task 013)
- Re-offering to riders who come online after the ride was created

## API

- `POST /rides`
- `GET /rides/current`
- `GET /rides/{rideId}`

## Acceptance criteria

- [ ] `POST /rides` → `201` `Ride` in `requested`, `expiresAt = requestedAt + 60 s`, fare matches `/rides/estimate`
- [ ] Second request while one is active → `409 ACTIVE_RIDE_EXISTS`; rider token → `403`
- [ ] Rider 2 km away (online, fresh location) receives `ride:offered`; rider 4 km away, offline, on_trip, or with a stale location does not
- [ ] After 60 s with no accept → `expired`; consumer gets `ride:updated`, offered riders get `ride:offer_withdrawn` `expired` (fake timers)
- [ ] `GET /rides/current` → `200` with the active ride or `data: null`; `GET /rides/{id}` by an unrelated user → `404`
- [ ] Mobile: consumer sees searching state and expiry message; rider sees and loses the offer card
- [ ] Unit tests added for every new/changed function, handler, slice, endpoint, schema, hook, and component
- [ ] Tests cover the cases above and pass; coverage is 100% in every touched codebase (ADR 0013), output pasted in Notes

## Notes

