# PRD: Ride-Hailing App

> What we're building and why. Keep it short. If it isn't here, it isn't in scope.

## Problem

Riders in Indonesia struggle to get a ride quickly because street hailing and phone-call dispatch give no visibility into whether a driver is coming or when. Drivers waste time cruising empty looking for passengers. Both sides lack a simple way to find each other, agree on a price up front, and track the trip.

## Goal

A rider can request a ride from their phone, see a fare estimate, get matched with a nearby online driver, watch that driver approach on a map, and complete the trip. The driver can go online, accept the request, and complete the trip from their own phone. We prove it by running a full ride end to end on two real devices.

## Users

- **Rider**: requests and pays for rides.
- **Driver**: goes online, accepts rides, completes trips.

## Core user flows (in scope)

1. Sign up / log in (rider and driver)
2. Rider requests a ride (pickup, destination, fare estimate)
3. Driver goes online and receives a ride request
4. Driver accepts → rider sees driver location live
5. Trip starts → trip completes
6. Trip history

## Non-goals (explicitly out of scope)

<!-- These matter as much as the goals. Agents must not build these. -->
- Real payment processing (mock it)
- Surge / dynamic pricing
- Ride pooling / shared rides
- Ratings & reviews
- Admin dashboard
- Multi-city / multi-currency / i18n
- Production-grade scaling, HA, or compliance

## Success criteria

- [ ] A full ride (request → match → accept → start → complete) works end to end on two real devices
- [ ] Rider sees a fare estimate within 2 s of entering pickup and destination
- [ ] An online driver within 3 km receives the request within 5 s
- [ ] Driver's location updates on the rider's map at least every 3 s
- [ ] Both rider and driver can see the completed trip in their history

## Open questions

Each has a proposed answer. Confirm or change before building the related tasks.

- **One app with a role switch, or two apps?** Proposed: one app; the user's role comes from login (`user.role`).
- **Real GPS or simulated driver movement?** Proposed: both. Real GPS on device, plus a dev-only "simulate driver" mode for solo testing.
- **Motorbike, car, or both?** Proposed: motorbike only for now. Other vehicle types are in `docs/BACKLOG.md`.
- **Payment?** Proposed: mocked cash. Fare is shown; driver taps "cash received" on completion.
- **How are drivers matched?** Proposed: broadcast to all online drivers within 3 km; first to accept wins.
- **Fare formula?** Proposed: base fare + per-km rate in IDR, rounded to a whole number. No surge.
- **What if no driver accepts?** Proposed: the request expires after 60 s; the rider can retry.
- **Who can cancel, and when?** Proposed: the rider any time before the trip starts; the driver before arriving at pickup.
