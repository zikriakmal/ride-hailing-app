# 024: Ride assistance (live rides, timeline, force-cancel)

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 021, 011, 013
- **PRD flow:** 10. Ride assistance

## Goal

Staff see every active ride on a list and a live map, open any ride's full timeline, and force-cancel a stuck ride, which both apps learn about immediately.

## Scope

**In:**
- `GET /admin/rides` (`status` incl. `active`, `userId`, pagination); active rides include `rider.location`
- `GET /admin/rides/{rideId}`: timeline built from ride timestamps + audit entries for the ride + tickets opened about it
- `POST /admin/rides/{rideId}/cancel` (staff, reason): reuses the shared transition function in `internal/rides/lifecycle.go`; `cancelledBy: support`, `cancel_reason`; rider back to `online`; `ride:updated` to both, `ride:offer_withdrawn` while `requested`; audit `ride.force_cancelled`
- Consumer and Rider apps: show "Ride cancelled by support" when `cancelledBy: support`
- Back office `features/rides`: active rides table + Leaflet map polling every 5 s (paused when tab hidden), ride detail with timeline, force-cancel dialog

**Out (don't build here):**
- Reassigning a ride to another rider, refunds, contacting users by phone from the app (backlog)

## API

- `GET /admin/rides`, `GET /admin/rides/{rideId}`, `POST /admin/rides/{rideId}/cancel`

## Acceptance criteria

- [ ] `status=active` returns only requested/accepted/arrived/in_progress rides, with rider locations for assigned ones
- [ ] Timeline lists each status change with actor, plus staff actions and linked tickets, oldest first
- [ ] Force-cancel works from every active state; on `completed`/`cancelled`/`expired` → `409 INVALID_TRANSITION`; missing reason → `400`
- [ ] After force-cancel both apps update within 5 s and show the support message; the rider can receive offers again
- [ ] Back office: map markers move between polls; polling stops when the tab is hidden (fake timers + visibility test)
- [ ] Unit tests added for every new/changed function, handler, slice, endpoint, schema, hook, and component
- [ ] Tests cover the cases above and pass; coverage is 100% in every touched codebase (ADR 0013), output pasted in Notes

## Notes

