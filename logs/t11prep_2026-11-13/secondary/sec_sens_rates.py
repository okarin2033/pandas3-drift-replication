# Sensitivities of Amendment 11 on the secondary statistics of section 8 (LR82.2 item 10, REVIEW W-3).
# Written 2026-11-13 in the T11 preparation step. Status: draft; decides nothing.
#
# The frozen analyzer recomputes the five tests and the three keys of `run_tests` under each sensitivity of Amendment 11 (LR13 a, b, LR14,
# LR16 a, b, LR17). This tool builds the remaining secondary statistics of section 8 that the frozen code computes from `flat` rows with
# one function: the per model x stratum rates with Wilson and task-cluster bootstrap intervals and the rare-event bound, the per model x
# family rates, and `rare_M` (the fields summarize() copies from the rates). It does so ONLY by calling frozen functions with the frozen
# alternative inputs:
#   alternative inputs   lead_rulings.tasks_with_flags, lead_rulings_2.load_pre_lr1_oracle / _deps_with / _flagged_ids / load_flags_all
#   rebuilt rows         analyze_full.build_per_program (the same call as lead_rulings_2.alt_analysis)
#   statistics           analyze_full.flatten, analyze_full.rate_tables; stratum R without the ruled tasks: lead_rulings_2.stratum_rates
#                        through lr61_report.without_ruled (LR61, LR70)
# Not built (listed in CHOICES_RULED.md, to be recorded as a deviation): the per-family H4 (h4_stratum_M.per_family) and the sensitivities of
# section 8 that need code outside a single frozen function (3.x-only denominator, de-duplication, fixed-weight pooling).
# It reads run records through build_per_program, so it runs at T11 (after the frozen analysis) on the study's runs; on test data it runs
# on the pilot regression with synthetic flag files. A self-check recomputes the primary rate tables from per_program.jsonl and compares
# them with summary.json (exit 3 on a difference): this shows that the call matches the frozen one.
#   envs/tools/bin/python -I -B sec_sens_rates.py <common> --runs runs --gen-dir generations --targets E0a~E1,E0a~E2 \
#       --oracle-pre-lr1 <copy> [--oracle-pre-lr1-seal <seal>] --flags-before tasks/FLAGS_BEFORE_LR2.tsv \
#       --flags-before-lr2-3 tasks/FLAGS_BEFORE_LR2_3.tsv --exposure tasks/exposure_regex.tsv --B 10000 --seed 20261111
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sec_common as C  # noqa: E402

TARGETS_DEFAULT = ('E0a~E1', 'E0a~E2')
LR16_KEYS = (('a', 'lr16_nonunique_whole_row', 'index labels not unique: the whole row is the identity key'),
             ('b', 'lr16_not_found_order_only', 'sort key located in neither result: read as ORDER_ONLY'))
RATE_FIELDS = ('x', 'n', 'generated', 'rate', 'wilson_lo', 'wilson_hi', 'boot_lo', 'boot_hi', 'boot_dropped', 'cp_deff_upper', 'deff', 'icc',
               'n_eff', 'rare_event')


class Frozen:
    """The frozen modules, imported through sec_common.harness (no bytecode)."""

    def __init__(self, study):
        C.harness(study)
        import analyze_full as af
        import lead_rulings as lr
        import lead_rulings_2 as lr2
        import lr61_report as lr61
        self.af, self.lr, self.lr2, self.lr61 = af, lr, lr2, lr61


def alternatives(F, tasks, deps, flags_yes, flags_23, flags_all, pre_oracle_deps):
    """-> [(id, label text, alt tasks, ids to rebuild, deps for the rebuild)] for the sensitivities of Amendment 11, built exactly as
    lead_rulings_2.lr13 / flags_snapshot / lr16 build them."""
    lr, lr2 = F.lr, F.lr2
    out = [('LR13 (a)', 'pre-LR1 key rule with the current flags', tasks, lr2._flagged_ids(tasks), pre_oracle_deps)]
    alt, changed = lr.tasks_with_flags(tasks, flags_yes)
    out.append(('LR13 (b)', 'pre-LR1 key rule with the flags hashed before LR2', alt, lr2._flagged_ids(alt) | set(changed), pre_oracle_deps))
    alt, changed = lr.tasks_with_flags(tasks, flags_23)
    out.append(('LR14', 'flags sealed before the LR14/LR18 card edits', alt, set(changed), deps))
    for part, key, reading in LR16_KEYS:
        alt = [dict(t, **{key: True}) if t.get('order_significant') else t for t in tasks]
        out.append(('LR16 (%s)' % part, reading, alt, lr2._flagged_ids(tasks), deps))
    alt, changed = lr.tasks_with_flags(tasks, flags_all)
    out.append(('LR17', 'flags before LR2 for all tasks', alt, set(changed), deps))
    return out


def alt_rows(F, runs, models, gen_dir, per_program, alt_tasks, rebuild_ids, deps_alt):
    rebuilt = F.af.build_per_program(runs, [t for t in alt_tasks if t['id'] in set(rebuild_ids)], models, deps_alt, gen_dir) \
        if rebuild_ids else []
    rb = {p['program_id']: p for p in rebuilt}
    return [rb.get(p['program_id'], p) for p in per_program], len(rebuilt)


def rate_rows(F, pps, tasks, plan, pair, B, seed, use_numpy):
    """The frozen rate tables of one pair as flat rows (model x stratum, model x family)."""
    af, lr = F.af, F.lr
    tmap = {t['id']: t for t in tasks}
    flat = [af.flatten(p, pair, tmap) for p in pps]
    models = lr._models_all(plan, pps)
    rates, fam = af.rate_tables(flat, models, lr._univ(tasks), B, seed, use_numpy)
    rows = []
    for m in models:
        for s, e in sorted((rates.get(m) or {}).items()):
            rows.append(dict(model=m, stratum=s, family=None, **{k: C.nn(e.get(k)) for k in RATE_FIELDS}))
        for q, e in sorted((fam.get(m) or {}).items()):
            rows.append(dict(model=m, stratum='M', family=q, **{k: C.nn(e.get(k)) for k in RATE_FIELDS}))
    return rows


def self_check_primary(F, inp, plan, pairs, use_numpy):
    """The primary rate tables recomputed from per_program.jsonl equal summary.targets[pair].rates (x, n, rate, bootstrap bounds)."""
    if (inp.summary.get('B'), inp.summary.get('seed')) != (inp.B, inp.seed):
        raise C.Refuse('--B %s --seed %s differ from the analyzer run (B %s, seed %s): the primary check needs the same bootstrap' % (
            inp.B, inp.seed, inp.summary.get('B'), inp.summary.get('seed')))
    diffs = []
    for pair in pairs:
        mine = rate_rows(F, inp.per_program, inp.tasks, plan, pair, inp.B, inp.seed, use_numpy)
        ref = (((inp.summary.get('targets') or {}).get(pair) or {}).get('rates')) or {}
        for r in mine:
            if r['family'] is not None:
                continue
            e = (ref.get(r['model']) or {}).get(r['stratum'])
            if e is None:
                diffs.append('%s %s %s: no cell in summary.json' % (pair, r['model'], r['stratum']))
                continue
            for k in ('x', 'n', 'boot_lo', 'boot_hi'):
                a, b = r[k], C.nn(e.get(k))
                if (a is None) != (b is None) or (a is not None and abs(a - b) > 1e-12):
                    diffs.append('%s %s %s %s: tool %r, summary %r' % (pair, r['model'], r['stratum'], k, a, b))
    if diffs:
        raise C.SelfCheckFailed('primary rate tables differ from summary.json:\n  ' + '\n  '.join(diffs[:20]))
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    C.add_common_args(ap)
    ap.add_argument('--runs', required=True)
    ap.add_argument('--gen-dir', required=True)
    ap.add_argument('--targets', default=','.join(TARGETS_DEFAULT))
    ap.add_argument('--exposure', default=None, help="as analyze_full.py: tasks/exposure_regex.tsv, or 'none' for test data")
    ap.add_argument('--oracle-pre-lr1', default=None)
    ap.add_argument('--oracle-pre-lr1-seal', default=None)
    ap.add_argument('--flags-before', default=None)
    ap.add_argument('--flags-before-lr2-3', default=None)
    ap.add_argument('--dtype-signal', choices=('default', 'on', 'off'), default='default')
    ap.add_argument('--ruled-path', default=None)
    a = ap.parse_args(argv)
    for p in (a.runs, a.gen_dir):
        if not os.path.isdir(p):
            raise C.Refuse('%r is not a folder' % os.path.basename(p))
    inp = C.load_inputs(a)
    C.harness(inp.study)
    F = Frozen(inp.study)
    pairs = [x for x in a.targets.split(',') if x]
    deps = F.af.load_deps(inp.study, a.exposure)
    if a.dtype_signal != 'default':
        import attribution as _attr
        _attr.DTYPE_SIGNAL_DEFAULT = (a.dtype_signal == 'on')
    plan = F.af.default_plan(inp.study)
    plan['n_tasks'] = len(inp.tasks)
    use_numpy = None
    kw = {}
    if a.oracle_pre_lr1:
        kw['path'] = os.path.abspath(a.oracle_pre_lr1)
    if a.oracle_pre_lr1_seal:
        kw['seal'] = os.path.abspath(a.oracle_pre_lr1_seal)
    try:
        pre = F.lr2.load_pre_lr1_oracle(**kw)
    except F.lr2.SealError as e:
        raise C.Refuse(str(e))
    dpre = F.lr2._deps_with(deps, pre.classify_program)
    flags_yes = F.lr.load_flags_before(a.flags_before or F.lr.FLAGS_BEFORE_FILE)
    flags_all = F.lr2.load_flags_all(a.flags_before or F.lr.FLAGS_BEFORE_FILE)
    flags_23 = F.lr2.load_flags_all(a.flags_before_lr2_3 or F.lr2.FLAGS_BEFORE_LR2_3_FILE)
    C.self_check(inp)
    self_check_primary(F, inp, plan, pairs, use_numpy)
    ruled = C.get_ruled(inp)
    alts = alternatives(F, inp.tasks, deps, flags_yes, flags_23, flags_all, dpre)
    rows, counts, r_rows = [], {}, []
    for ident, reading, alt_tasks, rebuild_ids, deps_alt in alts:
        pps, n_rebuilt = alt_rows(F, a.runs, inp.models, a.gen_dir, inp.per_program, alt_tasks, rebuild_ids, deps_alt)
        counts[ident] = {'reading': reading, 'tasks_rebuilt': len(set(rebuild_ids)), 'programs_rebuilt': n_rebuilt}
        for pair in pairs:
            for r in rate_rows(F, pps, alt_tasks, plan, pair, inp.B, inp.seed, use_numpy):
                rows.append(dict(r, sensitivity=ident, pair=pair, variant='all tasks'))
            if ruled is not None:
                blk = F.lr61.without_ruled(lambda pp, tk, pair=pair: F.lr2.stratum_rates(pp, tk, plan, 'R', inp.B, inp.seed, use_numpy, pair),
                                           pps, alt_tasks, ruled=ruled)
                for m, e in sorted(blk['result'].items()):
                    r_rows.append(dict(model=m, stratum='R', family=None, sensitivity=ident, pair=pair,
                                       variant='without ruled R tasks (LR61/LR70)', **{k: C.nn(e.get(k)) for k in RATE_FIELDS}))
    rows += r_rows
    cols = ['sensitivity', 'pair', 'variant', 'model', 'stratum', 'family'] + list(RATE_FIELDS)
    meta = C.meta_block(inp, os.path.abspath(__file__), ['B.38s'], {'sensitivities': counts, 'pairs': pairs, 'primary_check': 'passed',
                                                                    'oracle_pre_lr1_name': os.path.basename(pre.__file__)})
    md = C.header_md(inp, 'B.38s', 'Rate tables of section 8 under the sensitivities of Amendment 11', meta,
                     'Per model x stratum rates (Wilson, task-cluster bootstrap, rare-event bound) and per model x family rates recomputed by the '
                     'frozen analyze_full.rate_tables on the rows of each sensitivity (LR13 a, b, LR14, LR16 a, b, LR17), built by the frozen '
                     'build_per_program with the frozen alternative inputs. The primary tables were recomputed first and equal summary.json. '
                     'Stratum-R rows are repeated without the ruled R tasks (LR61/LR70). Not built: the per-family H4 and the other section 8 '
                     'sensitivities (see CHOICES_RULED.md).')
    md += ['', 'Rows rebuilt per sensitivity: ' + '; '.join('%s: %d programs of %d tasks' % (k, v['programs_rebuilt'], v['tasks_rebuilt'])
                                                            for k, v in counts.items()), '',
           C.md_table(['sensitivity', 'pair', 'variant', 'model', 'stratum', 'x', 'n', 'rate', 'boot_lo', 'boot_hi'],
                      [r for r in rows if r['family'] is None], 80)]
    C.emit(a.out, 'B.38s', inp, meta, md, [('rates', cols, rows)], {'item': 'B.38s', 'rows': rows, 'sensitivities': counts})
    print('wrote B38s.{json,md,tsv} (primary check passed)')
    return 0


if __name__ == '__main__':
    sys.exit(C.run_main(main))
