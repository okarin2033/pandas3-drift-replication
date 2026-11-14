# Model-level family of the secondary analyses: B.11 (drift by capability tier), B.12 (drift by 2.3.3 clean rate), B.35 (H4 with
# model-equal weighting), B.36 (pilot warning definition for H3 and H4).
# Written 2026-11-13 in the T11 preparation step. Status: draft; decides nothing; none of these
# items carries a test (estimates with intervals only).
#   python3 -I -B sec_model_level.py --analysis B.11|B.12|B.35|B.36|all ...
import argparse
import collections
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sec_common as C  # noqa: E402

# ---- named constants (choices; CHOICES_AS_BUILT.md)
TIERS = collections.OrderedDict([                       # 4.1 l.135-137 (judgement tier, exploratory only)
    ('T-small-open', ['openai__gpt-oss-20b', 'qwen__qwen3.5-9b', 'qwen__qwen3.6-35b-a3b', 'google__gemma-4-31b-it']),
    ('T-large-open', ['deepseek__deepseek-v3.2']),
    ('T-small-closed', ['anthropic__claude-haiku-4.5', 'anthropic__claude-haiku-5.5', 'openai__gpt-5.4-mini']),
    ('T-frontier', ['openai__gpt-5.6-terra', 'anthropic__claude-sonnet-5.5']),
])
B11_PAIR, B11_STRATUM = 'E0a~E1', 'M'                   # I-7: model-equal mean over the tier's models, stratum M, E0a~E1, paired bootstrap
B12_CLEAN_DEFINITION = 'clean_on_233 / generated'       # I-8
B12_PAIR = 'E0a~E1'
B12_RANK_STATISTIC = False                              # C-9 default (a): table only
B35_PAIRS = ('E0a~E1', 'E0a~E2')
B35_ENTRY_RULE = 'at least one drift program in R+A'    # C-22 default
B36_PAIRS = ('E0a~E1', 'E0a~E2')
B36_EXTEND_TO_H3_H4 = True                              # C-23 default (b)


# ------------------------------------------------------------------------------------------------ B.11
def b11(inp, tool, outdir):
    stats = inp.stats
    rows = C.flat_rows(inp.per_program, B11_PAIR, inp.tmap, set(inp.models))
    rows = [r for r in rows if r['stratum'] == B11_STRATUM]
    out, notes = [], []
    stat, info = {}, {}
    for tier, members in TIERS.items():
        present = [m for m in members if m in inp.models]
        ent = [m for m in present if sum(r['clean'] for r in rows if r['model'] == m) > 0]
        info[tier] = {'tier_models': members, 'present': present, 'entering': ent}
        if len(present) < len(members):
            notes.append('%s: %d of %d tier models present in the data (%s absent)' % (
                tier, len(present), len(members), ', '.join(sorted(set(members) - set(present))) or '-'))
        if ent:
            stat[tier] = (lambda v, ent=ent: C._mean([v.ratio('silent', 'clean', model=m, stratum=B11_STRATUM) for m in ent]))
    res = {}
    if stat:
        res = stats.cluster_bootstrap_multi(rows, stat, ['silent', 'clean'], ('model', 'stratum', 'fam'), B=inp.B, seed=inp.seed,
                                            tasks=[t for t in inp.tasks_univ if t['stratum'] == B11_STRATUM])
    for tier, i in info.items():
        r = res.get(tier)
        per = {}
        for m in i['present']:
            sub = [x for x in rows if x['model'] == m]
            x, n = sum(z['silent'] for z in sub), sum(z['clean'] for z in sub)
            per[m] = {'x': x, 'n': n, 'rate': (x / n if n else None)}
        out.append({'pair': B11_PAIR, 'stratum': B11_STRATUM, 'tier': tier, 'models_in_tier': len(i['tier_models']),
                    'models_present': len(i['present']), 'models_entering': len(i['entering']),
                    'rate_model_equal': C.nn(r['estimate']) if r else None, 'boot_lo': C.nn(r['lo']) if r else None,
                    'boot_hi': C.nn(r['hi']) if r else None, 'boot_dropped': r['dropped'] if r else None,
                    'per_model': per})
    unassigned = sorted(set(inp.models) - {m for v in TIERS.values() for m in v})
    meta = C.meta_block(inp, tool, ['B.11'], {'pair': B11_PAIR, 'stratum': B11_STRATUM})
    cols = ['pair', 'stratum', 'tier', 'models_in_tier', 'models_present', 'models_entering', 'rate_model_equal', 'boot_lo', 'boot_hi',
            'boot_dropped']
    md = C.header_md(inp, 'B.11', 'Drift by capability tier (model-equal mean of the stratum-M silent rate)', meta,
                     'Tier lists from 4.1 l.135-137. No test.')
    md += ['', C.md_table(cols, out)]
    if notes or unassigned:
        md += ['', 'Notes: ' + '; '.join(notes + (['models in no tier: ' + ', '.join(unassigned)] if unassigned else []))]
    return C.emit(outdir, 'B.11', inp, meta, md, [('tiers', cols, out)],
                  {'item': 'B.11', 'tiers': out, 'notes': notes, 'models_in_no_tier': unassigned})


# ------------------------------------------------------------------------------------------------ B.12
def b12_core(inp, frozen=None):
    stats = inp.stats
    rows = []
    for m in inp.models:
        for s in list(C.STRATA) + ['ALL']:
            pp = [p for p in inp.per_program if p['model'] == m and (s == 'ALL' or p['stratum'] == s)]
            if not pp:
                continue
            gen = len(pp)
            clean = sum(1 for p in pp if p.get('clean_on_233'))
            fr = C.flat_rows(pp, B12_PAIR, inp.tmap)
            x, n = sum(r['silent'] for r in fr), sum(r['clean'] for r in fr)
            cp, clo, chi = C.wilson(stats, clean, gen)
            rp, rlo, rhi = C.wilson(stats, x, n)
            rows.append({'pair': B12_PAIR, 'model': m, 'stratum': s, 'generated': gen, 'clean_on_233': clean, 'clean_rate': cp,
                         'clean_wilson_lo': clo, 'clean_wilson_hi': chi, 'silent_x': x, 'silent_n': n, 'silent_rate': rp,
                         'silent_wilson_lo': rlo, 'silent_wilson_hi': rhi})
            if frozen is not None and s != 'ALL':       # LR82.2 item 8 (S-3): the cell as the frozen analyzer reports it
                rows[-1].update(C.frozen_rate_cell(frozen, B12_PAIR, m, s))
    return rows


def b12(inp, tool, outdir):
    rows, mr = C.row_variants(inp, lambda sub: b12_core(sub, inp if sub.per_program is inp.per_program else None),
                              keep=lambda r: r['stratum'] in ('R', 'ALL'))
    cols = ['variant', 'pair', 'model', 'stratum', 'generated', 'clean_on_233', 'clean_rate', 'clean_wilson_lo', 'clean_wilson_hi', 'silent_x',
            'silent_n', 'silent_rate', 'silent_wilson_lo', 'silent_wilson_hi'] + C.FROZEN_COLUMNS
    meta = C.meta_block(inp, tool, ['B.12'], {'clean_definition': B12_CLEAN_DEFINITION, 'rank_statistic': B12_RANK_STATISTIC, 'lr61': mr})
    md = C.header_md(inp, 'B.12', 'Drift rate next to the 2.3.3 clean rate (table only)', meta,
                     'clean rate = %s (I-8); C-9 default: table only, no rank statistic. Wilson intervals at the program level. The columns '
                     'frozen_* repeat the cell of summary.json (strata M, R, A; all tasks) as the frozen analyzer reports it (LR82.2 item 8).' % B12_CLEAN_DEFINITION)
    md += ['', C.md_table(cols, [r for r in rows], 80)]
    return C.emit(outdir, 'B.12', inp, meta, md, [('table', cols, rows)], {'item': 'B.12', 'rows': rows, 'lr61_without_ruled': mr})


# ------------------------------------------------------------------------------------------------ H4 / H3 helpers
def h4_models_stat(num, den, models, strata=('R', 'A')):
    def f(v):
        rs = []
        for m in models:
            d = v.sum(den, model=m, stratum=set(strata))
            if d == 0:
                return None
            rs.append(v.sum(num, model=m, stratum=set(strata)) / d)
        return sum(rs) / len(rs)
    return f


def h4_pooled_stat(num, den, strata=('R', 'A')):
    def f(v):
        d = v.sum(den, stratum=set(strata))
        return None if d == 0 else v.sum(num, stratum=set(strata)) / d
    return f


def _summ(r):
    return {'estimate': C.nn(r['estimate']), 'boot_lo': C.nn(r['lo']), 'boot_hi': C.nn(r['hi']), 'dropped': r['dropped'],
            'n_valid': r['n_valid']}


def _rr(logrr):
    if logrr is None or (isinstance(logrr, float) and math.isnan(logrr)):
        return None
    return math.inf if logrr > 700 else math.exp(logrr)


# ------------------------------------------------------------------------------------------------ B.35
def b35_core(inp, frozen=None):
    stats = inp.stats
    out = []
    for pair in B35_PAIRS:
        rows = [r for r in C.flat_rows(inp.per_program, pair, inp.tmap, set(inp.models)) if r['stratum'] in ('R', 'A')]
        ent = [m for m in inp.models if sum(r['drift'] for r in rows if r['model'] == m) > 0]
        per = {}
        for m in inp.models:
            sub = [r for r in rows if r['model'] == m]
            d, u = sum(r['drift'] for r in sub), sum(r['drift_unwarned'] for r in sub)
            per[m] = {'drift': d, 'drift_unwarned': u, 'share': (u / d if d else None), 'enters': m in ent}
        stat = {'pooled_program_weighted': h4_pooled_stat('drift_unwarned', 'drift')}
        if ent:
            stat['model_equal'] = h4_models_stat('drift_unwarned', 'drift', ent)
        res = stats.cluster_bootstrap_multi(rows, stat, ['drift', 'drift_unwarned'], ('model', 'stratum', 'fam'), B=inp.B, seed=inp.seed,
                                            tasks=[t for t in inp.tasks_univ if t['stratum'] in ('R', 'A')]) if rows else {}
        e = {'pair': pair, 'entering_models': ent, 'n_entering': len(ent), 'per_model': per}
        for k, r in res.items():
            e[k] = _summ(r)
        out.append(e)
    flat = []
    for e in out:
        for k in ('pooled_program_weighted', 'model_equal'):
            if k in e:
                row = dict(e[k], pair=e['pair'], estimator=k, n_entering=e['n_entering'], per_model=e['per_model'],
                           entering_models=e['entering_models'])
                if k == 'pooled_program_weighted' and frozen is not None:      # LR82.2 item 8 (S-3): the frozen H4 of this pair
                    f = C.frozen_test(frozen, e['pair'], 'H4')
                    row.update({'frozen_estimate': f['estimate'], 'frozen_lo': f['lo'], 'frozen_hi': f['hi']})
                flat.append(row)
    return flat


def b35(inp, tool, outdir):
    flat, mr = C.row_variants(inp, lambda sub: b35_core(sub, inp if sub.per_program is inp.per_program else None))
    cols = ['variant', 'pair', 'estimator', 'estimate', 'boot_lo', 'boot_hi', 'dropped', 'n_valid', 'n_entering',
            'frozen_estimate', 'frozen_lo', 'frozen_hi']
    meta = C.meta_block(inp, tool, ['B.35'], {'pairs': list(B35_PAIRS), 'entry_rule': B35_ENTRY_RULE, 'lr61': mr})
    md = C.header_md(inp, 'B.35', 'H4 with model-equal weighting (share of drift programs without a 2.3.3 warning, strata R+A)', meta,
                     'Entry rule (C-22): %s; the registered program-weighted H4 estimator is printed beside it. A resample is dropped when an '
                     'entering model has no drift program in it. No p-value. The columns frozen_* repeat the H4 of summary.json (frozen analyzer) on the '
                     'program-weighted row.' % B35_ENTRY_RULE)
    md += ['', C.md_table(cols, flat)]
    return C.emit(outdir, 'B.35', inp, meta, md, [('h4', cols, flat)], {'item': 'B.35', 'results': flat, 'lr61_without_ruled': mr})


# ------------------------------------------------------------------------------------------------ B.36
def b36_core(inp, frozen=None):
    stats = inp.stats
    out, flat = [], []
    for pair in B36_PAIRS:
        rows = C.flat_rows(inp.per_program, pair, inp.tmap, set(inp.models))
        for r in rows:
            r['grp'] = stats.h3_group(r['fam']) if r['stratum'] == 'M' else None
        mrows = [r for r in rows if r['stratum'] == 'M']
        elig = stats.h3_eligible_models(mrows, inp.models)
        ra = [r for r in rows if r['stratum'] in ('R', 'A')]
        defs = collections.OrderedDict([('frozen (prereg)', ('silent', 'drift_unwarned')),
                                        ('pilot', ('silent_pilotdef', 'drift_unwarned_pilot'))])
        e = {'pair': pair, 'h3_entering_models': elig}
        for name, (snum, hnum) in defs.items():
            if elig:
                def f3(v, snum=snum):
                    g1 = [v.ratio(snum, 'clean', model=m, stratum='M', grp='G1') for m in elig]
                    g2 = [v.ratio(snum, 'clean', model=m, stratum='M', grp='G2') for m in elig]
                    if any(x is None for x in g1 + g2):
                        return None
                    return stats.log_rr(sum(g1) / len(g1), sum(g2) / len(g2))
                r3 = stats.cluster_bootstrap_multi(mrows, {'h3': f3}, [snum, 'clean'], ('model', 'stratum', 'fam', 'grp'), B=inp.B,
                                                   seed=inp.seed, tasks=[t for t in inp.tasks_univ if t['stratum'] == 'M'])['h3']
                s3 = _summ(r3)
                s3['rr'] = _rr(s3['estimate'])
                s3['rr_lo'], s3['rr_hi'] = _rr(s3['boot_lo']), _rr(s3['boot_hi'])
                e['H3 ' + name] = s3
                row3 = {'pair': pair, 'statistic': 'H3 (RR, G1/G2)', 'warning_definition': name, 'estimate': s3['rr'],
                        'boot_lo': s3['rr_lo'], 'boot_hi': s3['rr_hi'], 'dropped': s3['dropped'], 'n_valid': s3['n_valid']}
                if name.startswith('frozen') and frozen is not None:            # LR82.2 item 8 (S-3): the H3 of summary.json (RR scale)
                    f = C.frozen_test(frozen, pair, 'H3')
                    row3.update({'frozen_estimate': _rr(f['estimate']), 'frozen_lo': _rr(f['lo']), 'frozen_hi': _rr(f['hi'])})
                flat.append(row3)
            if ra:
                r4 = stats.cluster_bootstrap_multi(ra, {'h4': h4_pooled_stat(hnum, 'drift')}, [hnum, 'drift'],
                                                   ('model', 'stratum', 'fam'), B=inp.B, seed=inp.seed,
                                                   tasks=[t for t in inp.tasks_univ if t['stratum'] in ('R', 'A')])['h4']
                s4 = _summ(r4)
                e['H4 ' + name] = s4
                row4 = {'pair': pair, 'statistic': 'H4 (share unwarned)', 'warning_definition': name, 'estimate': s4['estimate'],
                        'boot_lo': s4['boot_lo'], 'boot_hi': s4['boot_hi'], 'dropped': s4['dropped'], 'n_valid': s4['n_valid']}
                if name.startswith('frozen') and frozen is not None:
                    f = C.frozen_test(frozen, pair, 'H4')
                    row4.update({'frozen_estimate': f['estimate'], 'frozen_lo': f['lo'], 'frozen_hi': f['hi']})
                flat.append(row4)
        out.append(e)
    return flat


def b36(inp, tool, outdir):
    if not B36_EXTEND_TO_H3_H4:
        raise C.Refuse('B36_EXTEND_TO_H3_H4 is False: B.36 is not run (C-23 (a): the frozen code gives d1, d2a, d3 only)')
    flat, mr = C.row_variants(inp, lambda sub: b36_core(sub, inp if sub.per_program is inp.per_program else None),
                              keep=lambda r: r['statistic'].startswith('H4'))
    cols = ['variant', 'pair', 'statistic', 'warning_definition', 'estimate', 'boot_lo', 'boot_hi', 'dropped', 'n_valid',
            'frozen_estimate', 'frozen_lo', 'frozen_hi']
    meta = C.meta_block(inp, tool, ['B.36'], {'pairs': list(B36_PAIRS), 'lr61': mr})
    md = C.header_md(inp, 'B.36', 'Pilot warning definition for H3 and H4', meta,
                     'The pilot definition (category module pandas, or a pandas frame on the stack and not RuntimeWarning, without the NumPy '
                     'exclusion) replaces the registered one in the silent outcome (H3) and in the 2.3.3 warning of the denominator split (H4). '
                     'Estimates and intervals only; the frozen definition is printed beside it, and the columns frozen_* repeat the H3 (RR scale) and H4 '
                     'of summary.json on its rows (LR82.2 item 8). C-23 default (b).')
    md += ['', C.md_table(cols, flat)]
    return C.emit(outdir, 'B.36', inp, meta, md, [('table', cols, flat)], {'item': 'B.36', 'results': flat, 'lr61_without_ruled': mr})


ITEMS = {'B.11': b11, 'B.12': b12, 'B.35': b35, 'B.36': b36}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--analysis', required=True, help='B.11, B.12, B.35, B.36 or all')
    C.add_common_args(ap)
    a = ap.parse_args(argv)
    inp = C.load_inputs(a)
    items = list(ITEMS) if a.analysis == 'all' else [a.analysis]
    for it in items:
        if it not in ITEMS:
            raise C.Refuse('unknown analysis %r' % it)
    sc = C.self_check(inp)
    for it in items:
        base = ITEMS[it](inp, os.path.abspath(__file__), a.out)
        print('wrote', os.path.basename(base) + '.{json,md,tsv}', '(self-check passed)' if sc['passed'] else '')
    return 0


if __name__ == '__main__':
    sys.exit(C.run_main(main))
