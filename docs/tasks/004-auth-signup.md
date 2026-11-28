# 004: Auth signup

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 003
- **PRD flow:** 1. Sign up / log in

## Goal

A new consumer signs up in the Consumer app, a new rider in the Rider app, and each lands logged in on their app's home screen. Riders register their motorbike's plate and model.

## Scope

**In:**
- `POST /auth/signup` per `docs/api/openapi.yaml`; creates `User` (+ `Rider` row with `status: offline` for riders)
- Email stored lowercased; duplicate email (case-insensitive) → `409 EMAIL_TAKEN`
- `@ride/core`: `signup` endpoint, `baseSignupSchema` (zod: name, email, `+62` phone, password)
- `@ride/features/auth`: `SignupForm` organism with the base fields and a slot for extra fields
- Consumer app: `SignupScreen` sends `role: consumer` (no role picker)
- Rider app: `riderSignupSchema` = base + `vehicle`; `VehicleFields` organism in the slot; sends `role: rider`
- Link to/from login in both apps

**Out (don't build here):**
- Email/phone verification, OTP
- Rider document upload or approval
- Vehicle types other than motorbike

## API

- `POST /auth/signup`

## Acceptance criteria

- [ ] Valid consumer signup → `201` `AuthResponse`, no `rider` field on user
- [ ] Valid rider signup with vehicle → `201` `AuthResponse`, `user.rider.status = offline`
- [ ] Rider without `vehicle`, or consumer with `vehicle` → `400 VALIDATION_ERROR`
- [ ] Invalid email / phone not matching `+62…` / password < 8 chars → `400` with one `VALIDATION_ERROR` item per bad field (all reported at once, `field` set)
- [ ] Existing email (any case) → `409 EMAIL_TAKEN`
- [ ] Sending `role: admin`/`support`, `status`, or `id` can't create a staff account or set those fields (mass assignment test); 6th signup per hour from one IP → `429`
- [ ] Password stored as bcrypt hash
- [ ] `signupSchema` unit-tested with the same invalid cases as the backend (email, `+62` phone, password length, rider without vehicle)
- [ ] Mobile: success stores token and goes to the app's home; each `errors` item shows under the field named by `field`, including nested `vehicle.plate`
- [ ] Security (docs/SECURITY.md): authz matrix tests for every endpoint touched (no token → `401`, wrong role → `403`, other user's resource → `404`, suspended → `403`, owner → success); input-abuse tests (oversized body, extra fields ignored, boundary values); no sensitive fields in raw responses
- [ ] Unit tests added for every new/changed function, handler, slice, endpoint, schema, hook, and component
- [ ] Tests cover the cases above and pass; coverage is 100% in every touched codebase (ADR 0013), output pasted in Notes

## Notes

