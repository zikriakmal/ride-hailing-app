# 0006: Email + password with a JWT access token

- **Date:** 2026-11-27
- **Status:** proposed

## Context

Consumers and riders log in from the app. The API and the socket both need to know who is calling and their role. Refresh tokens, social login, and password reset are in the backlog.

## Decision

Passwords hashed with bcrypt (cost 12, `golang.org/x/crypto/bcrypt`). Login/signup return a stateless JWT (`golang-jwt/jwt/v5`, HS256, `{ sub, role }`, 7-day expiry, secret `JWT_SECRET`). The app stores it in `expo-secure-store` and sends `Authorization: Bearer`; the WebSocket sends the same header on connect. Logout deletes the token on the device.

## Alternatives considered

- **Server sessions + cookies**: cookies are awkward in React Native, and the socket would need a separate mechanism.
- **Short access token + refresh token**: more secure, but more code; parked in backlog.
- **Auth provider (Firebase Auth, Auth0)**: external dependency for a demo.

## Consequences

- No server-side token revocation on logout: logout is device-only; a leaked token is valid until expiry. **Suspension is the exception**: the server checks `suspended_at` on every request (ADR 0015).
- Staff (`support`, `admin`) tokens expire after 12 h instead of 7 days (ADR 0015).
- Role is in the token, so role checks need no DB lookup.
- Changing `JWT_SECRET` logs everyone out.
