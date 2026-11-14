"""MECH_A summariser (pkg:MECH_A, 2026-11-11). Reads the harness records/comparisons under mechanisms/confirm/runs/<id>/
and writes one line per program attempt (TSV) plus a readable detail file. Standard library + harness modules only.
usage: python3 -I -B summarize_A.py OUT_PREFIX PROGRAM_ID [PROGRAM_ID ...]   (PROGRAM_ID like S01 or S01_b)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(S, 'harness'))
import run_programs, warndef  # noqa: E402

CONFIGS = ['E0a', 'E0b', 'E1', 'E2', 'E0pa', 'E3', 'E4']
PAIRS = ['E0a~E0b', 'E0a~E1', 'E0a~E2', 'E0pa~E3', 'E0pa~E4']
LOUD = {'error', 'timeout', 'cpu_limit', 'memory_limit', 'crash'}


def short(v, n=300):
    s = json.dumps(v, ensure_ascii=False, sort_keys=True)
    return s if len(s) <= n else s[:n] + '...'


def yn(b):
    return 'na' if b is None else ('yes' if b else 'no')


def main():
    out, pids = sys.argv[1], sys.argv[2:]
    rows, detail = [], []
    for p in pids:
        cid = p.split('_')[0]
        root = os.path.join(S, 'mechanisms', 'confirm', 'runs', cid)
        prog = 'confirm/' + p
        recs = {c: run_programs.load_record(root, c, prog) for c in CONFIGS}
        comps = {}
        for pr in PAIRS:
            f = os.path.join(root, 'compare', pr, prog + '.json')
            comps[pr] = json.load(open(f)) if os.path.exists(f) else None
        st = {c: (recs[c] or {}).get('status') for c in CONFIGS}
        w233 = warndef.warned_233(recs['E0a'], 'prereg') if recs['E0a'] else None
        w233p = warndef.warned_233(recs['E0a'], 'pilot') if recs['E0a'] else None
        w3x = any(bool(warndef.pandas_warnings(recs[c], 'prereg')) for c in ('E1', 'E2') if recs[c])
        w3xpa = any(bool(warndef.pandas_warnings(recs[c], 'prereg')) for c in ('E3', 'E4') if recs[c])
        cls = {pr: (comps[pr] or {}).get('class') for pr in PAIRS}
        drift = {pr: (comps[pr] or {}).get('drift') for pr in PAIRS}
        silent = {pr: (comps[pr] or {}).get('silent') for pr in PAIRS}
        mag = {pr: (comps[pr] or {}).get('magnitude') for pr in PAIRS}
        det = cls['E0a~E0b'] == 'IDENTICAL'
        row = {'program': p, 'det_E0a_E0b': yn(det)}
        for c in CONFIGS:
            row['st_' + c] = st[c] or 'NA'
        for pr in PAIRS:
            row['class_' + pr] = cls[pr] or ('NA' if comps[pr] is None else 'null')
            row['drift_' + pr] = yn(drift[pr])
            row['silent_' + pr] = yn(silent[pr])
            row['mag_' + pr] = mag[pr] or '-'
        row.update({'warn233_prereg': yn(w233), 'warn233_pilot': yn(w233p), 'warn3x_prereg': yn(w3x),
                    'warn3xpa_prereg': yn(w3xpa), 'loud_E1': yn(st['E1'] in LOUD), 'loud_E2': yn(st['E2'] in LOUD)})
        rows.append(row)
        detail.append('=' * 20 + ' ' + p)
        detail.append('statuses: ' + short(st))
        detail.append('classes: ' + short(cls) + ' magnitude: ' + short(mag))
        for c in CONFIGS:
            r = recs[c]
            if not r:
                continue
            ws = [w for w in (r.get('warnings') or []) if w.get('phase') == 'user']
            line = '%s %s' % (c, r.get('status'))
            if r.get('exc_type'):
                line += ' EXC %s: %s (line %s)' % (r.get('exc_type'), (r.get('exc_msg') or '')[:200], r.get('exc_user_line'))
            detail.append(line)
            for w in ws:
                detail.append('   W[%s|prereg=%s|pilot=%s] %s line %s: %s' % (
                    w.get('category_qualname'), warndef.is_pandas_warning(w, 'prereg'), warndef.is_pandas_warning(w, 'pilot'),
                    w.get('category_module'), w.get('user_line'), (w.get('message') or '')[:220].replace('\n', ' ')))
            if c in ('E0a', 'E1', 'E2', 'E0pa', 'E4') and r.get('status') == 'ok':
                detail.append('   result: ' + short(r.get('result'), 400))
                detail.append('   dtypes: ' + short(r.get('result_dt'), 200) + ' type ' + str(r.get('result_type')))
        for pr in PAIRS:
            if comps[pr] and comps[pr].get('first_diff'):
                detail.append('   first_diff %s: %s' % (pr, short(comps[pr]['first_diff'], 300)))
    keys = list(rows[0].keys())
    with open(out + '.tsv', 'w', encoding='utf-8') as f:
        f.write('\t'.join(keys) + '\n')
        for r in rows:
            f.write('\t'.join(str(r[k]) for k in keys) + '\n')
    with open(out + '.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(detail) + '\n')
    for r in rows:
        print(r['program'], 'det', r['det_E0a_E0b'], '| E1', r['class_E0a~E1'], '| E2', r['class_E0a~E2'], '| E3', r['class_E0pa~E3'],
              '| E4', r['class_E0pa~E4'], '| w233', r['warn233_prereg'], r['warn233_pilot'], '| w3x', r['warn3x_prereg'],
              '| silentE1', r['silent_E0a~E1'], '| st', r['st_E0a'], r['st_E1'], r['st_E2'])


if __name__ == '__main__':
    main()
