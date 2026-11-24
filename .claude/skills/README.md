# Skills

Each skill is a folder with a `SKILL.md`. The agent reads the `description` to decide when to load it, so write it as "Use when…".

```
.claude/skills/
  <skill-name>/
    SKILL.md          ← required: frontmatter + instructions
    template.md       ← optional supporting files the skill points to
    scripts/…         ← optional helper scripts
```

## Skills in this repo

| Skill | Use when |
|-------|----------|
| `api-contract-change` | Adding or changing an endpoint, request, or response |
| `new-task` | Turning a PRD flow or backlog item into a task file |
| `new-adr` | Recording a decision about stack, library, pattern, or trade-off |

## Boilerplate for a new skill

Copy this into `.claude/skills/<skill-name>/SKILL.md`:

```markdown
---
name: <skill-name>
description: Use when <trigger situation>. <What it produces, in one line.>
---

# <Skill title>

## When to use
- <situation>
- Not for: <adjacent situation that should use something else>

## Steps
1. <step>
2. <step>

## Rules
- <hard constraint>

## Done when
- [ ] <verifiable check>
```

Tips:
- Keep `SKILL.md` short. Move long templates or reference material into sibling files and link to them.
- Put trigger words people actually say into `description`.
- Add `disable-model-invocation: true` to the frontmatter if the skill should run only when invoked as `/<skill-name>`.
