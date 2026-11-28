# 0008: Forms with React Hook Form + zod

- **Date:** 2026-11-28
- **Status:** proposed

## Context

Signup, login, and destination search need instant client-side validation, plus server validation errors (one `VALIDATION_ERROR` item per `field` in the envelope) shown under the right input.

## Decision

- **React Hook Form** for every form, with `@hookform/resolvers/zod`.
- **zod** schemas per form in the feature's `schemas.ts`, mirroring the constraints in `docs/api/openapi.yaml` (min lengths, `+62` phone pattern, rider requires `vehicle`). Form types come from `z.infer`.
- One shared helper `applyServerErrors(errors, setError)` in `@ride/core` maps each `errors[].field` to `setError(field, { message })`; items without a matching field go to `root.serverError` and show above the submit button.
- Inputs connect to RHF through a shared `FormField` molecule using `Controller`, so atoms stay unaware of RHF.

## Alternatives considered

- **Formik + Yup**: older, more re-renders, Yup's TS inference is weaker.
- **Validation only on the server**: simpler, but a round trip for every typo.
- **Generating zod from OpenAPI** (e.g. orval / openapi-zod-client): avoids drift, but adds a codegen tool for ~3 forms; revisit if forms multiply (backlog).

## Consequences

- Validation rules exist in two places (spec and zod); a unit test per schema checks the same edge cases as the backend tests.
- Server errors and client errors render identically.
- zod is used for forms only, not to re-validate API responses (types come from the spec).
