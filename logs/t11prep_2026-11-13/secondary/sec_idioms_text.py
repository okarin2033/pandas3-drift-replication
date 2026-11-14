# B.10 (part 2): static idiom shares for the four example idioms of FULL_PREREG section 17 (dtype == object, astype(str), int64 epochs,
# observed= passed explicitly), by the new regexes of idiom_regex_sec17.tsv (LR82.2 item 5). The 53 frozen regexes stay in sec_idioms.py.
# Written 2026-11-13 in the T11 preparation step. Status: draft; decides nothing.
#
# Reads the TEXT of generated programs, named on the command line by --gen-dir (T11: generations/, only after the analysis, LR80 item 8;
# tests: logs/regression/inputs/generations, hand-made folders). The file of program `gen/<model>/<task>__s<k>` is <gen-dir>/<model>/<task>__s<k>.py.
# The regex table is applied with the frozen harness/exposure_scan.py (load, scan; Python `re`, re.MULTILINE); its sha256 is written into
# the header. The clause "on columns with missing values" (section 17) is not expressible on program text and is stated as such in the output.
#   python3 -I -B sec_idioms_text.py --per-program P --summary S --tasks T --out DIR --gen-dir G [--regex-tsv idiom_regex_sec17.tsv] --B 10000 --seed 20261111
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sec_common as C  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_REGEX_TSV = os.path.join(HERE, 'idiom_regex_sec17.tsv')
DENOMINATOR = 'generated non-empty programs (empty_source false) whose file was found, not pair-clean'   # as sec_idioms.py (I-6)
MISSING_CLAUSE = ('The clause "on columns with missing values" (section 17, astype(str)) is not expressible on program text: every astype(str) '
                  'is counted, whether or not the column holds missing values.')
N03_NOTE = ('Note on the regex for integer epochs (N03, LR83.4 f, LR84.3 c): a text scan cannot see the unit of the datetime, so N03 matches every '
            'cast of a date or time to int64 on a line with a date or time word, and also some other casts to int64 (for example an int64 cast '
            'of a timedelta component on such a line). The share of N03 is a share of programs with such a cast, not of programs that compute '
            'epochs in seconds. The four regexes are fixed and were not revised after programs were read.')


def program_path(gen_dir, program_id):
    rel = program_id[len('gen/'):] if program_id.startswith('gen/') else program_id
    return os.path.join(gen_dir, rel + '.py')


def scan_programs(inp, gen_dir, rows):
    """-> {program_id: sorted ids of the regexes that match} for every non-empty program whose file exists; list of missing ids."""
    import exposure_scan as es          # the frozen scanner (put on sys.path by sec_common.harness)
    matched, missing = {}, []
    for p in inp.per_program:
        if p.get('empty_source'):
            continue
        path = program_path(gen_dir, p['program_id'])
        if not os.path.isfile(path):
            missing.append(p['program_id'])
            continue
        matched[p['program_id']] = es.scan_file(path, rows)
    return matched, missing


def shares(sub, matched, ids, stats):
    out = []
    for m in sub.models:
        for s in C.STRATA:
            pp = [p for p in sub.per_program if p['model'] == m and p['stratum'] == s and p['program_id'] in matched]
            empty = sum(1 for p in sub.per_program if p['model'] == m and p['stratum'] == s and p.get('empty_source'))
            if not pp and not empty:
                continue
            n = len(pp)
            for i in ids + ['ANY']:
                x = sum(1 for p in pp if (matched[p['program_id']] if i == 'ANY' else i in matched[p['program_id']]))
                pr, lo, hi = C.wilson(stats, x, n)
                out.append({'model': m, 'stratum': s, 'idiom': i, 'x': x, 'n': n, 'empty_programs': empty, 'share': pr,
                            'wilson_lo': lo, 'wilson_hi': hi})
    return out


def run(inp, tool, outdir, gen_dir, regex_tsv):
    import exposure_scan as es
    C.harness(inp.study)
    rows = es.load(regex_tsv)
    ids = [cid for cid, _ in rows]
    fam = {r['id']: r.get('family') for r in C.read_tsv(regex_tsv)}
    matched, missing = scan_programs(inp, gen_dir, rows)
    cells, mr = C.row_variants(inp, lambda sub: shares(sub, matched, ids, inp.stats), keep=lambda r: r['stratum'] == 'R')
    for c in cells:
        c['family'] = fam.get(c['idiom'])
    cols = ['variant', 'model', 'stratum', 'idiom', 'family', 'x', 'n', 'empty_programs', 'share', 'wilson_lo', 'wilson_hi']
    meta = C.meta_block(inp, tool, ['B.10'], {'basis': 'new regexes for the four examples of section 17 (LR82.2 item 5)', 'denominator': DENOMINATOR,
                                              'regex_table_sha256': C.sha256_file(regex_tsv), 'regex_ids': ids,
                                              'programs_scanned': len(matched), 'program_files_missing': len(missing),
                                              'gen_dir_name': os.path.basename(os.path.normpath(gen_dir)), 'lr61': mr})
    md = C.header_md(inp, 'B.10', 'Static idiom shares, new regexes for the four examples of section 17', meta,
                     'Denominator: %s. Wilson 95%% only. %s Programs scanned: %d; program files not found: %d (left out of the denominators). '
                     'Stratum-R rows are repeated without the ruled R tasks (LR61/LR70). No cell is singled out in the text unless a rule fixed '
                     'before T11 selects it. %s' % (DENOMINATOR, MISSING_CLAUSE, len(matched), len(missing), N03_NOTE))
    md += ['', C.md_table(cols, [c for c in cells if c['idiom'] == 'ANY'], 60), '',
           'Per idiom cells: TSV (%d rows).' % len(cells)]
    return C.emit(outdir, 'B.10_new', inp, meta, md, [('shares', cols, cells)],
                  {'item': 'B.10', 'basis': 'new regexes (section 17 examples)', 'cells': cells, 'idiom_ids': ids,
                   'missing_clause_note': MISSING_CLAUSE, 'note_N03': N03_NOTE, 'program_files_missing': len(missing), 'lr61_without_ruled': mr})


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    C.add_common_args(ap)
    ap.add_argument('--gen-dir', required=True, help='folder with <model>/<task>__s<k>.py (T11: generations, after the analysis)')
    ap.add_argument('--regex-tsv', default=DEFAULT_REGEX_TSV)
    ap.add_argument('--ruled-path', default=None)
    a = ap.parse_args(argv)
    if not os.path.isdir(a.gen_dir):
        raise C.Refuse('--gen-dir is not a folder')
    inp = C.load_inputs(a, {'idiom_regex_sec17.tsv': a.regex_tsv})
    C.self_check(inp)
    base = run(inp, os.path.abspath(__file__), a.out, a.gen_dir, a.regex_tsv)
    print('wrote', os.path.basename(base) + '.{json,md,tsv}')
    return 0


if __name__ == '__main__':
    sys.exit(C.run_main(main))
