# 001: Auth login

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** none
- **PRD flow:** 1. Sign up / log in

## Goal

A registered user (rider or driver) can log in with email + password and receive an access token the mobile app uses for later requests.

## Scope

**In:**
- `POST /auth/login` as defined in `docs/api/openapi.yaml`
- Password hashing + verification
- Issue access token
- Mobile login screen calling the endpoint, storing the token securely

**Out (don't build here):**
- Sign-up (separate task)
- Password reset, OAuth / social login, refresh tokens, 2FA

## Acceptance criteria

- [ ] Valid credentials → `200` with `accessToken` and `user` matching the `AuthResponse` schema
- [ ] Wrong password or unknown email → `401` with `Error` body, same message for both (no user enumeration)
- [ ] Malformed body → `400` with `Error` body
- [ ] Passwords are stored hashed, never in plain text
- [ ] Mobile: successful login stores token and navigates to the role's home screen
- [ ] Mobile: failed login shows an error message
- [ ] Tests cover the cases above and pass

## Notes

<!-- Decisions, surprises, follow-ups. Out-of-scope ideas go to docs/BACKLOG.md. -->
