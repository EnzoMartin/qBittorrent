"""Post-conditions for the two delete-only source modifications.

Every method asserts BOTH halves: the pattern is present at the upstream tag,
and absent (or, for the two retained bounds, still present) at HEAD. The
upstream half is what stops these tests passing vacuously -- if upstream renames
or moves the code we removed, the tag-side assertion fails and the merge is
reported as a rename rather than as a clean removal. A test that only asserted
absence at HEAD would go green on a tree where the surface had simply moved.

Two methods assert that something SURVIVED. They are not redundant. Each marks a
bound on a security claim, and a future maintainer "completing" the deletion
would break a documented contract:

  * SearchPluginManager stays linked into qbt_base, so the claim is "the search
    API is not reachable", not "the plugin-execution code is absent".
  * The autorun preferences() getters stay, so the claim is that the values
    cannot be WRITTEN through the API, not that the feature is invisible.

DEFECT PROOF (mutation applied and observed 2026-08-12): re-added the line
"    api/searchcontroller.cpp" to src/webui/CMakeLists.txt in the working tree.
test_search_cmake_entries_removed failed on the assertNotIn, naming
api/searchcontroller.cpp as still present at HEAD. Reverting the line returned
that test to green. The mutation was made in the working tree and was seen,
which is the property head_text exists for: reading `git show HEAD:` instead
would have left it invisible -- see _support.py.
"""

import unittest

from _support import head_text, tag_text

CMAKE = "src/webui/CMakeLists.txt"
WEBAPP = "src/webui/webapplication.cpp"
APPCTL = "src/webui/api/appcontroller.cpp"
APPLICATION = "src/app/application.cpp"


class TestSearchSurfaceRemoved(unittest.TestCase):
    def test_search_cmake_entries_removed(self):
        tag = tag_text(CMAKE)
        self.assertIn("api/searchcontroller.h", tag)
        self.assertIn("api/searchcontroller.cpp", tag)

        head = head_text(CMAKE)
        self.assertNotIn("api/searchcontroller.h", head)
        self.assertNotIn("api/searchcontroller.cpp", head)

    def test_search_registration_removed(self):
        # Case-insensitive so this also catches the #include, whose path is
        # lowercase while the symbol is not.
        self.assertIn("searchcontroller", tag_text(WEBAPP).lower())
        self.assertNotIn("searchcontroller", head_text(WEBAPP).lower())


class TestAutorunSurfaceRemoved(unittest.TestCase):
    def test_autorun_setters_removed(self):
        self.assertIn("setAutoRun", tag_text(APPCTL))
        self.assertNotIn("setAutoRun", head_text(APPCTL))

    def test_autorun_getters_retained(self):
        # The bound on the claim: reads still work, writes do not.
        self.assertIn("isAutoRunOnTorrentAddedEnabled", tag_text(APPCTL))
        self.assertIn("isAutoRunOnTorrentAddedEnabled", head_text(APPCTL))


class TestClaimBounds(unittest.TestCase):
    def test_search_plugin_manager_still_linked(self):
        # src/base/ is untouched, so the plugin-execution code is still in the
        # binary. Asserting this keeps the security claim honest in both
        # directions: an over-broad future deletion here would break the link.
        self.assertIn("SearchPluginManager::freeInstance", tag_text(APPLICATION))
        self.assertIn("SearchPluginManager::freeInstance", head_text(APPLICATION))


if __name__ == "__main__":
    unittest.main()
