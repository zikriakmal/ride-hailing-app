# 005: Session restore and logout

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 003
- **PRD flow:** 1. Sign up / log in

## Goal

A user who logged in earlier opens their app and goes straight to its home screen. They can log out. An expired or invalid token sends them back to login.

## Scope

**In:**
- `GET /me`
- Auth guard used by every protected route: missing/invalid/expired token → `401 UNAUTHORIZED`
- Role guard helper: wrong role → `403 FORBIDDEN` (used by later tasks)
- `@ride/features/auth` `useSessionBootstrap(appRole)`, used in each app's `app/_layout.tsx`: read token from secure store → `authSlice` → `getMe` → `(main)` if `user.role === appRole`, else clear token and show login
- Mobile: any `401` envelope dispatches `auth/loggedOut`, which clears secure store, resets the RTK Query cache, and shows login
- Mobile: logout button on both apps' home screens

**Out (don't build here):**
- Refresh tokens, server-side revocation

## API

- `GET /me`

## Acceptance criteria

- [ ] `GET /me` with a valid token → `200` `User` (with `rider` for riders)
- [ ] No token, malformed token, wrong signature, or expired token → `401 UNAUTHORIZED`
- [ ] Role guard returns `403 FORBIDDEN` for the wrong role (unit test on a dummy route)
- [ ] Mobile: relaunch with a stored valid token skips login
- [ ] Mobile: logout clears the token and API cache and shows login; a `401` from any endpoint does the same (test with `axios-mock-adapter`)
- [ ] Security (docs/SECURITY.md): authz matrix tests for every endpoint touched (no token → `401`, wrong role → `403`, other user's resource → `404`, suspended → `403`, owner → success); input-abuse tests (oversized body, extra fields ignored, boundary values); no sensitive fields in raw responses
- [ ] Unit tests added for every new/changed function, handler, slice, endpoint, schema, hook, and component
- [ ] Tests cover the cases above and pass; coverage is 100% in every touched codebase (ADR 0013), output pasted in Notes

## Notes

