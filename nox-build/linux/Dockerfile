# Build qbittorrent-nox (Linux x64) from this repository's tree.
#
# MUST-VERIFY-BEFORE-SHIP: No build of this recipe has ever been executed.
# Every version number, path, library name, and assertion below is derived from
# source reading only. Verify by running the build and recording the outcome.
#
# Pinned versions (must be updated together — see the Windows recipe rationale
# in .github/workflows/publish-nox.yml for full reasoning):
#   qBittorrent: this repository's tree, branched from release-5.2.3
#   libtorrent:  v2.0.13  (SSL peer-cert exact-match floor; security-load-bearing)
#   Qt:          6.10.2 from Ubuntu 26.04 apt
#
# WHY ubuntu:26.04 (NOT ubuntu:24.04):
#   qBittorrent release-5.2.3 sets minQt6Version 6.6.0 (CheckPackages.cmake,
#   REQUIRED). Ubuntu 24.04 ships Qt 6.4.2, which fails the configure check.
#   Measured 2026-08-12 on ubuntu:26.04: qt6-base-dev candidate 6.10.2+dfsg-7,
#   which satisfies the floor.
#
# TORRENT_SSL_PEERS:
#   libtorrent enables SSL peer support (TORRENT_SSL_PEERS) when built with
#   OpenSSL. Built without it, set_ssl_certificate_buffer becomes a SILENT
#   no-op: the engine accepts an SSL certificate, reports success, and then
#   serves an ordinary torrent that any peer can join. Nothing observable
#   distinguishes that build from a correct one short of watching an
#   unauthenticated peer complete a transfer.
#   The libssl-dev dependency below is therefore load-bearing, not optional.
#   A build-time assertion greps compile_commands.json for TORRENT_SSL_PEERS
#   and fails the build if it is absent.
#
# libtorrent install prefix (/usr/local vs /usr):
#   CMAKE_INSTALL_PREFIX=/usr with GNUInstallDirs on Debian/Ubuntu installs
#   shared libraries to lib/x86_64-linux-gnu (multiarch path). The COPY glob
#   in the runtime stage cannot predict the multiarch suffix. Using
#   CMAKE_INSTALL_PREFIX=/usr/local places libraries at /usr/local/lib
#   (arch-independent) so the COPY glob is deterministic.
#
# MUST-VERIFY-BEFORE-SHIP:
#   Launch the built nox once against a fresh profile directory and compare the
#   configuration file it writes against any hand-authored configuration
#   intended for it. Key names, section headers and QSettings serialisation are
#   derived from source reading, not from a file the engine actually
#   generated. Note that QSettings picks the file name by platform: on Linux the
#   engine reads qBittorrent.conf, not qBittorrent.ini.
#   The exact Qt6 runtime library names in the runtime stage below (libqt6*t64)
#   reflect Ubuntu's package naming; verify `ldd qbittorrent-nox` against the
#   runtime stage after a successful build and update if they differ.

# ============================================================================
# Stage 1: build
# ============================================================================
FROM ubuntu:26.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

# Build-time dependencies.
# libssl-dev: required for TORRENT_SSL_PEERS in libtorrent (load-bearing).
# qt6-base-dev provides Core, Network, Sql, Xml headers used by qBT nox.
# libboost-dev group: qBT base library uses Boost.System, Chrono, MultiIndex.
# Boost.Multiprecision, which libtorrent needs, is header-only and ships inside
# libboost-dev on this image — there is no libboost-multiprecision-dev package
# to add, and naming one aborts the stage before anything compiles.
# ca-certificates is explicit because it is only a *Recommends* of git, which
# --no-install-recommends drops: without the trust store every HTTPS clone below
# fails with "Problem with the SSL CA cert (path? access rights?)".
#
# qt6-base-private-dev is required, not optional: qBittorrent's base library links
# Qt::CorePrivate, whose INTERFACE_INCLUDE_DIRECTORIES names
# /usr/include/<triplet>/qt6/QtCore/<qt-version>. Debian ships that tree in the
# private package, so with only qt6-base-dev the qBT configure step fails with
# "Imported target Qt6::CorePrivate includes non-existent path".
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    cmake \
    ninja-build \
    git \
    python3 \
    pkg-config \
    libssl-dev \
    libboost-dev \
    libboost-system-dev \
    libboost-chrono-dev \
    zlib1g-dev \
    qt6-base-dev \
    qt6-base-private-dev \
    qt6-tools-dev \
    && rm -rf /var/lib/apt/lists/*

# ---- libtorrent --------------------------------------------------------
# Supplied from nox-build/pins.json by the caller, with no defaults. A default
# here would be a second copy of the version, and the drift it permits is
# undetectable in one direction: the runtime floor asserts >=, so a Dockerfile
# bumped without the pin file passes while the floor it is checked against
# silently weakens.
ARG LT_TAG
ARG LT_COMMIT

# --recurse-submodules is required, not an optimisation: `deps/try_signal` is a
# submodule and CMakeLists.txt:548 lists try_signal.cpp in the torrent-rasterbar
# sources, so a plain clone fails at configure with "Cannot find source file".
#
# The tag is fetched and the commit asserted, because a tag is movable and this
# one decides whether SSL peer certificates are compared exactly or by prefix.
RUN test -n "$LT_TAG" -a -n "$LT_COMMIT" \
      || { echo "ERROR: LT_TAG and LT_COMMIT must be passed as build args, from nox-build/pins.json."; exit 1; } \
    && git clone --depth 1 --branch "$LT_TAG" \
       --recurse-submodules --shallow-submodules \
       https://github.com/arvidn/libtorrent.git /src/libtorrent \
    && ACTUAL=$(git -C /src/libtorrent rev-parse HEAD) \
    && [ "$ACTUAL" = "$LT_COMMIT" ] \
       || { echo "ERROR: $LT_TAG resolves to $ACTUAL but pins.json records $LT_COMMIT. The tag moved."; exit 1; }

WORKDIR /src/libtorrent
# CMAKE_INSTALL_PREFIX=/usr/local: installs to /usr/local/lib (arch-independent).
# CMAKE_EXPORT_COMPILE_COMMANDS=ON: produces compile_commands.json for the
# TORRENT_SSL_PEERS assertion below.
RUN cmake -B build -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=ON \
    -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
    && cmake --build build --parallel \
    && cmake --install build

# Assert TORRENT_SSL_PEERS was compiled in.
# compile_commands.json carries -DTORRENT_SSL_PEERS=1 when OpenSSL::SSL is
# available at cmake configure time. Without this define, set_ssl_certificate_buffer
# is a silent no-op, so the resulting binary serves ordinary torrents while
# reporting that it applied a certificate.
RUN grep -q 'TORRENT_SSL_PEERS' /src/libtorrent/build/compile_commands.json \
    || { echo "ERROR: TORRENT_SSL_PEERS absent from compile_commands.json — OpenSSL was not found during libtorrent configure. set_ssl_certificate_buffer would be a silent no-op."; exit 1; }

# ---- qBittorrent -------------------------------------------------------
# The source is this repository's own committed tree: upstream at the branched
# tag, plus the delete-only commits that remove the search API surface and the
# autorun setPreferences handlers. Building from the tree rather than cloning
# upstream and patching is what makes the published binary's relationship to
# upstream checkable — the diff is the branch's own history.
#
# The build context is the repository root, so .dockerignore at the root governs
# what arrives here. Nothing CMake reads may be excluded: the root CMakeLists.txt
# calls add_subdirectory(dist) unconditionally, and dist/unix installs man pages
# from doc/, so excluding either fails the configure step below.
COPY . /src/qbt

# GUI=OFF: we only need the WebUI (nox mode).
# CMAKE_PREFIX_PATH=/usr/local: finds the installed libtorrent.
WORKDIR /src/qbt
RUN cmake -B build -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DGUI=OFF \
    -DWEBUI=ON \
    -DTESTING=OFF \
    -DCMAKE_PREFIX_PATH=/usr/local \
    && cmake --build build --parallel

# ============================================================================
# Stage 2: runtime
# Minimal image carrying the built binary and its shared libraries.
# ============================================================================
FROM ubuntu:26.04 AS runtime

ENV DEBIAN_FRONTEND=noninteractive

# Runtime shared libraries.
# The 't64' suffix marks Ubuntu's time64-transition variants and is NOT uniform
# across the Qt 6 modules: only Core carries it, so naming the others with the
# suffix aborts the stage.
# MUST-VERIFY: the Boost runtime package below is known WRONG, and is left in
# place only so that its replacement is chosen from a measurement rather than
# from a second guess. Measured against ubuntu:26.04 on 2026-08-12:
#   * libboost-dev depends on libboost1.90-dev, so the builder links Boost 1.90,
#     while this line installs the 1.83 runtime — a soname that cannot satisfy it;
#   * no libboost-system1.90.0 package exists at all, because Boost.System is
#     header-only at that version.
# So the correct answer is plausibly to install no Boost runtime here. Do not
# apply that from this note: run `ldd` against the built binary, read the
# sonames it actually names, and rewrite this list from that output.
# qBittorrent keeps its resume data in SQLite through QSqlDatabase, so the
# driver plugin is a runtime requirement, not an optional extra.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    libboost-system1.83.0 \
    zlib1g \
    libqt6core6t64 \
    libqt6network6 \
    libqt6xml6 \
    libqt6sql6 \
    libqt6sql6-sqlite \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /src/qbt/build/qbittorrent-nox /usr/local/bin/qbittorrent-nox
# libtorrent shared library installed to /usr/local/lib (deterministic path,
# no multiarch suffix — see CMAKE_INSTALL_PREFIX note in the header).
COPY --from=builder /usr/local/lib/libtorrent-rasterbar.so* /usr/local/lib/

RUN ldconfig

ENTRYPOINT ["/usr/local/bin/qbittorrent-nox"]
