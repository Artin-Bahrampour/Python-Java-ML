#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
rm -rf "$ROOT/build"
mkdir -p "$ROOT/build/classes"
find "$ROOT/src/main/java" -name '*.java' -print0 | xargs -0 javac --release 21 -Xlint:all -d "$ROOT/build/classes"
echo "Build completed: $ROOT/build/classes"
