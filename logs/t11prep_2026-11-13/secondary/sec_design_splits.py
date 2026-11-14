# Design-split family of the secondary analyses: B.07 (per catalogue row), B.13 (task-level share of tasks with any drift),
# B.15 (stratum R by question date against each model's knowledge cutoff), B.29 (stratum A by invited / not invited).
# Written 2026-11-13 in the T11 preparation step. Status: draft; decides nothing.
#
# Reads per_program.jsonl, summary.json, tasks.json (catalogue_row, so_creation_date, invited_ids_reviewer / _author, family) and, for
# B.15, models.tsv (vendor_knowledge_cutoff). Pair-clean rule B.0.2. Stratum R results are also given without the tasks of
# tasks/RULED_FIDELITY_FAILS.tsv through lr61_report.without_ruled (B.0.6).
#   python3 -I -B sec_design_splits.py --analysis B.07|B.13|B.15|B.29|all ...
import argparse
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sec_common as C  # noqa: E402

# ---- named constants (choices; CHOICES_AS_BUILT.md)
B07_PAIRS = ('E0a~E1', 'E0a~E2')        # I-4: the registered text says "per catalogue row" only
B07_OUTCOMES = ('silent',)
B13_PAIR = 'E0a~E1'                     # I-9
B13_OUTCOMES = ('silent', 'drift_any')  # C-10 default: (a) silent SUBSTANTIVE and (c) any drift including NUMERIC_SMALL
B15_PAIRS = ('E0a~E1', 'E0a~E2')        # I-10: E2 too
B15_OUTCOMES = ('silent',)
B15_MONTH_ONLY = 'three cells'          # C-11 default (a): before / inside the month / after; the alternatives are (b) inside = before,
                                        # (c) inside = after (set this constant to 'inside=before' or 'inside=after')
B29_PAIR = 'E0a~E1'
B29_OUTCOMES = ('silent', 'drift', 'drift_any')   # I-13: 4.3 says "drift"; the primary silent outcome and both drift readings
B29_COMMON_MODELS = True                           # LR82.2 item 8 (S-6): the two groups are pooled over the same models
B29_INVITED_BASES = ('reviewer', 'author')        # C-17: (a) invited_ids_reviewer (4.3 l.185) first, (b) invited_ids_author beside it
SPLIT_NO_DATE = 'no_date'


def parse_cutoffs(text):
    """vendor_knowledge_cutoff text -> list of {basis, kind ('day'|'month'), iso}. [] when no date is documented. Two dates of one
    model (for example reliable and training data) give two entries; equal dates are merged."""
    out = []
    for m in re.finditer(r'(\d{4}-\d{2}(?:-\d{2})?)(?:\s*\(?(reliable|training data|pre-training data)\)?)?', text or ''):
        iso, basis = m.group(1), m.group(2) or 'vendor'
        kind = 'day' if len(iso) == 10 else 'month'
        for o in out:
            if o['iso'] == iso:
                if basis not in o['basis'].split('/'):
                    o['basis'] += '/' + basis
                break
        else:
            out.append({'basis': basis, 'kind': kind, 'iso': iso})
    return out


def date_cell(date, cutoff, month_only=B15_MONTH_ONLY):
    """'before' / 'inside' / 'after' for one question date against one cutoff; 'no_date' without a date."""
    if not date:
        return SPLIT_NO_DATE
    d = str(date)[:10]
    if cutoff['kind'] == 'day':
        return 'before' if d < cutoff['iso'] else 'after'
    month = cutoff['iso']
    if d[:7] < month:
        return 'before'
    if d[:7] > month:
        return 'after'
    return {'three cells': 'inside', 'inside=before': 'before', 'inside=after': 'after'}[month_only]


# ------------------------------------------------------------------------------------------------ B.07
def b07(inp, tool, outdir):
    cells_all, ruled_meta, rows_by_pair = [], {}, {}
    for pair in B07_PAIRS:
        def compute(sub, pair=pair):
            rows = C.flat_rows(sub.per_program, pair, sub.tmap, set(sub.models))
            row_of = {t['id']: t.get('catalogue_row') for t in sub.tasks}
            rows = [r for r in rows if r['stratum'] == 'M' and row_of.get(r['task_id'])]
            cs = C.rate_cells(sub, rows, B07_OUTCOMES, strata=('M',), split_of=lambda r: row_of[r['task_id']], families=False,
                              pooled=True, cell_bootstrap=False)
            return [dict(c, pair=pair) for c in cs]
        cells, mr = C.cells_variants(inp, compute)
        cells_all += cells
        rows_by_pair[pair] = C.flat_rows(inp.per_program, pair, inp.tmap, set(inp.models))
    meta = C.meta_block(inp, tool, ['B.07'], {'pairs': list(B07_PAIRS)})
    cols = ['pair', 'catalogue_row', 'model', 'x', 'n', 'rate', 'wilson_lo', 'wilson_hi', 'boot_lo', 'boot_hi', 'boot_dropped',
            'rare_event', 'cp_deff_upper', 'entering_models']
    rows = [dict(c, catalogue_row=c['split']) for c in cells_all if c['model'] != 'MODEL_EQUAL_MEAN']
    pooled = [dict(c, catalogue_row=c['split']) for c in cells_all if c['model'] == 'MODEL_EQUAL_MEAN']
    n_tasks = collections.Counter(t.get('catalogue_row') for t in inp.tasks if t.get('stratum') == 'M' and t.get('catalogue_row'))
    md = C.header_md(inp, 'B.07', 'Rates per catalogue row (stratum M)', meta,
                     'Cells: Wilson + rare bound per model x row (C-6 default (a)); beside them the model-equal mean per row with a '
                     'paired task-cluster bootstrap (C-6 (c)). %d rows, 1 to %d tasks per row. No test.' % (len(n_tasks), max(n_tasks.values() or [0])))
    md += ['', 'Model-equal mean of the silent rate per catalogue row:', '',
           C.md_table(['pair', 'catalogue_row', 'rate', 'boot_lo', 'boot_hi', 'boot_dropped', 'entering_models'], pooled, 90),
           '', 'No cell is singled out in the text unless a rule fixed before T11 selects it (REVIEW P-8). Per model x row cells: TSV.']
    return C.emit(outdir, 'B.07', inp, meta, md, [('cells', cols, rows), ('model_equal', cols, pooled)],
                  {'item': 'B.07', 'cells': rows, 'model_equal_mean_per_row': pooled, 'tasks_per_row': dict(n_tasks)})


# ------------------------------------------------------------------------------------------------ B.13
def task_rows(rows, outcomes):
    """Collapse program rows to task rows per model: clean = 1 if any pair-clean program, outcome = 1 if any clean program has it."""
    by = collections.OrderedDict()
    for r in rows:
        k = (r['model'], r['task_id'])
        t = by.setdefault(k, dict(model=r['model'], task_id=r['task_id'], stratum=r['stratum'], fam=r['fam'], gen=1, clean=0,
                                  clean_own=0, **{o: 0 for o in outcomes}))
        if r['clean']:
            t['clean'] = 1
            for o in outcomes:
                if r[o]:
                    t[o] = 1
        if r['clean_own']:
            t['clean_own'] = 1
    return list(by.values())


def b13(inp, tool, outdir):
    def compute(sub):
        rows = C.flat_rows(sub.per_program, B13_PAIR, sub.tmap, set(sub.models))
        tr = task_rows(rows, B13_OUTCOMES)
        return [dict(c, pair=B13_PAIR, unit='task') for c in
                C.rate_cells(sub, tr, B13_OUTCOMES, families=True, pooled=True, rare_mode='plain')]
    cells, mr = C.cells_variants(inp, compute)
    meta = C.meta_block(inp, tool, ['B.13'], {'pair': B13_PAIR, 'lr61': mr})
    md = C.header_md(inp, 'B.13', 'Share of tasks with at least one drifting program', meta,
                     'Unit: task. Denominator: tasks with at least one pair-clean program of the model (I-9). Outcomes: silent '
                     'SUBSTANTIVE and any drift (C-10). Wilson over tasks; rare bound: plain Clopper-Pearson (no clustering).')
    md += ['', C.md_table(C.DISPLAY_COLUMNS, C.display_cells(cells))]
    return C.emit(outdir, 'B.13', inp, meta, md, [('shares', ['pair', 'unit'] + C.CELL_COLUMNS, cells)],
                  {'item': 'B.13', 'cells': cells, 'lr61_without_ruled': mr})


# ------------------------------------------------------------------------------------------------ B.15
def model_cutoffs(inp):
    """{model key: [cutoff entries]} from models.tsv; models not in the frame map to None."""
    out = {}
    if not inp.models_rows:
        return out
    for r in inp.models_rows:
        out[C.model_key(r['openrouter_id'])] = parse_cutoffs(r.get('vendor_knowledge_cutoff'))
    return out


def b15(inp, tool, outdir):
    if not inp.models_rows:
        raise C.Refuse('B.15 needs --models-tsv')
    cuts = model_cutoffs(inp)
    cells_all, ruled_meta, notes = [], {}, []
    for pair in B15_PAIRS:
        for m in inp.models:
            variants = cuts.get(m)
            if variants is None:
                notes.append('%s: not in models.tsv, unsplit' % m)
                variants = []
            if not variants:
                variants = [None]
            for cut in variants:
                def compute(sub, pair=pair, m=m, cut=cut):
                    rows = [r for r in C.flat_rows(sub.per_program, pair, sub.tmap, {m}) if r['stratum'] == 'R']
                    date = {t['id']: t.get('so_creation_date') for t in sub.tasks}
                    if cut is None:
                        so = lambda r: 'all (cutoff unknown or not documented)'
                    else:
                        so = lambda r: date_cell(date.get(r['task_id']), cut)
                    cs = C.rate_cells(sub, rows, B15_OUTCOMES, strata=('R',), split_of=so, families=False, pooled=False, models=[m])
                    return [dict(c, pair=pair, cutoff_basis=(cut['basis'] if cut else None), cutoff=(cut['iso'] if cut else None))
                            for c in cs]
                cells, mr = C.cells_variants(inp, compute)
                cells_all += cells
                if mr:
                    ruled_meta = mr
    meta = C.meta_block(inp, tool, ['B.15'], {'pairs': list(B15_PAIRS), 'month_only_rule': B15_MONTH_ONLY, 'lr61': ruled_meta or None})
    cols = ['pair', 'variant', 'model', 'cutoff', 'cutoff_basis', 'split', 'x', 'n', 'rate', 'wilson_lo', 'wilson_hi', 'boot_lo',
            'boot_hi', 'boot_dropped', 'rare_event', 'cp_deff_upper']
    dq = collections.Counter(date_cell(t.get('so_creation_date'), {'kind': 'day', 'iso': '9999-12-31'}) for t in inp.tasks
                             if t.get('stratum') == 'R')
    md = C.header_md(inp, 'B.15', 'Stratum R rates by question date against each model cutoff', meta,
                     '"before" = so_creation_date strictly before the cutoff (I-10); month-only cutoffs: %s (C-11); models without a '
                     'documented cutoff are unsplit; a model with two documented dates has one block per date.' % B15_MONTH_ONLY)
    md += ['', C.md_table(['pair', 'variant', 'model', 'cutoff', 'cutoff_basis', 'split', 'x', 'n', 'rate', 'wilson_lo', 'wilson_hi'],
                          cells_all, 120)]
    if notes:
        md += ['', 'Notes: ' + '; '.join(sorted(set(notes)))]
    md += ['', 'No cell is singled out in the text unless a rule fixed before T11 selects it.']
    return C.emit(outdir, 'B.15', inp, meta, md, [('cells', cols, cells_all)],
                  {'item': 'B.15', 'cells': cells_all, 'notes': sorted(set(notes)), 'n_R_tasks_without_date':
                   sum(1 for t in inp.tasks if t.get('stratum') == 'R' and not t.get('so_creation_date'))})


# ------------------------------------------------------------------------------------------------ B.29
def diff_pooled(inp, rows, outcome, a='invited', b='not invited'):
    """Model-equal pooled rate(a) - rate(b) on stratum A with the paired task-cluster bootstrap; resample dropped when an entering
    model has a zero denominator in either cell."""
    stats = inp.stats
    ent = [m for m in inp.models if sum(r['clean'] for r in rows if r['model'] == m and r['split'] == a) > 0
           and sum(r['clean'] for r in rows if r['model'] == m and r['split'] == b) > 0]
    if not ent:
        return None

    def f(v):
        xs = [v.ratio(outcome, 'clean', model=m, stratum='A', split=a) for m in ent]
        ys = [v.ratio(outcome, 'clean', model=m, stratum='A', split=b) for m in ent]
        if any(z is None for z in xs + ys):
            return None
        return sum(xs) / len(xs) - sum(ys) / len(ys)
    res = stats.cluster_bootstrap_multi(rows, {'d': f}, [outcome, 'clean'], ('model', 'stratum', 'fam', 'split'), B=inp.B,
                                        seed=inp.seed, tasks=[t for t in inp.tasks_univ if t['stratum'] == 'A'])['d']
    return {'outcome': outcome, 'entering_models': len(ent), 'difference': C.nn(res['estimate']), 'boot_lo': C.nn(res['lo']),
            'boot_hi': C.nn(res['hi']), 'boot_dropped': res['dropped']}


def b29(inp, tool, outdir):
    cells_all, diffs = [], []
    for basis in B29_INVITED_BASES:
        field = 'invited_ids_' + basis
        inv = {t['id']: ('invited' if (t.get(field) or []) else 'not invited') for t in inp.tasks}
        rows = [dict(r, split=inv.get(r['task_id'])) for r in C.flat_rows(inp.per_program, B29_PAIR, inp.tmap, set(inp.models))
                if r['stratum'] == 'A']

        def compute(sub, inv=inv):
            rs = [r for r in C.flat_rows(sub.per_program, B29_PAIR, sub.tmap, set(sub.models)) if r['stratum'] == 'A']
            return C.rate_cells(sub, rs, B29_OUTCOMES, strata=('A',), split_of=lambda r: inv.get(r['task_id']), families=False,
                                pooled=True, common_entering=B29_COMMON_MODELS)
        cells = compute(inp)
        cells_all += [dict(c, pair=B29_PAIR, variant='all tasks', invited_basis=basis) for c in cells]
        for o in B29_OUTCOMES:
            d = diff_pooled(inp, rows, o)
            if d:
                diffs.append(dict(d, invited_basis=basis, pair=B29_PAIR))
    n_inv = {b: sum(1 for t in inp.tasks if t.get('stratum') == 'A' and (t.get('invited_ids_' + b) or [])) for b in B29_INVITED_BASES}
    meta = C.meta_block(inp, tool, ['B.29'], {'pair': B29_PAIR, 'tasks_invited_in_A': n_inv})
    cols = ['pair', 'invited_basis', 'outcome', 'model', 'split', 'x', 'n', 'rate', 'wilson_lo', 'wilson_hi', 'boot_lo', 'boot_hi',
            'boot_dropped', 'rare_event', 'cp_deff_upper', 'entering_models']
    md = C.header_md(inp, 'B.29', 'Stratum A drift by invited / not invited', meta,
                     'Invited = non-empty invited_ids_reviewer (C-17 (a), the field 4.3 names); invited_ids_author beside it. '
                     'Model-equal pooled rate of each group and their paired-bootstrap difference. No test.')
    md += ['', C.md_table(cols, [c for c in cells_all if c['model'] == 'MODEL_EQUAL_MEAN'], 60), '',
           'Pooled difference (invited minus not invited):', '',
           C.md_table(['pair', 'invited_basis', 'outcome', 'difference', 'boot_lo', 'boot_hi', 'boot_dropped', 'entering_models'], diffs)]
    return C.emit(outdir, 'B.29', inp, meta, md, [('cells', cols, cells_all), ('differences', list(diffs[0]) if diffs else ['pair'], diffs)],
                  {'item': 'B.29', 'cells': cells_all, 'differences': diffs})


ITEMS = {'B.07': b07, 'B.13': b13, 'B.15': b15, 'B.29': b29}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--analysis', required=True, help='B.07, B.13, B.15, B.29 or all')
    C.add_common_args(ap)
    ap.add_argument('--ruled-path', default=None)
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
