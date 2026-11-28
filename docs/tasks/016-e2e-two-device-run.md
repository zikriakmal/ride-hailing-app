# 016: End-to-end run on two devices

- **Status:** todo   <!-- todo | in-progress | blocked | done -->
- **Depends on:** 013, 014, 015, 019
- **PRD flow:** all; PRD success criteria

## Goal

Prove the PRD success criteria on two real phones and record the result.

## Scope

**In:**
- Use the deployed backend (`https://api.<domain>`); both apps built with that URL; phones on mobile data (not the same Wi-Fi)
- Walk through the checklist below; record timings and any bugs
- Write results in this file's Notes; file each bug as a new task (`new-task` skill)
- Tick the PRD success criteria that passed

**Out (don't build here):**
- Fixing bugs inside this task (each gets its own task)

## API

- none

## Acceptance criteria

- [ ] Install the Consumer app on phone A and the Rider app on phone B; fresh signup on each
- [ ] Rider goes online; consumer sees fare estimate in ≤ 2 s
- [ ] Consumer requests; rider gets offer in ≤ 5 s (measured with a stopwatch or log timestamps)
- [ ] Rider accepts; consumer map updates rider position at least every 3 s (log timestamps)
- [ ] Arrive → start → complete; both apps show the summary
- [ ] Both histories show the trip
- [ ] Consumer cancel and expiry paths each tried once
- [ ] `docs/PRD.md` success criteria ticked; results recorded below

## Notes

