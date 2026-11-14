# Attribution family of the secondary analyses: B.30 (attribution shares per target) and B.31 (hand attribution agreement).
# Written 2026-11-13 in the T11 preparation step. Status: draft; decides nothing.
#
# B.30 (11 l.465-466): per target (E0a~E1 and E0a~E2 separately) the share of attributed drift programs whose primary label is l, the
# share carrying l among their labels, and the number of drift programs with a truncated trace; pooled (program-weighted) and per model.
# B.31 (11 l.467-468; STAGE2 T12.5): the hand primary label on the double-coded sample against the automatic primary label of E0a~E1.
#   python3 -I -B sec_attribution.py --analysis B.30 ...
#   python3 -I -B sec_attribution.py --analysis B.31 --hand harm/hand_attribution.tsv ...
import argparse
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sec_common as C  # noqa: E402

B30_PAIRS = ('E0a~E1', 'E0a~E2')
# C-18 default: both denominators side by side. 'any' = every attributed drift program (the analyzer attributes when drift is true,
# any magnitude); 'substantive' = SUBSTANTIVE drift only.
B30_DENOMINATORS = ('any', 'substantive')
B31_PAIR = 'E0a~E1'
B31_LABEL_SEPARATORS = r'[;,|]'      # separators of the `labels` column of harm/hand_attribution.tsv (C-19; format not registered)
NO_LABEL = '(no primary label)'


def drift_programs(per_program, pair, models, denominator):
    out = []
    for p in per_program:
        if p['model'] not in models:
            continue
        kind, t = C.pair_status(p, pair)
        if kind != 'CLEAN' or not t.get('drift'):
            continue
        if denominator == 'substantive' and t.get('magnitude') != 'SUBSTANTIVE':
            continue
        out.append((p, t))
    return out


def b30_core(inp):
    stats = inp.stats
    rows, trunc = [], []
    for pair in B30_PAIRS:
        for den in B30_DENOMINATORS:
            dp = drift_programs(inp.per_program, pair, set(inp.models), den)
            # LR82.2 item 8 (S-7): the pooled shares per stratum stand beside the pooled ones (scope `stratum M`, `stratum R`, `stratum A`)
            scopes = ([('pooled', dp)] + [('stratum ' + st, [(p, t) for p, t in dp if p['stratum'] == st]) for st in C.STRATA]
                      + [(m, [(p, t) for p, t in dp if p['model'] == m]) for m in inp.models])
            for scope, sub in scopes:
                n = len(sub)
                prim = collections.Counter((t.get('primary_label') or NO_LABEL) for p, t in sub)
                comp = collections.Counter(l for p, t in sub for l in set(t.get('labels') or []))
                for kind, cnt in (('primary', prim), ('component', comp)):
                    for lab in sorted(cnt):
                        pr, lo, hi = C.wilson(stats, cnt[lab], n)
                        rows.append({'pair': pair, 'denominator': den, 'scope': scope, 'kind': kind, 'label': lab, 'count': cnt[lab],
                                     'n_drift': n, 'share': pr, 'wilson_lo': lo, 'wilson_hi': hi})
                t_true = sum(1 for p, t in sub if t.get('trace_truncated') is True)
                t_none = sum(1 for p, t in sub if t.get('trace_truncated') is None)
                trunc.append({'pair': pair, 'denominator': den, 'scope': scope, 'n_drift': n, 'trace_truncated': t_true,
                              'trace_truncated_unknown': t_none})
    return [dict(r, table='share') for r in rows] + [dict(r, table='trunc') for r in trunc]


def b30(inp, tool, outdir):
    allr, mr = C.row_variants(inp, b30_core)
    rows = [r for r in allr if r['table'] == 'share']
    trunc = [r for r in allr if r['table'] == 'trunc']
    cols = ['variant', 'pair', 'denominator', 'scope', 'kind', 'label', 'count', 'n_drift', 'share', 'wilson_lo', 'wilson_hi']
    meta = C.meta_block(inp, tool, ['B.30'], {'pairs': list(B30_PAIRS), 'denominators': list(B30_DENOMINATORS), 'lr61': mr})
    md = C.header_md(inp, 'B.30', 'Attribution shares per target', meta,
                     'Denominators (C-18): any = every pair-clean drift program, substantive = SUBSTANTIVE drift only. Primary-label and '
                     'component-label shares; component shares do not sum to 1 (multi-label). Wilson 95% (program level).')
    md += ['', 'Pooled shares (program-weighted):', '', C.md_table(cols, [r for r in rows if r['scope'] == 'pooled'], 120), '',
           'Drift programs with a truncated trace:', '', C.md_table(['variant', 'pair', 'denominator', 'scope', 'n_drift', 'trace_truncated',
                                                                   'trace_truncated_unknown'], [t for t in trunc if t['scope'] == 'pooled']),
           '', 'Per-model shares: TSV.']
    return C.emit(outdir, 'B.30', inp, meta, md, [('shares', cols, rows), ('truncated', ['variant', 'pair', 'denominator', 'scope', 'n_drift', 'trace_truncated', 'trace_truncated_unknown'], trunc)],
                  {'item': 'B.30', 'shares': rows, 'truncated_traces': trunc, 'lr61_without_ruled': mr})


def read_hand(path):
    rows = C.read_tsv(path)
    out = {}
    for r in rows:
        pid = r['program_id']
        if pid in out:
            raise C.Refuse('hand attribution file: duplicate program_id %s' % pid)
        labs = [x.strip() for x in re.split(B31_LABEL_SEPARATORS, r.get('labels') or '') if x.strip()]
        out[pid] = {'primary': (r.get('primary_label') or '').strip() or None, 'labels': labs}
    return out


def b31(inp, tool, outdir, hand_path):
    stats = inp.stats
    hand = read_hand(hand_path)
    by_id = {p['program_id']: p for p in inp.per_program}
    unmatched = sorted(pid for pid in hand if pid not in by_id)

    def core(sub):
        sub_by = {p['program_id']: p for p in sub.per_program}
        items, not_drift = [], []
        comp_a_in_h = comp_h_in_a = 0
        for pid, h in sorted(hand.items()):
            p = sub_by.get(pid)
            if p is None:
                continue
            kind, t = C.pair_status(p, B31_PAIR)
            if kind != 'CLEAN' or not t.get('drift'):
                not_drift.append(pid)
                continue
            a = t.get('primary_label') or NO_LABEL
            hlab = h['primary'] or NO_LABEL
            fam = C.family_code(p.get('family')) if p['stratum'] == 'M' else None
            items.append((p['task_id'], p['stratum'], fam, hlab, a))
            comp_a_in_h += 1 if a in h['labels'] or a == hlab else 0
            comp_h_in_a += 1 if hlab in (t.get('labels') or []) or hlab == a else 0
        n = len(items)
        agree = sum(1 for it in items if it[3] == it[4])
        pr, lo, hi = C.wilson(stats, agree, n)
        res = {'n_items': n, 'raw_agreement': pr, 'agree': agree, 'wilson_lo': lo, 'wilson_hi': hi,
               'items_not_pair_clean_drift': len(not_drift), 'hand_ids_not_in_per_program': len(unmatched),
               'auto_primary_among_hand_labels': comp_a_in_h, 'hand_primary_among_auto_labels': comp_h_in_a}
        if n:
            cats = sorted({it[3] for it in items} | {it[4] for it in items})
            kb = C.stratified_agreement(sub, items, cats, stat_kinds=('kappa',))['kappa']       # rule (iii): stratified task-cluster bootstrap
            res.update({'kappa': kb['estimate'], 'kappa_lo': kb['lo'], 'kappa_hi': kb['hi'], 'kappa_dropped': kb['dropped']})
        return [res]
    rows, mr = C.row_variants(inp, core)
    res = rows[0]
    wo = [r for r in rows if r['variant'] != 'all tasks']
    meta = C.meta_block(inp, tool, ['B.31'], {'pair': B31_PAIR, 'hand_file_sha256': C.sha256_file(hand_path), 'lr61': mr})
    cols = ['variant', 'n_items', 'agree', 'raw_agreement', 'wilson_lo', 'wilson_hi', 'kappa', 'kappa_lo', 'kappa_hi', 'kappa_dropped',
            'items_not_pair_clean_drift', 'hand_ids_not_in_per_program']
    md = C.header_md(inp, 'B.31', 'Hand attribution against the automatic primary label (E0a~E1)', meta,
                     'Raw agreement with Wilson (the registered word is "agreement"), Cohen\'s kappa beside it with the stratified task-cluster '
                     'bootstrap (rule (iii)). The second row leaves out the programs of the ruled R tasks (LR61/LR70, rule (vi)).')
    md += ['', C.md_table(cols, rows)]
    return C.emit(outdir, 'B.31', inp, meta, md, [('agreement', cols, rows)],
                  {'item': 'B.31', 'result': res, 'result_without_ruled': wo[0] if wo else None, 'unmatched_ids': unmatched,
                   'lr61_without_ruled': mr})


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--analysis', required=True, help='B.30 or B.31')
    C.add_common_args(ap)
    ap.add_argument('--ruled-path', default=None)
    ap.add_argument('--hand', default=None, help='B.31: harm/hand_attribution.tsv (program_id, primary_label, labels)')
    a = ap.parse_args(argv)
    if a.analysis not in ('B.30', 'B.31'):
        raise C.Refuse('unknown analysis %r' % a.analysis)
    if a.analysis == 'B.31' and not a.hand:
        raise C.Refuse('B.31 needs --hand')
    inp = C.load_inputs(a, {'hand_attribution.tsv': a.hand} if a.hand else None)
    C.self_check(inp)
    tool = os.path.abspath(__file__)
    base = b30(inp, tool, a.out) if a.analysis == 'B.30' else b31(inp, tool, a.out, a.hand)
    print('wrote', os.path.basename(base) + '.{json,md,tsv}')
    return 0


if __name__ == '__main__':
    sys.exit(C.run_main(main))
