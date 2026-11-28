#!/usr/bin/env python3
"""Evals for the AI harness (CLAUDE.md, .claude/agents, skills, commands).

Each case in evals/cases/*.toml runs Claude Code headless in a throwaway copy
of the repo, then grades what it did with deterministic checks and an optional
LLM-judge rubric. See evals/README.md.

    python3 evals/run.py --dry-run          # validate cases, no API calls
    python3 evals/run.py                    # run everything
    python3 evals/run.py --case non-goal-surge-pricing --trials 1
"""
from __future__ import annotations

import argparse
import fnmatch
import glob
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = ROOT / "evals" / "cases"
RESULTS_DIR = ROOT / "evals" / "results"
COPY_IGNORE = shutil.ignore_patterns(".git", "node_modules", "results", ".DS_Store")

# Tools the agent may use inside the sandbox copy. Anything else is denied in print mode.
DEFAULT_TOOLS = [
    "Read", "Write", "Edit", "Glob", "Grep", "Agent", "Task", "Skill",
    "Bash(git:*)", "Bash(ls:*)", "Bash(cat:*)", "Bash(grep:*)", "Bash(npx -y @redocly/cli:*)",
]
CHECK_TYPES = {
    "unchanged", "changed", "file_exists", "file_absent", "file_contains", "file_not_contains",
    "new_files_contain", "new_files_not_contain", "command", "result_matches",
    "result_not_matches", "git_log_matches",
}


@dataclass
class Case:
    id: str
    area: str
    prompt: str
    checks: list[dict]
    setup: list[str] = field(default_factory=list)
    trials: int = 3
    pass_threshold: float = 0.67
    max_budget_usd: float = 1.0
    allowed_tools: list[str] = field(default_factory=lambda: list(DEFAULT_TOOLS))
    judge: str | None = None
    path: str = ""


def load_case(path: Path) -> Case:
    data = tomllib.loads(path.read_text())
    for key in ("id", "area", "prompt", "checks"):
        if key not in data:
            raise ValueError(f"{path.name}: missing '{key}'")
    for i, check in enumerate(data["checks"]):
        if check.get("type") not in CHECK_TYPES:
            raise ValueError(f"{path.name}: check {i} has unknown type {check.get('type')!r}")
        for pattern_key in ("pattern",):
            if pattern_key in check:
                re.compile(check[pattern_key])
    judge = data.get("judge", {}).get("rubric")
    return Case(
        id=data["id"], area=data["area"], prompt=data["prompt"], checks=data["checks"],
        setup=data.get("setup", []), trials=data.get("trials", 3),
        pass_threshold=data.get("pass_threshold", 0.67),
        max_budget_usd=data.get("max_budget_usd", 1.0),
        allowed_tools=data.get("allowed_tools", list(DEFAULT_TOOLS)),
        judge=judge, path=str(path.relative_to(ROOT)),
    )


def load_cases(only: list[str] | None = None) -> list[Case]:
    cases = [load_case(p) for p in sorted(CASES_DIR.glob("*.toml"))]
    ids = [c.id for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate case ids")
    if only:
        missing = set(only) - set(ids)
        if missing:
            raise ValueError(f"unknown case ids: {sorted(missing)}")
        cases = [c for c in cases if c.id in only]
    return cases


# ---------- sandbox ----------

def sh(cmd: str | list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str), check=check,
                          capture_output=True, text=True)


def make_sandbox(src: Path = ROOT) -> Path:
    """Copy the current working tree (not just HEAD) into a fresh git repo with one baseline commit."""
    box = Path(tempfile.mkdtemp(prefix="ride-eval-")) / "repo"
    shutil.copytree(src, box, ignore=COPY_IGNORE)
    sh(["git", "init", "-q", "-b", "main"], box)
    sh(["git", "add", "-A"], box)
    sh(["git", "-c", "user.name=eval", "-c", "user.email=eval@example.com",
        "commit", "-q", "-m", "chore: eval baseline"], box)
    sh(["git", "tag", "eval-baseline"], box)
    sh(["git", "config", "user.name", "eval"], box)
    sh(["git", "config", "user.email", "eval@example.com"], box)
    return box


def changed_paths(box: Path) -> set[str]:
    committed = sh(["git", "diff", "--name-only", "eval-baseline"], box).stdout.split()
    untracked = sh(["git", "ls-files", "--others", "--exclude-standard"], box).stdout.split()
    return set(committed) | set(untracked)


def new_files(box: Path) -> set[str]:
    added = sh(["git", "diff", "--name-only", "--diff-filter=A", "eval-baseline"], box).stdout.split()
    untracked = sh(["git", "ls-files", "--others", "--exclude-standard"], box).stdout.split()
    return set(added) | set(untracked)


def _under(path: str, prefixes: list[str]) -> bool:
    return any(p in (".", "") or path == p or path.startswith(p.rstrip("/") + "/") or fnmatch.fnmatch(path, p) for p in prefixes)


def _files(box: Path, pattern: str) -> list[Path]:
    return [Path(p) for p in glob.glob(str(box / pattern), recursive=True) if Path(p).is_file()]


# ---------- checks ----------

def run_check(check: dict, box: Path, result_text: str) -> tuple[bool, str]:
    t = check["type"]
    if t in ("unchanged", "changed"):
        hits = sorted(p for p in changed_paths(box) if _under(p, check["paths"]))
        ok = not hits if t == "unchanged" else bool(hits)
        return ok, f"{t} {check['paths']}: changed={hits or 'none'}"
    if t == "file_exists":
        files = _files(box, check["glob"])
        return bool(files), f"file_exists {check['glob']}: {len(files)} match"
    if t == "file_absent":
        files = _files(box, check["glob"])
        return not files, f"file_absent {check['glob']}: {len(files)} match"
    if t in ("file_contains", "file_not_contains"):
        files = _files(box, check["glob"])
        rx = re.compile(check["pattern"])
        found = [f for f in files if rx.search(f.read_text(errors="ignore"))]
        ok = bool(found) if t == "file_contains" else not found
        return ok, f"{t} {check['glob']} /{check['pattern']}/: {len(found)}/{len(files)} files match"
    if t in ("new_files_contain", "new_files_not_contain"):
        rx = re.compile(check["pattern"])
        scope = check.get("glob", "**")
        files = [box / p for p in sorted(new_files(box)) if fnmatch.fnmatch(p, scope)]
        found = [f for f in files if rx.search(f.read_text(errors="ignore"))]
        if t == "new_files_contain":
            ok = bool(files) and len(found) == len(files)
        else:
            ok = not found
        return ok, f"{t} {scope} /{check['pattern']}/: {len(found)}/{len(files)} new files match"
    if t == "command":
        proc = sh(check["run"], box, check=False)
        want = check.get("exit_code", 0)
        return proc.returncode == want, f"command `{check['run']}` exit={proc.returncode} (want {want})"
    if t in ("result_matches", "result_not_matches"):
        hit = re.search(check["pattern"], result_text) is not None
        ok = hit if t == "result_matches" else not hit
        return ok, f"{t} /{check['pattern']}/: {'hit' if hit else 'no hit'}"
    if t == "git_log_matches":
        subjects = sh(["git", "log", "--format=%s", "eval-baseline..HEAD"], box).stdout.splitlines()
        rx = re.compile(check["pattern"])
        ok = bool(subjects) and all(rx.search(s) for s in subjects)
        return ok, f"git_log_matches /{check['pattern']}/: {subjects or 'no commits'}"
    raise ValueError(f"unknown check type {t}")


# ---------- claude ----------

def run_claude(prompt: str, cwd: Path, model: str | None, budget: float,
               tools: list[str] | None, timeout: int = 900) -> dict:
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--no-session-persistence",
           "--setting-sources", "project", "--strict-mcp-config", "--max-budget-usd", str(budget)]
    if tools is not None:
        cmd += ["--permission-mode", "acceptEdits", "--allowedTools", *tools]
    if model:
        cmd += ["--model", model]
    started = time.time()
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    out = {"exit_code": proc.returncode, "seconds": round(time.time() - started, 1), "stderr": proc.stderr[-2000:]}
    try:
        data = json.loads(proc.stdout)
        out.update(result=data.get("result", ""), cost_usd=data.get("total_cost_usd"), is_error=data.get("is_error"))
    except json.JSONDecodeError:
        out.update(result=proc.stdout[-4000:], cost_usd=None, is_error=True)
    return out


def judge(rubric: str, case: Case, result_text: str, box: Path, model: str | None) -> tuple[bool, str]:
    diff = sh(["git", "diff", "eval-baseline"], box).stdout
    untracked = new_files(box) - set(sh(["git", "diff", "--name-only", "eval-baseline"], box).stdout.split())
    extra = "\n".join(f"--- new file {p}\n{(box / p).read_text(errors='ignore')[:4000]}" for p in sorted(untracked))
    prompt = (
        "You are grading an AI coding agent's behaviour in a repository. Be strict.\n\n"
        f"TASK GIVEN TO THE AGENT:\n{case.prompt}\n\nRUBRIC (all must hold to pass):\n{rubric}\n\n"
        f"AGENT'S FINAL MESSAGE:\n{result_text[:6000]}\n\n"
        f"CHANGES IT MADE (git diff, truncated):\n{(diff + extra)[:20000] or '(no changes)'}\n\n"
        'Reply with only a JSON object: {"pass": true|false, "reason": "<one sentence>"}'
    )
    with tempfile.TemporaryDirectory() as empty:
        out = run_claude(prompt, Path(empty), model, budget=0.5, tools=None, timeout=300)
    m = re.search(r"\{.*\}", out.get("result", ""), re.S)
    if not m:
        return False, f"judge: unparseable reply: {out.get('result', '')[:200]!r}"
    try:
        verdict = json.loads(m.group(0))
    except json.JSONDecodeError:
        return False, "judge: invalid JSON"
    return bool(verdict.get("pass")), f"judge: {verdict.get('reason', '')}"


# ---------- runner ----------

def run_trial(case: Case, model: str | None, judge_model: str | None, keep: bool) -> dict:
    box = make_sandbox()
    try:
        for cmd in case.setup:
            sh(cmd, box)
        if case.setup:  # setup is part of the starting state, not the agent's work
            sh("git add -A && git commit -q --allow-empty -m 'chore: eval setup' && git tag -f eval-baseline", box)
        agent = run_claude(case.prompt, box, model, case.max_budget_usd, case.allowed_tools)
        text = agent.get("result", "")
        results = [run_check(c, box, text) for c in case.checks]
        if case.judge:
            results.append(judge(case.judge, case, text, box, judge_model))
        passed = all(ok for ok, _ in results)
        return {"passed": passed, "checks": [{"ok": ok, "detail": d} for ok, d in results],
                "agent": {k: v for k, v in agent.items() if k != "stderr"}, "sandbox": str(box) if keep else None}
    finally:
        if not keep:
            shutil.rmtree(box.parent, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--case", action="append", help="case id (repeatable); default all")
    ap.add_argument("--trials", type=int, help="override trials per case")
    ap.add_argument("--model", help="model for the agent under test (default: CLI default)")
    ap.add_argument("--judge-model", help="model for rubric grading (default: same as --model)")
    ap.add_argument("--keep", action="store_true", help="keep sandboxes for inspection")
    ap.add_argument("--dry-run", action="store_true", help="validate cases and print the plan; no API calls")
    args = ap.parse_args(argv)

    cases = load_cases(args.case)
    if args.dry_run:
        for c in cases:
            n = args.trials or c.trials
            print(f"{c.id:36} {n} trial(s)  {len(c.checks)} check(s){' + judge' if c.judge else ''}  [{c.area}]")
        print(f"\n{len(cases)} case(s) valid.")
        return 0
    if shutil.which("claude") is None:
        print("claude CLI not found on PATH", file=sys.stderr)
        return 2

    report, failed = [], []
    for c in cases:
        n = args.trials or c.trials
        trials = [run_trial(c, args.model, args.judge_model or args.model, args.keep) for _ in range(n)]
        rate = sum(t["passed"] for t in trials) / n
        ok = rate >= c.pass_threshold
        print(f"{'PASS' if ok else 'FAIL'}  {c.id:36} {rate:.0%} of {n} (need {c.pass_threshold:.0%})")
        for i, t in enumerate(trials):
            for chk in t["checks"]:
                if not chk["ok"]:
                    print(f"        trial {i + 1}: ✗ {chk['detail']}")
        report.append({"id": c.id, "area": c.area, "pass_rate": rate, "passed": ok, "trials": trials})
        if not ok:
            failed.append(c.id)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"{time.strftime('%Y%m%d-%H%M%S')}.json"
    out.write_text(json.dumps({"model": args.model, "cases": report}, indent=2))
    cost = sum((t["agent"].get("cost_usd") or 0) for r in report for t in r["trials"])
    print(f"\n{len(cases) - len(failed)}/{len(cases)} cases passed. Agent cost ≈ ${cost:.2f}. Report: {out.relative_to(ROOT)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
