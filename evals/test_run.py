"""Unit tests for the eval runner's checks and case loading (no API calls).

    python3 -m unittest discover -s evals
"""
import shutil
import tempfile
import unittest
from pathlib import Path

import run


class SandboxChecks(unittest.TestCase):
    def setUp(self):
        self.src = Path(tempfile.mkdtemp())
        (self.src / "docs" / "tasks").mkdir(parents=True)
        (self.src / "docs" / "PRD.md").write_text("# PRD\n")
        (self.src / "docs" / "tasks" / "001-a.md").write_text("Status: todo\n")
        (self.src / ".git").mkdir()  # must be ignored by the copy
        self.box = run.make_sandbox(self.src)

    def tearDown(self):
        shutil.rmtree(self.src, ignore_errors=True)
        shutil.rmtree(self.box.parent, ignore_errors=True)

    def check(self, **c):
        return run.run_check(c, self.box, "final message mentions a Non-Goal")[0]

    def test_unchanged_and_changed(self):
        self.assertTrue(self.check(type="unchanged", paths=["docs/PRD.md"]))
        self.assertFalse(self.check(type="changed", paths=["docs"]))
        (self.box / "docs" / "PRD.md").write_text("# PRD\nedited\n")
        self.assertFalse(self.check(type="unchanged", paths=["docs/PRD.md"]))
        self.assertTrue(self.check(type="changed", paths=["docs"]))

    def test_dot_means_whole_repo(self):
        self.assertTrue(self.check(type="unchanged", paths=["."]))
        (self.box / "new.md").write_text("x")
        self.assertFalse(self.check(type="unchanged", paths=["."]))

    def test_committed_changes_count_as_changed(self):
        (self.box / "docs" / "PRD.md").write_text("changed\n")
        run.sh("git add -A && git commit -qm 'docs: x'", self.box)
        self.assertTrue(self.check(type="changed", paths=["docs/PRD.md"]))

    def test_untracked_file_counts_as_changed_and_new(self):
        (self.box / "docs" / "tasks" / "002-b.md").write_text("Rider app\n")
        self.assertTrue(self.check(type="changed", paths=["docs/tasks"]))
        self.assertTrue(self.check(type="new_files_contain", glob="docs/tasks/*.md", pattern="Rider"))
        self.assertTrue(self.check(type="new_files_not_contain", glob="docs/tasks/*.md", pattern="(?i)driver"))
        self.assertFalse(self.check(type="new_files_not_contain", glob="docs/tasks/*.md", pattern="Rider"))

    def test_new_files_contain_requires_some_new_file(self):
        self.assertFalse(self.check(type="new_files_contain", glob="docs/tasks/*.md", pattern="."))

    def test_file_exists_absent_contains(self):
        self.assertTrue(self.check(type="file_exists", glob="docs/tasks/001-*.md"))
        self.assertTrue(self.check(type="file_absent", glob="docs/tasks/999-*.md"))
        self.assertTrue(self.check(type="file_contains", glob="docs/tasks/*.md", pattern="todo"))
        self.assertTrue(self.check(type="file_not_contains", glob="docs/**/*.md", pattern="secret123"))
        self.assertFalse(self.check(type="file_contains", glob="docs/tasks/*.md", pattern="done"))

    def test_command_and_result(self):
        self.assertTrue(self.check(type="command", run="test -f docs/PRD.md"))
        self.assertTrue(self.check(type="command", run="false", exit_code=1))
        self.assertTrue(self.check(type="result_matches", pattern="(?i)non-goal"))
        self.assertTrue(self.check(type="result_not_matches", pattern="surge"))

    def test_git_log_matches_all_new_commits(self):
        self.assertFalse(self.check(type="git_log_matches", pattern="^docs: "))  # no commits yet
        (self.box / "x.md").write_text("x")
        run.sh("git add -A && git commit -qm 'docs: add x'", self.box)
        self.assertTrue(self.check(type="git_log_matches", pattern="^docs: "))
        (self.box / "y.md").write_text("y")
        run.sh("git add -A && git commit -qm 'Add y'", self.box)
        self.assertFalse(self.check(type="git_log_matches", pattern="^docs: "))

    def test_git_dir_not_copied(self):
        self.assertEqual(run.sh(["git", "rev-list", "--count", "HEAD"], self.box).stdout.strip(), "1")


class CaseLoading(unittest.TestCase):
    def test_all_repo_cases_are_valid(self):
        cases = run.load_cases()
        self.assertGreater(len(cases), 0)
        for c in cases:
            self.assertTrue(c.checks or c.judge, c.id)
            self.assertGreater(c.trials, 0)

    def test_bad_case_rejected(self):
        with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as f:
            f.write('id="x"\narea="a"\nprompt="p"\n[[checks]]\ntype="nope"\n')
        with self.assertRaises(ValueError):
            run.load_case(Path(f.name))

    def test_unknown_case_id_rejected(self):
        with self.assertRaises(ValueError):
            run.load_cases(["does-not-exist"])


if __name__ == "__main__":
    unittest.main()
