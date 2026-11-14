#!/bin/bash
# Re-run naive (E0a,E0b,E1,E2) and reference (E0a,E0b,E0pa,E1,E2,E3,E4) of the given task ids with --force, then re-check.
# Written 2026-11-11 by pkg:TASKS_M1. Usage: tasks/M1/tools/rerun.sh WORKDIR ID [ID ...]
set -e
M1="$(cd "$(dirname "$0")/.." && pwd)"; S="$(cd "$M1/../.." && pwd)"; WORK="$1"; shift
cd "$S"
pat=$(printf '"%s"|' "$@"); pat="${pat%|}"
grep -E "\"task_id\": ($pat)" tasks/M1/runs/jobs_naive.jsonl > "$WORK/jobs_naive_sub.jsonl"
grep -E "\"task_id\": ($pat)" tasks/M1/runs/jobs_ref.jsonl > "$WORK/jobs_ref_sub.jsonl"
python3 -I -B harness/run_programs.py --jobs "$WORK/jobs_naive_sub.jsonl" --configs E0a,E0b,E1,E2 --out-root tasks/M1/runs/naive --work "$WORK/work" --workers 2 --mem-limit-gb 2 --compare --force | tail -2
python3 -I -B harness/run_programs.py --jobs "$WORK/jobs_ref_sub.jsonl" --configs E0a,E0b,E0pa,E1,E2,E3,E4 --out-root tasks/M1/runs/ref --work "$WORK/work" --workers 2 --mem-limit-gb 2 --compare --force | tail -2
