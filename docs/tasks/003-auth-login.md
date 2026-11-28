# 003: Auth login

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 001, 002
- **PRD flow:** 1. Sign up / log in

## Goal

A registered user (consumer or rider) can log in with email + password and receive an access token the mobile app uses for later requests.

## Scope

**In:**
- `POST /auth/login` as defined in `docs/api/openapi.yaml`
- Password hashing + verification
- Issue JWT access token (ADR 0006: HS256, `{ sub, role }`, 7 days)
- Email matched case-insensitively
- Unknown email still runs a bcrypt compare against a dummy hash (no timing leak); JWT validation pins `alg` HS256 and checks `exp`, `iat`, `iss`, `aud`
- Login rate limits from docs/SECURITY.md (per email failures, per IP)
- `@ride/core`: `login` endpoint (RTK Query), `authSlice` (`token`, `user`), `loginSchema` (zod)
- `@ride/features/auth`: `LoginForm` organism with React Hook Form, taking the app's role
- Each app: `features/auth/LoginScreen` page on `FormTemplate`; token saved to `expo-secure-store`
- A test-only way to create a user (factory/seed), since signup is task 004

**Out (don't build here):**
- Sign-up (separate task)
- Password reset, OAuth / social login, refresh tokens, 2FA

## API

- `POST /auth/login`

## Acceptance criteria

- [ ] Valid credentials → `200` envelope; `data` has `accessToken` and `user` matching the `AuthResponse` schema
- [ ] Wrong password or unknown email → `401 INVALID_CREDENTIALS`, same message for both (no user enumeration)
- [ ] Malformed body (missing field, bad email, password < 8) → `400 VALIDATION_ERROR`
- [ ] Tokens with `alg: none`, a different alg, wrong `aud`/`iss`, or expired are rejected
- [ ] 11th failed login for one email within 15 min → `429 RATE_LIMITED`; response time for unknown email vs wrong password differs by < 20% (statistical test over N tries)
- [ ] Returned token verifies with `JWT_SECRET` and carries `sub` and `role`
- [ ] Passwords are stored hashed, never in plain text
- [ ] Mobile: successful login stores token and navigates to the app's home screen
- [ ] Mobile: logging in to the Rider app with a consumer account (or vice versa) shows "Please use the … app", stores no token, and stays on login
- [ ] Mobile: zod blocks submit for an invalid email or short password, with messages under the fields
- [ ] Mobile: `401 INVALID_CREDENTIALS` shows above the submit button; server field errors show under their fields (via `applyServerErrors`)
- [ ] Security (docs/SECURITY.md): authz matrix tests for every endpoint touched (no token → `401`, wrong role → `403`, other user's resource → `404`, suspended → `403`, owner → success); input-abuse tests (oversized body, extra fields ignored, boundary values); no sensitive fields in raw responses
- [ ] Unit tests added for every new/changed function, handler, slice, endpoint, schema, hook, and component
- [ ] Tests cover the cases above and pass; coverage is 100% in every touched codebase (ADR 0013), output pasted in Notes

## Notes

<!-- Decisions, surprises, follow-ups. Out-of-scope ideas go to docs/BACKLOG.md. -->
