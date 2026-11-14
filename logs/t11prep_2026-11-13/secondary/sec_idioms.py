# B.10 Static idiom counts (secondary: "static scan of version-sensitive idioms (secondary)", 16 W4 l.577; 17 l.599-600).
# Written 2026-11-13 in the T11 preparation step. Status: draft; decides nothing.
#
# Input: per_program.jsonl `exposure_match` (the catalogue ids whose frozen regex of tasks/exposure_regex.tsv matches the program
# text, computed by the frozen analyzer) and `empty_source`: the 53 frozen regexes. The four example idioms of section 17 as new regexes
# (LR82.2 item 5) are in sec_idioms_text.py, which reads program text. Stratum-R rows carry the LR61/LR70 variant (LR82.2 item 7).
#   python3 -I -B sec_idioms.py --per-program P --summary S --tasks T --out DIR [--exposure-tsv tasks/exposure_regex.tsv]
import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sec_common as C  # noqa: E402

IDIOM_BASIS = 'exposure_match (the 53 frozen regexes), C-8 (b)'   # C-8
DENOMINATOR = 'generated non-empty programs (empty_source false), not pair-clean'   # I-6
IDIOM_BOOTSTRAP = False                                            # C-2: Wilson only for the 53 x model x stratum shares


def shares(sub, ids):
    stats = sub.stats
    rows = []
    for m in sub.models:
        for s in C.STRATA:
            pp = [p for p in sub.per_program if p['model'] == m and p['stratum'] == s and not p.get('empty_source')]
            empty = sum(1 for p in sub.per_program if p['model'] == m and p['stratum'] == s and p.get('empty_source'))
            if not pp and not empty:
                continue
            n = len(pp)
            for i in ids:
                x = sum(1 for p in pp if i in (p.get('exposure_match') or []))
                pr, lo, hi = C.wilson(stats, x, n)
                rows.append({'model': m, 'stratum': s, 'idiom': i, 'x': x, 'n': n, 'empty_programs': empty,
                             'share': pr, 'wilson_lo': lo, 'wilson_hi': hi})
            if ids:
                x = sum(1 for p in pp if p.get('exposure_match'))
                pr, lo, hi = C.wilson(stats, x, n)
                rows.append({'model': m, 'stratum': s, 'idiom': 'ANY', 'x': x, 'n': n, 'empty_programs': empty,
                             'share': pr, 'wilson_lo': lo, 'wilson_hi': hi})
    return rows


def run(inp, tool, outdir, exposure_tsv=None):
    fam_of = {}
    ids = set()
    if exposure_tsv:
        for r in C.read_tsv(exposure_tsv):
            ids.add(r['id'])
            fam_of[r['id']] = r.get('family')
    for p in inp.per_program:
        ids.update(p.get('exposure_match') or [])
    ids = sorted(ids)
    # LR82.2 items 5 and 7 (S-1): every stratum-R row is repeated without the tasks of the ruled list (LR61/LR70)
    rows, mr = C.row_variants(inp, lambda sub: shares(sub, ids), keep=lambda r: r['stratum'] == 'R')
    for r in rows:
        r['family'] = fam_of.get(r['idiom'])
    cols = ['variant', 'model', 'stratum', 'idiom', 'family', 'x', 'n', 'empty_programs', 'share', 'wilson_lo', 'wilson_hi']
    meta = C.meta_block(inp, tool, ['B.10'], {'basis': IDIOM_BASIS, 'denominator': DENOMINATOR, 'lr61': mr,
                                              'exposure_tsv_sha256': C.sha256_file(exposure_tsv) if exposure_tsv else None})
    md = C.header_md(inp, 'B.10', 'Static idiom counts (the 53 frozen regexes)', meta,
                     'Basis: %s. Denominator: %s. Wilson 95%% only. Idiom ids seen in the data: %d. Stratum-R rows are repeated without the '
                     'ruled R tasks (LR61/LR70). The four examples of section 17 as new regexes are in sec_idioms_text.py.' % (IDIOM_BASIS, DENOMINATOR, len(ids)))
    md += ['', C.md_table(cols, [r for r in rows if r['idiom'] == 'ANY'], 60), '',
           'Per idiom cells (%d rows): TSV. No cell is singled out in the text unless a rule fixed before T11 selects it.' % len(rows)]
    return C.emit(outdir, 'B.10', inp, meta, md, [('shares', cols, rows)],
                  {'item': 'B.10', 'basis': IDIOM_BASIS, 'denominator': DENOMINATOR, 'cells': rows, 'idiom_ids': ids, 'lr61_without_ruled': mr})


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    C.add_common_args(ap)
    ap.add_argument('--ruled-path', default=None)
    ap.add_argument('--exposure-tsv', default=None, help='tasks/exposure_regex.tsv (optional: lists idioms with zero matches too)')
    a = ap.parse_args(argv)
    inp = C.load_inputs(a, {'exposure_regex.tsv': a.exposure_tsv} if a.exposure_tsv else None)
    C.self_check(inp)
    base = run(inp, os.path.abspath(__file__), a.out, a.exposure_tsv)
    print('wrote', os.path.basename(base) + '.{json,md,tsv}')
    return 0


if __name__ == '__main__':
    sys.exit(C.run_main(main))
