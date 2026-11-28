# 025: Support tickets (backend + back office queue)

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 021
- **PRD flow:** 11. Support tickets (and the API for 7. Report a problem)

## Goal

Tickets exist end to end on the server: users can create and reply via the API, and staff work a prioritized queue in the back office: assign, reply, add internal notes, and resolve.

## Scope

**In:**
- Migrations: `ticket`, `ticket_message` + indexes
- User side: `POST/GET /tickets`, `GET /tickets/{ticketId}`, `POST /tickets/{ticketId}/messages`: owner only; `rideId` must be the caller's ride; internal notes never returned; staff shown as "Support"; reply to `resolved` reopens
- Staff side: `GET /admin/tickets` (filters, urgent first), `GET/PATCH /admin/tickets/{ticketId}`, `POST /admin/tickets/{ticketId}/messages` (`internal` flag); audit for assign/status/priority/reply/note
- `ticket:updated` push to the owner on staff reply or status change (not on notes)
- Back office `features/tickets`: queue (filters, "assigned to me", urgent badge, poll 15 s), ticket page (thread with notes styled differently, reply/note composer, assign, priority, resolve), links to user and ride
- Ticket links on the user profile (023) and ride detail (024) pages

**Out (don't build here):**
- The in-app screens for consumers/riders (026)
- Attachments, email notifications, SLAs, canned replies (backlog)

## API

- `POST /tickets`, `GET /tickets`, `GET /tickets/{ticketId}`, `POST /tickets/{ticketId}/messages`
- `GET /admin/tickets`, `GET /admin/tickets/{ticketId}`, `PATCH /admin/tickets/{ticketId}`, `POST /admin/tickets/{ticketId}/messages`

## Acceptance criteria

- [ ] `safety` tickets are created `urgent` and listed first; others `normal`
- [ ] `rideId` of someone else's ride → `404`; another user's ticket → `404`
- [ ] Internal notes never appear in `/tickets/*` responses (test asserts on raw JSON); staff names never appear there either
- [ ] Assigning an `open` ticket → `in_progress`; resolve sets `resolvedAt`; user reply on `resolved` → `open`, `resolvedAt` cleared
- [ ] Staff reply pushes `ticket:updated` to the owner; an internal note pushes nothing
- [ ] Each staff write produces the matching audit entry
- [ ] Security (docs/SECURITY.md): authz matrix tests for every endpoint touched (no token → `401`, wrong role → `403`, other user's resource → `404`, suspended → `403`, owner → success); input-abuse tests (oversized body, extra fields ignored, boundary values); no sensitive fields in raw responses
- [ ] Unit tests added for every new/changed function, handler, slice, endpoint, schema, hook, and component
- [ ] Tests cover the cases above and pass; coverage is 100% in every touched codebase (ADR 0013), output pasted in Notes

## Notes

