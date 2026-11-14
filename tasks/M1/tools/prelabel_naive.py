# Information only (not an acceptance item, not used to change any prediction): automatic harm pre-label (section 10.2,
# harness/harm_prelabel.py) of each naive solution's E0a vs E1 results against the task's reference (E0a run), next to the
# predicted direction that was written before any run. Used to look for reference or card bugs.
# Written 2026-11-11 by pkg:TASKS_M1.  python3 -I -B tasks/M1/tools/prelabel_naive.py -> tasks/M1/logs/naive_prelabel.tsv
import csv, json, os, sys
TOOLS = os.path.dirname(os.path.abspath(__file__)); M1 = os.path.dirname(TOOLS); STUDY = os.path.dirname(os.path.dirname(M1))
sys.path.insert(0, os.path.join(STUDY, 'harness'))
import run_programs, harm_prelabel  # noqa: E402
MAP = {'HARM_3X': 'HARM', 'FIX_3X': 'FIX', 'BOTH_ACCEPTABLE': 'BOTH'}
rows = []
for tid in sorted(d for d in os.listdir(M1) if d.startswith('M_QF')):
    task = json.load(open(os.path.join(M1, tid, 'task.json'), encoding='utf-8'))
    ref = run_programs.load_record(os.path.join(M1, 'runs', 'ref'), 'E0a', 'ref/' + tid)
    a = run_programs.load_record(os.path.join(M1, 'runs', 'naive'), 'E0a', 'naive/' + tid)
    b = run_programs.load_record(os.path.join(M1, 'runs', 'naive'), 'E1', 'naive/' + tid)
    pl = harm_prelabel.harm_prelabel(a, b, ref, task)
    pred = task['predicted_direction']['direction']
    rows.append({'task': tid, 'predicted': pred, 'prelabel_E1': pl['label'],
                 'agree': 'yes' if MAP.get(pl['label']) == pred else 'no',
                 'detail': json.dumps(pl.get('failed'), ensure_ascii=False, default=str)[:400]})
with open(os.path.join(M1, 'logs', 'naive_prelabel.tsv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t', lineterminator='\n'); w.writeheader(); w.writerows(rows)
print('agree %d/%d' % (sum(r['agree'] == 'yes' for r in rows), len(rows)))
for r in rows:
    if r['agree'] == 'no':
        print(r['task'], r['predicted'], r['prelabel_E1'], r['detail'][:300])
