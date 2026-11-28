# 015: Dev-only simulate rider

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 011
- **PRD flow:** PRD rule "Location" (testing aid)

## Goal

One developer can test a full ride without walking around: the Rider app can fake its GPS and move toward pickup, then toward dropoff.

## Scope

**In:**
- Rider app `features/dev-tools`: dev toggle (shown only when `__DEV__`): replaces real GPS with a position that moves in a straight line toward the next target (pickup while `accepted`, dropoff while `in_progress`) at ~30 km/h, sending through the normal `PUT /riders/me/location`
- Optional backend seed script: one consumer + one rider account with known passwords, documented in `README.md`

**Out (don't build here):**
- Any backend simulation endpoint
- Routing along roads

## API

- none

## Acceptance criteria

- [ ] Toggle is absent in production builds (`__DEV__` false)
- [ ] With the toggle on, sent positions step toward the target and stop at it (unit test of the step function)
- [ ] Seed script creates the two accounts idempotently
- [ ] Security (docs/SECURITY.md, MASVS): nothing sensitive outside secure store or in logs; release build is HTTPS/WSS-only
- [ ] Unit tests added for every new/changed function, handler, slice, endpoint, schema, hook, and component
- [ ] Tests cover the cases above and pass; coverage is 100% in every touched codebase (ADR 0013), output pasted in Notes

## Notes

