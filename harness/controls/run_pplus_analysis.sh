#!/bin/bash
# VERIFY: analyzer + evaluation of the P+ controls (re-runnable after harness fixes; run records are not recomputed).
S="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$S"
envs/tools/bin/python -I -B harness/analyze_full.py --runs logs/controls/pplus/runs --tasks logs/controls/pplus/tasks.json --models ctlplus \
  --out logs/controls/pplus/results --gen-dir logs/controls/pplus/generations --label 'oracle controls P+, not study data' \
  --targets E0a~E1,E0a~E2 --exposure none --no-sensitivities > logs/controls/pplus_analyze_console_2026-11-11.txt 2>&1
python3 -I -B harness/controls/pplus_eval.py --out logs/controls/pplus_eval_2026-11-11.md --json logs/controls/pplus_eval_2026-11-11.json
