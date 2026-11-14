#!/bin/bash
# Written 2026-11-11 by pkg:MECH_B. Runs MECH_B confirmation programs through the harness CLI (harness/run_programs.py).
# Usage (from anywhere): bash run_B.sh <attempt: a|b> <id> [<id> ...]
# Jobs file per id and attempt: runs/<id>/jobs_<attempt>.jsonl; out-root runs/<id>/ (resumable; existing records are skipped).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
S="$(cd "$HERE/../.." && pwd)"
ATT="$1"; shift
WORK="${MECH_B_WORK:?set MECH_B_WORK to a scratch directory}"
cd "$S"
for ID in "$@"; do
  if [ "$ATT" = a ]; then PID="confirm/$ID"; PROG="mechanisms/confirm/$ID.py"; CARD="mechanisms/confirm/$ID.card.json";
  else PID="confirm/${ID}_b"; PROG="mechanisms/confirm/${ID}_b.py"; CARD="mechanisms/confirm/${ID}_b.card.json"; fi
  mkdir -p "mechanisms/confirm/runs/$ID"
  printf '{"program_id": "%s", "program_path": "%s", "task_id": null, "card": "%s", "fixtures_root": "mechanisms/confirm/data/%s"}\n' \
    "$PID" "$PROG" "$CARD" "$ID" > "mechanisms/confirm/runs/$ID/jobs_$ATT.jsonl"
  python3 -I -B harness/run_programs.py --jobs "mechanisms/confirm/runs/$ID/jobs_$ATT.jsonl" \
    --configs E0a,E0b,E1,E2,E0pa,E3,E4 --out-root "mechanisms/confirm/runs/$ID" --work "$WORK" --workers 2 --compare \
    --mem-limit-gb 2 2>&1 | sed "s/^/[$ID $ATT] /"
done
