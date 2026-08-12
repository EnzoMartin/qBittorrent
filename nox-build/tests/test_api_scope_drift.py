"""The WebUI API scope set, asserted in two directions.

Two questions, two tests, and they mean different things:

  * The post-merge invariant -- what this build exposes -- must equal the
    reviewed set exactly. A scope that appears here without review is an
    unreviewed API surface in a published binary.
  * Upstream drift -- what the tag exposes -- must equal the reviewed set plus
    the scopes we deliberately removed. When upstream ADDS a scope, this is the
    test that stops the merge so the new controller can be read and classified
    before it ships.

Additions and removals are reported separately because they are different
events: an addition is unreviewed surface, a removal means upstream deleted
something we assumed was there.
"""

import re
import unittest
from pathlib import Path

from _support import REPO_ROOT, head_text, tag_text, upstream_tag

WEBAPP = "src/webui/webapplication.cpp"
SCOPES_FILE = REPO_ROOT / "nox-build" / "reviewed-api-scopes.txt"

# 'auth' is dispatched from m_authController directly rather than through
# registerAPIController(), so no shape-only scan can see it. It is declared here
# and added to both extracted sets.
UNDISCOVERABLE_SCOPES = {"auth"}

# Scopes present at the upstream tag that this build deliberately removes.
REMOVED_SCOPES = {"search"}

# A shape-only scan that matched nothing would compare an empty set against an
# empty set and report perfect agreement. Nine are registered at the tag; eight
# is a floor low enough not to encode the exact count twice.
MINIMUM_EXTRACTED = 8

_SCOPE = re.compile(r'registerAPIController\(u"([a-z]+)"_s')


def _extract(source):
    return set(_SCOPE.findall(source))


def _reviewed():
    lines = SCOPES_FILE.read_text(encoding="utf-8").splitlines()
    return {
        line.strip()
        for line in lines
        if line.strip() and not line.lstrip().startswith("#")
    }


class TestApiScopeDrift(unittest.TestCase):
    def test_head_scopes_match_the_reviewed_set(self):
        found = _extract(head_text(WEBAPP))
        self.assertGreaterEqual(
            len(found),
            MINIMUM_EXTRACTED,
            f"extracted only {len(found)} scopes from {WEBAPP} at HEAD; the "
            "pattern has stopped matching and this comparison would be vacuous",
        )
        shipped = found | UNDISCOVERABLE_SCOPES
        reviewed = _reviewed()
        self.assertEqual(
            shipped,
            reviewed,
            f"unreviewed scopes: {sorted(shipped - reviewed)}; "
            f"reviewed but missing: {sorted(reviewed - shipped)}",
        )

    def test_upstream_tag_scopes_match_reviewed_plus_removed(self):
        found = _extract(tag_text(WEBAPP))
        self.assertGreaterEqual(
            len(found),
            MINIMUM_EXTRACTED,
            f"extracted only {len(found)} scopes from {WEBAPP} at "
            f"{upstream_tag()}; the pattern has stopped matching",
        )
        at_tag = found | UNDISCOVERABLE_SCOPES
        expected = _reviewed() | REMOVED_SCOPES
        self.assertEqual(
            at_tag,
            expected,
            f"upstream added: {sorted(at_tag - expected)} -- review each "
            f"controller and decide whether it is an RCE surface before "
            f"merging; upstream removed: {sorted(expected - at_tag)}",
        )


if __name__ == "__main__":
    unittest.main()
