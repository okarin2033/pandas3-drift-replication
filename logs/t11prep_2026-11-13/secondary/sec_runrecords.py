# Run-record tables of the secondary analyses (LR82.2 items 4 and 11): B.04 exception type of LOUD programs, B.05 split of warning-only
# programs by warning category, B.08 stdout and file differences, X-3 neutralised warning-filter calls.
# Written 2026-11-13 in the T11 preparation step. Status: draft; decides nothing.
#
# Run records are read ONLY through the frozen loader `harness/run_programs.load_record(runs_root, run_config, program_id)`; the
# program ids and the pair-clean rule come from per_program.jsonl (sec_common.pair_status). The classification itself (LOUD, warning-only,
# new pandas warnings) is the frozen one: the tool calls harness/warndef.py (pandas_warnings, warning_signature) and reads the class and
# status of the pair block; it never classifies a result itself.
#   python3 -I -B sec_runrecords.py --analysis B.04|B.05|B.08|X-3|all --runs RUNS_ROOT <common> [--pairs E0a~E1,E0a~E2] [--configs E0a,E0b,E1,E2]
# Study data: --runs runs (T11, after the integrity check). Test data: logs/regression/runs with --test-label.
import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sec_common as C  # noqa: E402

# ---- named constants (choices; CHOICES_RULED.md)
B04_PAIRS = ('E0a~E1', 'E0a~E2')        # the two T11 targets (I-2)
B05_PAIRS = ('E0a~E1', 'E0a~E2')        # I-3
B08_PAIRS = ('E0a~E1',)                 # I-5: 12 l.473-474 names no pair; E1 is the primary target
X3_CONFIGS = ('E0a', 'E0b', 'E1', 'E2') # run configs whose records are counted for the neutralised filter calls
NO_EXC = '(none)'
FILES_DIFF_KINDS = ('basenames', 'sha256')   # C-7 (a): raw differences; repr-only changes are included, stated in the output


class RunRecords:
    """Reads run records through the frozen loader; counts what it could not find."""

    def __init__(self, study, runs_root):
        C.harness(study)                  # puts harness/ on sys.path, no bytecode
        import run_programs
        import warndef
        self.rp, self.wd = run_programs, warndef
        self.root = runs_root
        self.missing = collections.Counter()
        self.reads = 0

    def get(self, config, program_id):
        rec = self.rp.load_record(self.root, config, program_id)
        self.reads += 1
        if rec is None:
            self.missing[config] += 1
        return rec


def pair_configs(pair):
    base, target = pair.split('~')
    return base, target


def _fam(p):
    return C.family_code(p.get('family')) if p['stratum'] == 'M' else None


# ------------------------------------------------------------------------------------------------ B.04
def b04_rows(inp, rr, pairs, notes):
    """LOUD programs (pair-clean, class LOUD) by target run status and exception type (record of the target run)."""
    c = collections.Counter()
    for pair in pairs:
        _, tgt = pair_configs(pair)
        for p in inp.per_program:
            if p['model'] not in inp.models:
                continue
            kind, t = C.pair_status(p, pair)
            if kind != 'CLEAN' or t.get('class') != 'LOUD':
                continue
            rec = rr.get(tgt, p['program_id'])
            if rec is None:
                notes['LOUD program without a target run record'] += 1
                c[(pair, p['model'], p['stratum'], 'record missing', NO_EXC)] += 1
                continue
            st = rec.get('status')
            fd = t.get('first_diff') or {}
            if fd.get('kind') == 'status' and fd.get('b') != st:
                notes['status of the record differs from first_diff.b of the pair block'] += 1
            et = rec.get('exc_type') if st == 'error' else None
            c[(pair, p['model'], p['stratum'], str(st), et or NO_EXC)] += 1
    return [{'pair': a, 'model': b, 'stratum': s, 'target_status': st, 'exc_type': et, 'count': n}
            for (a, b, s, st, et), n in sorted(c.items())]


# ------------------------------------------------------------------------------------------------ B.05
def new_pandas_warnings(rr, base, tgt):
    """Pandas warnings of the target run whose signature is not among the baseline's (the frozen warning-only definition)."""
    wd = rr.wd
    base_sigs = {wd.warning_signature(w) for w in wd.pandas_warnings(base)}
    return [w for w in wd.pandas_warnings(tgt) if wd.warning_signature(w) not in base_sigs]


def b05_rows(inp, rr, pairs, notes):
    c = collections.Counter()
    n_wo = collections.Counter()
    for pair in pairs:
        b, tg = pair_configs(pair)
        for p in inp.per_program:
            if p['model'] not in inp.models:
                continue
            kind, t = C.pair_status(p, pair)
            if kind != 'CLEAN' or not t.get('warning_only'):
                continue
            base, tgt = rr.get(b, p['program_id']), rr.get(tg, p['program_id'])
            n_wo[(pair, p['model'], p['stratum'])] += 1
            if base is None or tgt is None:
                notes['warning-only program without both run records'] += 1
                continue
            new = new_pandas_warnings(rr, base, tgt)
            if not new:
                notes['warning-only program without a new pandas warning in the records'] += 1
                continue
            cats = {w.get('category_qualname') for w in new}
            for cat in cats:
                c[(pair, p['model'], p['stratum'], str(cat))] += 1
            fut = any(rr.wd.is_future_dep(w) for w in new)
            c[(pair, p['model'], p['stratum'], '(any Future/Deprecation/PendingDeprecation)')] += 1 if fut else 0
    rows = []
    for (pair, m, s, cat), n in sorted(c.items()):
        if n:
            rows.append({'table': 'categories', 'pair': pair, 'model': m, 'stratum': s, 'category': cat, 'programs': n,
                         'warning_only_programs': n_wo[(pair, m, s)]})
    rows += [{'table': 'totals', 'pair': a, 'model': m, 'stratum': s, 'warning_only_programs': n} for (a, m, s), n in sorted(n_wo.items())]
    return rows


# ------------------------------------------------------------------------------------------------ B.08
def files_differ(fa, fb):
    """-> (basenames differ, any sha256 differs among the common names or a name is missing on one side)."""
    fa, fb = fa or {}, fb or {}
    names = set(fa) != set(fb)
    sha = names or any((fa[k] or {}).get('sha256') != (fb[k] or {}).get('sha256') for k in fa)
    return names, sha


def b08_rows(inp, rr, pairs, notes):
    stats = inp.stats
    acc = collections.defaultdict(lambda: collections.Counter())
    for pair in pairs:
        b, tg = pair_configs(pair)
        for p in inp.per_program:
            if p['model'] not in inp.models:
                continue
            kind, t = C.pair_status(p, pair)
            if kind != 'CLEAN':
                continue
            base, tgt = rr.get(b, p['program_id']), rr.get(tg, p['program_id'])
            if base is None or tgt is None:
                notes['pair-clean program without both run records'] += 1
                continue
            drift = 'drift' if t.get('drift') else 'no drift'
            sd = base.get('stdout_sha256') != tgt.get('stdout_sha256')
            fn, fs = files_differ(base.get('files_written'), tgt.get('files_written'))
            for scope in ((pair, p['model'], p['stratum'], 'all'), (pair, p['model'], p['stratum'], drift)):
                a = acc[scope]
                a['n'] += 1
                a['stdout_differs'] += int(sd)
                a['files_basenames_differ'] += int(fn)
                a['files_sha256_differ'] += int(fs)
                a['either_differs'] += int(sd or fs)
    rows = []
    for (pair, m, s, sub), a in sorted(acc.items()):
        r = {'pair': pair, 'model': m, 'stratum': s, 'subset': sub, 'n': a['n']}
        for k in ('stdout_differs', 'files_basenames_differ', 'files_sha256_differ', 'either_differs'):
            pr, lo, hi = C.wilson(stats, a[k], a['n'])
            r.update({k: a[k], k + '_rate': pr, k + '_lo': lo, k + '_hi': hi})
        rows.append(r)
    return rows


# ------------------------------------------------------------------------------------------------ X-3
def x3_rows(inp, rr, configs):
    acc = collections.defaultdict(lambda: collections.Counter())
    for p in inp.per_program:
        if p['model'] not in inp.models:
            continue
        for cfg in configs:
            rec = rr.get(cfg, p['program_id'])
            a = acc[(p['model'], cfg)]
            if rec is None:
                a['records_missing'] += 1
                continue
            v = rec.get('warning_filter_calls_neutralised') or 0
            a['records'] += 1
            a['records_with_calls'] += 1 if v > 0 else 0
            a['calls_total'] += v
            a['calls_max'] = max(a['calls_max'], v)
    return [{'model': m, 'run_config': cfg, 'records': a['records'], 'records_missing': a['records_missing'],
             'records_with_neutralised_calls': a['records_with_calls'], 'neutralised_calls_total': a['calls_total'],
             'neutralised_calls_max_in_a_record': a['calls_max']} for (m, cfg), a in sorted(acc.items())]


# ------------------------------------------------------------------------------------------------ driver
ITEMS = ('B.04', 'B.05', 'B.08', 'X-3')


def variants(inp, rr, fn, pairs):
    """LR82 rule (vi): every table with stratum-R rows carries the rows recomputed without the tasks of the ruled list (LR61, LR70),
    through lr61_report.without_ruled. -> (rows with a `variant` column, notes of the all-tasks pass, lr61 meta)."""
    notes = collections.Counter()

    def core(sub):
        return fn(sub, rr, pairs, notes if sub.per_program is inp.per_program else collections.Counter())
    rows, mr = C.row_variants(inp, core, keep=lambda r: r['stratum'] == 'R')
    return rows, notes, mr


def run_item(inp, rr, item, a, tool, outdir):
    extra = {'pairs': list(a.pairs), 'runs_root_name': os.path.basename(a.runs)}
    if item == 'B.04':
        rows, notes, mr = variants(inp, rr, b04_rows, a.pairs)
        cols = ['variant', 'pair', 'model', 'stratum', 'target_status', 'exc_type', 'count']
        meta = C.meta_block(inp, tool, ['B.04'], dict(extra, records_read=rr.reads, lr61=mr))
        md = C.header_md(inp, 'B.04', 'LOUD programs by target run status and exception type (run records)', meta,
                         'LOUD = the frozen class of the pair block. exc_type is the exc_type of the target run record, for status error only. '
                         'The LOUD rates are in the B.04 table of sec_pair_rates.py. Stratum-R rows are repeated without the ruled R tasks (LR61/LR70).')
        md += ['', C.md_table(cols, rows, 100)]
        if notes:
            md += ['', 'Notes: ' + '; '.join('%s: %d' % kv for kv in sorted(notes.items()))]
        return C.emit(outdir, 'B.04_exc', inp, meta, md, [('exc', cols, rows)], {'item': 'B.04', 'rows': rows, 'notes': dict(notes),
                                                                              'records_missing_by_config': dict(rr.missing), 'lr61_without_ruled': mr})
    if item == 'B.05':
        allr, notes, mr = variants(inp, rr, b05_rows, a.pairs)
        rows = [r for r in allr if r['table'] == 'categories']
        tot = [r for r in allr if r['table'] == 'totals']
        cols = ['variant', 'pair', 'model', 'stratum', 'category', 'programs', 'warning_only_programs']
        tcols = ['variant', 'pair', 'model', 'stratum', 'warning_only_programs']
        meta = C.meta_block(inp, tool, ['B.05'], dict(extra, records_read=rr.reads, lr61=mr))
        md = C.header_md(inp, 'B.05', 'Warning-only programs by warning category (run records)', meta,
                         'Warning-only = the frozen flag of the pair block (class IDENTICAL or DTYPE_ONLY and a pandas warning signature on the '
                         'target that the baseline run lacks). Category = category_qualname of those new warnings; a program with several '
                         'categories is counted once in each, so the rows do not add up to the program count. Stratum-R rows are repeated '
                         'without the ruled R tasks (LR61/LR70).')
        md += ['', C.md_table(cols, rows, 100), '', 'Warning-only programs per cell:', '', C.md_table(tcols, tot, 60)]
        if notes:
            md += ['', 'Notes: ' + '; '.join('%s: %d' % kv for kv in sorted(notes.items()))]
        return C.emit(outdir, 'B.05_cat', inp, meta, md, [('categories', cols, rows), ('totals', tcols, tot)],
                      {'item': 'B.05', 'rows': rows, 'totals': tot, 'notes': dict(notes), 'records_missing_by_config': dict(rr.missing),
                       'lr61_without_ruled': mr})
    if item == 'B.08':
        rows, notes, mr = variants(inp, rr, b08_rows, a.pairs)
        cols = ['variant', 'pair', 'model', 'stratum', 'subset', 'n', 'stdout_differs', 'stdout_differs_rate', 'stdout_differs_lo',
                'stdout_differs_hi', 'files_basenames_differ', 'files_basenames_differ_rate', 'files_sha256_differ',
                'files_sha256_differ_rate', 'files_sha256_differ_lo', 'files_sha256_differ_hi', 'either_differs', 'either_differs_rate']
        meta = C.meta_block(inp, tool, ['B.08'], dict(extra, records_read=rr.reads, files_diff_kinds=list(FILES_DIFF_KINDS), lr61=mr))
        md = C.header_md(inp, 'B.08', 'Stdout and written-file differences between baseline and target (run records)', meta,
                         'Raw sha256 differences (C-7 (a)): repr-only changes of the output are included, which is stated here and in the paper. '
                         'stdout_differs = stdout_sha256 of the baseline run differs from that of the target run; files_basenames_differ = the sets '
                         'of written file names differ; files_sha256_differ = the names differ or a common name has another sha256. Subsets: all '
                         'pair-clean programs, with drift, without drift (the frozen drift flag). Wilson 95%. Label: secondary (12 l.473-474). '
                         'Stratum-R rows are repeated without the ruled R tasks (LR61/LR70).')
        md += ['', C.md_table(cols, rows, 100)]
        if notes:
            md += ['', 'Notes: ' + '; '.join('%s: %d' % kv for kv in sorted(notes.items()))]
        return C.emit(outdir, 'B.08', inp, meta, md, [('differences', cols, rows)], {'item': 'B.08', 'rows': rows, 'notes': dict(notes),
                                                                                  'records_missing_by_config': dict(rr.missing),
                                                                                  'lr61_without_ruled': mr})
    rows = x3_rows(inp, rr, a.configs)
    cols = ['model', 'run_config', 'records', 'records_missing', 'records_with_neutralised_calls', 'neutralised_calls_total',
            'neutralised_calls_max_in_a_record']
    meta = C.meta_block(inp, tool, ['X-3'], {'configs': list(a.configs), 'records_read': rr.reads, 'runs_root_name': os.path.basename(a.runs)})
    md = C.header_md(inp, 'X-3', 'Program calls of warnings.simplefilter / filterwarnings that the harness neutralised', meta,
                     'Section 6 l.302: program warning-filter calls are neutralised and counted (run-record field warning_filter_calls_neutralised). '
                     'All generated programs of the models, all configs given; no pair rule is applied and no stratum split, so no result on '
                     'stratum R is reported.')
    md += ['', C.md_table(cols, rows, 100)]
    return C.emit(outdir, 'X-3', inp, meta, md, [('neutralised', cols, rows)], {'item': 'X-3', 'rows': rows, 'records_missing_by_config': dict(rr.missing)})


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--analysis', required=True, help='B.04, B.05, B.08, X-3 or all')
    C.add_common_args(ap)
    ap.add_argument('--runs', required=True, help='runs root (T11: runs; pilot: logs/regression/runs)')
    ap.add_argument('--pairs', default=None, help='comma-separated pairs (default per item)')
    ap.add_argument('--configs', default=','.join(X3_CONFIGS), help='X-3: run configs')
    ap.add_argument('--ruled-path', default=None)      # accepted for a uniform command line; the run-record tables are not results on stratum R
    a = ap.parse_args(argv)
    items = list(ITEMS) if a.analysis == 'all' else [a.analysis]
    for it in items:
        if it not in ITEMS:
            raise C.Refuse('unknown analysis %r' % it)
    if not os.path.isdir(a.runs):
        raise C.Refuse('runs root %r is not a folder' % os.path.basename(a.runs))
    a.configs = tuple(x for x in a.configs.split(',') if x)
    inp = C.load_inputs(a)
    sc = C.self_check(inp)
    rr = RunRecords(inp.study, a.runs)
    tool = os.path.abspath(__file__)
    defaults = {'B.04': B04_PAIRS, 'B.05': B05_PAIRS, 'B.08': B08_PAIRS}
    for it in items:
        a2 = argparse.Namespace(**vars(a))
        a2.pairs = tuple(x for x in a.pairs.split(',') if x) if a.pairs else defaults.get(it, ())
        base = run_item(inp, rr, it, a2, tool, a.out)
        print('wrote', os.path.basename(base) + '.{json,md,tsv}', '(self-check passed)' if sc['passed'] else '')
    return 0


if __name__ == '__main__':
    sys.exit(C.run_main(main))
