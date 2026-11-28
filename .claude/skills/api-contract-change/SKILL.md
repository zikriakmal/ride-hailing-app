---
name: api-contract-change
description: Use when adding, changing, or removing an API endpoint, request/response field, status code, or error shape. Updates docs/api/openapi.yaml first, then backend and mobile to match.
---

# API contract change

The spec in `docs/api/openapi.yaml` is the source of truth between backend and mobile.

## When to use
- New endpoint, or a change to an existing one's path, params, body, response, or status codes
- Not for: internal refactors that leave request and response unchanged

## Steps
1. **Spec first.** Edit `docs/api/openapi.yaml`:
   - Reuse `components/schemas` and `components/responses`; don't inline duplicates.
   - Every response body is the envelope: success responses use a `*Envelope` schema (add one if the `data` type is new), error responses use `ErrorResponse`. No `204`s; return `data: null`.
   - Set `operationId` (camelCase) and `tags`.
   - Mark protected endpoints with `security: [{ bearerAuth: [] }]`.
2. **Validate** the spec. <!-- TODO: e.g. `npx @redocly/cli lint docs/api/openapi.yaml` -->
3. **Breaking?** Removing or renaming a field, making a field required, or changing a type breaks clients. If so, say so explicitly and ask before you continue.
4. **Backend**: implement or adjust the handler to match the spec exactly.
5. **Mobile**: update the API client and types to match. <!-- TODO: codegen command if used -->
6. **Tests**: add or adjust contract tests that check responses against the schema.

## Rules
- Never change backend or mobile API code without the spec change in the same commit.
- Field names: camelCase. Timestamps: ISO 8601 UTC strings. IDs: strings.

## Done when
- [ ] Spec updated and validates
- [ ] Backend and mobile both match the spec
- [ ] Contract tests pass
