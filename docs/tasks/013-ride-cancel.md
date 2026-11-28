# 013: Cancel a ride

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 012
- **PRD flow:** 5 (edge case); PRD rule "Cancelling"

## Goal

The consumer can cancel before the trip starts; the rider can cancel before arriving. The other party is told immediately.

## Scope

**In:**
- `POST /rides/{rideId}/cancel` using the shared transition function and the rules in `docs/ARCHITECTURE.md`
- Sets `cancelled_by`, `cancelled_at`; assigned rider back to `online`
- `ride:updated` to both parties; while `requested`, `ride:offer_withdrawn` (`cancelled`) to offered riders
- Both apps' `features/trip` (shared `cancelRide` endpoint in `@ride/core`): Cancel button where allowed (with confirm); "Ride cancelled by …" message to the other side

**Out (don't build here):**
- Cancellation fees, reasons, penalties

## API

- `POST /rides/{rideId}/cancel`

## Acceptance criteria

- [ ] Consumer cancels in `requested`, `accepted`, `arrived` → `200`, `cancelledBy: consumer`
- [ ] Consumer cancels in `in_progress` → `409 INVALID_TRANSITION`
- [ ] Rider cancels in `accepted` → `200`, `cancelledBy: rider`; in `arrived` or later → `409`
- [ ] Unrelated user → `404`; rider status back to `online` after cancel
- [ ] Offered riders get `ride:offer_withdrawn` `cancelled` when a `requested` ride is cancelled
- [ ] Mobile: cancel button only shown when allowed; other party sees the message
- [ ] Unit tests added for every new/changed function, handler, slice, endpoint, schema, hook, and component
- [ ] Tests cover the cases above and pass; coverage is 100% in every touched codebase (ADR 0013), output pasted in Notes

## Notes

