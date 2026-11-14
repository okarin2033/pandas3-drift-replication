# VERIFY (T6): program-by-program comparison of the new harness (E0a/E0b/E1/E2 + A1-A4 + traces) with the pilot's results/per_program.jsonl.
# Written 2026-11-11 by pkg:VERIFY. Standard library only (host side); the pilot folder is read, never written.
# Run: python3 -I -B harness/controls/reg_compare.py [--analysis logs/regression/results] [--runs logs/regression/runs]
# Writes logs/regression/comparison_E1.tsv, comparison_E2.tsv, differences.tsv, attribution_comparison.tsv, regression_counts.json.
#
# Three class columns per program and target (pilot vocabulary: EXCL_FAIL EXCL_NONDET LOUD SILENT_DRIFT WARNED_DRIFT ORDER_ONLY
# WARNING_ONLY DTYPE_ONLY IDENTICAL):
#   pilot            the pilot's cls_E1 / cls_E2 from pilots/r3/results/per_program.jsonl
#   new_pilotdef     the NEW records classified with the PILOT definitions (pilot warning definition, pilot order/dtype rule, unflagged
#                    card). Like-with-like: a difference to `pilot` can only come from the harness, the hash seed of E0b or the environment.
#   new_study        the NEW records classified with the pre-registered definitions (section 3 warning definition; unflagged cards, so
#                    order/dtype never drift); magnitude and primary silent flag reported separately.
import argparse, collections, gzip, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.dirname(os.path.dirname(HERE))
P = os.path.join(os.path.dirname(os.path.dirname(S)), 'pilots', 'r3')
sys.path.insert(0, os.path.join(S, 'harness'))
import oracle, run_programs, warndef  # noqa: E402

PAIRS = {'E1': ('E0a', 'E1'), 'E2': ('E0a', 'E2')}


def style(recs, tgt, wdef):
    """Pilot-vocabulary class of one program on one target; wdef = 'pilot' | 'prereg' warning definition."""
    e0a, e0b, t = recs.get('E0a'), recs.get('E0b'), recs.get(tgt)
    excl, _ = oracle.baseline_exclusion(e0a, e0b)
    if excl:
        return excl
    if t is None:
        return 'MISSING'
    c = oracle.compare(e0a, t, None)                      # unflagged card: order and dtype never drift
    if c.get('run_problem'):
        return 'HARNESS'
    if c['class'] == 'LOUD':
        return 'LOUD'
    cp = c['class_pilot_rule']
    pw_t = warndef.pandas_warnings(t, wdef)
    if cp in ('VALUE_DRIFT', 'NO_RESULT'):
        return 'WARNED_DRIFT' if pw_t else 'SILENT_DRIFT'
    if cp == 'ORDER_ONLY':
        return 'ORDER_ONLY'
    if {warndef.warning_signature(w) for w in pw_t} - {warndef.warning_signature(w) for w in warndef.pandas_warnings(e0a, wdef)}:
        return 'WARNING_ONLY'
    return cp


def wdesc(w):
    return '%s: %s' % (w.get('category_qualname'), (w.get('message') or '')[:70].replace('\t', ' ').replace('\n', ' '))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--analysis', default=os.path.join(S, 'logs', 'regression', 'results'))
    ap.add_argument('--runs', default=os.path.join(S, 'logs', 'regression', 'runs'))
    ap.add_argument('--out', default=os.path.join(S, 'logs', 'regression'))
    a = ap.parse_args()
    pilot = {}
    for ln in open(os.path.join(P, 'results', 'per_program.jsonl'), encoding='utf-8'):
        d = json.loads(ln)
        pilot[(d['model'], d['prog'])] = d
    newpp = {}
    for ln in open(os.path.join(a.analysis, 'per_program.jsonl'), encoding='utf-8'):
        d = json.loads(ln)
        newpp[d['program_id']] = d
    lab_map = {}
    for ln in open(os.path.join(S, 'harness', 'pilot_label_map.tsv'), encoding='utf-8'):
        if ln.startswith('#') or not ln.strip() or ln.startswith('pilot_label'):
            continue
        f = ln.rstrip('\n').split('\t')
        lab_map[f[0]] = (set(f[1].split(';')), f[2])
    rows, diffs, attr_rows = [], [], []
    counts = collections.Counter()
    for (model, prog), pd_ in sorted(pilot.items()):
        pid = 'gen/pilot_%s/%s' % (model, prog)
        recs = run_programs.load_program_records(a.runs, pid, ['E0a', 'E0b', 'E1', 'E2'])
        npp = newpp.get(pid)
        for tname, (b, tg) in PAIRS.items():
            pc = pd_.get('cls_' + tname)
            npd = style(recs, tg, 'pilot')
            nst = style(recs, tg, 'prereg')
            blk = ((npp or {}).get('targets') or {}).get('E0a~' + tg) or {}
            excl = (npp or {}).get('exclusion')
            cause0 = cause1 = ''
            if pc != npd:
                if npd == 'EXCL_NONDET' and pc != 'EXCL_NONDET':
                    cause0 = 'E0b hash seed (PYTHONHASHSEED=1 in E0b, 0 in the pilot)'
                else:
                    cause0 = 'UNEXPLAINED'
            if npd != nst:
                pw_pilot = {wdesc(w) for w in warndef.pandas_warnings(recs.get(tg), 'pilot')} | {wdesc(w) for w in warndef.pandas_warnings(recs.get('E0a'), 'pilot')}
                pw_pre = {wdesc(w) for w in warndef.pandas_warnings(recs.get(tg), 'prereg')} | {wdesc(w) for w in warndef.pandas_warnings(recs.get('E0a'), 'prereg')}
                gone = sorted(pw_pilot - pw_pre)
                cause1 = 'warning definition section 3 vs pilot: %s' % ('; '.join(gone) if gone else 'UNEXPLAINED (no warning differs)')
            row = {'program_id': pid, 'target': tname, 'pilot': pc, 'new_pilotdef': npd, 'new_study': nst,
                   'study_class_oracle': blk.get('class'), 'magnitude': blk.get('magnitude'), 'silent_primary': blk.get('silent'),
                   'cause_pilotdef_vs_pilot': cause0, 'cause_study_vs_pilotdef': cause1}
            rows.append(row)
            counts['programs_%s' % tname] += 1
            if pc == npd:
                counts['same_pilotdef_%s' % tname] += 1
            if pc == nst:
                counts['same_study_%s' % tname] += 1
            if pc != nst:
                diffs.append(row)
            # attribution (drift programs on this target in the pilot or in the new harness)
            lab = pd_.get('mech_' + tname) or None
            nlabs = blk.get('labels') or []
            if (pc in ('SILENT_DRIFT', 'WARNED_DRIFT')) or blk.get('drift'):
                comps = [x for x in (lab or '').replace('|', '+').split('+') if x]
                ok_ids = set().union(*[lab_map[c][0] for c in comps if c in lab_map]) if comps else set()
                fams = {lab_map[c][1] for c in comps if c in lab_map}
                prim = blk.get('primary_label')
                famof = None
                try:
                    import attribution
                    famof = attribution.family_of(prim)
                except Exception:
                    pass
                agree_prim = bool(prim in ok_ids or famof in fams)
                agree_any = bool(set(nlabs) & ok_ids or {attribution.family_of(x) for x in nlabs} & fams) if nlabs else False
                attr_rows.append({'program_id': pid, 'target': tname, 'pilot_cls': pc, 'new_pilotdef': npd, 'pilot_label': lab, 'new_primary': prim,
                                  'new_labels': ','.join(nlabs), 'step': blk.get('attribution_step'), 'truncated': blk.get('trace_truncated'),
                                  'agree_primary': agree_prim, 'agree_any_label': agree_any,
                                  'has_T2': ('T2' in recs) or None})
    os.makedirs(a.out, exist_ok=True)
    keys = list(rows[0].keys())
    for tname in PAIRS:
        with open(os.path.join(a.out, 'comparison_%s.tsv' % tname), 'w', encoding='utf-8') as f:
            f.write('\t'.join(keys) + '\n')
            for r in rows:
                if r['target'] == tname:
                    f.write('\t'.join(str(r[k]) if r[k] is not None else '' for k in keys) + '\n')
    with open(os.path.join(a.out, 'differences.tsv'), 'w', encoding='utf-8') as f:
        f.write('\t'.join(keys) + '\n')
        for r in diffs:
            f.write('\t'.join(str(r[k]) if r[k] is not None else '' for k in keys) + '\n')
    if attr_rows:
        ak = list(attr_rows[0].keys())
        with open(os.path.join(a.out, 'attribution_comparison.tsv'), 'w', encoding='utf-8') as f:
            f.write('\t'.join(ak) + '\n')
            for r in attr_rows:
                f.write('\t'.join(str(r[k]) if r[k] is not None else '' for k in ak) + '\n')
    cm = {}
    for tname in PAIRS:
        cm[tname] = {'pilot_vs_new_pilotdef': collections.Counter((r['pilot'], r['new_pilotdef']) for r in rows if r['target'] == tname and r['pilot'] != r['new_pilotdef']),
                     'pilot_vs_new_study': collections.Counter((r['pilot'], r['new_study']) for r in rows if r['target'] == tname and r['pilot'] != r['new_study']),
                     'class_counts_pilot': collections.Counter(r['pilot'] for r in rows if r['target'] == tname),
                     'class_counts_new_pilotdef': collections.Counter(r['new_pilotdef'] for r in rows if r['target'] == tname),
                     'class_counts_new_study': collections.Counter(r['new_study'] for r in rows if r['target'] == tname)}
    def enc(o):
        if isinstance(o, collections.Counter):
            return {'%s -> %s' % k if isinstance(k, tuple) else str(k): v for k, v in o.items()}
        return o
    out = {'counts': dict(counts), 'matrices': {t: {k: enc(v) for k, v in d.items()} for t, d in cm.items()}}
    with open(os.path.join(a.out, 'regression_counts.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out['counts']))
    for t in PAIRS:
        print(t, 'pilot vs new_pilotdef differences:', dict(out['matrices'][t]['pilot_vs_new_pilotdef']))
        print(t, 'pilot vs new_study differences:', dict(out['matrices'][t]['pilot_vs_new_study']))
    unexpl = [r for r in rows if 'UNEXPLAINED' in (r['cause_pilotdef_vs_pilot'] + r['cause_study_vs_pilotdef'])]
    print('UNEXPLAINED rows:', len(unexpl))
    return 0


if __name__ == '__main__':
    sys.exit(main())
