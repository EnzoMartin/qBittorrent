"""Shared helpers for the nox-build post-condition tests.

Two asymmetric readers, and the asymmetry is deliberate.

`head_text` reads the WORKING TREE. `tag_text` reads a committed blob via
`git show <tag>:<path>`. A test that read both sides with `git show` could not
see a working-tree mutation, so anyone recording a DEFECT PROOF would be
recording it for a gate that never fired -- the mutation would be invisible and
the test would pass while the surface was present. The upstream side has no such
hazard: it names an immutable tag, so reading it from git is correct and reading
it from the filesystem would be impossible.
"""

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def upstream_tag():
    """The upstream tag this branch was cut from.

    Read from UPSTREAM_TAG or fail. There is deliberately no derivation from the
    current branch or ref: on a tag push `git rev-parse --abbrev-ref HEAD` does
    not yield the branch name, and a branch without a '/' would make a split
    raise IndexError. A fallback that nobody calls, and that is wrong when it is
    called, is worse than no fallback. Both live callers set the variable
    explicitly.
    """
    tag = os.environ.get("UPSTREAM_TAG")
    if not tag:
        raise RuntimeError(
            "UPSTREAM_TAG is not set. These tests compare this tree against the "
            "upstream tag it was branched from, and guessing that tag is how a "
            "post-condition test starts passing vacuously. Set it explicitly, "
            "e.g. UPSTREAM_TAG=release-5.2.3."
        )
    return tag


def head_text(relative_path):
    """Read a file from the WORKING TREE, so a mutation to it is visible."""
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8", errors="replace")


def tag_text(relative_path):
    """Read a file as it exists at the upstream tag."""
    return subprocess.run(
        ["git", "show", f"{upstream_tag()}:{relative_path}"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        errors="replace",
    ).stdout


def git_lines(*args):
    """Run a git command in the repository and return its non-empty output lines."""
    out = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        errors="replace",
    ).stdout
    return [line for line in out.splitlines() if line.strip()]
