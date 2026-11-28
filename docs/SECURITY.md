# Security

> How we build this securely, and how to report a problem. Every task follows this file; the reviewer agent checks it. Decision and scope: ADR 0016.

## Reporting a vulnerability

Don't open a public issue. Use GitHub's **private vulnerability reporting** (Security tab → "Report a vulnerability") or email the maintainer. Include steps to reproduce and the impact. We acknowledge within 3 days and aim to fix high/critical issues within 14 days. Please don't test against other people's accounts or degrade the service.

## Baseline

| Standard | Applies to | Target |
|----------|-----------|--------|
| [OWASP ASVS 4.0](https://owasp.org/www-project-application-security-verification-standard/) | backend, back office | **Level 2** for the chapters below |
| [OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/) | backend API | every item has a control + test |
| [OWASP Top 10 (2025)](https://owasp.org/Top10/) | backend, back office | every item has a control |
| [OWASP MASVS 2](https://mas.owasp.org/MASVS/) | Consumer and Rider apps | **L1** (STORAGE, CRYPTO, AUTH, NETWORK, PLATFORM, CODE, PRIVACY) |
| CIS-style host hardening | VPS | checklist in "Infrastructure" below |

What we hold that matters: names, emails, phone numbers, password hashes, live and historical **locations** (pickup/dropoff, rider position), ride history, support conversations, and staff powers (suspend, cancel, read everything). Indonesia's Personal Data Protection Law (UU PDP No. 27/2022) applies to this kind of data. Full compliance is a non-goal, but the privacy rules below follow its spirit (minimum data, purpose limits, access control, breach response).

## Threat model (short)

| Asset | Main threats | Key controls |
|-------|--------------|--------------|
| User accounts | credential stuffing, enumeration, token theft | rate limits, generic errors, bcrypt, short staff tokens, secure storage |
| Other users' rides/tickets | IDOR/BOLA by changing an id | ownership check in every query, 404 for not-yours, authz tests |
| Live locations | stalking via rider/consumer position | location shared only with the counterpart of an **active** ride, and with staff |
| Staff powers | stolen staff account, insider misuse | `support`/`admin` split, reasons required, append-only audit, rate-limited login, optional IP allow-list |
| Ride flow integrity | double-accept, fake completion, fare tampering | conditional updates, server-side fare, role + assignment checks |
| Server & data | RCE, SQLi, leaked secrets, lost DB | parameterized queries, distroless non-root image, secrets only on VPS, encrypted backups |
| Supply chain | malicious dependency or action | lockfiles, pinned versions/SHAs, scanners in CI, Dependabot |

## OWASP API Security Top 10 (2023) → our controls

| # | Risk | Control in this project | Verified by |
|---|------|-------------------------|-------------|
| API1 | Broken Object Level Authorization | Every repository query for a ride/ticket/user is **scoped by the caller** (`WHERE id = ? AND (consumer_id = ? OR rider_id = ?)`), never "load by id then check". Not-yours → `404 NOT_FOUND` (don't reveal existence). | Authz matrix test per endpoint (owner / other user / wrong role / staff / no token) |
| API2 | Broken Authentication | bcrypt cost 12; JWT HS256 with ≥ 32-byte secret, `alg` pinned, `exp`/`iat`/`iss`/`aud` checked; 7 d user / 12 h staff tokens; suspension checked per request; login rate limits; same error for unknown email and wrong password, with a dummy bcrypt compare so timing matches | Unit tests for token validation (wrong alg, expired, bad sig, wrong aud); enumeration timing test |
| API3 | Broken Object Property Level Authorization | Handlers only accept the **generated request types** and write with explicit field lists (GORM `Select(...)`/maps), so no mass assignment (`role`, `status`, `fareFinal` can't be set by clients). Responses are built from spec DTOs, **never** GORM models, so `password_hash` and internal fields can't leak. Counterpart phone numbers only while the ride is active. | Tests that send extra fields (`role: admin`, `fareEstimate: 1`) and assert they're ignored; contract tests on every response |
| API4 | Unrestricted Resource Consumption | Request body ≤ 1 MB (nginx + Gin); server read/write/idle timeouts; pagination `limit` ≤ 50; search `q` ≤ 100 chars and ≥ 2; text ≤ 2 000; per-user rate limits (below); WebSocket: ≤ 5 connections per user, inbound messages ignored and capped at 1 KB, ping/pong timeout | Tests for limits; rate-limit tests with a fake clock |
| API5 | Broken Function Level Authorization | Route groups: public, authenticated, role-scoped (`consumer`, `rider`, `/admin` staff, admin-only). Guards are middleware on the group, not checks inside handlers. | Authz matrix test generated from a table of every route × every role |
| API6 | Unrestricted Access to Sensitive Business Flows | One active ride per consumer/rider; ride request rate limit; offers only to fresh-location online riders; ticket creation rate limit; signup rate limit per IP | Tests per rule |
| API7 | Server-Side Request Forgery | The backend never fetches a URL supplied by a client. Geocoding runs on the device. Any future outbound call goes through an allow-listed client. | Code review; `gosec` |
| API8 | Security Misconfiguration | Gin release mode in prod; no stack traces in responses (`INTERNAL_ERROR` only); API headers below; CORS **off** (back office is same-origin); TLS only via nginx; containers read-only, non-root, `cap_drop: ALL` | Header tests; Trivy config scan; ZAP baseline (task 028) |
| API9 | Improper Inventory Management | `openapi.yaml` is the complete inventory; a test fails if the router has a route that isn't in the spec (or vice versa); one environment, one version | Route-vs-spec test (task 001) |
| API10 | Unsafe Consumption of APIs | We consume no third-party APIs server-side. Mobile treats geocoder output as untrusted display text (length-limited, never executed). | Review |

## OWASP Top 10 (2025) → our controls

| # | Category | Control |
|---|----------|---------|
| A01 | Broken Access Control | API1/API3/API5 above; staff actions behind `requireStaff`/`requireAdmin`; back office hides UI the role can't use, **but the server enforces it** |
| A02 | Security Misconfiguration | API8; hardened compose; nginx config reviewed; secrets never in images |
| A03 | Software Supply Chain Failures | Lockfiles committed (`go.sum`, `pnpm-lock.yaml`), `--frozen-lockfile`; GitHub Actions pinned to commit SHAs; base images pinned by digest; Dependabot for Go, npm, Docker, Actions; `govulncheck`, `osv-scanner`, Trivy in CI; SBOM + provenance on image builds |
| A04 | Cryptographic Failures | TLS 1.2+ only (nginx), HSTS; bcrypt for passwords; `crypto/rand` for anything random; backups encrypted with `age`; no custom crypto; secrets ≥ 32 bytes |
| A05 | Injection | GORM with `?` placeholders only; no string-built SQL (`gosec` G201/G202); no shell exec with user input; React escapes output; no `dangerouslySetInnerHTML`; tickets rendered as plain text |
| A06 | Insecure Design | Contract-first, threat model above, state machine with conditional updates, one-active-ride rules, reasons + audit for staff powers |
| A07 | Authentication Failures | API2; no default accounts (first admin via CLI with stdin password); staff passwords ≥ 12 chars; 2FA in backlog |
| A08 | Software or Data Integrity Failures | Images only built in CI and deployed by SHA; migrations reviewed SQL; audit log append-only (DB trigger); deploy requires green CI |
| A09 | Logging & Alerting Failures | Structured `slog` logs with request ID, user ID, route, status; auth failures, rate-limit hits, `403`s, and all staff actions are logged; **never** log passwords, tokens, full phone numbers, or exact locations; backup `last-success` check |
| A10 | Mishandling of Exceptional Conditions | Panic recovery returns the `500` envelope; errors are wrapped, not swallowed; DB transactions roll back on any error (including audit write failure); fail closed (auth/DB errors deny access) |

## Backend rules (Go / Gin / GORM)

- **Authorization in the query.** Load owned resources with the owner in the `WHERE` clause. Return `404` for "exists but not yours".
- **No GORM models in responses.** Map to generated API types.
- **Explicit writes.** `Create`/`Updates` with selected fields only; never bind a request straight into a model.
- **Validate at the edge.** OpenAPI request validator on every route (except `/ws`, which validates its handshake). Extra business rules in the handler.
- **Errors.** Return the envelope with a code and a safe message. Log the detail server-side with the request ID.
- **Rate limits** (in-memory token buckets keyed by user ID or IP; `429 RATE_LIMITED`):

| Endpoint | Limit |
|----------|-------|
| `POST /auth/login` | 10 failures / 15 min per email; 20 / min per IP (nginx adds 5 / min per IP on `admin.<domain>`) |
| `POST /auth/signup` | 5 / hour per IP |
| `PUT /riders/me/location` | 2 / s per rider |
| `POST /rides`, `POST /rides/estimate` | 10 / min per user |
| `POST /tickets`, ticket messages | 10 / hour per user |
| `/admin/*` | 120 / min per staff user |
| Everything else authenticated | 300 / min per user |

- **HTTP server**: `ReadHeaderTimeout 5s`, `ReadTimeout 15s`, `WriteTimeout 15s`, `IdleTimeout 60s`; `MaxBytesReader` 1 MB.
- **API response headers**: `X-Content-Type-Options: nosniff`, `Cache-Control: no-store` on authenticated responses, `Content-Type: application/json; charset=utf-8`. No `Server` version header.
- **Secrets** come only from env; the app refuses to start in `production` if `JWT_SECRET` is shorter than 32 bytes.
- **Static analysis**: `golangci-lint` with `gosec`, `errcheck`, `bodyclose`, `sqlclosecheck`; `govulncheck ./...`.

## Back office rules (React web)

- Strict CSP (see `docs/INFRA.md`), `frame-ancestors 'none'`, HSTS, `Referrer-Policy: no-referrer`, `X-Content-Type-Options: nosniff`.
- No `dangerouslySetInnerHTML`, `eval`, or inline scripts (ESLint `react/no-danger`, `no-eval`).
- Token in memory + `sessionStorage` only; cleared on logout, `401`, `ACCOUNT_SUSPENDED`. No token in URLs or logs.
- The UI hides actions a role can't take, but every check is also on the server.
- Destructive actions (suspend, force-cancel, disable staff) need a confirm dialog with a reason.
- Show personal data only where the task needs it; mask phone numbers in lists (`+62 812-****-7890`), full value on the profile page.

## Mobile rules (OWASP MASVS L1)

| MASVS | Rule |
|-------|------|
| STORAGE | Token only in `expo-secure-store` (Keychain / Keystore). No personal data in AsyncStorage, logs, or crash reports. Clear on logout. |
| CRYPTO | No custom crypto; rely on platform TLS and secure store. |
| AUTH | Server is the authority; app role checks are UX only. Logout on `401`/`ACCOUNT_SUSPENDED`/socket `4003`. |
| NETWORK | HTTPS/WSS only in release builds (Android `usesCleartextTraffic=false` outside dev; iOS ATS on). Certificate pinning is in the backlog. |
| PLATFORM | Ask for location only when needed (foreground only), explain why in the permission text. No unneeded permissions. Deep links (if any) don't carry tokens. |
| CODE | No secrets in the bundle. The Google Maps key is restricted to our package names and SHA-1 certs in the Google console. `__DEV__`-only code (simulate rider) is stripped from release builds. Dependencies scanned in CI. |
| PRIVACY | Show the counterpart's phone and live position only during an active ride. History shows names, not phone numbers. |

## Data protection & privacy

- **Minimum data**: we store the rider's **last** location only, not a track. Rides keep pickup/dropoff for history.
- **Who sees what**:

| Data | Consumer | Rider | Support | Admin |
|------|----------|-------|---------|-------|
| Own profile | ✓ | ✓ | — | — |
| Counterpart name | during + after ride | during + after ride | ✓ | ✓ |
| Counterpart phone | active ride only | active ride only | ✓ | ✓ |
| Rider live location | own active ride only | own | active rides | active rides |
| Tickets | own (no internal notes) | own (no internal notes) | all | all |
| Audit log | — | — | ✓ | ✓ |

- **Retention** (proposed): tickets and audit entries kept 2 years; backups 3 months (rotation in ADR 0011); suspended accounts kept until deletion is requested (account deletion flow is in the backlog).
- **Logs** keep IDs, not personal data: phone numbers masked, coordinates rounded to 2 decimals (~1 km) if logged at all. Docker log rotation keeps about 30 MB per service.

## Infrastructure & pipeline

- **VPS**: SSH key-only, no root login, `fail2ban`, `unattended-upgrades`, `ufw` allowing 22/80/443 only; our services bind to `127.0.0.1`.
- **Deploy key**: the `deploy` user isn't in `sudo`. Its `authorized_keys` entry for GitHub Actions uses a **forced command** (`command="/opt/ride/deploy.sh",no-port-forwarding,no-agent-forwarding,no-pty`), so the key can only run the deploy script with an image tag.
- **Database**: `ride` role with least privilege on its own database; loopback only; no extensions or server-level settings.
- **Containers**: distroless/unprivileged images, read-only root FS, `no-new-privileges`, `cap_drop: ALL`, memory limits, base images pinned by digest.
- **Secrets**: `/opt/ride/.env` `chmod 600`; GitHub secrets scoped to the `production` environment; `GITHUB_TOKEN` with minimal `permissions:` per job; no secrets in images (`docker history` checked in task 019).
- **CI security jobs** (task 018): `gitleaks` (secrets in commits), `golangci-lint` + `gosec`, `govulncheck`, `osv-scanner` on `pnpm-lock.yaml` and `go.sum`, Trivy (image vulnerabilities + misconfig, fail on HIGH/CRITICAL with a fix available), Dependabot for all ecosystems, CodeQL for Go and TypeScript on `main`. A HIGH/CRITICAL finding blocks the merge unless an exception is written in `docs/security-exceptions.md` with an expiry date.
- **DAST**: OWASP ZAP baseline scan against the deployed API and back office before launch and after big changes (task 028).

## Security testing required in every task

Each task that adds or changes an endpoint must include:

1. **Authz matrix tests**: for every endpoint touched: no token → `401`; wrong role → `403`; another user's resource → `404`; suspended account → `403 ACCOUNT_SUSPENDED`; correct owner/role → success.
2. **Input abuse tests**: oversized and malformed bodies, extra fields (mass assignment), boundary values (limits, lengths, coordinates).
3. **No sensitive data in responses**: assert `password_hash`, internal notes, and other users' phone numbers aren't in the raw JSON.
4. **Audit**: staff writes produce exactly one audit entry; failures produce none.

These count toward the 100% coverage rule (ADR 0013).

## Security review checklist (reviewer agent)

- [ ] Every new query on an owned resource is scoped by the caller (API1)
- [ ] Every new route is in a guarded group with the right roles, and listed in the authz matrix test (API5)
- [ ] Requests bind generated types; writes use explicit fields; responses use DTOs (API3)
- [ ] Limits: body size, pagination, string lengths, rate limit for new write endpoints (API4, API6)
- [ ] No string-built SQL, `exec` with input, `dangerouslySetInnerHTML`, or `eval` (A05)
- [ ] No secrets, tokens, passwords, full phone numbers, or exact locations in logs, errors, or the repo (A09, A04)
- [ ] Errors return the envelope without internals; failures roll back (A10)
- [ ] New dependencies are needed, maintained, and pass `govulncheck`/`osv-scanner` (A03)
- [ ] Staff actions require a reason where the PRD says so and write audit entries
- [ ] Mobile: nothing sensitive outside secure store; release builds HTTPS-only (MASVS)

## Incident response (short)

1. **Contain**: disable the affected staff/user account in the back office, or rotate `JWT_SECRET` (logs everyone out) by editing `/opt/ride/.env` and running `docker compose up -d api`.
2. **Assess**: audit log, nginx logs, `docker compose logs api`, recent deploys.
3. **Fix**: `hotfix(…)` commit → CI → deploy; roll back with `deploy.yml` `tag` if faster.
4. **Notify**: if personal data was exposed, tell affected users and record what happened, when, and what was done (UU PDP expects notification within 3 × 24 hours).
5. **Learn**: write a short ADR or task for the root cause.
