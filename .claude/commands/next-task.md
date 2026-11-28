---
description: Pick up the next todo task and implement it
argument-hint: "[task number, optional]"
---

Pick up a task and work it to done.

1. Read `CLAUDE.md`, `docs/PRD.md`, and `docs/ARCHITECTURE.md`.
2. Choose the task:
   - If an argument was given (`$ARGUMENTS`), use `docs/tasks/$ARGUMENTS-*.md`.
   - Otherwise, the lowest-numbered file in `docs/tasks/` with `Status: todo` whose `Depends on` tasks are all `done`.
3. Set its `Status:` to `in-progress`. Summarize the goal and acceptance criteria back in 3–5 lines, and list anything unclear. If something blocks you, ask before writing code.
4. If the task touches the API, follow the `api-contract-change` skill (spec first). If you make a decision worth recording, use the `new-adr` skill.
5. Implement the smallest change that meets the acceptance criteria. Anything extra goes to `docs/BACKLOG.md`.
6. Write unit tests for everything you added or changed, alongside the code (use the `tester` agent if helpful). Run the coverage command for every touched codebase; it must report 100% (ADR 0013). Tick criteria in the task file as they're verified.
7. Run the `reviewer` agent on the task. Fix blocking findings.
8. Set `Status: done`, add notes to the task file (including the coverage summary), and report what changed with the test and coverage output.
