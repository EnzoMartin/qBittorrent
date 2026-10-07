# Modifications to qBittorrent

> **MUST-VERIFY-BEFORE-SHIP: no build of this branch has produced a binary yet.**
> The source structure this file describes is confirmed to exist — the deletions
> are commits on this branch and can be read directly. What remains unverified is
> that the modified tree *compiles* and that the resulting binary behaves as
> claimed. Do not ship a binary from this branch until a build has succeeded.

This file satisfies GPLv3 §5(a): the modified work must carry prominent notices
stating that you modified it, and giving a relevant date.

**Base:** qBittorrent `release-5.2.4` (WebAPI 2.15.1)
**Date:** 2026-08-12 (§1–§3); 2026-10-06 (§4; rebased onto `release-5.2.4`)

**Licensing follows upstream's own scoping, which is two-tiered.** Per
`release-5.2.4:COPYING`, the source is **GPLv2-or-later** and binary distribution
is **GPLv3-or-later**, with the **OpenSSL linking exception added in both cases**.
This fork elects no single version and narrows nothing; the exception matters
because the source tier is v2+, where Apache-2.0 OpenSSL is not compatible
without it.

---

## What was changed

The following lines were deleted from the qBittorrent source tree, and one
bounded observability addition was made; see §6 for the addition.

### 1. Search-plugin controller (`src/webui/CMakeLists.txt`, `src/webui/webapplication.cpp`)

Both search-controller entries (`api/searchcontroller.h` and `api/searchcontroller.cpp`)
are removed from the `qbt_webui` build target, and the controller's dispatch registration
is removed from `src/webui/webapplication.cpp`. Those deletions remove the API surface: no
`search/*` endpoint is reachable, so `search/installPlugin` cannot be called.

**The header entry is as load-bearing as the source entry.** AUTOMOC generates a
meta-object for every `Q_OBJECT` header listed in a target's sources, so removing only the
`.cpp` leaves `mocs_compilation.cpp` referencing slot implementations that no longer exist
and `qbt_webui` fails at link with one undefined reference per slot.

**The search sources under `src/base/` are deliberately untouched, and the claim here is bounded accordingly.**
`SearchPluginManager` stays compiled into `qbt_base`, because `src/app/application.cpp`
calls `SearchPluginManager::freeInstance()` and deleting the base sources breaks the
link. The claimable property is therefore *"the search API is not reachable"*, **not**
*"the plugin-execution code is absent from the binary"*. Anything that reached
`SearchPluginManager` by another route would still find it.

**Reason:** The search API exposes `search/installPlugin(source)` which stores an
arbitrary `.py` file and later executes it through a spawned Python interpreter
(`searchpluginmanager.cpp:548-561` at `release-5.2.4`). This is a live code-execution
primitive (`api/searchcontroller.cpp:255-261`). Because qBittorrent's build system
has no CMake flag to disable the search subsystem — it is compiled into `qbt_base`
and `qbt_webui` unconditionally — source deletion is the only available build-time
mitigation.

### 2. Autorun setPreferences handlers (`src/webui/api/appcontroller.cpp`)

Lines **692–701** at `release-5.2.4` were removed from the `setPreferences` WebUI API
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

Line **2138** at `release-5.2.4` was removed from the `SSLParametersAction` GET
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

### 4. SSL parameters in fastresume data (`src/base/bittorrent/bencoderesumedatastorage.cpp`)

Lines **76–78**, **277–282** and **447–452** at `release-5.2.4` were removed:
- **76–78:** the `KEY_SSL_CERTIFICATE`, `KEY_SSL_PRIVATE_KEY` and `KEY_SSL_DH_PARAMS` key names;
- **277–282:** the load statement that set a restored torrent's `sslParameters` from them;
- **447–452:** the three writes that stored a torrent's certificate, private key and DH parameters in its `.fastresume` file.

A restored torrent therefore starts with no SSL parameters. A torrent that is not restarted keeps whatever `torrents/setSSLParameters` gave it.

**Reason: the stored parameters were reported but never loaded.** At `release-5.2.4`, a torrent's parameters reach libtorrent (`set_ssl_certificate_buffer`) only from `TorrentImpl::applySSLParameters`. That runs from `setSSLParameters` and from `SessionImpl::handleTorrentNeedCertAlert`.
- **The alert arrives first.** libtorrent `v2.0.13` posts `torrent_need_cert_alert` from `torrent::init_ssl`, during `torrent_ptr->start()` in `session_impl::add_torrent`. That is *before* the `add_torrent_alert` whose handler creates the `TorrentImpl`.
- **So the alert is dropped.** The handler finds no torrent and returns.
- **A re-apply does nothing.** `setSSLParameters` with the restored parameters returns at its equality check.
- **The result:** after a restart, every SSL torrent restored from fastresume reported a certificate through the `SSLParameters` GET that libtorrent did not have. It refused every SSL peer until a *different* certificate was set.
- **After the deletion,** the GET reports no certificate for a restored torrent. A caller that sets the torrent's parameters then reaches `applySSLParameters`, and the context `init_ssl` created already exists.

**This also stops writing every swarm private key to disk**, one per `.fastresume` file in the profile.

**Bounds on the claim:**
- **SQLite storage is not modified.** It is used only when `BitTorrent\Session\ResumeDataStorageType` is `SQLite`; the default is `Legacy`, which is this file.
- **`SSLParameters` and the WebUI setter are untouched.** So is the JSON serialisation of `sslParameters` in `addtorrentparams.cpp`, which carries parameters supplied when a torrent is added.
- **Old files keep their keys until rewritten.** A `.fastresume` file written by an earlier build still holds the old keys until the torrent's next resume-data save rewrites it without them. This build ignores them on load.

### 5. Repository configuration (`.github/`)

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

- Under `src/`, only §6's observability addition was made; all other source changes are deletions.
- The `about.html` notice page, all licence headers, and the OpenSSL linking
  exception in every source file are untouched (GPLv3 §5(d), §4).
- DHT, LSD, PeX, UPnP, RSS, and IPv6 remain in the binary; they are not build-gated
  upstream and are controlled only by runtime configuration.
- The WebUI (`WEBUI=ON`) is kept — it is the only control channel for a headless build.
- The search sources under `src/base/` are untouched, so `SearchPluginManager` is still compiled in;
  `src/app/application.cpp` links it. See §1 for the bound this places on the
  security claim.
- **The WebUI's browser-side search assets remain.** Only the controller registration
  was removed, so the shipped markup and scripts for a scope that now answers 404 are
  still present. Enumerate them rather than trusting a list here, which will go stale:

  ```
  git ls-tree -r --name-only release-5.2.4 -- src/webui/www/private | grep -i search
  ```

---

## How to reproduce

Check out the upstream tag and apply the commits on this branch:

```
git clone https://github.com/qbittorrent/qBittorrent.git
cd qBittorrent
git checkout release-5.2.4
git remote add hardened <this repository>
git fetch hardened
git cherry-pick release-5.2.4..hardened/hardened/release-5.2.4
```

Or read the delta directly:

```
git log --oneline release-5.2.4..HEAD
git diff release-5.2.4..HEAD -- src/
```

The source-side diff is seven files: 32 deletions across five existing files, and
7 inserted lines across three existing files (`nativesessionextension.cpp`,
`sessionimpl.cpp`, `src/base/CMakeLists.txt`) plus two new files
(`peerconnectionlog.h`, `peerconnectionlog.cpp`). Any insertion beyond §6's
exact set contradicts the claim above.

---

### 6. Peer-connection logging (`src/base/bittorrent/peerconnectionlog.{h,cpp}`)

**Date:** 2026-10-07

**Exact inserted lines in existing upstream files:**

`src/base/bittorrent/sessionimpl.cpp`, `loadLTSettings()`:
```
        | lt::alert::connect_notification
```
inserted directly after `const lt::alert_category_t alertMask = lt::alert::error_notification`.

`src/base/bittorrent/nativesessionextension.cpp`, `on_alert()`:
```
#include "peerconnectionlog.h"
```
added after `#include "nativetorrentextension.h"`, and:
```
    case lt::peer_connect_alert::alert_type:
    case lt::peer_error_alert::alert_type:
    case lt::peer_disconnected_alert::alert_type:
        logPeerConnectionAlert(alert);
        break;
```
inserted between the `fastresume_rejected_alert` case's `break;` and `default:`.

`src/base/CMakeLists.txt`: `bittorrent/peerconnectionlog.h` added after
`bittorrent/peeraddress.h`; `bittorrent/peerconnectionlog.cpp` added after
`bittorrent/peeraddress.cpp`.

**Two new files:** `src/base/bittorrent/peerconnectionlog.h` and
`src/base/bittorrent/peerconnectionlog.cpp`.

**What this addition does:**

The mask line makes libtorrent post `peer_connect_alert` and
`peer_disconnected_alert` (the `connect` category), which are not posted today.
`peer_error_alert` is already in the mask via `peer_notification`. All three alert
types are routed to `logPeerConnectionAlert`, which is the only reader of them.

`logPeerConnectionAlert`:
- counts `peer_connect_alert` occurrences without logging each one;
- logs every `peer_error_alert`;
- logs a `peer_disconnected_alert` only when `op == operation_t::connect` or the
  error category is `asio.ssl` — ordinary closes stay out;
- rate-limits per (alert type, operation, error category name, error value) to one
  log line per 60-second window on a steady clock, reporting the suppressed count
  on the next logged line for that key after the window closes;
- caps the key map at 48 entries, with an overflow key for anything beyond;
- logs WARNING for SSL-category errors and INFO for all others;
- writes every line under the stable prefix `peer-connection: `, which consumers
  of `log/main` parse.

`alert->message()` carries the torrent name (or `" - "` for an incoming handshake
with no torrent), the endpoint, and the error text. It never carries certificate
fields — those are only in `torrent_log`, which is not enabled here.

**What this addition does not cover:**

- The specific cause of an SSL failure: the error text is the OpenSSL reason string
  (`ERR_reason_error_string`), not the certificate's identity or chain detail.
- Whether the failure is outgoing (a desktop connecting to a seeder) or incoming
  (a seeder receiving an incoming connection) — only the operation field (`op`)
  distinguishes them, and `peer_error_alert` for incoming SSL handshake failures
  carries `op == ssl_handshake` rather than `connect`.
- The real alert and log volume under load: the cost of the extra `connect_notification`
  alerts is unmeasured.

**"These lines only log" is a review claim** over `peerconnectionlog.cpp` — a file
of N lines at review time — and not a tested property. There is no automated test
for it at this release.
