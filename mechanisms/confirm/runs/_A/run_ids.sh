#!/bin/bash
# MECH_A driver (2026-11-11): runs each confirm program through the harness CLI into runs/<id>/ (resumable).
# usage: run_ids.sh JOBS.jsonl   (run from anywhere)
set -u
S="$(cd "$(dirname "$0")/../../../.." && pwd)"
JOBS="$1"
WORK="${MECH_A_WORK:-/tmp/mech_a_work}"
CONFIGS="E0a,E0b,E1,E2,E0pa,E3,E4"
cd "$S"
while IFS= read -r line; do
  pid=$(printf '%s' "$line" | python3 -I -c 'import json,sys; print(json.loads(sys.stdin.read())["program_id"])')
  id=${pid#confirm/}; id=${id%_b}
  one="$WORK/jobs_$(basename "$pid").jsonl"; mkdir -p "$WORK"; printf '%s\n' "$line" > "$one"
  python3 -I -B harness/run_programs.py --jobs "$one" --configs "$CONFIGS" --out-root "mechanisms/confirm/runs/$id" \
     --work "$WORK/w" --workers 2 --mem-limit-gb 2 --compare 2>&1 | tail -3 | sed "s|^|[$pid] |"
done < "$JOBS"
