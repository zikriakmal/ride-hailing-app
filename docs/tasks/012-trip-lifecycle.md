# 012: Arrive, start, and complete the trip

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 011
- **PRD flow:** 5. Trip starts → trip completes

## Goal

The rider moves the ride through Arrived → Start trip → Complete (cash received). Both apps show each step within seconds and end on a trip summary with the fare.

## Scope

**In:**
- `POST /rides/{rideId}/arrive`, `/start`, `/complete` (assigned rider only), via one shared transition function in `internal/rides/lifecycle.go`
- Complete sets `fare_final = fare_estimate`, rider back to `online`
- `ride:updated` to both parties on each step
- Rider app `features/trip`: one primary button per state; Complete confirms "Cash received Rp X?"
- Consumer app `features/trip`: status banner per state; summary screen on completion

**Out (don't build here):**
- Cancellation (task 013)
- Receipts, tips, ratings

## API

- `POST /rides/{rideId}/arrive`
- `POST /rides/{rideId}/start`
- `POST /rides/{rideId}/complete`

## Acceptance criteria

- [ ] Each endpoint moves the ride one step and sets its timestamp; `ride:updated` reaches consumer and rider
- [ ] Out-of-order call (e.g. `start` on `accepted`, `complete` on `arrived`) → `409 INVALID_TRANSITION`
- [ ] Another rider or the consumer calling these → `403 FORBIDDEN`
- [ ] After complete: `fareFinal = fareEstimate`, rider status `online`, `GET /rides/current` → `data: null` for both
- [ ] Mobile: both apps reflect each state and show the summary
- [ ] Unit tests added for every new/changed function, handler, slice, endpoint, schema, hook, and component
- [ ] Tests cover the cases above and pass; coverage is 100% in every touched codebase (ADR 0013), output pasted in Notes

## Notes

