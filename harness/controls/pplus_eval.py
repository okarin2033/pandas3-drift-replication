# VERIFY (T5.11, P+): evaluate the positive controls from the analyzer output (per_program.jsonl) and the run records.
# Written 2026-11-11 by pkg:VERIFY. Standard library only (host side). Run:
#   python3 -I -B harness/controls/pplus_eval.py [--results logs/controls/pplus/results] [--runs logs/controls/pplus/runs] [--out logs/controls/pplus_eval_<date>.md]
# Pass rule (FULL_PREREG section 9, STAGE2 T5.11): for every CONFIRMED row, its deciding program must be value drift on each target
# for which the status file says drift (E1 always, E2 where drift_E2 = yes), and the row's own catalogue id must be among the
# attribution labels (primary label reported). For L rows (LOUD_CONFIRMED): class LOUD on E1 and E2 (never drift) and the L id among the
# labels of attribution.attribute (analyze_full.py attributes drift programs only, by design; LOUD is attributed here directly).
import argparse, collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(S, 'harness'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', default=os.path.join(S, 'logs', 'controls', 'pplus', 'results'))
    ap.add_argument('--runs', default=os.path.join(S, 'logs', 'controls', 'pplus', 'runs'))
    ap.add_argument('--expect', default=os.path.join(S, 'logs', 'controls', 'pplus', 'pplus_expect.json'))
    ap.add_argument('--out', default=None)
    ap.add_argument('--json', default=None)
    a = ap.parse_args()
    import attribution, run_programs
    expect = json.load(open(a.expect))
    pp = {}
    for ln in open(os.path.join(a.results, 'per_program.jsonl'), encoding='utf-8'):
        r = json.loads(ln)
        pp[r['task_id']] = r
    rows, fails = [], []
    for tid in sorted(expect):
        e = expect[tid]
        r = pp.get(tid)
        pid = 'gen/ctlplus/%s__s0' % tid
        base = {'tid': tid, 'row': e['row'], 'attempt': e['attempt'], 'deciding': e['deciding'], 'status': e['status']}
        if r is None:
            rows.append(dict(base, pair='-', ok=False, why='no per_program line')); fails.append(tid)
            continue
        loud_row = e['status'] == 'LOUD_CONFIRMED'
        pairs = []
        if loud_row:
            pairs = ['E0a~E1', 'E0a~E2']
        else:
            if e['status_drift_E1'] == 'yes': pairs.append('E0a~E1')
            if e['status_drift_E2'] == 'yes': pairs.append('E0a~E2')
        for pair in (pairs if (e['deciding'] or e.get('supplementary')) else ['E0a~E1', 'E0a~E2']):
            t = r['targets'].get(pair)
            rec = dict(base, pair=pair, scored=bool(e['deciding'] and pair in pairs), clean=r['clean_on_233'],
                       cls=(t or {}).get('class'), drift=(t or {}).get('drift'), mag=(t or {}).get('magnitude'),
                       silent=(t or {}).get('silent'), warned=((t or {}).get('warned_target') or {}).get('prereg'))
            ok, why = True, []
            if not r['clean_on_233']:
                ok = False; why.append('not clean on 2.3.3: %s' % r.get('exclusion_detail'))
            if t is None:
                ok = False; why.append('no target block')
            elif loud_row:
                if t['class'] != 'LOUD': ok = False; why.append('class %s, expected LOUD' % t['class'])
                if t['drift']: ok = False; why.append('LOUD counted as drift')
                tgt = pair.split('~')[1]
                recs = run_programs.load_program_records(a.runs, pid, ['E0a', tgt])
                att = attribution.attribute({'program_id': pid, 'source': open(os.path.join(S, 'logs', 'controls', 'pplus', 'generations', 'ctlplus', tid + '__s0.py')).read()},
                                            recs, None, None, tgt)
                rec.update(labels=att['labels'], primary=att['primary'], step=att['step'])
            else:
                if not t['drift']: ok = False; why.append('class %s is not drift' % t['class'])
                rec.update(labels=t.get('labels'), primary=t.get('primary_label'), step=t.get('attribution_step'),
                           trunc=t.get('trace_truncated'))
            if ok and e['row'] not in (rec.get('labels') or []):
                ok = False; why.append('own id %s not in labels %s' % (e['row'], rec.get('labels')))
            rec['supplementary'] = bool(e.get('supplementary'))
            rec['ok'] = ok if (rec['scored'] or rec['supplementary']) else None
            rec['why'] = '; '.join(why)
            rows.append(rec)
            if rec['scored'] and not ok:
                fails.append('%s/%s' % (tid, pair))
    scored = [x for x in rows if x.get('scored')]
    n_ok = sum(1 for x in scored if x['ok'])
    rows_ids = sorted({x['row'] for x in scored})
    row_ok = {rid: all(x['ok'] for x in scored if x['row'] == rid) for rid in rows_ids}
    prim_own = sum(1 for x in scored if x.get('primary') == x['row'])
    L = []
    L.append('# P+ evaluation (positive controls)')
    L.append('')
    L.append('Generated by harness/controls/pplus_eval.py from %s' % os.path.relpath(a.results, S))
    L.append('')
    L.append('Scored checks (deciding program x target with drift/LOUD in the status file): %d, passed %d (%.1f%%). Rows covered: %d, rows with every check passed: %d.'
             % (len(scored), n_ok, 100.0 * n_ok / max(1, len(scored)), len(rows_ids), sum(row_ok.values())))
    L.append('Primary label equals the own id for %d of %d scored checks (the requirement is: own id among the labels).' % (prim_own, len(scored)))
    L.append('')
    L.append('| program | row | pair | scored | class | drift | magnitude | silent | clean | labels | primary | step | ok | note |')
    L.append('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    for x in rows:
        L.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
            x['tid'], x['row'], x['pair'], 'yes' if x.get('scored') else 'info', x.get('cls'), x.get('drift'), x.get('mag'), x.get('silent'),
            x.get('clean'), ' '.join(x.get('labels') or []), x.get('primary'), x.get('step'), x.get('ok'), x.get('why', '')))
    text = '\n'.join(L) + '\n'
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(text)
    if a.json:
        json.dump({'scored': len(scored), 'passed': n_ok, 'fails': fails, 'rows': rows}, open(a.json, 'w'), indent=1)
    print(text.split('\n\n')[2] if False else '\n'.join(L[:6]))
    print('FAILS: %s' % (fails or 'none'))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
