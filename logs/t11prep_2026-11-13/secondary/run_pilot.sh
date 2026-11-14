#!/bin/bash
# Runs every secondary-analysis tool, one process at a time with nice 19, on the PILOT regression outputs and on the oracle/harm controls
# (logs/regression, logs/controls: "not study data"). Run from the study folder S:
#   bash logs/t11prep_2026-11-13/secondary/run_pilot.sh
# Outputs go to logs/t11prep_2026-11-13/secondary/out_pilot/<dataset>/ ; the console of every call to out_pilot/console_pilot.txt.
# Exit codes of the tools are recorded; a refusal (2) where one is expected is part of the test (B.16 on data without stratum R).
set -u
S="$PWD"
SC=logs/t11prep_2026-11-13/secondary
PY=envs/tools/bin/python
OUT=$SC/out_pilot
WI=$OUT/wiring_inputs
mkdir -p "$OUT"
LOG=$OUT/console_pilot.txt
: > "$LOG"
run() {  # run <dataset> <script> <args...>
  local ds="$1"; shift
  local script="$1"; shift
  echo "=== $ds : $script $*" >> "$LOG"
  nice -n 19 $PY -I -B "$SC/$script" "$@" >> "$LOG" 2>&1
  echo "--- exit $?" >> "$LOG"
}
common() {  # common <results dir> <tasks json> <label> <out dir>
  echo "--per-program $1/per_program.jsonl --summary $1/summary.json --tasks $2 --models-tsv models/models.tsv --test-label $3 --out $4"
}
# ---- dataset 1: pilot regression (480 programs, two pilot models, stratum A, pairs E0a~E1 and E0a~E2)
D=$OUT/regression; L="pilot regression, not study data"; R=logs/regression/results; T=logs/regression/inputs/tasks.json
printf '%s\n' "$L" > "$OUT/LABEL.txt"
mkdir -p "$D"; printf '%s\n' "$L" > "$D/LABEL.txt"
C="--per-program $R/per_program.jsonl --summary $R/summary.json --tasks $T --models-tsv models/models.tsv --out $D"
run regression sec_pair_rates.py --analysis all $C --test-label "$L"
run regression sec_design_splits.py --analysis all $C --test-label "$L"
run regression sec_model_level.py --analysis all $C --test-label "$L"
run regression sec_idioms.py $C --test-label "$L"
run regression sec_attribution.py --analysis B.30 $C --test-label "$L"
run regression sec_attribution.py --analysis B.31 --hand $WI/hand_attribution_synthetic.tsv $C --test-label "$L"
run regression sec_agreement.py --analysis B.32 --coder-a $WI/coder_a_synthetic.tsv --coder-b $WI/coder_b_synthetic.tsv --coder-b-kind model $C --test-label "$L"
run regression sec_agreement.py --analysis B.33 --coder-a $WI/coder_a_synthetic.tsv --coder-b $WI/coder_b_synthetic.tsv $C --test-label "$L"
run regression sec_agreement.py --analysis B.25 --resolved $WI/resolved_codes_synthetic.tsv $C --test-label "$L"
run regression sec_agreement.py --analysis B.22 --second-rating $WI/second_rating_synthetic.tsv $C --test-label "$L"
run regression sec_ablation.py --analysis B.17 --hint-per-program $WI/hint_arm_wiring_per_program.jsonl --sample-tasks $WI/sample_tasks_synthetic.tsv --ablation-models pilot_qwen35_9b $C --test-label "$L"
run regression sec_ablation.py --analysis B.16 --arm-per-program $WI/arm_default_effort_wiring_per_program.jsonl --arm-expected-programs 144 --arm-model pilot_sonnet55 --main-model pilot_sonnet55 $C --test-label "$L"
run regression sec_gee.py --analysis B.19 $C --test-label "$L"
run regression sec_gee.py --analysis B.20 $C --test-label "$L"
# ---- dataset 2: oracle control P+ (56 programs, stratum M, 41-row catalogue subset)
for ds in pplus pminus harm_wiring; do
  D=$OUT/controls_$ds; R=logs/controls/$ds/results; T=logs/controls/$ds/tasks.json
  L=$(python3 -I -B -c "import json,sys; print(json.load(open(sys.argv[1]))['label'])" $R/summary.json)
  mkdir -p "$D"; printf '%s\n' "$L" > "$D/LABEL.txt"
  C="--per-program $R/per_program.jsonl --summary $R/summary.json --tasks $T --models-tsv models/models.tsv --out $D"
  run controls_$ds sec_pair_rates.py --analysis all $C --test-label "$L"
  run controls_$ds sec_design_splits.py --analysis all $C --test-label "$L"
  run controls_$ds sec_model_level.py --analysis all $C --test-label "$L"
  run controls_$ds sec_idioms.py $C --test-label "$L"
  run controls_$ds sec_attribution.py --analysis B.30 $C --test-label "$L"
  run controls_$ds sec_gee.py --analysis B.19 $C --test-label "$L"
  run controls_$ds sec_gee.py --analysis B.20 $C --test-label "$L"
  if [ "$ds" = harm_wiring ]; then
    run controls_$ds sec_agreement.py --analysis B.33 --coder-a $WI/harm_wiring_coder_a_synthetic.tsv $C --test-label "$L"
  fi
done
echo "done" >> "$LOG"
