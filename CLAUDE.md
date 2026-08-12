# CLAUDE.md

## Scope of reference (read this first)

**Every statement in this repository must be true of this repository alone, and
every reference in it must resolve for a reader who has only this repository and
its public upstreams.** Cite upstream qBittorrent, libtorrent, Qt, the base
distribution, or a public specification freely — they are dependencies of this
build and a reader can reach them. Explain every shape by the technical
constraint that produced it.

This holds in the source, in commit messages, in tag annotations, in release
notes and in workflow metadata. **Commit messages ship inside the Corresponding
Source archive**, so anything written in one is conveyed to every recipient and
cannot afterwards be withdrawn.

## What this repository is

A maintained fork of qBittorrent carrying **delete-only** source modifications,
publishing a hardened `qbittorrent-nox` as a container image and as Windows
Release assets, each accompanied by its Corresponding Source.

Two things are removed, both remote-code-execution surfaces reachable from the
WebUI API and neither disableable by a build flag:

- the search-plugin controller registration (`search/installPlugin` stores and
  later executes an arbitrary Python file);
- the autorun `setPreferences` handlers (an arbitrary program run on torrent
  add or completion).

`MODIFICATIONS.md` at the root is the GPLv3 §5(a) notice and states the bound on
each claim. `nox-build/` holds the build recipe, the notices and the tests.

**This build also guarantees that SSL peer support is compiled in**, which is why
the recipe asserts `TORRENT_SSL_PEERS` on both platforms and pins a libtorrent
floor. libtorrent degrades silently when built without OpenSSL:
`set_ssl_certificate_buffer` becomes a no-op, so the engine accepts a
certificate, reports success, and serves an ordinary torrent. A degraded build is
indistinguishable from a correct one at every interface it exposes, and a
published binary that cannot be checked for this is not worth publishing.

**Branch topology.** One branch per upstream version, cut fresh from that
version's tag and never rebased. The version branch is the repository's default
branch. `master` is never written to and stays byte-identical to upstream, as the
audit reference. Branches accumulate by design: the claim *upstream tag X plus
exactly these public commits* holds only while the tree that produced a shipped
binary stays reachable.

**Versioning.** `release-<upstream-tag>-mod.<n>`, restarting at 1 for each new
upstream tag. Not SemVer — this build asserts no compatibility contract of its
own, and the only identity worth encoding is which upstream release it derives
from and how many modifications have been applied.

## Merging a new upstream version

1. `git fetch upstream --tags`
2. `git switch -c hardened/<new-tag> <new-tag>` — **from the tag, never from the
   previous branch.**
3. `UPSTREAM_TAG=<new-tag> python3 -m unittest discover -s nox-build/tests` —
   expected to **FAIL**. This is the baseline proving the tests are not passing
   vacuously against the new tree.
4. `python3 -m unittest discover -s nox-build/tests -p "test_api_scope_drift.py"`
   — **an added scope stops the merge.** Read the new controller, decide whether
   it is an RCE surface, and update `nox-build/reviewed-api-scopes.txt` in its own
   commit with the review in the message.
5. `git rm ":(glob).github/workflows/*"` and replace `.github/dependabot.yml`,
   then restore ours. **Recompute this deletion; do not cherry-pick the old one.**
   A recomputed deletion covers a workflow upstream added since the last tag and
   cannot conflict, where a replayed one conflicts on every file upstream edited
   and silently misses every file upstream added.
6. `bash nox-build/upstream-delta.sh <old-tag> <new-tag>` — read the scoped delta.
7. `git cherry-pick <first>..<last>` for the source deletions and the build
   system. **Conflicts here are the signal**, not an obstacle: they mean upstream
   moved the code we remove. Resolve by reading the new source, never by forcing
   the old hunk.
8. Re-run the full discovery. Expected `OK`.
9. Update `MODIFICATIONS.md` — new tag, new date, new line ranges.
9a. **Review the SHA-pinned actions in `publish-nox.yml`.** Every `uses:` is
    pinned to a commit, which is the only immutable form — a tag can be moved by
    anyone who gains access to the action's repository, and this workflow runs
    with `contents: write` and `packages: write`. Measured 2026-08-12: Dependabot
    does not bump SHA-pinned actions, so nothing does this for you. Resolve each
    trailing version comment to the current release and re-pin deliberately.
10. **Re-point the repository's default branch to `hardened/<new-tag>`.** Until
    this runs, `workflow_dispatch` cannot reach the new branch's workflow,
    Dependabot watches the old branch's Dockerfile, and any schedule resolves
    against the old tree.
11. Tag `<new-tag>-mod.1` and push.

## Residual: `master` still carries upstream's workflows

Upstream's workflows are removed from this branch, not disabled in settings, so a
push here can fire only the workflow this branch carries. **`master` still holds
them.** Nothing pushes to `master` and no pull request targets it; if either ever
does, upstream's macOS, Windows, Ubuntu and Coverity matrices run on this public
repository. `nox-build/tests/test_ci_surface.py` asserts the version branch's
workflow set; nothing asserts `master`'s, because nothing is supposed to touch it.

**A pull request targeting `master` is never approved.** Outside contributors
require approval before any workflow runs on their pull request; that approval is
not given for a `master`-targeted request, because approving one runs the
inherited matrix. Redirect it to the current version branch or close it.
