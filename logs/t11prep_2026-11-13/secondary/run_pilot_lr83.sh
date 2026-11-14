#!/bin/bash
# LR83 revision of run_pilot_lr83.sh (B.22 with the pairs table; X-5 from the controls of record; X-7 provider of the main run); LR82 revision of run_pilot.sh: runs every secondary-analysis tool, one process at a time with nice 19, on the PILOT regression outputs and
# on the oracle/harm controls (logs/regression, logs/controls: "not study data"), with --B 10000 --seed 20261111 written out in every
# call (LR82.2 item 8, S-9). Run from the study folder S:
#   bash logs/t11prep_2026-11-13/secondary/run_pilot_lr83.sh
# Outputs: logs/t11prep_2026-11-13/secondary/out_pilot_lr83/<dataset>/ ; console of every call in out_pilot_lr83/console_pilot.txt.
# Exit codes are recorded; a refusal (2) where one is expected is part of the test (B.16 on data without stratum R).
set -u
SC=logs/t11prep_2026-11-13/secondary
PY=envs/tools/bin/python
OUT=$SC/out_pilot_lr83
WI=$OUT/wiring_inputs
BS="--B 10000 --seed 20261111"
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
mkdir -p "$WI"
echo "=== wiring inputs : make_wiring_inputs.py" >> "$LOG"
nice -n 19 python3 -I -B "$SC/make_wiring_inputs.py" "$PWD" "$WI" >> "$LOG" 2>&1
echo "--- exit $?" >> "$LOG"
# ---- dataset 1: pilot regression (480 programs, two pilot models, stratum A, pairs E0a~E1 and E0a~E2)
D=$OUT/regression; L="pilot regression, not study data"; R=logs/regression/results; T=logs/regression/inputs/tasks.json
printf '%s\n' "$L" > "$OUT/LABEL.txt"
mkdir -p "$D"; printf '%s\n' "$L" > "$D/LABEL.txt"
C="--per-program $R/per_program.jsonl --summary $R/summary.json --tasks $T --models-tsv models/models.tsv --out $D $BS"
run regression sec_pair_rates.py --analysis all $C --test-label "$L"
run regression sec_runrecords.py --analysis all --runs logs/regression/runs $C --test-label "$L"
run regression sec_design_splits.py --analysis all $C --test-label "$L"
run regression sec_model_level.py --analysis all $C --test-label "$L"
run regression sec_idioms.py $C --test-label "$L"
run regression sec_idioms_text.py --gen-dir logs/regression/inputs/generations $C --test-label "$L"
run regression sec_attribution.py --analysis B.30 $C --test-label "$L"
run regression sec_attribution.py --analysis B.31 --hand $WI/hand_attribution_synthetic.tsv $C --test-label "$L"
run regression sec_agreement.py --analysis B.32 --coder-a $WI/coder_a_synthetic.tsv --coder-b $WI/coder_b_synthetic.tsv --coder-b-kind model $C --test-label "$L"
run regression sec_agreement.py --analysis B.33 --coder-a $WI/coder_a_synthetic.tsv --coder-b $WI/coder_b_synthetic.tsv $C --test-label "$L"
run regression sec_agreement.py --analysis B.25 --resolved $WI/resolved_codes_synthetic.tsv $C --test-label "$L"
run regression sec_agreement.py --analysis B.22 --second-rating $WI/second_rating_synthetic.tsv --pairs-table $WI/second_rating_pairs_synthetic.tsv $C --test-label "$L"
run regression sec_ablation.py --analysis B.17 --hint-per-program $WI/hint_arm_wiring_per_program.jsonl --sample-tasks $WI/sample_tasks_synthetic.tsv --ablation-models pilot_qwen35_9b $C --test-label "$L"
run regression sec_ablation.py --analysis B.16 --arm-per-program $WI/arm_default_effort_wiring_per_program.jsonl --arm-expected-programs 144 --arm-model pilot_sonnet55 --main-model pilot_sonnet55 $C --test-label "$L"
run regression sec_gee.py --analysis B.19 $C --test-label "$L"
run regression sec_gee.py --analysis B.20 $C --test-label "$L"
run regression sec_sens_rates.py --runs logs/regression/runs --gen-dir logs/regression/inputs/generations --exposure none --oracle-pre-lr1 $WI/oracle_copy_synthetic.py --oracle-pre-lr1-seal $WI/oracle_copy_synthetic.sha256 --flags-before $WI/flags_synthetic.tsv --flags-before-lr2-3 $WI/flags23_synthetic.tsv $C --test-label "$L"
run regression sec_process_report.py --gen-dir logs/regression/inputs/generations --run-start 2026-11-12T20:51:18Z --planned 240 $C --test-label "$L"
# item 12: resolution sheet and resolved-codes file on SYNTHETIC coder files (wiring only), then the frozen reader of --codes
echo "=== regression : sec_resolution.py sheet / resolve (synthetic wiring inputs)" >> "$LOG"
nice -n 19 $PY -I -B "$SC/sec_resolution.py" sheet --coder-a $WI/coder_a_res_synthetic.tsv --coder-b $WI/coder_b_res_synthetic.tsv --coder-b-answers $WI/coder_b_answers_synthetic.jsonl --out $D/resolution >> "$LOG" 2>&1; echo "--- exit $?" >> "$LOG"
nice -n 19 $PY -I -B "$SC/sec_resolution.py" resolve --coder-a $WI/coder_a_res_synthetic.tsv --coder-b $WI/coder_b_res_synthetic.tsv --answers $WI/resolution_answers_synthetic.csv --key $WI/sheet_key_synthetic.json --out $D/resolution >> "$LOG" 2>&1; echo "--- exit $?" >> "$LOG"
echo "=== regression : analyze_full.read_codes on the resolved file" >> "$LOG"
nice -n 19 $PY -I -B -c "
import sys; sys.dont_write_bytecode = True; sys.path.insert(0, 'harness')
import analyze_full as af
c = af.read_codes('$D/resolution/codes_resolved.tsv'); print('read_codes: %d rows read, first %s' % (len(c), sorted(c.items())[0]))" >> "$LOG" 2>&1; echo "--- exit $?" >> "$LOG"
# static tables (registered texts, control evaluations; no per_program input)
SD=$OUT/static; mkdir -p "$SD"
run static sec_static_tables.py x1 --amendment2 FULL_PREREG_AMENDMENT_2.md --freeze-parameters logs/t8_2026-11-13/FREEZE_PARAMETERS.md --out $SD
run static sec_static_tables.py x7 --amendment13 FULL_PREREG_AMENDMENT_13.md --amendment14 FULL_PREREG_AMENDMENT_14.md --out $SD
run static sec_static_tables.py x5 --pplus logs/t8apply_2026-11-13/runs/pplus_eval.json --pminus logs/t8apply_2026-11-13/runs/pminus_eval.json --lr16 logs/t8apply_2026-11-13/runs/lr16_eval.json --harm-wiring logs/controls/harm_wiring_eval_2026-11-11.txt --first-pplus logs/controls/pplus_eval_2026-11-11.json --first-pminus logs/controls/pminus_eval_2026-11-11.json --out $SD
# ---- datasets 2 to 4: oracle controls P+, P-, harm wiring
for ds in pplus pminus harm_wiring; do
  D=$OUT/controls_$ds; R=logs/controls/$ds/results; T=logs/controls/$ds/tasks.json
  L=$(python3 -I -B -c "import json,sys; print(json.load(open(sys.argv[1]))['label'])" $R/summary.json)
  mkdir -p "$D"; printf '%s\n' "$L" > "$D/LABEL.txt"
  C="--per-program $R/per_program.jsonl --summary $R/summary.json --tasks $T --models-tsv models/models.tsv --out $D $BS"
  run controls_$ds sec_pair_rates.py --analysis all $C --test-label "$L"
  run controls_$ds sec_runrecords.py --analysis all --runs logs/controls/$ds/runs $C --test-label "$L"
  run controls_$ds sec_design_splits.py --analysis all $C --test-label "$L"
  run controls_$ds sec_model_level.py --analysis all $C --test-label "$L"
  run controls_$ds sec_idioms.py $C --test-label "$L"
  run controls_$ds sec_idioms_text.py --gen-dir logs/controls/$ds/generations $C --test-label "$L"
  run controls_$ds sec_attribution.py --analysis B.30 $C --test-label "$L"
  run controls_$ds sec_gee.py --analysis B.19 $C --test-label "$L"
  run controls_$ds sec_gee.py --analysis B.20 $C --test-label "$L"
  if [ "$ds" = harm_wiring ]; then
    run controls_$ds sec_agreement.py --analysis B.33 --coder-a $WI/harm_wiring_coder_a_synthetic.tsv $C --test-label "$L"
  fi
done
echo "done" >> "$LOG"
