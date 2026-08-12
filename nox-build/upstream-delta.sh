#!/bin/sh
# Reading aid: show what changed upstream between two tags, over the paths this
# fork's modifications touch or depend on.
#
# This GATES NOTHING. It does not substitute for the drift test, which is what
# actually stops a merge — run
#   UPSTREAM_TAG=<new-tag> python3 -m unittest discover -s nox-build/tests
# for that. This exists so a human can see, in one screen, whether upstream has
# moved the code the deletions target before reading the full diff.
#
# Usage: bash nox-build/upstream-delta.sh <old-tag> <new-tag>

set -eu

if [ $# -ne 2 ]; then
    echo "usage: $0 <old-tag> <new-tag>" >&2
    exit 2
fi

# Resolve against the repository this script lives in, not the caller's working
# directory. Without this, running it from another checkout diffs THAT
# repository's refs and reports a confident answer about the wrong tree -- or
# fails with "bad revision" on tags that exist here.
cd "$(dirname "$0")/.."

git diff --stat "$1".."$2" -- src/webui/ src/base/ CMakeLists.txt src/webui/CMakeLists.txt
