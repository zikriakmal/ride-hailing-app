# Harness evals

Checks that the AI harness (`CLAUDE.md`, `.claude/agents`, `.claude/skills`, `.claude/commands`, `docs/SECURITY.md`) makes the agent behave the way the rules say. Run them after changing any of those files, or after switching models.

## How it works

For each case in `cases/*.toml`, `run.py`:

1. Copies the current working tree (uncommitted edits included, no `.git`/`node_modules`) into a temp git repo with one baseline commit.
2. Runs the case's `setup` commands (part of the starting state).
3. Runs `claude -p "<prompt>"` headless in that copy, with project settings only, no MCP servers, a budget cap, and only the tools in `allowed_tools`.
4. Grades the result with deterministic checks and, optionally, an LLM judge rubric. A trial passes only if every check passes.
5. Repeats `trials` times (agents are non-deterministic). The case passes if the pass rate is at least `pass_threshold` (default 2 of 3).

Your real repo is never touched. Reports go to `evals/results/` (gitignored).

## Commands

```bash
python3 -m unittest discover -s evals        # unit tests for the runner (no API calls)
python3 evals/run.py --dry-run               # validate every case, show the plan
python3 evals/run.py                         # run all cases (costs API credits)
python3 evals/run.py --case terminology-rider --trials 1
python3 evals/run.py --model claude-sonnet-5-5 --judge-model claude-opus-5-5
python3 evals/run.py --case security-bola-review --keep   # keep sandboxes to inspect
```

Needs Python 3.11+ and the `claude` CLI logged in. Exit code is non-zero if any case fails.

## Cases

| Case | Rule under test |
|------|-----------------|
| `non-goal-surge-pricing` | Rule 4: a non-goal request (surge pricing) makes the agent stop and ask, with no edits |
| `scope-control-backlog` | Rules 1–2: an out-of-scope idea goes to one line in `BACKLOG.md`, nothing else |
| `contract-first-spec-before-code` | Rule 3 + `api-contract-change`: spec edited, lint passes, no code touched |
| `new-task-template` | `new-task` skill: next number, template, security + coverage criteria, roadmap updated, "rider" not "driver" |
| `security-bola-review` | Reviewer agent + `docs/SECURITY.md`: flags BOLA, SQL injection, non-envelope response |
| `conventional-commit` | Conventional Commits + co-author trailer |
| `terminology-rider` | Terms: rider = motorbike driver, Rider app |
| `done-means-verified` | Rules 7–9: refuses to mark a task done without evidence |

## Writing a case

```toml
id = "my-case"                    # unique, kebab-case
area = "which rule or file this guards"
prompt = "What the user says to the agent."
trials = 3                        # optional
pass_threshold = 0.67             # optional
max_budget_usd = 1.0              # optional, per trial
setup = ["shell commands run in the sandbox before the agent"]   # optional
allowed_tools = ["Read", "Edit"]  # optional, defaults in run.py

[[checks]]
type = "unchanged"                # see table below
paths = ["backend", "frontend"]

[judge]                           # optional LLM grading
rubric = "Bullet points that must all hold."
```

| Check `type` | Fields | Passes when |
|--------------|--------|-------------|
| `unchanged` / `changed` | `paths` (dirs, files, globs; `"."` = whole repo) | nothing / something under them changed vs. baseline (committed or not) |
| `file_exists` / `file_absent` | `glob` | a file matches / none does |
| `file_contains` / `file_not_contains` | `glob`, `pattern` (regex) | some file matches / no file matches |
| `new_files_contain` / `new_files_not_contain` | `glob`, `pattern` | every new file matches (and at least one exists) / no new file matches |
| `command` | `run`, `exit_code` (default 0) | the shell command exits with that code in the sandbox |
| `result_matches` / `result_not_matches` | `pattern` | the agent's final message matches / doesn't |
| `git_log_matches` | `pattern` | every commit the agent made matches (and it made at least one) |

Prefer deterministic checks. Use the judge only for things a regex can't see ("asked before acting"), and write the rubric so a strict grader can say pass or fail.

When a real agent session breaks a rule, turn it into a case: the prompt that caused it plus a check that would have caught it.
