# Written 2026-11-11 by pkg:MECH_B (STAGE2 T2). Reads the harness outputs under mechanisms/confirm/runs/<id>/ (run records and
# compare files written by harness/run_programs.py --compare) and prints / writes per-attempt facts. No outcome is computed here
# that the harness did not compute: classes, drift, magnitude and warning flags are copied from the compare files; warning
# messages are copied from the run records.
# Usage (from the study folder): python3 -I -B mechanisms/confirm/summarize_B.py [--json OUT.json] [ids ...]
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(S, 'harness'))
import warndef  # noqa: E402

IDS = (['G0%d' % i for i in range(1, 9)] + ['R0%d' % i for i in range(1, 8)] + ['N0%d' % i for i in range(1, 8)]
       + ['I0%d' % i for i in range(1, 7)] + ['X01', 'X02'])
PAIRS = ['E0a~E0b', 'E0a~E1', 'E0a~E2', 'E0pa~E3', 'E0pa~E4']


def rec(cid, cfg, pid):
    p = os.path.join(HERE, 'runs', cid, cfg, 'confirm', pid + '.json.gz')
    if not os.path.exists(p):
        return None
    with gzip.open(p, 'rt', encoding='utf-8') as f:
        return json.load(f)


def cmp_(cid, pair, pid):
    p = os.path.join(HERE, 'runs', cid, 'compare', pair, 'confirm', pid + '.json')
    if not os.path.exists(p):
        return None
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def user_warnings(r, definition):
    out = []
    for w in (r or {}).get('warnings', []):
        if w.get('phase') != 'user':
            continue
        if warndef.is_pandas_warning(w, definition):
            out.append('%s: %s' % (w.get('category_qualname'), (w.get('message') or '')[:160].replace('\n', ' ').replace('\t', ' ')))
    return out


def attempt(cid, att):
    pid = cid if att == 'a' else cid + '_b'
    if not os.path.exists(os.path.join(HERE, pid + '.py')):
        return None
    out = {'id': cid, 'attempt': att, 'program': pid + '.py'}
    for cfg in ['E0a', 'E0b', 'E1', 'E2', 'E0pa', 'E3', 'E4']:
        r = rec(cid, cfg, pid)
        out['status_' + cfg] = r.get('status') if r else 'MISSING'
        if r and r.get('status') not in ('ok', 'no_result'):
            out['err_' + cfg] = ('%s: %s' % (r.get('exc_type'), r.get('exc_msg') or ''))[:200].replace('\n', ' ').replace('\t', ' ')
        out['max_rss_mb_' + cfg] = round((r or {}).get('max_rss_bytes', 0) / 2 ** 20, 1) if r and r.get('max_rss_bytes') else None
    e0a = rec(cid, 'E0a', pid)
    out['warn_E0a_prereg'] = user_warnings(e0a, 'prereg')
    out['warn_E0a_pilot'] = user_warnings(e0a, 'pilot')
    for cfg in ['E1', 'E2', 'E3', 'E4']:
        out['warn_%s_prereg' % cfg] = user_warnings(rec(cid, cfg, pid), 'prereg')
    for pair in PAIRS:
        c = cmp_(cid, pair, pid)
        if c is None:
            out[pair] = None
            continue
        out[pair] = {k: c.get(k) for k in ('class', 'class_pilot_rule', 'drift', 'magnitude', 'silent', 'silent_all_magnitudes',
                                            'warned_E0a', 'warned_target', 'first_diff', 'excluded', 'run_problem', 'order_note',
                                            'baseline_status', 'target_status')}
    return out


def main(argv):
    js = None
    if '--json' in argv:
        i = argv.index('--json')
        js = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    ids = argv or IDS
    allres = []
    for cid in ids:
        for att in ('a', 'b'):
            a = attempt(cid, att)
            if a is None:
                continue
            allres.append(a)
            if js:
                continue
            print('==', cid, att, ' '.join('%s=%s' % (c, a['status_' + c]) for c in ['E0a', 'E0b', 'E1', 'E2', 'E0pa', 'E3', 'E4']))
            for pair in PAIRS:
                c = a[pair]
                if c:
                    print('   %-8s %-12s pilot_rule=%-12s mag=%s silent=%s warnT=%s fd=%s %s' % (
                        pair, c['class'], c['class_pilot_rule'], c['magnitude'], c['silent'], c['warned_target'],
                        json.dumps(c['first_diff'], default=str)[:140], c.get('excluded') or ''))
            print('   warnE0a prereg:', a['warn_E0a_prereg'][:3])
            if a['warn_E0a_pilot'] != a['warn_E0a_prereg']:
                print('   warnE0a pilot :', a['warn_E0a_pilot'][:3])
            for cfg in ['E1', 'E2']:
                if a['warn_%s_prereg' % cfg]:
                    print('   warn%s:' % cfg, a['warn_%s_prereg' % cfg][:2])
            for cfg in ['E0a', 'E1', 'E2', 'E3', 'E4']:
                if a.get('err_' + cfg):
                    print('   err%s:' % cfg, a['err_' + cfg])
    if js:
        with open(js, 'w', encoding='utf-8') as f:
            json.dump(allres, f, indent=1, sort_keys=True, default=str)
            f.write('\n')


if __name__ == '__main__':
    main(sys.argv[1:])
