#!/bin/bash
# VERIFY (T6, step 4): analyzer over the regression records + comparison with the pilot. Re-runnable (run records are not recomputed).
S="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$S"
envs/tools/bin/python -I -B harness/analyze_full.py --runs logs/regression/runs --tasks logs/regression/inputs/tasks.json \
  --models pilot_qwen35_9b,pilot_sonnet55 --out logs/regression/results --gen-dir logs/regression/inputs/generations \
  --label 'pilot regression, not study data' --targets E0a~E1,E0a~E2 --exposure none > logs/regression/analyze_console_2026-11-11.txt 2>&1
python3 -I -B harness/controls/reg_compare.py
python3 -I -B harness/controls/reg_records.py
