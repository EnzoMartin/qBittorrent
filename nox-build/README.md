# Building `qbittorrent-nox`

This file is part of the Corresponding Source pack required by GPLv3 §1
("including scripts to control those [generate and install] activities").

It describes how to reproduce the `qbittorrent-nox` binaries published by this
repository.

---

## Pinned versions

**Read `pins.json`, not this section.** Values are deliberately not repeated
here: a copy the build reads cannot drift, a copy the build compares drifts
loudly, and a copy only a human reads drifts silently while looking
authoritative. This section had four wrong rows before it was reduced to
pointers.

| Where | What it pins |
|---|---|
| `pins.json` | libtorrent (tag and commit), vcpkg, Qt for Windows, the upstream tag, and the assertion floors |
| `windows/vcpkg-ports.txt` | the vcpkg port set. Separate because it is the download cache key |
| `.github/workflows/publish-nox.yml` | GitHub Action refs, SHA-pinned. Bumped by hand — Dependabot does not maintain SHA pins (measured 2026-08-12) |
| `linux/Dockerfile` | the base image, as a literal `FROM` so Dependabot can update it |

Qt on Linux is not pinned at all: it comes from the base image's apt, and the
Dockerfile's `WHY ubuntu:26.04` block records the `minQt6Version` 6.6.0 floor
that decides the base.

**On every upstream version bump:** follow the merge procedure in the root
`CLAUDE.md`. Re-check the items verified by reading rather than by test:
- that the deletion sites still match the new source;
- that libtorrent's SSL peer-certificate comparison is still an exact match
  rather than a prefix compare (`torrent::verify_peer_cert` in
  `src/torrent.cpp`; upstream's changelog does not record that fix, so release
  notes will not tell you);
- that `peer_error_alert` is still in the `peer` category and
  `peer_disconnected_alert`/`peer_connect_alert` still in the `connect` category
  (`include/libtorrent/alert_types.hpp`);
- that the two posting sites for these alert types are unchanged: the outgoing
  path (`peer_connection::disconnect` in `src/peer_connection.cpp`) and the
  incoming-SSL-handshake path (`session_impl::ssl_handshake` in
  `src/session_impl.cpp`);
- that `peer_endpoint_t` is still `tcp::endpoint` in libtorrent 2.0.x (it
  becomes a variant in 2.1; a handler that reads the endpoint field, rather than
  using `message()`, needs a `LIBTORRENT_VERSION_NUM >= 20100` branch).

---

## Linux

The Linux binary is built and published as a container image.

```
docker build -f nox-build/linux/Dockerfile -t nox-engine:local \
  --build-arg LT_TAG="$(jq -r .libtorrent.tag nox-build/pins.json)" \
  --build-arg LT_COMMIT="$(jq -r .libtorrent.commit nox-build/pins.json)" \
  .
```

The libtorrent arguments have no defaults in the Dockerfile and the build fails
without them. That is deliberate: a default would be a second copy of the
version, and the drift it permits is invisible in one direction — the runtime
floor asserts a minimum, so a Dockerfile bumped without `pins.json` passes while
the floor it is checked against silently weakens.

The context is the **repository root**, not `nox-build/linux`. The recipe does
`COPY . /src/qbt`, so the image is built from this repository's own committed
tree rather than by cloning upstream and applying a patch. That is what makes the
published binary's relationship to upstream checkable: the delta is the branch's
git history.

`.dockerignore` lives at the root, because Docker resolves it against the context
root. Keep it minimal — nothing CMake reads may be excluded. `add_subdirectory(dist)`
is unconditional in the root `CMakeLists.txt` and `dist/unix` installs man pages
from `doc/`, so excluding either fails the build at configure.

### Corresponding Source for the image

The image links Qt, OpenSSL and zlib as **stock distribution packages** (Boost is
used at build time as headers only and is not a runtime dependency),
at versions entirely unlike the vcpkg versions the Windows build uses. Shipping
the Windows pack as this image's Corresponding Source would publish source that
does not correspond to the binary, so the Linux pack is its own thing:

| Item | How it is produced |
|---|---|
| Pristine upstream source at the branched tag | `git archive` |
| This fork's delta against that tag | `git format-patch <tag>..HEAD` |
| The build recipe | `nox-build/` and the publish workflow |
| The §5(a) modification notice | root `MODIFICATIONS.md` |
| The installed-package manifest | `docker run --rm --entrypoint dpkg-query <image> -W -f='${Package} ${Version} ${source:Package}\n'` |

The manifest is generated from the **finished image**, not from the builder
stage. That is deliberate: it describes the layer set actually conveyed to a
recipient rather than an intermediate they never receive.

Everything the manifest lists is discharged by **pointing**: GPLv3 §6(d) permits
Corresponding Source to live on "a different server (operated by you or a third
party)", and the distribution's own archive is that server. Pin those pointers to
`snapshot.ubuntu.com` rather than `archive.ubuntu.com` — §6(d) obliges
availability "for as long as needed", and a suite eventually migrates off the
rolling archive.

**Read the manifest for genuinely GPLv2-only packages.** GPLv2 §3 requires
equivalent access "from the same place" and carries no third-party-server
allowance, so pointing does not discharge a v2-only entry — it must be
accompanied or offered directly. A v2-**or-later** entry is fine: elect v3 and
point.

---

## Windows

### Prerequisites

- Windows Server 2025 (the binary is win-x64 only; `release-5.2.4-mod.2` was built
  on image `win25-vs2026/20260925.250.1`)
- Visual Studio 2026 (VS 18), MSVC toolset 14.51, Windows SDK 10.0.26100.0, with
  the "Desktop development with C++" workload
- [vcpkg](https://vcpkg.io/) — check out vcpkg at the `vcpkg.commit` in
  `nox-build/pins.json`; the CI workflow fetches that exact commit
- [Qt 6.10.x](https://www.qt.io/download-open-source) — installed by
  `jurplel/install-qt-action` in CI; install manually for local builds (dynamic,
  `win64_msvc2022_64`)
- Git, CMake ≥ 3.20, Ninja

### 1. Obtain the source

Clone this repository and check out the version branch. The modifications are
already applied — they are commits, not a patch to be run.

### 2. Bootstrap vcpkg

```powershell
$vcpkgRef = (Get-Content nox-build\pins.json | ConvertFrom-Json).vcpkg.commit
New-Item -ItemType Directory vcpkg
git -C vcpkg init
git -C vcpkg fetch --depth 1 origin $vcpkgRef
git -C vcpkg checkout --detach FETCH_HEAD
.\vcpkg\bootstrap-vcpkg.bat -disableMetrics
```

### 3. Clone and build libtorrent

```powershell
$lt = Get-Content nox-build\pins.json | ConvertFrom-Json
git clone --depth 1 --branch $lt.libtorrent.tag `
    --recurse-submodules --shallow-submodules `
    https://github.com/arvidn/libtorrent.git lt-src
# A tag is movable, and this one decides whether SSL peer certificates are
# compared exactly or by prefix: stop if it no longer resolves to the pinned commit.
if ((git -C lt-src rev-parse HEAD).Trim() -ne $lt.libtorrent.commit) { throw "libtorrent tag moved" }
cmake -B lt-src\build -G Ninja -S lt-src `
    -DCMAKE_BUILD_TYPE=Release `
    -DBUILD_SHARED_LIBS=OFF `
    -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL `
    -DCMAKE_INSTALL_PREFIX="$PWD\lt-install" `
    -DCMAKE_TOOLCHAIN_FILE="vcpkg\scripts\buildsystems\vcpkg.cmake" `
    -DVCPKG_TARGET_TRIPLET=x64-windows-static-md
cmake --build lt-src\build --parallel
cmake --install lt-src\build
```

### 4. Configure

```powershell
cmake -B build -G "Ninja" `
  -DCMAKE_BUILD_TYPE=Release `
  -DGUI=OFF `
  -DWEBUI=ON `
  -DTESTING=OFF `
  -DSTACKTRACE=ON `
  -DMSVC_RUNTIME_DYNAMIC=ON `
  -DCMAKE_TOOLCHAIN_FILE="vcpkg\scripts\buildsystems\vcpkg.cmake" `
  -DVCPKG_TARGET_TRIPLET=x64-windows-static-md `
  -DCMAKE_PREFIX_PATH="$PWD\lt-install;<path-to-Qt6-install>"
```

**The triplet is `x64-windows-static-md`, and it is not interchangeable.** Static
libraries with the dynamic CRT (`/MD`), matching `MSVC_RUNTIME_DYNAMIC=ON`.
Building with `x64-windows-static` instead links `/MT` and mixes CRTs, which is
undefined behaviour rather than a style choice; `x64-windows` links the
dependencies dynamically and produces a bundle missing DLLs it needs.

**Qt linkage.** Qt is linked dynamically. This is our chosen build shape — it
keeps the Qt libraries replaceable and avoids mixed-runtime hazards — not a
licence requirement; LGPLv3 §4(d) permits either a shared-library form or a
suitable relinking mechanism.

### 5. Build

```powershell
cmake --build build --config Release --parallel
```

The output is `build\qbittorrent-nox.exe`.

### 6. Stage the bundle

Copy the following beside `qbittorrent-nox.exe`:

```
qbittorrent-nox.exe
Qt6Core.dll
Qt6Network.dll
Qt6Sql.dll
Qt6Xml.dll
plugins\tls\qcertonlybackend.dll
plugins\tls\qopensslbackend.dll
plugins\tls\qschannelbackend.dll
plugins\sqldrivers\qsqlite.dll
qt.conf
THIRD-PARTY-NOTICES.md
licenses\
  COPYING
  COPYING.GPLv2
  COPYING.GPLv3
  AUTHORS
  LGPL-3.0.txt
  libtorrent-LICENSE.txt
  OpenSSL-Apache-2.0.txt
```

### 7. Verify

Required before shipping any binary:

- `app/webapiVersion` returns `2.15.1` or higher
- `app/buildInfo`'s libtorrent field reports `2.0.13` or higher
- `GET /api/v2/search/plugins` returns **404**

The 404 must be observed **authenticated**. `doProcessRequest` throws
`ForbiddenHTTPError` before the controller lookup, so an unauthenticated request
returns 403 against a pristine engine too — a 403 here is **inconclusive**, never
a pass. Confirm the credential works in the same session by checking that
`app/webapiVersion` returns 200 with it.

The WebUI API key must be `qbt_` plus **exactly 28** characters. `Utils::APIKey::isValid`
requires the prefix and a total length of exactly 32. A short key is silently
ignored: no session is created and every authenticated call answers 403.

---

## Reading what changed upstream

```
bash nox-build/upstream-delta.sh <old-tag> <new-tag>
```

A reading aid over the paths the modifications touch. It gates nothing; the
drift test in `nox-build/tests/` is what stops a merge.
