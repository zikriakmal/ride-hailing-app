# 026: Report a problem in the Consumer and Rider apps

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 025, 014
- **PRD flow:** 7. Report a problem

## Goal

Consumers and riders report a problem from a ride (or from Help), see their tickets, read support replies, and reply back, in both apps.

## Scope

**In:**
- `@ride/core`: ticket endpoints + `createTicketSchema` (zod: category, message ≤ 2 000)
- `@ride/features`: `ReportProblemForm`, `TicketList`, `TicketThread` organisms and screens
- Each app `features/support`: "Report a problem" from history rows, the active trip screen, and a Help entry; "My tickets" screen; thread with reply box (disabled while sending)
- `ticket:updated` → invalidate that ticket and the list; badge on Help when a reply is unread (local state)
- Category list per app: consumer sees `rider_behavior`, rider sees `consumer_behavior`; both see the rest

**Out (don't build here):**
- Photo attachments, push notifications (backlog)

## API

- none new (uses `/tickets/*` from 025)

## Acceptance criteria

- [ ] Consumer reports a `lost_item` from a completed ride; it appears in the back office queue linked to that ride
- [ ] A staff reply appears in the app thread within 5 s via `ticket:updated`; internal notes never appear
- [ ] Replying to a resolved ticket reopens it (status shown in the app)
- [ ] Validation errors (empty message, > 2 000 chars) show under the field; server errors in the banner
- [ ] Unit tests added for every new/changed function, handler, slice, endpoint, schema, hook, and component
- [ ] Tests cover the cases above and pass; coverage is 100% in every touched codebase (ADR 0013), output pasted in Notes

## Notes

