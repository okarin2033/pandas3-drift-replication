# Acceptance summary of package TASKS_M1 -> tasks/M1/SUMMARY.md. Every number is computed here from files under the study
# folder or from the output of the harness scripts run as subprocesses (validator, lint, render check, regex build).
# Written 2026-11-11 by pkg:TASKS_M1.   python3 -I -B tasks/M1/tools/summarize.py
import collections, csv, json, os, subprocess, sys, time

TOOLS = os.path.dirname(os.path.abspath(__file__))
M1 = os.path.dirname(TOOLS)
STUDY = os.path.dirname(os.path.dirname(M1))
FAMS = ['QF1_STRING', 'QF2_DATETIME', 'QF3_COW', 'QF4_GROUPBY']


def tsv(p):
    with open(p, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE))


def run(args):
    r = subprocess.run([sys.executable, '-I', '-B'] + args, cwd=STUDY, capture_output=True, text=True)
    lines = [ln for ln in (r.stdout + r.stderr).strip().split('\n') if ln.strip()]
    return r.returncode, lines[-1] if lines else ''


def main():
    now = time.strftime('%Y-%m-%d %H:%M %Z')
    tasks = {}
    for tid in sorted(d for d in os.listdir(M1) if d.startswith('M_QF')):
        with open(os.path.join(M1, tid, 'task.json'), encoding='utf-8') as f:
            tasks[tid] = json.load(f)
    quota = tsv(os.path.join(STUDY, 'mechanisms', 'confirm', 'quota_allocation.tsv'))
    status = {r['id']: r for r in tsv(os.path.join(STUDY, 'mechanisms', 'confirm', 'status.tsv'))}
    naive = {r['task']: r for r in tsv(os.path.join(M1, 'logs', 'naive_check.tsv'))}
    ref = {r['task']: r for r in tsv(os.path.join(M1, 'logs', 'ref_check.tsv'))}
    pre = {r['task']: r for r in tsv(os.path.join(M1, 'logs', 'naive_prelabel.tsv'))}
    rx = tsv(os.path.join(M1, 'exposure_regex_part.tsv'))
    checks = {
        'validator': run(['harness/validate_tasks.py', '--pkg', 'M1']),
        'lint (task.json rendering)': run(['harness/lint_prompts.py', '--pkg', 'M1']),
        'render --check (staged prompt files)': run(['harness/render_prompts.py', '--pkg', 'M1', '--check']),
        'exposure regex build/test': run(['tasks/M1/tools/build_regex.py']),
    }
    L = []
    L.append('# TASKS_M1 summary: stratum-M tasks for QF1_STRING, QF2_DATETIME, QF3_COW, QF4_GROUPBY')
    L.append('')
    L.append('Written %s by pkg:TASKS_M1 (`tasks/M1/tools/summarize.py`; every number below is computed by that script from the '
             'files named in each section). All items are drafted_by pkg:TASKS_M1, status: prepared'
             '. No paid call, no network, no key file and no git were used.' % now)
    L.append('')
    # ---- quota
    L.append('## 1. Quota per family and row (`mechanisms/confirm/quota_allocation.tsv` vs `tasks/M1/*/task.json`)')
    L.append('')
    L.append('| family | row | slots allocated | tasks built (catalogue_row) | ids match | status (status.tsv) |')
    L.append('|---|---|---|---|---|---|')
    all_ok = True
    fam_count = collections.Counter()
    for q in quota:
        if q['family'] not in FAMS:
            continue
        slots = [s for s in q['task_slots'].split(',') if s]
        built = sorted(t for t, d in tasks.items() if d['catalogue_row'] == q['row_id'])
        ok = sorted(slots) == built
        all_ok &= ok
        fam_count[q['family']] += len(built)
        L.append('| %s | %s | %s | %d | %s | %s |' % (q['family'], q['row_id'], q['n_tasks'], len(built), 'yes' if ok else 'NO',
                                                  status.get(q['row_id'], {}).get('status', '?')))
    L.append('')
    L.append('Tasks per family: ' + ', '.join('%s %d' % (f, fam_count[f]) for f in FAMS) + '; total %d. Exact quota: **%s**.'
             % (len(tasks), 'PASS' if all_ok and all(fam_count[f] == 16 for f in FAMS) else 'FAIL'))
    L.append('')
    # ---- naive
    npass = sum(r['pass'] == 'PASS' for r in naive.values())
    e1 = collections.Counter(r['E1'].split('/')[0] for r in naive.values())
    sil = sum(r['E1'].endswith('/silent') for r in naive.values())
    warned = sum(r['E1'].endswith('/warned') for r in naive.values())
    L.append('## 2. Naive solutions (section 4.4a; `logs/naive_check.tsv`, runs in `runs/naive/`)')
    L.append('')
    L.append('Run with `harness/run_programs.py` on E0a, E0b, E1, E2 (F-main, 2 workers, `--mem-limit-gb 2`). Pass = clean on '
             '2.3.3 (E0a ok, E0a~E0b IDENTICAL) and value drift on a target where the row was confirmed.')
    L.append('')
    L.append('- PASS: **%d/%d** (%s).' % (npass, len(naive), 'PASS' if npass == len(naive) else 'FAIL'))
    L.append('- E0a~E1 classes: %s; drift with magnitude SUBSTANTIVE and no pandas warning on E1 (silent): %d; drift with a pandas '
             'warning on E1: %d.' % (', '.join('%s %d' % kv for kv in sorted(e1.items())), sil, warned))
    L.append('- Naive solutions with a pandas Future/Deprecation warning on E0a (2.3.3): %d.'
             % sum(r['warned_E0a'] == 'True' for r in naive.values()))
    L.append('')
    # ---- references
    rpass = sum(r['pass'] == 'PASS' for r in ref.values())
    cls = collections.Counter()
    for r in ref.values():
        for c in ('E0a~E0pa', 'E0a~E1', 'E0a~E2', 'E0a~E3', 'E0a~E4'):
            cls[r[c]] += 1
    L.append('## 3. References (section 10.1, STAGE2 T4.5; `logs/ref_check.tsv`, runs in `runs/ref/`)')
    L.append('')
    L.append('Run on E0a, E0b, E0pa, E1, E2, E3, E4; each of E0pa, E1, E2, E3, E4 compared with E0a by `oracle.compare` under the '
             'task card; E0a~E0b must be IDENTICAL; every property check of the card evaluated with `harm_prelabel.check_properties` '
             'on all six results.')
    L.append('')
    L.append('- PASS: **%d/%d** (%s).' % (rpass, len(ref), 'PASS' if rpass == len(ref) else 'FAIL'))
    L.append('- Classes over the 5 x %d comparisons: %s.' % (len(ref), ', '.join('%s %d' % kv for kv in sorted(cls.items()))))
    L.append('')
    # ---- cards
    flags = sum(isinstance(d['order_significant'], bool) and isinstance(d['dtype_significant'], bool) for d in tasks.values())
    dirs = collections.Counter(d['predicted_direction']['direction'] for d in tasks.values() if d.get('predicted_direction'))
    osig = sum(d['order_significant'] for d in tasks.values())
    dsig = sum(d['dtype_significant'] for d in tasks.values())
    L.append('## 4. Cards (section 10.1)')
    L.append('')
    L.append('- Tasks with both flags set: %d/%d (order_significant true: %d, dtype_significant true: %d).'
             % (flags, len(tasks), osig, dsig))
    L.append('- Tasks with a predicted direction: %d/%d (%s); written in `tools/spec_qf*.py` before any run.'
             % (sum(1 for d in tasks.values() if d.get('predicted_direction')), len(tasks),
                ', '.join('%s %d' % kv for kv in sorted(dirs.items()))))
    L.append('- Property checks per task (generic 2 + task-specific): min %d, max %d.'
             % (min(len(d['property_checks']) for d in tasks.values()), max(len(d['property_checks']) for d in tasks.values())))
    agree = sum(r['agree'] == 'yes' for r in pre.values())
    L.append('- Information only (not an acceptance item; no prediction was changed): the automatic pre-label (section 10.2) of '
             'each naive E0a/E1 pair against its reference equals the predicted direction for %d/%d tasks (`logs/naive_prelabel.tsv`); '
             'the others are cases whose acceptable variants (timestamp precision, alias spelling, extra columns) the automatic '
             'comparator cannot express.' % (agree, len(pre)))
    L.append('')
    # ---- regex
    rows_inv = [r for r in rx if not r['matches_naive'].endswith('/0')]
    full = all(r['matches_naive'].split('/')[0] == r['matches_naive'].split('/')[1] for r in rx)
    L.append('## 5. Exposure regexes (section 4.4c; `exposure_regex_part.tsv`, `logs/regex_check.tsv`)')
    L.append('')
    L.append('- Rows: %d (every SILENT catalogue row of the four families, confirmed or not); rows invited by at least one M1 task: '
             '%d; every naive solution of an inviting task matched: **%s**.' % (len(rx), len(rows_inv), 'PASS' if full else 'FAIL'))
    L.append('- References matched by their row\'s regex: ' + (', '.join('%s %s' % (r['id'], r['matches_reference'])
                                                                       for r in rx if not r['matches_reference'].startswith('0/'))
                                                            or 'none') + ' (all other rows 0).')
    L.append('')
    L.append('| id | family | naive matched | references matched |')
    L.append('|---|---|---|---|')
    for r in rx:
        L.append('| %s | %s | %s | %s |' % (r['id'], r['family'], r['matches_naive'], r['matches_reference']))
    L.append('')
    # ---- tool checks
    L.append('## 6. Validator, lint, prompts, blind export (script output, last line)')
    L.append('')
    for k, (rc, last) in checks.items():
        L.append('- %s: exit %d, `%s`' % (k, rc, last.replace(STUDY + '/', '').replace('`', "'")))
    nb = len([f for f in os.listdir(os.path.join(STUDY, 'tasks', 'blind', 'M1')) if f.endswith('.json')])
    L.append('- `harness/export_blind.py --pkg M1`: %d blind files in `tasks/blind/M1/`, `tasks/blind_reveal/M1/m_invited.json`, '
             '`tasks/_private/blind_map_M1.json`.' % nb)
    L.append('- Prompt files in `tasks/M1/prompts/`: %d.' % len([f for f in os.listdir(os.path.join(M1, 'prompts')) if f.endswith('.txt')]))
    L.append('')
    # ---- per-task table
    L.append('## 7. Task list')
    L.append('')
    L.append('| task | row | file | order_sig | predicted | naive E1 | naive E2 | reference |')
    L.append('|---|---|---|---|---|---|---|---|')
    for t, d in tasks.items():
        L.append('| %s | %s | %s | %s | %s | %s | %s | %s |' % (
            t, d['catalogue_row'], ','.join(f['path'].split('/')[1] for f in d['files']),
            ('yes (' + ','.join(d['sort_keys']) + ')') if d['order_significant'] else 'no',
            d['predicted_direction']['direction'], naive[t]['E1'], naive[t]['E2'], ref[t]['pass']))
    L.append('')
    with open(os.path.join(M1, 'SUMMARY.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('wrote SUMMARY.md; quota %s, naive %d/%d, refs %d/%d, regex %s' % (all_ok, npass, len(naive), rpass, len(ref), full))
    for k, (rc, last) in checks.items():
        print(k, rc, last[-120:])


if __name__ == '__main__':
    main()
