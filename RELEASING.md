# Releasing

A release is an annotated tag on the version branch. Pushing it runs
`.github/workflows/publish-nox.yml`, which builds both platforms, publishes them
to one GitHub Release with their Corresponding Source, and makes the release
public only after every check passes.

## Name

`release-<upstream-tag>-mod.<n>`, for example `release-5.2.4-mod.1`. `<n>` starts
at 1 for each upstream tag and increases by one for every later release from the
same version branch. The workflow derives the upstream tag from this name and
fails when it disagrees with `nox-build/pins.json`'s `upstream.tag`.

## When

- **A change merged into the current version branch:** tag the merge commit as
  the next `-mod.<n>`.
- **A new upstream version:** follow *Merging a new upstream version* in
  `CLAUDE.md` first. That procedure ends by tagging `-mod.1`.

## How

```
git fetch origin --tags
git tag -a release-<upstream-tag>-mod.<n> -m "release-<upstream-tag>-mod.<n>" <commit on hardened/<upstream-tag>>
git push origin release-<upstream-tag>-mod.<n>
```

The tag message is the tag name. **Never move or re-push a tag.** Consumers pin
the image digest a tag produced, and the release's own completeness check
compares that digest with what the tag resolves to in the registry.

## What the push runs

1. **`verify`:** derives the upstream tag from the ref, asserts it equals
   `pins.json`'s, and runs the post-condition tests in `nox-build/tests/`.
2. **`create-release`:** creates a **draft** release titled with the tag, unless
   one already exists.
3. **`publish-linux`:** builds the image, asserts its runtime floors, pushes
   `ghcr.io/<owner>/qbittorrent-nox:<tag>`, and uploads the Linux Corresponding
   Source pack and `image-digest.txt`.
4. **`publish-windows`:** builds the Windows bundle, asserts its runtime floors,
   and uploads `qbittorrent-nox-win-x64-<tag>.zip` with its checksum and the
   Windows Corresponding Source pack.
5. **`assert-release-complete`:** checks every expected asset is present, the
   registry digest equals `image-digest.txt`, every checksum verifies, and each
   pack's patch series applies to its own pristine upstream tarball. **Only this
   job un-drafts the release.**

## Reading a published release

- **Image:** `ghcr.io/<owner>/qbittorrent-nox@<digest>`, where the digest is the
  content of the release asset `image-digest.txt`. Pin the digest, not the tag.
- **Windows:** the release asset `qbittorrent-nox-win-x64-<tag>.zip`, with
  `qbittorrent-nox-win-x64-<tag>.zip.sha256` beside it.

## When a run fails

- **The release stays a draft.** No partial release is ever public.
- **Re-run the failed jobs** from the Actions page once the cause is fixed.
  `create-release` leaves an existing draft alone, and every upload uses
  `--clobber`, so a re-run converges on the same release.
- **Never cancel a run that is publishing.** A run cancelled between the image
  push and the source upload leaves a binary without its Corresponding Source,
  and the check that would report it dies with the run. The workflow sets
  `cancel-in-progress: false` for this reason.
- **A fix that needs a source change gets a new `-mod.<n>`,** never a moved tag.
