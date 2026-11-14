# Acceptance summary of package TASKS_M2 from script outputs only. Written 2026-11-11 by pkg:TASKS_M2. Standard library only:
#   python3 -I -B tasks/M2/tools/summary.py      -> tasks/M2/logs/acceptance.json (all numbers quoted in SUMMARY.md come from it)
import collections, csv, glob, json, os, re, time

TOOLS = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(TOOLS)
STUDY = os.path.dirname(os.path.dirname(PKG))
FAMS = ('QF5_ORDER', 'QF6_NA_DTYPE', 'QF7_INDEX_REDUCE', 'QF8_NUMERIC')


def main():
    tasks = {}
    for p in sorted(glob.glob(os.path.join(PKG, 'M_QF*', 'task.json'))):
        with open(p, encoding='utf-8') as f:
            t = json.load(f)
        tasks[t['id']] = t
    with open(os.path.join(STUDY, 'mechanisms', 'confirm', 'quota_allocation.tsv'), encoding='utf-8', newline='') as f:
        alloc = [r for r in csv.DictReader(f, delimiter='\t') if r['family'] in FAMS]
    quota = []
    for r in alloc:
        slots = [s for s in r['task_slots'].split(',') if s]
        got = [s for s in slots if s in tasks and tasks[s]['catalogue_row'] == r['row_id']]
        quota.append({'family': r['family'], 'row': r['row_id'], 'n_alloc': int(r['n_tasks']), 'n_tasks_on_row': len(got),
                      'exact': len(got) == len(slots) == int(r['n_tasks'])})
    slots_all = {s for r in alloc for s in r['task_slots'].split(',') if s}
    extra = sorted(set(tasks) - slots_all)
    with open(os.path.join(PKG, 'logs', 'check_results.json'), encoding='utf-8') as f:
        chk = {r['id']: r for r in json.load(f)['tasks']}
    fam = lambda tid: tasks[tid]['family']
    per_fam = collections.defaultdict(lambda: collections.Counter())
    for tid, r in chk.items():
        c = per_fam[fam(tid)]
        c['tasks'] += 1
        c['naive_ok'] += r['naive_ok']
        c['ref_ok'] += r['ref_ok']
        c['naive_silent_on_a_confirmed_target'] += any((r.get('naive_' + tg) or {}).get('silent') for tg in r['naive_drift_on_confirmed'])
        c['naive_warned_E0a_any_user_warning'] += r['naive_warned_E0a']
        c['prelabel_matches_prediction'] += r['prelabel_matches_prediction']
        c['pred_' + r['predicted']] += 1
        c['order_significant'] += r['order_significant']
        c['dtype_significant'] += r['dtype_significant']
        for tg in ('E1', 'E2'):
            cl = (r.get('naive_' + tg) or {}).get('class')
            c['naive_%s_%s' % (tg, cl)] += 1
    flags_ok = all(isinstance(t.get('order_significant'), bool) and isinstance(t.get('dtype_significant'), bool) for t in tasks.values())
    pred_ok = all((t.get('predicted_direction') or {}).get('direction') in ('HARM', 'FIX', 'BOTH') and
                  len((t.get('predicted_direction') or {}).get('reason') or '') >= 5 for t in tasks.values())
    prov_ok = all(t['drafted_by'] == 'pkg:TASKS_M2' and t['status'] == 'prepared'
                  for t in tasks.values())
    with open(os.path.join(PKG, 'logs', 'validate_M2.json'), encoding='utf-8') as f:
        val = json.load(f)
    with open(os.path.join(PKG, 'logs', 'lint_M2.txt'), encoding='utf-8') as f:
        lint_line = [ln for ln in f.read().splitlines() if ln.startswith('linted')][-1]
    with open(os.path.join(STUDY, 'mechanisms', 'catalogue.tsv'), encoding='utf-8', newline='') as f:
        silent_rows = [r['id'] for r in csv.DictReader(f, delimiter='\t') if r['scope'] == 'SILENT' and r['quota_family'] in FAMS]
    with open(os.path.join(PKG, 'exposure_regex_part.tsv'), encoding='utf-8') as f:
        lines = f.read().split('\n')
    hdr = lines[0].split('\t')
    rx = [dict(zip(hdr, ln.split('\t'))) for ln in lines[1:] if ln.strip()]
    rx_ids = [r['id'] for r in rx]

    def frac_full(s):
        a, b = s.split('/')
        return a == b
    blind = [p for p in glob.glob(os.path.join(STUDY, 'tasks', 'blind', 'M2', 'B*.json'))]
    with open(os.path.join(STUDY, 'tasks', 'blind_reveal', 'M2', 'm_invited.json'), encoding='utf-8') as f:
        reveal = json.load(f)
    prompts = glob.glob(os.path.join(PKG, 'prompts', 'M_QF*.txt'))
    out = {
        'written': time.strftime('%Y-%m-%d %H:%M %Z'),
        'n_tasks': len(tasks),
        'quota_rows': quota, 'quota_exact_all_rows': all(q['exact'] for q in quota), 'tasks_outside_slots': extra,
        'per_family': {k: dict(v) for k, v in sorted(per_fam.items())},
        'naive_ok': sum(r['naive_ok'] for r in chk.values()), 'ref_ok': sum(r['ref_ok'] for r in chk.values()),
        'ref_property_failures': sum(len(r['ref_property_failures']) for r in chk.values()),
        'prelabel_mismatches': sorted((tid, r['predicted'], r['naive_prelabel']) for tid, r in chk.items()
                                      if not r['prelabel_matches_prediction']),
        'flags_on_every_task': flags_ok, 'predicted_direction_on_every_task': pred_ok, 'provenance_ok': prov_ok,
        'validator': val, 'lint': lint_line, 'n_prompts': len(prompts),
        'exposure_rows': len(rx), 'exposure_rows_expected': len(silent_rows),
        'exposure_complete': sorted(rx_ids) == sorted(silent_rows),
        'exposure_all_naive_match': all(frac_full(r['matches_naive']) for r in rx),
        'exposure': {r['id']: {'naive': r['matches_naive'], 'reference': r['matches_reference']} for r in rx},
        'blind_files': len(blind), 'blind_reveal_entries': len(reveal.get('invited', {})),
    }
    with open(os.path.join(PKG, 'logs', 'acceptance.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ('quota_rows', 'exposure', 'per_family')}, indent=1))
    for k, v in out['per_family'].items():
        print(k, dict(sorted(v.items())))


if __name__ == '__main__':
    main()
