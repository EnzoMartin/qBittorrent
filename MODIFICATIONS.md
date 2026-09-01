# Modifications to qBittorrent

> **MUST-VERIFY-BEFORE-SHIP: no build of this branch has produced a binary yet.**
> The source structure this file describes is confirmed to exist — the deletions
> are commits on this branch and can be read directly. What remains unverified is
> that the modified tree *compiles* and that the resulting binary behaves as
> claimed. Do not ship a binary from this branch until a build has succeeded.

This file satisfies GPLv3 §5(a): the modified work must carry prominent notices
stating that you modified it, and giving a relevant date.

**Base:** qBittorrent `release-5.2.3` (WebAPI 2.15.1)
**Date:** 2026-08-12

**Licensing follows upstream's own scoping, which is two-tiered.** Per
`release-5.2.3:COPYING`, the source is **GPLv2-or-later** and binary distribution
is **GPLv3-or-later**, with the **OpenSSL linking exception added in both cases**.
This fork elects no single version and narrows nothing; the exception matters
because the source tier is v2+, where Apache-2.0 OpenSSL is not compatible
without it.

---

## What was changed

The following lines were deleted from the qBittorrent source tree. No lines were
added or modified; these are delete-only changes.

### 1. Search-plugin controller (`src/webui/CMakeLists.txt`, `src/webui/webapplication.cpp`)

Both search-controller entries (`api/searchcontroller.h` and `api/searchcontroller.cpp`)
are removed from the `qbt_webui` build target, and the controller's dispatch registration
is removed from `src/webui/webapplication.cpp`. Those deletions remove the API surface: no
`search/*` endpoint is reachable, so `search/installPlugin` cannot be called.

**The header entry is as load-bearing as the source entry.** AUTOMOC generates a
meta-object for every `Q_OBJECT` header listed in a target's sources, so removing only the
`.cpp` leaves `mocs_compilation.cpp` referencing slot implementations that no longer exist
and `qbt_webui` fails at link with one undefined reference per slot.

**`src/base/` is deliberately untouched, and the claim here is bounded accordingly.**
`SearchPluginManager` stays compiled into `qbt_base`, because `src/app/application.cpp`
calls `SearchPluginManager::freeInstance()` and deleting the base sources breaks the
link. The claimable property is therefore *"the search API is not reachable"*, **not**
*"the plugin-execution code is absent from the binary"*. Anything that reached
`SearchPluginManager` by another route would still find it.

**Reason:** The search API exposes `search/installPlugin(source)` which stores an
arbitrary `.py` file and later executes it through a spawned Python interpreter
(`searchpluginmanager.cpp:548-561` at `release-5.2.3`). This is a live code-execution
primitive (`api/searchcontroller.cpp:255-261`). Because qBittorrent's build system
has no CMake flag to disable the search subsystem — it is compiled into `qbt_base`
and `qbt_webui` unconditionally — source deletion is the only available build-time
mitigation.

### 2. Autorun setPreferences handlers (`src/webui/api/appcontroller.cpp`)

Lines **692–701** at `release-5.2.3` were removed from the `setPreferences` WebUI API
handler: the four `autorun_*` field handlers together with the two `// Run an external
program on …` comments that bound them.

The removal covers **both** the `if (hasKey(u"autorun_…"_s))` guard lines and the
`pref->setAutoRun…()` setter body lines. Removing the guards alone while leaving the
setter bodies would cause every `setPreferences` call to unconditionally execute all four
AutoRun setters — undefined behaviour from a dangling iterator and a permanently active
RCE surface.

**The `preferences()` getter keys at `:226-230` are retained deliberately.** They report
the AutoRun configuration rather than setting it; a client that reads them keeps working,
and the property claimed here is that the values cannot be **written** through the API,
not that the feature is invisible. Removing the getters would break readers for no
additional safety, so a future maintainer should not "complete" this deletion.

**Reason:** These fields expose `Preferences/AutoRun/*` over the API — an
authenticated caller can set `autorun_enabled=true` with an arbitrary `autorun_program`
and the program will be executed on every torrent completion or addition
(`preferences.cpp:1246-1269`). This is the CVE-2019-13640 class of vulnerability.
The underlying preference storage in `preferences.cpp` is not removed.

### 3. SSL private key disclosure (`src/webui/api/torrentscontroller.cpp`)

Line **2138** at `release-5.2.3` was removed from the `SSLParametersAction` GET
handler — the `KEY_PROP_SSL_PRIVATEKEY` entry in the `QJsonObject ret` initialiser
that serialised the torrent's private key material into the API response.

**`KEY_PROP_SSL_CERTIFICATE` and `KEY_PROP_SSL_DHPARAMS` are retained deliberately.**
The certificate is a public artefact; the DH parameters are non-secret. Both remain
in the response, so the endpoint continues to serve its diagnostic purpose. The
removal targets only the field that disclosed per-torrent secret key material to any
caller holding WebUI credentials.

**The constant at `:131` and the three write sites are retained deliberately.** The
constant `KEY_PROP_SSL_PRIVATEKEY` defined at `:131` is still used by
`setSSLParametersAction` at `:1159`, `:2146`, and `:2156` to accept and store key
material. The claimable property is therefore *"the GET endpoint no longer discloses
the private key"*, **not** *"the key cannot be set"*. The setter and the storage
path are untouched; a future maintainer should not extend this deletion to the
constant or the write sites.

**Reason:** `SSLParametersAction` returned `ssl_private_key` — the PEM-encoded
private key for the torrent's SSL peer configuration — to any authenticated WebUI
API caller. Private key material is not a diagnostic property of a torrent; it is a
credential that cannot be revoked without re-keying the torrent. Disclosing it over
an API with no per-method scope limit violates the principle of least disclosure.

### 4. Repository configuration (`.github/`)

None of this affects the binary. It is disclosed because it is part of this branch's diff
against the upstream tag, and a reader of the Corresponding Source should find no
unexplained deletions.

- Upstream's eight top-level workflow files were deleted and `.github/dependabot.yml` was
  replaced, so this branch builds and publishes rather than running upstream's test matrix.
  `.github/workflows/helper/` is untouched.
- `.github/ISSUE_TEMPLATE/` and `.github/FUNDING.yml` were deleted, and
  `.github/PULL_REQUEST_TEMPLATE.md` and `.github/SUPPORT.md` were replaced. This fork
  accepts no issues, pull requests or feature requests and offers no support; the
  replacements say so and point to upstream. `FUNDING.yml` was upstream's and rendered a
  sponsor button here, which a fork that modifies the software should not display.

---

## What was NOT changed

- No lines were added or modified under `src/` — these are delete-only changes.
- The `about.html` notice page, all licence headers, and the OpenSSL linking
  exception in every source file are untouched (GPLv3 §5(d), §4).
- DHT, LSD, PeX, UPnP, RSS, and IPv6 remain in the binary; they are not build-gated
  upstream and are controlled only by runtime configuration.
- The WebUI (`WEBUI=ON`) is kept — it is the only control channel for a headless build.
- `src/base/` is untouched, so `SearchPluginManager` is still compiled in;
  `src/app/application.cpp` links it. See §1 for the bound this places on the
  security claim.
- **The WebUI's browser-side search assets remain.** Only the controller registration
  was removed, so the shipped markup and scripts for a scope that now answers 404 are
  still present. Enumerate them rather than trusting a list here, which will go stale:

  ```
  git ls-tree -r --name-only release-5.2.3 -- src/webui/www/private | grep -i search
  ```

---

## How to reproduce

Check out the upstream tag and apply the commits on this branch:

```
git clone https://github.com/qbittorrent/qBittorrent.git
cd qBittorrent
git checkout release-5.2.3
git remote add hardened <this repository>
git fetch hardened
git cherry-pick release-5.2.3..hardened/hardened/release-5.2.3
```

Or read the delta directly:

```
git log --oneline release-5.2.3..HEAD
git diff release-5.2.3..HEAD -- src/
```

The source-side diff is four files and 15 deletions with no insertions. Any insertion
under `src/` contradicts the delete-only claim above.
