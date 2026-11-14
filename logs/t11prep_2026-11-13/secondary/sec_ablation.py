# Arm-comparison family of the secondary analyses: B.17 (version-hint ablation) and B.16 (default-effort sensitivity, Sonnet 5.5 on R).
# Written 2026-11-13 in the T11 preparation step. Status: draft; decides nothing; both arms run only if
# approved (LR80 item 9) and executed before T11.
#
# Inputs: the MAIN per_program.jsonl / summary.json (the summary must be COMPLETE, as for every tool) and the per_program.jsonl that
# analyze_full.py wrote for the arm's own runs root (that analyzer run prints INCOMPLETE by design, because generation_state plans
# 200 x 5 programs; the tool therefore does not read the arm's summary and instead refuses unless the arm holds the expected number of
# generated programs: REVIEW T-6, I-12).
#   python3 -I -B sec_ablation.py --analysis B.17 --hint-per-program H.jsonl --sample-tasks ABLATION_SAMPLE.tsv ...
#   python3 -I -B sec_ablation.py --analysis B.16 --arm-per-program D.jsonl --arm-expected-programs N ...
import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sec_common as C  # noqa: E402

PAIR = 'E0a~E1'
ABLATION_MODELS = ('qwen__qwen3.5-9b', 'google__gemma-4-31b-it', 'anthropic__claude-haiku-4.5', 'openai__gpt-5.4-mini')   # 5 l.265-272
ABLATION_TASKS_EXPECTED = 40
ABLATION_HINT_PER_TASK = 3            # k = 3 in the hint arm
ABLATION_NOHINT_SAMPLES = (0, 1, 2)   # the no-hint arm: the main run's s0-s2
B16_MODEL = 'anthropic__claude-sonnet-5.5'
B16_STRATUM = 'R'
B16_DIFFERENCE = True                 # C-12: (a) side by side is always given; (b) the paired-bootstrap difference is added


def read_sample_tasks(path):
    with open(path, encoding='utf-8') as f:
        lines = [ln.rstrip('\n') for ln in f if ln.strip() and not ln.startswith('#')]
    head = lines[0].split('\t')
    col = head.index('task_id') if 'task_id' in head else head.index('id') if 'id' in head else 0
    body = lines[1:] if ('task_id' in head or 'id' in head) else lines
    ids = [ln.split('\t')[col].strip() for ln in body]
    if len(set(ids)) != len(ids):
        raise C.Refuse('sample task file lists a task twice')
    return ids


def arm_stats(inp, rows, models, arms, tasks_univ, stratum):
    """Per model and arm: x, n, rate, Wilson; per model: difference arms[0] - arms[1] with the paired bootstrap (same resampled task
    multiset for both arms and all models). rows carry `arm` and `model`."""
    stats = inp.stats
    out, diffs = [], []
    stat = {}
    for m in models:
        stat[m] = (lambda v, m=m: (lambda a, b: None if a is None or b is None else a - b)(
            v.ratio('silent', 'clean', model=m, arm=arms[0]), v.ratio('silent', 'clean', model=m, arm=arms[1])))
    res = stats.cluster_bootstrap_multi(rows, stat, ['silent', 'clean'], ('model', 'stratum', 'fam', 'arm'), B=inp.B, seed=inp.seed,
                                        tasks=tasks_univ) if rows else {}
    for m in models:
        rate = {}
        for arm in arms:
            sub = [r for r in rows if r['model'] == m and r['arm'] == arm]
            c = C.cell_stats(stats, sub, 'silent')
            out.append({'model': m, 'arm': arm, 'x': c['x'], 'n': c['n'], 'generated': c['generated'], 'rate': c['rate'],
                        'wilson_lo': c['wilson_lo'], 'wilson_hi': c['wilson_hi'], 'rare_event': c['rare_event'],
                        'cp_deff_upper': c['cp_deff_upper']})
            rate[arm] = c['rate']
        b = res.get(m)
        d = None if rate[arms[0]] is None or rate[arms[1]] is None else rate[arms[0]] - rate[arms[1]]
        diffs.append({'model': m, 'difference': d, 'minuend': arms[0], 'subtrahend': arms[1],
                      'boot_lo': C.nn(b['lo']) if b else None, 'boot_hi': C.nn(b['hi']) if b else None,
                      'boot_dropped': b['dropped'] if b else None, 'boot_valid': b['n_valid'] if b else None})
    return out, diffs


def check_arm_complete(arm_pp, models, tasks, expected_per_cell, what):
    cnt = collections.Counter((p['model'], p['task_id']) for p in arm_pp)
    bad = [(m, t, cnt.get((m, t), 0)) for m in models for t in tasks if cnt.get((m, t), 0) != expected_per_cell]
    if bad:
        raise C.Refuse('%s is incomplete or has extra programs: %d (model, task) cells differ from %d programs (first: %s)' % (
            what, len(bad), expected_per_cell, bad[0]))


# ------------------------------------------------------------------------------------------------ B.17
def b17(inp, tool, outdir, hint_path, sample_path, models):
    hint_pp = C.read_jsonl(hint_path)
    sample = read_sample_tasks(sample_path)
    if len(sample) != ABLATION_TASKS_EXPECTED:
        raise C.Refuse('the sample file lists %d tasks, the plan has %d' % (len(sample), ABLATION_TASKS_EXPECTED))
    unknown = [t for t in sample if t not in inp.tmap]
    if unknown:
        raise C.Refuse('sample tasks not in tasks.json: %s' % unknown[:3])
    check_arm_complete([p for p in hint_pp if p['task_id'] in set(sample)], models, sample, ABLATION_HINT_PER_TASK, 'the hint arm')
    sset = set(sample)
    main_pp = [p for p in inp.per_program if p['task_id'] in sset and p.get('sample') in ABLATION_NOHINT_SAMPLES and p['model'] in models]
    check_arm_complete(main_pp, models, sample, len(ABLATION_NOHINT_SAMPLES), 'the no-hint arm (main run s0-s2)')
    rows = [dict(r, arm='no hint') for r in C.flat_rows(main_pp, PAIR, inp.tmap, set(models))]
    rows += [dict(r, arm='hint') for r in C.flat_rows([p for p in hint_pp if p['task_id'] in sset], PAIR, inp.tmap, set(models))]
    tk = [t for t in inp.tasks_univ if t['task_id'] in sset]
    cells, diffs = arm_stats(inp, rows, [m for m in models], ('no hint', 'hint'), tk, 'M')
    fam_counts = collections.Counter(t['fam'] for t in tk)
    meta = C.meta_block(inp, tool, ['B.17'], {'pair': PAIR, 'hint_per_program_sha256': C.sha256_file(hint_path),
                                              'sample_tasks_sha256': C.sha256_file(sample_path), 'models': list(models),
                                              'tasks_per_family': dict(fam_counts)})
    ccols = ['model', 'arm', 'x', 'n', 'generated', 'rate', 'wilson_lo', 'wilson_hi', 'rare_event', 'cp_deff_upper']
    dcols = ['model', 'difference', 'minuend', 'subtrahend', 'boot_lo', 'boot_hi', 'boot_dropped', 'boot_valid']
    md = C.header_md(inp, 'B.17', 'Version-hint ablation (stratum M, 40 tasks)', meta,
                     'Delta_m = r(no hint) - r(hint), r = silent / clean on %s; no-hint arm = main programs s0-s2; each arm judged clean by its '
                     'own E0a/E0b. Paired task-cluster bootstrap, one resampled task multiset for both arms and all models, stratified by '
                     'family. No p-value (the plan states an estimand, not a test).' % PAIR)
    md += ['', C.md_table(dcols, diffs), '', C.md_table(ccols, cells)]
    return C.emit(outdir, 'B.17', inp, meta, md, [('delta', dcols, diffs), ('arms', ccols, cells)],
                  {'item': 'B.17', 'delta': diffs, 'arms': cells})


# ------------------------------------------------------------------------------------------------ B.16
def b16(inp, tool, outdir, arm_path, expected, main_model, arm_model):
    arm_pp = [p for p in C.read_jsonl(arm_path) if p['model'] == arm_model]
    if len(arm_pp) != expected:
        raise C.Refuse('the default-effort arm holds %d programs of %s, expected %d (--arm-expected-programs)' % (len(arm_pp), arm_model, expected))
    arm_pp = [dict(p, model=main_model) for p in arm_pp]
    tasks_in_arm = {p['task_id'] for p in arm_pp}
    notR = [t for t in tasks_in_arm if inp.tmap.get(t, {}).get('stratum') != B16_STRATUM]
    if notR:
        raise C.Refuse('the arm holds programs of tasks outside stratum %s (first: %s)' % (B16_STRATUM, sorted(notR)[0]))   # LR82.2 item 8, D-1: sorted, not hash order
    ruled = C.get_ruled(inp)

    def build(excl):
        main_pp = [p for p in inp.per_program if p['model'] == main_model and p['task_id'] in tasks_in_arm and p['task_id'] not in excl]
        rows = [dict(r, arm='main (set effort)') for r in C.flat_rows(main_pp, PAIR, inp.tmap, {main_model})]
        rows += [dict(r, arm='default effort') for r in C.flat_rows([p for p in arm_pp if p['task_id'] not in excl], PAIR, inp.tmap,
                                                                    {main_model})]
        tk = [t for t in inp.tasks_univ if t['task_id'] in tasks_in_arm and t['task_id'] not in excl]
        return arm_stats(inp, rows, [main_model], ('main (set effort)', 'default effort'), tk, B16_STRATUM)
    variants = [('all tasks', build(set()))]
    if ruled is not None:
        variants.append(('without ruled R tasks (LR61/LR70)', build(set(ruled.ids))))
    cells, diffs = [], []
    for v, (c, d) in variants:
        cells += [dict(x, variant=v) for x in c]
        diffs += [dict(x, variant=v) for x in d]
    meta = C.meta_block(inp, tool, ['B.16'], {'pair': PAIR, 'arm_per_program_sha256': C.sha256_file(arm_path), 'model': main_model,
                                              'arm_model_key': arm_model, 'lr61': C.ruled_meta(ruled)})
    ccols = ['variant', 'model', 'arm', 'x', 'n', 'generated', 'rate', 'wilson_lo', 'wilson_hi', 'rare_event', 'cp_deff_upper']
    dcols = ['variant', 'model', 'difference', 'minuend', 'subtrahend', 'boot_lo', 'boot_hi', 'boot_dropped', 'boot_valid']
    md = C.header_md(inp, 'B.16', 'Default-effort sensitivity (%s on stratum R)' % main_model, meta,
                     'Side by side (C-12 (a)): silent / clean on %s per arm, Wilson 95%%; the difference with a paired task-cluster bootstrap '
                     'over the R tasks of the arm is added (C-12 (b)). Run settings of the arm are not fixed by any ruling (audit M-5).' % PAIR)
    md += ['', C.md_table(ccols, cells)]
    if B16_DIFFERENCE:
        md += ['', C.md_table(dcols, diffs)]
    return C.emit(outdir, 'B.16', inp, meta, md, [('arms', ccols, cells), ('difference', dcols, diffs)],
                  {'item': 'B.16', 'arms': cells, 'difference': diffs if B16_DIFFERENCE else None})


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--analysis', required=True, help='B.17 or B.16')
    C.add_common_args(ap)
    ap.add_argument('--hint-per-program')
    ap.add_argument('--sample-tasks')
    ap.add_argument('--ablation-models', default=','.join(ABLATION_MODELS))
    ap.add_argument('--arm-per-program')
    ap.add_argument('--arm-expected-programs', type=int)
    ap.add_argument('--arm-model', default=B16_MODEL)
    ap.add_argument('--main-model', default=B16_MODEL)
    ap.add_argument('--ruled-path', default=None)
    a = ap.parse_args(argv)
    if a.analysis == 'B.17':
        if not (a.hint_per_program and a.sample_tasks):
            raise C.Refuse('B.17 needs --hint-per-program and --sample-tasks')
        extra = {'hint_per_program.jsonl': a.hint_per_program, 'sample_tasks.tsv': a.sample_tasks}
    elif a.analysis == 'B.16':
        if not (a.arm_per_program and a.arm_expected_programs):
            raise C.Refuse('B.16 needs --arm-per-program and --arm-expected-programs')
        extra = {'arm_per_program.jsonl': a.arm_per_program}
    else:
        raise C.Refuse('unknown analysis %r' % a.analysis)
    inp = C.load_inputs(a, extra)
    C.self_check(inp)
    tool = os.path.abspath(__file__)
    if a.analysis == 'B.17':
        base = b17(inp, tool, a.out, a.hint_per_program, a.sample_tasks, a.ablation_models.split(','))
    else:
        base = b16(inp, tool, a.out, a.arm_per_program, a.arm_expected_programs, a.main_model, a.arm_model)
    print('wrote', os.path.basename(base) + '.{json,md,tsv}')
    return 0


if __name__ == '__main__':
    sys.exit(C.run_main(main))
