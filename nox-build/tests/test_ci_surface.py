"""The workflow set on this branch, asserted as an exact set.

Upstream's workflows are removed from this branch rather than disabled in
repository settings, which makes the deletion a property of the tree -- and a
property of the tree is something a test can hold. This fails on a
re-introduced upstream workflow, on a second workflow of ours added without
review, and on a merge that restored the directory.

The pathspec carries :(glob) because a bare '*' crosses '/' in git pathspecs and
would reach .github/workflows/helper/codeql/cpp.yaml. That file is a CodeQL
config, not a workflow, and is not registered as one -- so without :(glob) this
comparison fails on a correct tree, and the natural "fix" is deleting upstream's
helper configs.

This test needs no separate proof that its scan is not silently reading
nothing: it compares against an exact set, so an empty result FAILS the
comparison rather than satisfying it.
"""

import unittest

from _support import git_lines

EXPECTED_WORKFLOWS = {".github/workflows/publish-nox.yml"}


class TestCiSurface(unittest.TestCase):
    def test_workflow_set_is_exactly_ours(self):
        found = set(git_lines("ls-files", ":(glob).github/workflows/*"))
        self.assertEqual(
            found,
            EXPECTED_WORKFLOWS,
            f"unexpected workflows: {sorted(found - EXPECTED_WORKFLOWS)}; "
            f"missing: {sorted(EXPECTED_WORKFLOWS - found)}",
        )


if __name__ == "__main__":
    unittest.main()
