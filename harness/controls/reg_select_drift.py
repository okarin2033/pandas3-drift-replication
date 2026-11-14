# VERIFY (T6): choose the regression programs that drift on E0a~E1 or E0a~E2 (new oracle, unflagged cards) -> jobs_drift.jsonl for A1-A4 and traces.
# Written 2026-11-11 by pkg:VERIFY. Run: python3 -I -B harness/controls/reg_select_drift.py
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(S, 'harness'))
import oracle, run_programs
RUNS = os.path.join(S, 'logs', 'regression', 'runs')
jobs = [json.loads(l) for l in open(os.path.join(S, 'logs', 'regression', 'inputs', 'jobs.jsonl'))]
sel = []
for j in jobs:
    recs = run_programs.load_program_records(RUNS, j['program_id'], ['E0a', 'E0b', 'E1', 'E2'])
    cls = oracle.classify_program(recs, None, pairs=[('E0a', 'E1'), ('E0a', 'E2')])
    if cls['clean_on_233'] and any(t['drift'] for t in cls['targets'].values()):
        sel.append(j)
with open(os.path.join(S, 'logs', 'regression', 'inputs', 'jobs_drift.jsonl'), 'w') as f:
    for j in sel:
        f.write(json.dumps(j) + '\n')
print('drift programs (E1 or E2, clean on 2.3.3):', len(sel), 'of', len(jobs))
