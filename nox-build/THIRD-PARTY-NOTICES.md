# Third-Party Notices

> **MUST-VERIFY-BEFORE-SHIP: No build of this recipe has ever been executed.**
> The version numbers, licence attributions, and component descriptions below are
> derived from source reading at the pinned tags (`release-5.2.3`, `v2.0.13`,
> `openssl-3.5.1`, `1.86.0`, `1.3.1`). No binary has been produced yet from which
> actual linked versions could be confirmed. Verify that every version number
> matches the binary actually shipped before distributing this notice alongside it.

This directory contains `qbittorrent-nox.exe`, a modified build of qBittorrent,
and its dynamically linked Qt runtime libraries. The terms of the licences
governing these components are set out below.

**Clear directions to the Corresponding Source** (GPLv3 §6(d)):  
The Corresponding Source for this engine build — the qBittorrent source at the
pinned tag, the delta applied to it, the build recipe, and all linked library
sources (Qt, libtorrent, OpenSSL, Boost, zlib) — is published as a
`corresponding-source` archive attached to this build's release, and travels
with this binary wherever it is redistributed. Where the binary is distributed
on physical media rather than downloaded, the archive is on the same medium.

---

## qBittorrent (patched)

**Version:** release-5.2.3  
**Licence:** GNU General Public License version 3 or later (GPLv3+)  
**Modification:** delete-only patch removing search-plugin and autorun controller
registrations; see `MODIFICATIONS.md` and `licenses/COPYING` for details.  
**Licence texts:** `licenses/COPYING.GPLv3` (GPLv3), `licenses/COPYING.GPLv2` (GPLv2)  
**Attribution:** `licenses/AUTHORS`

The binary distribution is licensed under GPLv3+ because it embeds GPLv3+-licensed
icon assets (`src/icons/` La-Capitaine set; `src/qbittorrent_file.ico`), as stated
in `licenses/COPYING` and verified at the tag.

---

## Qt 6 (Core, Network, Sql, Xml; tls and sqldrivers plugins)

**Licence:** GNU Lesser General Public License version 3 (LGPLv3)  
**Licence texts:** `licenses/LGPL-3.0.txt`, `licenses/COPYING.GPLv3`

This build uses the Qt Framework, taken under its LGPLv3 licence option.
Qt source code for the modules included with this build is in the
`corresponding-source` archive described above, as required by LGPLv3 §4(d)(0)
and Qt's own open-source LGPL obligations
(qt.io/licensing/open-source-lgpl-obligations).

The Qt DLLs (`Qt6Core.dll`, `Qt6Network.dll`, `Qt6Sql.dll`, `Qt6Xml.dll`) and
plugins are dynamically linked and user-replaceable. To relink this application
against a modified version of Qt, replace the DLLs in this directory with
interface-compatible builds from the provided source.

Qt itself bundles third-party components whose notices are reproduced in the
Qt source archive's `LICENSES/` directory. Selected notices required in binary
redistribution:

- **QtEntryPoint** — BSD 3-Clause
- **zlib 1.3.x** (Qt-bundled copy) — zlib licence (no binary notice required)
- **BLAKE2** — CC0 / Apache 2.0
- **Penner easing functions** — BSD 3-Clause

Full attribution data is available from Qt's "Licenses and Attributions" pages
and in the Qt source provided in the `corresponding-source` archive.

---

## libtorrent-rasterbar

**Version:** v2.0.13  
**Licence:** BSD 3-Clause  
**Licence text:** `licenses/libtorrent-BSD-3-Clause.txt`

Copyright (c) 2003-2020, Arvid Norberg  
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software without
   specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

---

## OpenSSL

**Version:** 3.5.1  
**Licence:** Apache License 2.0  
**Licence text:** `licenses/OpenSSL-Apache-2.0.txt`

No NOTICE file exists at the openssl-3.5.1 repository root (verified via the
tag's root listing); Apache 2.0 §4(d)'s NOTICE-carrying condition therefore
carries nothing additional. The Apache 2.0 licence text is provided above.

The qBittorrent source carries an OpenSSL linking exception (reproduced in
`licenses/COPYING`) granted by the qBittorrent copyright holders.

---

## Boost

**Version:** 1.86.0  
**Licence:** Boost Software License 1.0 (BSL-1.0)

BSL-1.0 imposes no binary-notice obligation ("unless such copies or derivative
works are solely in the form of machine-executable object code generated by a
source language processor"). No binary-accompanying notice is required. The
licence text is included with the Boost source in the `corresponding-source`
archive.

---

## zlib

**Version:** 1.3.1  
**Licence:** zlib licence

The zlib licence requires that the notice remain in source distributions
("This notice may not be removed or altered from any source distribution")
but imposes no binary-accompanying obligation (acknowledgment "would be
appreciated but is not required"). The licence text is with the zlib source in
the `corresponding-source` archive.

---

## qBittorrent in-tree assets

The qBittorrent source includes third-party assets described in `licenses/AUTHORS`:

- **MooTools, Mocha UI, vanillaSelectBox** — MIT
- **flag-icons** — MIT
- **Ionicons-derived icons** — MIT
- **La-Capitaine icon set** (38 SVG files) — **GPLv3+** (forces binary to GPLv3+)
- **`qbittorrent_file.ico`** (based on Oxygen Icon Theme unknown.svg) — **GPLv3+**
- **`force-recheck.svg`** — CC-BY-4.0 (see `licenses/AUTHORS` for attribution)

Full attribution is in `licenses/AUTHORS`.

---

## Microsoft Visual C++ Runtime

The Windows build requires the Microsoft Visual C++ Redistributable.

**The CRT DLLs are never shipped beside the program.** Distributing
`vcruntime140.dll` or `msvcp140.dll` in the same directory as the executable
forfeits the GPL System Library exception, which is what permits linking against
a runtime the GPL does not cover. The redistributable is therefore installed
separately, by running Microsoft's `vc_redist.x64.exe`. The Windows build asserts
this: it fails if either DLL reaches the bundle.

**MUST-VERIFY-BEFORE-SHIP:** Microsoft's distributable-code terms governing
redistribution of `vc_redist.x64.exe` itself — as opposed to linking against the
runtime it installs — have not been verified. Anyone chaining that installer from
an installer of their own must check the current terms on Microsoft's Visual C++
Redistributable download page first. This item is open.
