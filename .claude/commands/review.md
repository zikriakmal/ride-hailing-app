---
description: Review current changes against the task, contract, and project rules
argument-hint: "[task file path, optional]"
---

Use the `reviewer` agent to review the current work.

- Task file: `$ARGUMENTS` if given, otherwise the task in `docs/tasks/` with `Status: in-progress`.
- Diff: uncommitted changes (`git diff`, `git diff --staged`).

Relay the reviewer's verdict and blocking findings. Don't apply fixes unless I ask.
