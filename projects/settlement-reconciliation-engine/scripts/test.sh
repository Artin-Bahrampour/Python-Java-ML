#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$ROOT/scripts/build.sh"
mkdir -p "$ROOT/build/test-classes"
find "$ROOT/src/test/java" -name '*.java' -print0 | xargs -0 javac --release 21 -cp "$ROOT/build/classes" -d "$ROOT/build/test-classes"
java -ea -cp "$ROOT/build/classes:$ROOT/build/test-classes" com.artin.reconciliation.TestRunner
