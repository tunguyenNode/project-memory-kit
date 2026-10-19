#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
UPSTREAM="${1:?Usage: bash run_checks.sh /path/to/click-git-checkout}"
PIN=2247b35ea1c47c727d7a06e51fa280e12a863ff6
WORK="$(mktemp -d)"
printf 'Retained test workspace: %s\n' "$WORK"
mkdir "$WORK/baseline" "$WORK/candidate"
git -C "$UPSTREAM" archive "$PIN" | tar -x -C "$WORK/baseline"
cp -R "$WORK/baseline/." "$WORK/candidate/"
cd "$WORK/candidate"
git apply --check "$HERE/feature.patch"
git apply "$HERE/feature.patch"
python3 -m venv "$WORK/venv"
PY="$WORK/venv/bin/python"
"$PY" -m pip install --index-url https://pypi.org/simple pytest==9.1.1
"$PY" -m pip install --index-url https://pypi.org/simple --no-deps -e .
export PYTHONPATH="$WORK/candidate/src" PYTHONDONTWRITEBYTECODE=1
"$PY" -m pytest tests/test_utils/test_format_filename.py -q
CLICK_BASELINE_ROOT="$WORK/baseline" "$PY" "$HERE/independent_feature_tests.py"
"$PY" -m pytest -q
