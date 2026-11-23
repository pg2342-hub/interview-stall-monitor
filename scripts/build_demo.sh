#!/usr/bin/env bash
# Rebuild the GitHub Pages demo in docs/: the sample weekly report and the gate report.
set -euo pipefail
cd "$(dirname "$0")/.."
python scripts/make_sample.py
python scripts/build_pages.py
(cd evals && PYTHONPATH=.. golive run golive.yml --out ../docs/gate)
rm -f docs/gate/results.json
python scripts/demo_chrome.py docs/index.html docs/gate/index.html --repo interview-stall-monitor
