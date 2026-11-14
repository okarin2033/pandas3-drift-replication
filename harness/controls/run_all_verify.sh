#!/bin/bash
# VERIFY: complete, resumable run of the oracle controls and the pilot regression with the final harness.
# Written 2026-11-11 by pkg:VERIFY. Usage (from anywhere): VERIFY_WORK=<scratch dir> harness/controls/run_all_verify.sh
# Needs no network, no key, no LLM. At most 2 workers, 2 GB per run. Re-running skips finished records.
set -u
S="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$S"
WORK="${VERIFY_WORK:?set VERIFY_WORK to a scratch directory}"
mkdir -p "$WORK/w"
RP="python3 -I -B -u harness/run_programs.py --work $WORK/w --workers 2 --mem-limit-gb 2"
CFG=E0a,E0b,E1,E2,A1,A2,A3,A4
echo "== P- controls"
python3 -I -B harness/controls/make_pminus.py && python3 -I -B harness/controls/pminus_build.py
$RP --jobs logs/controls/pminus/jobs.jsonl --configs E0a,E0b,E1,E2 --out-root logs/controls/pminus/runs > logs/controls/pminus_run_console_2026-11-11.txt 2>&1
envs/tools/bin/python -I -B harness/analyze_full.py --runs logs/controls/pminus/runs --tasks logs/controls/pminus/tasks.json --models ctlminus \
  --out logs/controls/pminus/results --gen-dir logs/controls/pminus/generations --label 'oracle controls P-, not study data' \
  --targets E0a~E1,E0a~E2 --exposure none --no-sensitivities > logs/controls/pminus_analyze_console_2026-11-11.txt 2>&1
python3 -I -B harness/controls/pminus_eval.py --out logs/controls/pminus_eval_2026-11-11.md --json logs/controls/pminus_eval_2026-11-11.json
echo "== P+ controls"
python3 -I -B harness/controls/pplus_build.py
$RP --jobs logs/controls/pplus/jobs.jsonl --configs $CFG --out-root logs/controls/pplus/runs --trace-drift --trace-e2 > logs/controls/pplus_run_console_2026-11-11.txt 2>&1
harness/controls/run_pplus_analysis.sh
echo "== harm pre-label wiring"
python3 -I -B harness/controls/harm_wiring.py
$RP --jobs logs/controls/harm_wiring/jobs.jsonl --configs $CFG --out-root logs/controls/harm_wiring/runs --trace-drift --trace-e2 > logs/controls/harm_wiring_run_console_2026-11-11.txt 2>&1
envs/tools/bin/python -I -B harness/analyze_full.py --runs logs/controls/harm_wiring/runs --tasks logs/controls/harm_wiring/tasks.json --models ctlharm \
  --out logs/controls/harm_wiring/results --gen-dir logs/controls/harm_wiring/generations --label 'harm wiring, not study data' \
  --targets E0a~E1,E0a~E2 --exposure none --no-sensitivities > logs/controls/harm_wiring_analyze_console_2026-11-11.txt 2>&1
python3 -I -B harness/controls/harm_wiring.py --eval > logs/controls/harm_wiring_eval_2026-11-11.txt
echo "== pilot regression (T6)"
python3 -I -B harness/controls/make_regression_inputs.py
$RP --jobs logs/regression/inputs/jobs.jsonl --configs E0a,E0b,E1,E2 --out-root logs/regression/runs > logs/regression/stage1_console_2026-11-11.txt 2>&1
python3 -I -B harness/controls/reg_select_drift.py
$RP --jobs logs/regression/inputs/jobs_drift.jsonl --configs $CFG --out-root logs/regression/runs --trace-drift --trace-e2 > logs/regression/stage2_console_2026-11-11.txt 2>&1
harness/controls/run_regression_analysis.sh
python3 -I -B harness/controls/reg_extra.py > logs/regression/extra_facts.txt
python3 -I -B harness/controls/make_regression_report.py
python3 -I -B harness/controls/disk_rss.py > logs/controls/disk_rss_2026-11-11.txt
echo "done"
