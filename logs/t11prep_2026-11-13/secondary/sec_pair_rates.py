# Pair-rate family of the secondary analyses: B.03 (E3, E4 against E0pa), B.04 (LOUD rates and status breakdown), B.05 (WARNING_ONLY
# counts), B.09 (latent drift on F-clean and F-dirty), B.14 (C1 control rate), B.34 (locally silent drift).
# Written 2026-11-13 in the T11 preparation step. Status: draft; decides nothing.
#
# Reads per_program.jsonl (pair blocks of every pair that analyze_full.build_per_program writes), summary.json, tasks.json.
# Pair-clean rule B.0.2: a program counts for pair q only if the block exists, `excluded` is None and `run_problem` is None; missing and
# excluded programs are counted by kind and are never in a denominator. The tool honours `excluded` itself (it does not use the frozen
# flatten(), which keys on clean_on_233; audit M-9).
#   python3 -I -B sec_pair_rates.py --analysis B.03|B.04|B.05|B.09|B.14|B.34|all --per-program P --summary S --tasks T --out DIR
import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sec_common as C  # noqa: E402

# ---- named constants (choices; CHOICES_AS_BUILT.md)
B03_PAIRS = ('E0pa~E3', 'E0pa~E4')
B03_OUTCOMES = ('silent', 'drift_any', 'loud')      # I-1: silent is the registered rate; drift_any and loud are added columns
B04_PAIRS = ('E0a~E1', 'E0a~E2')                    # I-2: the two T11 targets
B05_PAIRS = ('E0a~E1', 'E0a~E2')                    # I-3
B09_PAIRS = ('V-clean__E0a~V-clean__E1', 'V-dirty__E0a~V-dirty__E1')
B09_OUTCOMES = ('silent', 'drift_any')              # I-1 (LR82.2 item 2: denominator = main-clean and own-baseline-clean; n_own = own baseline alone)
B14_PAIRS = ('C1~E0a',)
B14_OUTCOMES = ('drift', 'drift_any', 'silent')     # LR82.2 item 3 (W-5): drift is the FIRST column, as section 9 words it; the others stay beside it
B34_PAIRS = ('E0a~E1', 'E0a~E2')
B34_OUTCOMES = ('loc_silent', 'loc_silent_any', 'loc_none')   # I-14: SUBSTANTIVE headline, any magnitude beside it, None count (C-21: None = not locally silent)
FAMILIES_IN_M = True                                # per-family cells inside M (Wilson + rare bound)

ANALYSES = {
    'B.03': ('Rates on E3 and E4 against E0pa', B03_PAIRS, B03_OUTCOMES),
    'B.04': ('LOUD rates and status breakdown', B04_PAIRS, ('loud',)),
    'B.05': ('WARNING_ONLY counts', B05_PAIRS, ('warning_only',)),
    'B.09': ('Latent drift on F-clean and F-dirty', B09_PAIRS, B09_OUTCOMES),
    'B.14': ('C1 control rate (adjacent-minor control)', B14_PAIRS, B14_OUTCOMES),
    'B.34': ('Locally silent drift', B34_PAIRS, B34_OUTCOMES),
}


def loud_breakdown(per_program, pair, models):
    """B.04: pair-clean LOUD programs by the target run status (first_diff.b of the status difference); exc_type is not in
    per_program.jsonl and is not reported by this tool."""
    c = collections.Counter()
    for p in per_program:
        if p['model'] not in models:
            continue
        kind, t = C.pair_status(p, pair)
        if kind != 'CLEAN' or t.get('class') != 'LOUD':
            continue
        fd = t.get('first_diff') or {}
        st = fd.get('b') if fd.get('kind') == 'status' else None
        c[(p['model'], p['stratum'], str(st) if st is not None else 'unknown')] += 1
    return [{'pair': pair, 'model': m, 'stratum': s, 'target_status': st, 'count': n} for (m, s, st), n in sorted(c.items())]


def run_item(inp, item, outdir, tool_file):
    title, pairs, outcomes = ANALYSES[item]
    all_cells, meta_ruled, rows_by_pair = [], {}, {}
    for pair in pairs:
        def compute(sub, pair=pair):
            rows = C.flat_rows(sub.per_program, pair, sub.tmap, set(sub.models))
            return [dict(c, pair=pair) for c in C.rate_cells(sub, rows, outcomes, families=FAMILIES_IN_M)]
        cells, mr = C.cells_variants(inp, compute)
        all_cells += cells
        if mr:
            meta_ruled[pair] = mr
        rows_by_pair[pair] = C.flat_rows(inp.per_program, pair, inp.tmap, set(inp.models))
    meta = C.meta_block(inp, tool_file, [item], {'pairs': list(pairs), 'outcomes': list(outcomes), 'lr61': meta_ruled or None})
    st_rows = C.status_rows(rows_by_pair, inp.models)
    tables = [('rates', ['pair'] + C.CELL_COLUMNS, all_cells),
              ('status_counts', ['pair', 'model', 'stratum', 'kind', 'count'], st_rows)]
    obj = {'item': item, 'title': title, 'cells': all_cells, 'status_counts': st_rows, 'lr61_without_ruled': meta_ruled or None}
    notes = {
        'B.09': 'Denominator = clean on 2.3.3 in the main run AND clean on the variant\'s own E0a/E0b (LR82.2 item 2, general rule (i)); '
                'column n_own = programs clean on the variant\'s own baseline alone, whatever their main status (kind MAIN_NOT_CLEAN in the '
                'status table). Plan label: secondary (4.4 l.226-227; F-dirty measures robustness to data the prompt did not describe).',
        'B.14': 'First column of every row: drift (SUBSTANTIVE), the C1 reference rate of section 9; drift_any and silent (no pandas warning in '
                'the E0a run) stand beside it, none is called the headline. A program that fails on 2.3.3 (the target of C1~E0a) is excluded '
                'and is not counted as a loud change; the baseline of this pair is C1 and a program whose C1 run did not complete is excluded '
                '(BASE_NOT_OK). Never the denominator of a "times more" claim (section 6).',
        'B.03': 'Plan label: secondary. Baseline E0pa has no determinism run of its own (LR82.1): the denominator is main-clean and E0pa ran ok; '
                'programs whose E0pa run did not complete are in the status table as BASE_NOT_OK, never in a denominator.',
    }
    md = C.header_md(inp, item, title, meta,
                     'Pair-clean programs only (clean on 2.3.3 in the main run and on the pair\'s own baseline; excluded and missing programs '
                     'are listed in the status table, never in a denominator). ' + notes.get(item, ''))
    if item == 'B.04':
        lb = []
        for pair in pairs:
            lb += loud_breakdown(inp.per_program, pair, set(inp.models))
        tables.append(('loud_status', ['pair', 'model', 'stratum', 'target_status', 'count'], lb))
        obj['loud_status'] = lb
        obj['not_reported'] = 'exc_type of LOUD programs: not in per_program.jsonl (run records are not an input of this tool)'
    md += ['', C.md_table(C.DISPLAY_COLUMNS, C.display_cells(all_cells)), '', 'Pair status counts (model x stratum x kind):', '',
           C.md_table(['pair', 'model', 'stratum', 'kind', 'count'], st_rows)]
    if item == 'B.04':
        md += ['', 'LOUD programs by target run status:', '',
               C.md_table(['pair', 'model', 'stratum', 'target_status', 'count'], tables[-1][2])]
    md += ['', 'No cell is singled out in the text unless a rule fixed before T11 selects it.']
    return C.emit(outdir, item, inp, meta, md, tables, obj)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--analysis', required=True, help='B.03, B.04, B.05, B.09, B.14, B.34 or all')
    C.add_common_args(ap)
    ap.add_argument('--ruled-path', default=None)
    a = ap.parse_args(argv)
    inp = C.load_inputs(a)
    items = list(ANALYSES) if a.analysis == 'all' else [a.analysis]
    for it in items:
        if it not in ANALYSES:
            raise C.Refuse('unknown analysis %r' % it)
    sc = C.self_check(inp)
    for it in items:
        base = run_item(inp, it, a.out, os.path.abspath(__file__))
        print('wrote', os.path.basename(base) + '.{json,md,tsv}', '(self-check passed)' if sc['passed'] else '')
    return 0


if __name__ == '__main__':
    sys.exit(C.run_main(main))
