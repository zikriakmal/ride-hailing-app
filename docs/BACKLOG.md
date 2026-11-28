# Backlog

> Ideas parked for later. Adding something here is how we say "not now" without losing it.
> One line each. Promote to `docs/tasks/` only when it's in scope per `docs/PRD.md`.

## Parked

### Auth & accounts
- Refresh tokens / session renewal and server-side token revocation
- Social login (Google, Apple)
- Password reset flow
- Phone OTP verification
- Rider document upload and approval

### Rides
- Car and other vehicle types (start with motorbike only)
- Scheduled rides
- Re-offer a `requested` ride to riders who come online after it was created
- Consumer sees nearby online riders on the map before requesting
- Cancellation reasons and fees
- Saved places (home, work) and recent destinations

### Maps & pricing
- Route-based distance and ETA (Directions API / OSRM) instead of haversine × 1.3
- Draw the route line on the map
- Address autocomplete (Places API)
- Metered final fare from the actual driven path
- PostGIS for the nearby-rider query
- Surge pricing

### Money & trust
- Real payment integration
- Ratings & reviews
- In-app chat / masked calling between consumer and rider

### Back office
- 2FA for staff accounts
- Ticket attachments (photos) and canned replies
- Ticket SLAs, escalation, and email notifications
- Refunds / fare adjustments from the back office
- Reassign a ride to another rider
- CSV export of users/rides; account deletion / data export requests
- Audit log retention and archiving
- Live updates in the back office over WebSocket instead of polling
- Staff self-service password change / reset

### Security
- Certificate pinning in the mobile apps
- Breached-password check (k-anonymity HIBP range API) at signup and staff creation
- Account deletion and personal-data export (UU PDP data subject requests)
- External pentest / bug bounty
- WAF or fail2ban jails for API abuse patterns

### Platform
- Push notifications (offers while the app is backgrounded)
- Background location for riders
- Managed database (RDS) instead of Postgres on the VPS
- Off-site backup copy (bucket or second server) so backups survive losing the VPS
- Alert when `last-success` backup is older than 26 h
- Staging environment
- Monitoring and alerting (uptime check, disk/CPU alarms)
- Mobile builds in CI (EAS Build) and store submission
- Redis pub/sub behind the WebSocket hub for multiple backend instances
- AsyncAPI spec for realtime events (replacing `docs/api/realtime.md`)
- Generate zod schemas and RTK Query endpoints from `openapi.yaml` (orval / openapi-zod-client)
- Storybook for atomic components
