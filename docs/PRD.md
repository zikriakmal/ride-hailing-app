# PRD: Ride-Hailing App

> What we're building and why. Keep it short. If it isn't here, it isn't in scope.

## Problem

Consumers in Indonesia struggle to get a ride quickly because street hailing and phone-call dispatch give no visibility into whether a rider is coming or when. Riders waste time cruising empty looking for passengers. Both sides lack a simple way to find each other, agree on a price up front, and track the trip.

## Goal

A consumer can request a ride from their phone, see a fare estimate, get matched with a nearby online rider, watch that rider approach on a map, and complete the trip. The rider can go online, accept the request, and complete the trip from their own phone. We prove it by running a full ride end to end on two real devices.

## Users

- **Consumer**: requests and pays for rides.
- **Rider**: goes online, accepts rides, completes trips. Rides a motorbike.
- **Support agent** (staff): helps consumers and riders. Answers support tickets, looks up users and rides, cancels stuck rides.
- **Admin** (staff): everything support can do, plus suspending accounts, editing profiles, and managing staff accounts.

Naming follows Gojek/Grab: **rider** is the motorbike driver, **consumer** is the passenger. Each has its own app: the **Consumer app** and the **Rider app**. Staff use the **Back office** web app.

One account has exactly one role. A person who wants to be both needs two accounts.

## Core user flows (in scope)

1. **Sign up / log in** (consumer and rider)
   - Sign up with name, email, phone, password, role. Riders also give vehicle plate and model.
   - Log in with email + password. The app remembers the session until logout or token expiry.
2. **Consumer requests a ride** (pickup, destination, fare estimate)
   - Pickup defaults to the consumer's current GPS position; the consumer can move the pin.
   - Destination is chosen by searching an address or dropping a pin.
   - The app shows distance and fare estimate before the consumer confirms.
3. **Rider goes online and receives a ride request**
   - Rider toggles online/offline. While online, the app sends their location every 3 s.
   - Online riders within 3 km of the pickup see the request (pickup, destination, fare) for up to 60 s.
4. **Rider accepts → consumer sees rider location live**
   - First rider to accept gets the ride; other riders see the request disappear.
   - Consumer sees rider name, plate, vehicle model, and the rider's position moving on a map.
5. **Trip starts → trip completes**
   - Rider taps "Arrived" at pickup, "Start trip" when the consumer is on board, "Complete — cash received" at the destination.
   - Both apps update within seconds of each step.
6. **Trip history**
   - Consumer and rider each see a list of their past rides (completed and cancelled), newest first, with date, pickup, destination, fare, and the other party's name.
7. **Report a problem** (consumer and rider apps)
   - From a past or current ride (or from Help, without a ride), the user picks a category, writes what happened, and sends it.
   - They see their tickets, staff replies, and status, and can reply while the ticket is open; replying to a resolved ticket reopens it.

### Back office (staff, web)

8. **Staff log in** at `admin.<domain>` with email + password. There's no public signup; an admin creates staff accounts.
9. **User and rider management**
   - Search consumers and riders by name, email, phone, or plate; filter by role and status.
   - Open a profile: details, vehicle (riders), rider status, ride history, tickets, and audit history.
   - Admin: edit name/phone/vehicle, **suspend** or **unsuspend** with a required reason.
10. **Ride assistance**
    - See all active rides on a list and a map (rider positions), refreshed every 5 s.
    - Open any ride: full timeline (each status change, who did it, staff actions, linked tickets).
    - **Force-cancel** a stuck active ride with a required reason; both apps are told immediately.
11. **Support tickets**
    - A queue of tickets filtered by status, category, priority, and assignee; safety tickets are marked urgent and sorted first.
    - Assign to self or another agent, reply to the user, add internal notes the user can't see, and resolve.
12. **Audit log**
    - Every staff action is recorded: who, when, what, which user/ride/ticket, the reason, and before/after values.
    - Searchable by staff member, target, and action. Entries can't be edited or deleted.

## Rules (proposed)

These were the open questions. Each has a proposed answer; confirm or change before building the related task.

| Topic | Proposed rule | Affects task |
|-------|---------------|--------------|
| Apps | Two apps on one backend: Consumer app and Rider app. Each app only accepts its own role; logging in with the other role shows "Please use the Consumer/Rider app" and keeps the user logged out. | 002, 003 |
| Location | Real GPS on device, plus a dev-only "simulate rider" mode that moves a rider along a straight line for solo testing. | 007, 015 |
| Vehicle | Motorbike only. Other types are in `docs/BACKLOG.md`. | 004 |
| Payment | Mocked cash. Rider taps "Complete — cash received". Final fare = estimated fare. | 012 |
| Matching | Broadcast to every `online` rider within 3 km (straight line) of pickup. First accept wins; later accepts get `409`. | 009, 010 |
| Fare formula | `max(10 000, 5 000 + 2 500 × km)` IDR, rounded **up** to the nearest Rp 500. No surge. | 006 |
| Distance | Straight-line (haversine) distance × 1.3 road factor. No routing API. See ADR 0005. | 006 |
| No rider accepts | Request expires after 60 s (`expired`). Consumer can request again. | 009 |
| Cancelling | Consumer: any time before the trip starts. Rider: only before tapping "Arrived". | 013 |
| One at a time | A consumer has at most one active ride. A rider has at most one active ride and receives no offers while on one. | 009, 010 |
| Session | Access token valid 7 days for consumers and riders, **12 hours for staff**. No refresh tokens (backlog). Expired token → back to login. | 003, 005, 020 |
| Staff permissions | `support`: view users/rides/tickets/audit, handle tickets, force-cancel rides. `admin`: all of support plus edit profiles, suspend/unsuspend, manage staff. First admin is created with a server CLI command. | 020, 022 |
| Suspension | A suspended account can't log in (`403 ACCOUNT_SUSPENDED`), its current token stops working at once, and its WebSocket is closed. A user with an active ride can't be suspended until the ride is force-cancelled. A suspended rider is set offline. Staff accounts are "disabled" the same way. | 023 |
| Force-cancel | Staff can cancel any active ride (`requested`, `accepted`, `arrived`, `in_progress`), recorded as `cancelledBy: support` with a reason. Not allowed on finished rides. | 024 |
| Tickets | Categories: `lost_item`, `fare`, `safety`, `rider_behavior`, `consumer_behavior`, `app_problem`, `account`, `other`. `safety` → priority `urgent`, else `normal` (staff can change). Status `open` → `in_progress` (assigned) → `resolved`; a user reply to `resolved` reopens it. Text only, max 2 000 chars per message. | 025, 026 |
| Audit | Every staff write writes an audit entry in the same transaction, or nothing happens. Reads aren't audited. Reason is required for suspend, unsuspend, profile edits, staff changes, and force-cancel. | 021 |

## Non-goals (explicitly out of scope)

<!-- These matter as much as the goals. Agents must not build these. -->
- Real payment processing (mock it)
- Surge / dynamic pricing
- Ride pooling / shared rides
- Ratings & reviews
- Multi-city / multi-currency / i18n (UI is English, currency is IDR)
- Production-grade scaling, HA, or compliance (one VM is enough; see `docs/INFRA.md`)
- Push notifications (the app must be open to receive offers)
- Rider verification / document upload
- Turn-by-turn navigation or route drawing

## Success criteria

- [ ] A full ride (request → match → accept → start → complete) works end to end on two real devices
- [ ] Consumer sees a fare estimate within 2 s of entering pickup and destination
- [ ] An online rider within 3 km receives the request within 5 s
- [ ] Rider's location updates on the consumer's map at least every 3 s
- [ ] Both consumer and rider can see the completed trip in their history

- [ ] A support agent can find a user, see a ride's timeline, force-cancel a stuck ride, and answer a ticket from the back office; each action appears in the audit log

Task 016 is the checklist run that ticks the ride criteria; task 027 ticks the back-office one.

## Assumptions & risks

- **Hosting.** The backend runs on our existing VPS behind its nginx (HTTPS), deployed automatically from `main` (see `docs/INFRA.md`). It's a single instance with the database on the same VPS: no high availability, a few seconds of downtime per deploy. Local development still runs on a laptop.
- **GPS indoors is poor.** Use the simulate-rider mode for solo testing; do the final run outdoors.
- **Straight-line distance underestimates fares** in dense areas. Acceptable for a demo; route-based distance is in the backlog.
- **Staff accounts are powerful.** A leaked staff password exposes every user's phone number and ride history. Mitigations: 12 h tokens, rate-limited login, audit log, optional IP allow-list on `admin.<domain>`; 2FA is in the backlog.
- **App must stay in the foreground** for riders to receive offers and send location (no background location, no push).
