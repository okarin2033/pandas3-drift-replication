# Shared library of the secondary-analysis tools (SECONDARY_SPEC.md part B, corrected by REVIEW_SPEC.md).
# LR82 revision 2026-11-13 (lead ruling LR82.2, items 1 to 12): the pair-clean rule requires the main 2.3.3 status as well as the pair's own
# baseline (general rule (i)); `n_own` (the pair's own baseline alone) is a column beside the denominator; agreement statistics use the
# stratified task-cluster bootstrap of the frozen engine; the frozen value is shown where a tool repeats a cell of the analyzer.
# Written 2026-11-13 in the T11 preparation step. Status: draft; decides nothing; every choice the plan does not make is a named constant here or at the
# top of the tool and is listed in CHOICES_AS_BUILT.md.
#
# Inputs of every tool (and nothing else): results/per_program.jsonl, results/summary.json, tasks/tasks.json, models/models.tsv and, for the
# agreement statistics, decoded coding files. Standard library plus the numpy of envs/tools (through harness/stats.py, optional).
# Run with `python3 -I -B` (standard library) or `envs/tools/bin/python -I -B` (numpy for the bootstrap); `-I` removes the script folder
# from sys.path, so every tool inserts its own folder first.
import collections
import datetime
import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------------------------- constants (C-choices)
B_DEFAULT = 10000                       # FULL_PREREG 8 lines 364-368
SEED = 20261111
STRATA = ('M', 'R', 'A')
QFS = ['QF%d' % i for i in range(1, 9)]
SELF_CHECK_PAIRS = ('E0a~E1', 'E0a~E2')  # B.0.3
SELF_CHECK_STOPS = True                  # REVIEW I-15: a difference stops the tool (exit 3); the follow-up (CHANGES row, deviation entry,
                                         # both outputs kept; REVIEW P-3) is for the lead
POOLED_STRATA = ('M', 'R', 'A')          # P-2: the model-equal pooled figure is printed for every stratum alike, none singled out
TEST_LABEL_REQUIRED_FOR_INCOMPLETE = True
# C-1 (REVIEW W-1): items the plan labels keep the plan's label; items without any label in the registered text get LABEL_UNLABELED.
LABEL_UNLABELED = 'exploratory'
ITEM_LABELS = {
    'B.03': ('secondary', '6 l.281, 292-293; 17 l.605'),
    'B.04': (None, '17 l.598; 3 l.111'),
    'B.05': (None, '17 l.598'),
    'B.07': (None, '17 l.599'),
    'B.08': ('secondary', '12 l.473-474; 17 l.599'),
    'B.09': ('secondary', '4.4 l.226-227; 6 l.296; 17 l.599'),
    'B.10': ('secondary', '16 W4 l.577; 17 l.599-600'),
    'B.11': ('exploratory', '4.1 l.135-137; 17 l.600'),
    'B.12': (None, '17 l.601'),
    'B.13': (None, '17 l.601'),
    'B.14': (None, '17 l.601; 9 l.405-408; 6 l.297'),
    'B.15': (None, '17 l.601-602; 12 l.493-494'),
    'B.16': ('secondary', '17 l.602; 13 l.513; LR77 (b), (c)'),
    'B.17': ('secondary, not confirmatory', '5 l.265-272; LR77 (a)'),
    'B.19': ('sensitivity', '8 l.387; 4.1 l.153-158; Amendment 1 S1'),
    'B.20': ('sensitivity', '8 l.384-386; Amendment 1 M7'),
    'B.22': ('added report (lead rulings LR3, LR4)', 'LEAD_RULINGS_LR1-LR12 l.25, 27'),
    'B.25': ('secondary check', '10.4 l.448-450; 17 l.604'),
    'B.29': (None, '4.3 l.185; Amendment 1 S4; 17 l.605'),
    'B.30': (None, '11 l.465-466'),
    'B.31': ('registered validation report', '11 l.467-468; STAGE2 T12.5'),
    'B.32': ('as registered (agreement of coders)', '10.4 l.446-457; STAGE2 T12.3'),
    'B.33': ('secondary check', '10.4 l.448-449'),
    'B.34': ('secondary', '3 l.106-107'),
    'B.35': ('sensitivity', '8 l.387 "model-equal weighting for H4"'),
    'B.36': ('sensitivity', '3 l.97-98; 8 l.386'),
    'B.38s': ('sensitivity', '8 l.384-388; Amendment 11 l.81-82 (registered secondary statistics of section 8); LR82.2 item 10'),
    # LR82.2 item 11 (items the review found missing) and item 12
    'B.40': ('reported with the results', 'LEAD_RULINGS_LR80 item 8'),
    'X-1': ('registered report (Amendment 2 (a) and (c))', 'Amendment 2 (a), (c); LR2.5'),
    'X-3': ('registered count', '6 l.302'),
    'X-4': ('registered report', '12 l.478-479; 13 l.538; STAGE2 T9.4'),
    'X-5': ('registered controls', '9'),
    'X-6': ('registered procedure (resolution of coding disagreements)', '10.4; LR82.2 item 12'),
    'X-7': ('registered disclosure', 'Amendments 13 and 14 (provider table)'),
}


def item_label(item):
    lab, src = ITEM_LABELS[item]
    return (lab if lab else LABEL_UNLABELED), src, (lab is None)


class Refuse(Exception):
    """The tool refuses to run (exit 2): INCOMPLETE or labelled input, missing file, inconsistent input."""


class SelfCheckFailed(Exception):
    """B.0.3: the tool's own x and n differ from summary.json (exit 3)."""


# ---------------------------------------------------------------------------------------------- files
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def find_study(explicit=None):
    """The study folder S (the one that holds harness/stats.py): --study, else the nearest parent of this file."""
    cands = [explicit] if explicit else []
    d = HERE
    for _ in range(8):
        cands.append(d)
        d = os.path.dirname(d)
    for c in cands:
        if c and os.path.isfile(os.path.join(c, 'harness', 'stats.py')):
            return os.path.abspath(c)
    raise Refuse('study folder not found (no harness/stats.py); give --study')


_harness_loaded = {}


def harness(study):
    """-> the frozen harness module stats (and lr61_report on demand); never edited, imported without bytecode."""
    hdir = os.path.join(study, 'harness')
    if hdir not in sys.path:
        sys.path.insert(0, hdir)
    sys.dont_write_bytecode = True
    import stats
    return stats


def lr61(study):
    harness(study)
    import lr61_report
    return lr61_report


def read_jsonl(path):
    out = []
    with open(path, encoding='utf-8') as f:
        for ln in f:
            if ln.strip():
                out.append(json.loads(ln))
    return out


def read_tsv(path):
    with open(path, encoding='utf-8') as f:
        lines = [ln.rstrip('\n') for ln in f if ln.strip() and not ln.startswith('#')]
    head = lines[0].split('\t')
    return [dict(zip(head, ln.split('\t'))) for ln in lines[1:]]


def family_code(fam):
    return fam.split('_')[0] if fam else None


def model_key(openrouter_id):
    return openrouter_id.replace('/', '__')


# ---------------------------------------------------------------------------------------------- inputs
class Inputs:
    pass


def add_common_args(ap, need_models=False):
    ap.add_argument('--per-program', required=True, help='results/per_program.jsonl')
    ap.add_argument('--summary', required=True, help='results/summary.json (its decision.status must be COMPLETE)')
    ap.add_argument('--tasks', required=True, help='tasks/tasks.json')
    ap.add_argument('--models-tsv', required=need_models, default=None, help='models/models.tsv')
    ap.add_argument('--out', required=True, help='output folder (created)')
    ap.add_argument('--B', type=int, default=B_DEFAULT)
    ap.add_argument('--seed', type=int, default=SEED)
    ap.add_argument('--study', default=None)
    ap.add_argument('--test-label', default=None,
                    help='non-study data only: the exact label of summary.json (for example "pilot regression, not study data"); '
                         'then an INCOMPLETE summary is accepted and every output carries the label')
    ap.add_argument('--models', default=None, help='comma-separated model keys to report (default: all present)')


def load_tasks(path):
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    return d if isinstance(d, list) else d['tasks']


def load_inputs(a, extra_files=None):
    """Read and check the inputs; refuse on INCOMPLETE (B.0 / task statement)."""
    inp = Inputs()
    inp.study = find_study(a.study)
    inp.stats = harness(inp.study)
    inp.B, inp.seed = a.B, a.seed
    with open(a.summary, encoding='utf-8') as f:
        inp.summary = json.load(f)
    dec = inp.summary.get('decision') or {}
    status = dec.get('status')
    label = inp.summary.get('label')
    inp.test_mode = False
    if status != 'COMPLETE':
        ok_test = bool(a.test_label) and label == a.test_label
        if not ok_test:
            raise Refuse('input is marked %r (summary.decision.status); the tool runs only on a COMPLETE decision '
                         '(or on non-study data with --test-label equal to the summary label)' % (status,))
        inp.test_mode = True
    if label:
        if not a.test_label or label != a.test_label:
            raise Refuse('summary.json carries the label %r; give --test-label with that exact text to run on non-study data' % (label,))
        inp.test_mode = True
    elif a.test_label:
        raise Refuse('--test-label given but summary.json has no label: not non-study data')
    inp.label = label if inp.test_mode else None
    inp.per_program = read_jsonl(a.per_program)
    n = inp.summary.get('n_programs')
    if n is not None and n != len(inp.per_program):
        raise Refuse('per_program.jsonl has %d lines but summary.n_programs is %s' % (len(inp.per_program), n))
    inp.tasks = load_tasks(a.tasks)
    inp.tmap = {t['id']: t for t in inp.tasks}
    inp.tasks_univ = [{'task_id': t['id'], 'stratum': t.get('stratum'), 'fam': family_code(t.get('family'))} for t in inp.tasks]
    inp.models_rows = read_tsv(a.models_tsv) if a.models_tsv else None
    present = sorted({p['model'] for p in inp.per_program})
    inp.models = [m for m in (a.models.split(',') if a.models else present) if m in present]
    inp.files = {'per_program.jsonl': sha256_file(a.per_program), 'summary.json': sha256_file(a.summary),
                 'tasks.json': sha256_file(a.tasks)}
    if a.models_tsv:
        inp.files['models.tsv'] = sha256_file(a.models_tsv)
    for k, v in (extra_files or {}).items():
        inp.files[k] = sha256_file(v)
    inp.ruled = None                    # tests may inject a lr61_report.RuledList
    inp.ruled_path = getattr(a, 'ruled_path', None)
    return inp


# ---------------------------------------------------------------------------------------------- pair rule (B.0.2)
def pair_status(p, pair):
    """-> (kind, target block). kind: NO_TARGET, RUN_PROBLEM, EXCL_FAIL, EXCL_NONDET, MISSING_BASE, BASE_NOT_OK, MAIN_NOT_CLEAN or CLEAN.
    CLEAN = the pair block exists, `excluded` is None, `run_problem` is None and the program is clean on 2.3.3 in the main run
    (LR82.2 item 2, general rule (i): main-clean and own-baseline-clean). MAIN_NOT_CLEAN = the pair's own gate is open (variant pairs
    whose own E0a/E0b are clean) but the program is not clean on 2.3.3 in the main run. A block without the `excluded` key falls back
    to the program's baseline exclusion (clean_on_233 / exclusion), the conservative reading."""
    t = (p.get('targets') or {}).get(pair)
    if t is None:
        return 'NO_TARGET', None
    if 'excluded' in t:
        ex = t['excluded']
    else:
        ex = None if p.get('clean_on_233') else (p.get('exclusion') or 'EXCL_FAIL')
    if ex:
        return str(ex).split(':')[0], t
    if t.get('run_problem'):
        return 'RUN_PROBLEM', t
    if p.get('clean_on_233') is False:
        return 'MAIN_NOT_CLEAN', t
    return 'CLEAN', t


STATUS_KINDS = ('CLEAN', 'NO_TARGET', 'RUN_PROBLEM', 'EXCL_FAIL', 'EXCL_NONDET', 'MISSING_BASE', 'BASE_NOT_OK', 'MAIN_NOT_CLEAN')


def outcome_fields(p, t, kind):
    """Numeric outcome flags of one program on one pair; every flag is 0 unless the pair is clean."""
    z = {'clean': 0, 'clean_own': 0, 'silent': 0, 'drift': 0, 'drift_any': 0, 'loud': 0, 'warned': 0, 'warning_only': 0,
         'loc_silent': 0, 'loc_silent_any': 0, 'loc_none': 0, 'silent_pilotdef': 0, 'drift_unwarned': 0, 'drift_warned_pilot': 0,
         'drift_unwarned_pilot': 0, 'clean_nd': 0}
    if kind == 'MAIN_NOT_CLEAN':
        z['clean_own'] = 1               # LR82.2 item 2: the pair's own baseline alone (variant pairs); outside the denominator
        return z
    if kind != 'CLEAN':
        return z
    drift_any = bool(t.get('drift'))
    subst = drift_any and t.get('magnitude') == 'SUBSTANTIVE'
    warned_t = bool((t.get('warned_target') or {}).get('prereg'))
    warned_t_pilot = bool((t.get('warned_target') or {}).get('pilot'))
    warned_233 = bool((p.get('warned_E0a') or {}).get('prereg'))
    ls = t.get('locally_silent')
    z.update({
        'clean': 1, 'clean_own': 1,
        'silent': 1 if t.get('silent') else 0,
        'drift': 1 if subst else 0, 'drift_any': 1 if drift_any else 0,
        'loud': 1 if t.get('class') == 'LOUD' else 0,
        'warned': 1 if (subst and warned_t) else 0,
        'warning_only': 1 if t.get('warning_only') else 0,
        'loc_silent': 1 if (subst and ls is True) else 0,
        'loc_silent_any': 1 if (drift_any and ls is True) else 0,
        'loc_none': 1 if (drift_any and ls is None) else 0,
        'silent_pilotdef': 1 if (subst and not warned_t_pilot) else 0,
        'drift_unwarned': 1 if (subst and not warned_233) else 0,
        'drift_warned_pilot': 1 if (subst and bool((p.get('warned_E0a') or {}).get('pilot'))) else 0,
        'drift_unwarned_pilot': 1 if (subst and not bool((p.get('warned_E0a') or {}).get('pilot'))) else 0,
        'clean_nd': 1 if p.get('duplicate_body_of') is None else 0,
    })
    return z


def flat_rows(per_program, pair, tmap=None, models=None):
    """One row per program for `pair` (B.0.2). Keys: model, task_id, stratum, fam, gen, status, plus outcome_fields."""
    out = []
    for p in per_program:
        if models is not None and p['model'] not in models:
            continue
        kind, t = pair_status(p, pair)
        task = (tmap or {}).get(p['task_id'], {})
        fam = family_code(p.get('family')) or family_code(task.get('family'))
        r = {'model': p['model'], 'task_id': p['task_id'], 'program_id': p.get('program_id'), 'stratum': p['stratum'],
             'fam': fam if p['stratum'] == 'M' else None, 'gen': 1, 'status': kind, 'sample': p.get('sample')}
        r.update(outcome_fields(p, t or {}, kind))
        out.append(r)
    return out


def status_counts(rows, models):
    """{(model, stratum): {kind: count}} for the exclusion/missing report (never part of a denominator)."""
    c = collections.defaultdict(lambda: collections.Counter())
    for r in rows:
        if r['model'] in models:
            c[(r['model'], r['stratum'])][r['status']] += 1
    return c


# ---------------------------------------------------------------------------------------------- self-check (B.0.3)
def self_check(inp):
    """x (silent) and n (clean) of E0a~E1 and E0a~E2 per model x stratum must equal summary.targets[q].rates[m][s].x/.n."""
    diffs = []
    for q in SELF_CHECK_PAIRS:
        tg = (inp.summary.get('targets') or {}).get(q)
        if tg is None:
            diffs.append('summary.targets has no %s' % q)
            continue
        rates = tg.get('rates') or {}
        rows = flat_rows(inp.per_program, q, inp.tmap)
        mine = collections.defaultdict(lambda: [0, 0])
        for r in rows:
            mine[(r['model'], r['stratum'])][0] += r['silent']
            mine[(r['model'], r['stratum'])][1] += r['clean']
        keys = set(mine) | {(m, s) for m, d in rates.items() for s in d}
        for (m, s) in sorted(keys):
            e = (rates.get(m) or {}).get(s)
            x, n = mine.get((m, s), [0, 0])
            if e is None:
                if x or n:
                    diffs.append('%s %s %s: tool x=%d n=%d, summary has no cell' % (q, m, s, x, n))
            elif (e.get('x'), e.get('n')) != (x, n):
                diffs.append('%s %s %s: tool x=%d n=%d, summary x=%s n=%s' % (q, m, s, x, n, e.get('x'), e.get('n')))
    # LOUD and WARNING_ONLY counts per model on E0a~E1 against summary.models[m]['outcomes_E0a~E1'] (when the summary has them)
    rows1 = flat_rows(inp.per_program, SELF_CHECK_PAIRS[0], inp.tmap)
    for m, e in (inp.summary.get('models') or {}).items():
        oc = (e or {}).get('outcomes_E0a~E1')
        if not isinstance(oc, dict):
            continue
        for key, field in (('LOUD', 'loud'), ('WARNING_ONLY', 'warning_only')):
            mine_n = sum(r[field] for r in rows1 if r['model'] == m)
            if oc.get(key, 0) != mine_n:
                diffs.append('E0a~E1 %s %s: tool %d, summary.models %s' % (m, key, mine_n, oc.get(key, 0)))
    if diffs and SELF_CHECK_STOPS:
        raise SelfCheckFailed('self-check B.0.3 failed:\n  ' + '\n  '.join(diffs[:30]) + ('\n  ... %d more' % (len(diffs) - 30) if len(diffs) > 30 else '')
                              + '\n  Follow-up (LR82.2 item 9): write this stop into the T11 log, keep both outputs, look for the cause in the code '
                                'and on pilot data without opening further study outputs; a change of a secondary tool after its hash is a '
                                'row in CHANGES.md; a defect of the frozen analyzer follows the plan (stop, fix, log, re-run everything affected).')
    return {'pairs': list(SELF_CHECK_PAIRS), 'differences': diffs, 'passed': not diffs}


# ---------------------------------------------------------------------------------------------- rate engine
def nn(v):
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v)):
        return None
    return v


def wilson(stats, x, n):
    if n <= 0:
        return None, None, None
    p, lo, hi = stats.wilson(x, n)
    return p, lo, hi


def rare(stats, rows, outcome):
    by = collections.defaultdict(list)
    for r in rows:
        if r['clean']:
            by[r['task_id']].append(r[outcome])
    rb = stats.rare_bound(by)
    return nn(rb['upper']), nn(rb['deff']), nn(rb['icc'])


def cell_stats(stats, rows, outcome, rare_mode='deff'):
    """rare_mode 'deff': design-effect-adjusted Clopper-Pearson bound (frozen rule, program level); 'plain': plain one-sided
    Clopper-Pearson (when the unit is the task, so there is no clustering to adjust for)."""
    x = sum(r[outcome] for r in rows)
    n = sum(r['clean'] for r in rows)
    p, lo, hi = wilson(stats, x, n)
    if n <= 0:
        up, deff, icc = None, None, None
    elif rare_mode == 'plain':
        up, deff, icc = nn(stats.cp_upper(x, n)), None, None
    else:
        up, deff, icc = rare(stats, rows, outcome)
    return {'x': x, 'n': n, 'n_own': sum(r['clean_own'] for r in rows), 'generated': sum(r['gen'] for r in rows), 'rate': p,
            'wilson_lo': lo, 'wilson_hi': hi, 'rare_event': bool(n > 0 and x < 5), 'cp_deff_upper': up, 'deff': deff, 'icc': icc}


def rate_cells(inp, rows, outcomes, strata=STRATA, splits=None, split_of=None, families=True, pooled=True, bootstrap=True,
               models=None, cell_bootstrap=True, rare_mode='deff', common_entering=False):
    """Per outcome x model x stratum (x split): x, n, Wilson, paired task-cluster bootstrap, rare bound; per family inside M
    (Wilson + rare bound); the model-equal pooled rate per stratum (and split) with a paired bootstrap that drops a resample when an
    entering model has n = 0 in it. `split_of(row)` assigns a split value (None = no split). `common_entering` (LR82.2 item 8, S-6): the
    pooled rate of every split is taken over the SAME models, those with a denominator in every split."""
    stats = inp.stats
    models = models or inp.models
    if split_of is not None:
        rows = [dict(r, split=split_of(r)) for r in rows]
    else:
        rows = [dict(r, split=None) for r in rows]
    cells = []
    fields = list(outcomes) + ['clean', 'clean_own', 'gen']
    for s in strata:
        rs = [r for r in rows if r['stratum'] == s and r['model'] in models]
        if not rs:
            continue
        sp_vals = sorted({r['split'] for r in rs}, key=str) if split_of is not None else [None]
        if splits is not None:
            sp_vals = [v for v in splits if v in sp_vals] + [v for v in sp_vals if v not in splits]
        stat = {}
        entering = {}
        for o in outcomes:
            for sp in sp_vals:
                if common_entering:
                    ent = [m for m in models if all(sum(r['clean'] for r in rs if r['model'] == m and r['split'] == s2) > 0
                                                    for s2 in sp_vals)]
                else:
                    ent = [m for m in models if sum(r['clean'] for r in rs if r['model'] == m and r['split'] == sp) > 0]
                entering[(o, sp)] = ent
                for m in (models if cell_bootstrap else []):
                    stat[('cell', o, m, sp)] = _ratio_stat(o, m, s, sp, split_of is not None)
                if pooled and s in POOLED_STRATA:
                    stat[('pool', o, '', sp)] = _pool_stat(o, ent, s, sp, split_of is not None)
        res = {}
        if bootstrap and stat:
            tk = [t for t in inp.tasks_univ if t['stratum'] == s]
            res = stats.cluster_bootstrap_multi(rs, stat, fields, ('model', 'stratum', 'fam', 'split'), B=inp.B, seed=inp.seed,
                                                tasks=tk)
        for o in outcomes:
            for sp in sp_vals:
                for m in models:
                    sub = [r for r in rs if r['model'] == m and r['split'] == sp]
                    if not sub:
                        continue
                    c = cell_stats(stats, sub, o, rare_mode)
                    b = res.get(('cell', o, m, sp))
                    c.update({'outcome': o, 'model': m, 'stratum': s, 'family': None, 'split': sp,
                              'boot_lo': nn(b['lo']) if b else None, 'boot_hi': nn(b['hi']) if b else None,
                              'boot_dropped': b['dropped'] if b else None})
                    cells.append(c)
                    if families and s == 'M':
                        for q in QFS:
                            sf = [r for r in sub if r['fam'] == q]
                            if sf:
                                cf = cell_stats(stats, sf, o, rare_mode)
                                cf.update({'outcome': o, 'model': m, 'stratum': s, 'family': q, 'split': sp, 'boot_lo': None,
                                           'boot_hi': None, 'boot_dropped': None})
                                cells.append(cf)
                if pooled and s in POOLED_STRATA:
                    ent = entering[(o, sp)]
                    if ent:
                        rate = _mean([_r(rs, o, m, sp) for m in ent])
                        b = res.get(('pool', o, '', sp))
                        cells.append({'outcome': o, 'model': 'MODEL_EQUAL_MEAN', 'stratum': s, 'family': None, 'split': sp,
                                      'x': None, 'n': None, 'n_own': None, 'generated': None, 'rate': rate, 'wilson_lo': None,
                                      'wilson_hi': None, 'rare_event': None, 'cp_deff_upper': None, 'deff': None, 'icc': None,
                                      'boot_lo': nn(b['lo']) if b else None, 'boot_hi': nn(b['hi']) if b else None,
                                      'boot_dropped': b['dropped'] if b else None, 'entering_models': len(ent)})
    return cells


def _r(rs, o, m, sp):
    sub = [r for r in rs if r['model'] == m and r['split'] == sp]
    n = sum(r['clean'] for r in sub)
    return None if n == 0 else sum(r[o] for r in sub) / n


def _mean(vals):
    return None if (not vals or any(v is None for v in vals)) else sum(vals) / len(vals)


def _ratio_stat(o, m, s, sp, use_split):
    if use_split:
        return lambda v: v.ratio(o, 'clean', model=m, stratum=s, split=sp)
    return lambda v: v.ratio(o, 'clean', model=m, stratum=s)


def _pool_stat(o, ent, s, sp, use_split):
    def f(v):
        kw = {'stratum': s}
        if use_split:
            kw['split'] = sp
        vals = [v.ratio(o, 'clean', model=m, **kw) for m in ent]
        return _mean(vals)
    return f


CELL_COLUMNS = ['variant', 'outcome', 'model', 'stratum', 'family', 'split', 'x', 'n', 'n_own', 'generated', 'rate', 'wilson_lo',
                'wilson_hi', 'boot_lo', 'boot_hi', 'boot_dropped', 'rare_event', 'cp_deff_upper', 'entering_models']


# ---------------------------------------------------------------------------------------------- LR61 / LR70 (B.0.6)
def has_stratum_R(inp):
    return any(t.get('stratum') == 'R' for t in inp.tasks)


def with_ruled(inp, compute):
    """compute(per_program, tasks) -> result. Returns (main, lr61 block | None). The block is produced by lr61_report.without_ruled and
    is labelled lr61_report.LABEL; it exists when the tasks hold stratum R. Raises Refuse if the ruled list cannot be read."""
    main = compute(inp.per_program, inp.tasks)
    if not has_stratum_R(inp):
        return main, None
    mod = lr61(inp.study)
    try:
        ruled = inp.ruled if inp.ruled is not None else mod.load_ruled(inp.study, inp.ruled_path)
    except Exception as e:                                         # RuledListError and file errors
        raise Refuse('LR61/LR70: the ruled list cannot be used: %s' % e)
    blk = mod.without_ruled(compute, inp.per_program, inp.tasks, ruled=ruled)
    return main, blk


def cells_variants(inp, compute_cells):
    """compute_cells(per_program, tasks_univ_filter) -> list of cells. Adds the without-ruled variant for stratum R."""
    def compute(pps, tasks):
        sub = _SubInputs(inp, pps, tasks)
        return compute_cells(sub)
    main, blk = with_ruled(inp, compute)
    out = [dict(c, variant='all tasks') for c in main]
    meta = None
    if blk is not None:
        out += [dict(c, variant='without ruled R tasks (LR61/LR70)') for c in blk['result'] if c['stratum'] == 'R']
        meta = {k: blk[k] for k in ('label', 'ruled_file', 'ruled_file_sha256', 'listed_tasks', 'tasks_left_out',
                                    'n_tasks_kept', 'n_programs_left_out')}
    return out, meta


class _SubInputs:
    """The same inputs on a subset of programs and tasks (for the without-ruled call)."""

    def __init__(self, inp, pps, tasks):
        self.__dict__.update(inp.__dict__)
        self.per_program = pps
        self.tasks = tasks
        self.tmap = {t['id']: t for t in tasks}
        self.tasks_univ = [{'task_id': t['id'], 'stratum': t.get('stratum'), 'fam': family_code(t.get('family'))} for t in tasks]


# ---------------------------------------------------------------------------------------------- output
def jsonable(o):
    if isinstance(o, float):
        if math.isnan(o):
            return None
        if math.isinf(o):
            return 'inf' if o > 0 else '-inf'
        return o
    if isinstance(o, dict):
        return {str(k) if not isinstance(k, str) else k: jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, set, frozenset)):
        return [jsonable(v) for v in (sorted(o, key=str) if isinstance(o, (set, frozenset)) else o)]
    return o


def fmt(v, d=3):
    if v is None:
        return ''
    if isinstance(v, bool):
        return 'yes' if v else 'no'
    if isinstance(v, float):
        if math.isnan(v):
            return ''
        if math.isinf(v):
            return 'inf' if v > 0 else '-inf'
        return ('%.' + str(d) + 'f') % v
    return str(v)


def meta_block(inp, tool_file, item_ids, extra=None):
    created = datetime.datetime.now().astimezone().strftime('%Y-%m-%dT%H:%M:%S%z')
    m = {'label': inp.label, 'test_mode': inp.test_mode, 'items': item_ids,
         'inputs_sha256': inp.files, 'B': inp.B, 'seed': inp.seed,
         'tool': os.path.basename(tool_file), 'tool_sha256': sha256_file(tool_file),
         'sec_common_sha256': sha256_file(os.path.abspath(__file__)),
         'harness_stats_sha256': sha256_file(os.path.join(inp.study, 'harness', 'stats.py')),
         'created': created, 'numpy_used': getattr(inp.stats, '_np', None) is not None}
    if extra:
        m.update(extra)
    return m


def write_tsv(path, columns, rows):
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write('\t'.join(columns) + '\n')
        for r in rows:
            f.write('\t'.join(fmt(r.get(c), 6) if not isinstance(r.get(c), str) else r.get(c).replace('\t', ' ').replace('\n', ' ')
                              for c in columns) + '\n')


def md_table(columns, rows, limit=80, d=3):
    lines = ['| ' + ' | '.join(columns) + ' |', '|' + '|'.join('---' for _ in columns) + '|']
    for r in rows[:limit]:
        lines.append('| ' + ' | '.join(fmt(r.get(c), d) for c in columns) + ' |')
    if len(rows) > limit:
        lines.append('| ... %d more rows in the TSV |' % (len(rows) - limit) + ' |' * (len(columns) - 1))
    return '\n'.join(lines)


def header_md(inp, item, title, meta, note=None):
    lab, src, defaulted = item_label(item)
    lines = ['### %s %s' % (item, title), '',
             '- **Label: %s** (source: %s%s).' % (lab, src, '; C-1 default, the plan gives no label' if defaulted else '')]
    if inp.test_mode:
        lines.append('- **DATA LABEL: %s.**' % inp.label)
    lines.append('- Inputs (sha256, first 12): ' + ', '.join('%s %s' % (k, v[:12]) for k, v in sorted(meta['inputs_sha256'].items())))
    lines.append('- B = %d, seed = %d, tool %s (%s), created %s.' % (meta['B'], meta['seed'], meta['tool'], meta['tool_sha256'][:12],
                                                                    meta['created']))
    if note:
        lines.append('- ' + note)
    return lines


def emit(outdir, item, inp, meta, md, tables, obj):
    """Write <item>.json, <item>.md and one TSV per table: tables = [(name, columns, rows)] (the first one is <item>.tsv)."""
    os.makedirs(outdir, exist_ok=True)
    base = os.path.join(outdir, item.replace('.', ''))
    doc = dict(obj)
    doc['meta'] = meta
    doc['label'] = inp.label
    with open(base + '.json', 'w', encoding='utf-8') as f:
        json.dump(jsonable(doc), f, indent=1, sort_keys=False)
        f.write('\n')
    with open(base + '.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(md) + '\n')
    for i, (name, cols, rows) in enumerate(tables):
        write_tsv(base + ('.tsv' if i == 0 else '__%s.tsv' % name), cols, rows)
    return base


def exit_for(exc):
    return 2 if isinstance(exc, Refuse) else 3 if isinstance(exc, SelfCheckFailed) else 1


def run_main(fn, argv=None):
    try:
        return fn(argv)
    except (Refuse, SelfCheckFailed) as e:
        sys.stderr.write('%s: %s\n' % (e.__class__.__name__, e))
        return exit_for(e)


# ---------------------------------------------------------------------------------------------- display helpers
def display_cells(cells, with_family=False):
    """Compact rows for the Markdown block: families only when asked."""
    out = []
    for c in cells:
        if c.get('family') and not with_family:
            continue
        xn = '' if c.get('x') is None else '%s/%s' % (c['x'], c['n'])
        w = '' if c.get('wilson_lo') is None else '[%s, %s]' % (fmt(c['wilson_lo']), fmt(c['wilson_hi']))
        b = '' if c.get('boot_lo') is None else '[%s, %s]' % (fmt(c['boot_lo']), fmt(c['boot_hi']))
        out.append({'pair': c.get('pair'), 'variant': c.get('variant'), 'outcome': c['outcome'], 'model': c['model'],
                    'stratum': c['stratum'], 'family': c.get('family'), 'split': c.get('split'), 'x/n': xn,
                    'rate': c.get('rate'), 'Wilson 95%': w, 'bootstrap 95%': b,
                    'rare': ('x<5; CP-DEFF upper ' + fmt(c.get('cp_deff_upper'))) if c.get('rare_event') else ''})
    return out


DISPLAY_COLUMNS = ['pair', 'variant', 'outcome', 'model', 'stratum', 'split', 'x/n', 'rate', 'Wilson 95%', 'bootstrap 95%', 'rare']


def status_rows(rows_by_pair, models):
    """Flat table of the clean / excluded / missing counts: pair, model, stratum, kind, count."""
    out = []
    for pair, rows in rows_by_pair.items():
        c = status_counts(rows, models)
        for (m, s) in sorted(c):
            for k in STATUS_KINDS:
                if c[(m, s)].get(k):
                    out.append({'pair': pair, 'model': m, 'stratum': s, 'kind': k, 'count': c[(m, s)][k]})
    return out


def row_variants(inp, core, keep=None):
    """core(sub_inputs) -> list of row dicts. Returns (rows, lr61 meta | None): the rows on all tasks, plus (when the tasks hold stratum R)
    the same rows recomputed without the tasks of tasks/RULED_FIDELITY_FAILS.tsv (variant column; B.0.6, LR70)."""
    main, blk = with_ruled(inp, lambda pps, tasks: core(_SubInputs(inp, pps, tasks)))
    rows = [dict(r, variant='all tasks') for r in main]
    meta = None
    if blk is not None:
        rows += [dict(r, variant='without ruled R tasks (LR61/LR70)') for r in blk['result'] if keep is None or keep(r)]
        meta = {k: blk[k] for k in ('label', 'ruled_file', 'ruled_file_sha256', 'listed_tasks', 'tasks_left_out', 'n_tasks_kept',
                                    'n_programs_left_out')}
    return rows, meta


def get_ruled(inp):
    """The RuledList of LR61/LR70 when the tasks hold stratum R, else None (for tools that filter two arms themselves)."""
    if not has_stratum_R(inp):
        return None
    mod = lr61(inp.study)
    try:
        return inp.ruled if inp.ruled is not None else mod.load_ruled(inp.study, inp.ruled_path)
    except Exception as e:
        raise Refuse('LR61/LR70: the ruled list cannot be used: %s' % e)


def ruled_meta(ruled):
    return None if ruled is None else {'ruled_file': ruled.rel, 'ruled_file_sha256': ruled.sha256, 'listed_tasks': list(ruled.ids)}


def task_of(program_id):
    """task id from a program id of the form gen/<model>/<task>__s<k>(.py)."""
    base = program_id.rsplit('/', 1)[-1]
    if base.endswith('.py'):
        base = base[:-3]
    return base.rsplit('__s', 1)[0]


# ---------------------------------------------------------------------------------------------- LR82.2 item 8 helpers
def median(vals):
    """The usual median (LR82.2 item 8, S-8): the middle element, or the mean of the two middle elements; None for an empty list."""
    v = sorted(vals)
    n = len(v)
    if n == 0:
        return None
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0


FROZEN_COLUMNS = ['frozen_x', 'frozen_n', 'frozen_rate', 'frozen_boot_lo', 'frozen_boot_hi']


def frozen_rate_cell(inp, pair, model, stratum):
    """LR82.2 item 8 (S-3): the cell of summary.targets[pair].rates[model][stratum] as the frozen analyzer reports it (one joint
    bootstrap), for a tool that repeats the cell with its own bootstrap. -> dict of frozen_* columns (all None when absent)."""
    e = ((((inp.summary.get('targets') or {}).get(pair) or {}).get('rates') or {}).get(model) or {}).get(stratum)
    if not e:
        return {c: None for c in FROZEN_COLUMNS}
    return {'frozen_x': e.get('x'), 'frozen_n': e.get('n'), 'frozen_rate': nn(e.get('rate')), 'frozen_boot_lo': nn(e.get('boot_lo')),
            'frozen_boot_hi': nn(e.get('boot_hi'))}


def frozen_test(inp, pair, key):
    """summary.targets[pair].tests[key] as the frozen analyzer reports it: {'estimate','lo','hi'} (None when absent)."""
    e = (((inp.summary.get('targets') or {}).get(pair) or {}).get('tests') or {}).get(key) or {}
    return {'estimate': nn(e.get('estimate')), 'lo': nn(e.get('lo')), 'hi': nn(e.get('hi'))}


# ---------------------------------------------------------------------------------------------- agreement statistics (LR82.2 items 7, 8)
def contingency_fields(cats):
    return ['ct_%d_%d' % (i, j) for i in range(len(cats)) for j in range(len(cats))]


def agreement_item_row(task_id, stratum, fam, a, b, cats):
    """One coded item as a row of the frozen bootstrap engine: the count of the cell (a, b) of the contingency table is 1."""
    r = {'task_id': task_id, 'stratum': stratum, 'fam': fam if stratum == 'M' else None}
    ia, ib = cats.index(a), cats.index(b)
    for i in range(len(cats)):
        for j in range(len(cats)):
            r['ct_%d_%d' % (i, j)] = 1 if (i == ia and j == ib) else 0
    return r


def _table_from_view(v, cats):
    k = len(cats)
    return [[v.sum('ct_%d_%d' % (i, j)) for j in range(k)] for i in range(k)]


def agreement_from_table(T, kind):
    """Cohen's kappa, Gwet's AC1 or raw agreement from a contingency table T[i][j] (rater 1 in rows); the same definitions as
    harness/stats.py (cohen_kappa, gwet_ac1; the category set of AC1 = categories with a positive margin in either rating)."""
    k = len(T)
    n = sum(sum(r) for r in T)
    if n == 0:
        return float('nan')
    po = sum(T[i][i] for i in range(k)) / n
    if kind == 'raw':
        return po
    if kind in ('wkappa_linear', 'wkappa_quadratic'):
        # weighted kappa for ordinal levels 0..k-1: 1 - sum w O / sum w E with disagreement weights |i-j| or (i-j)^2
        O = [[T[i][j] / n for j in range(k)] for i in range(k)]
        ra = [sum(O[i]) for i in range(k)]
        rb = [sum(O[i][j] for i in range(k)) for j in range(k)]

        def w(i, j):
            d = abs(i - j)
            return d if kind == 'wkappa_linear' else d * d
        num = sum(w(i, j) * O[i][j] for i in range(k) for j in range(k))
        den = sum(w(i, j) * ra[i] * rb[j] for i in range(k) for j in range(k))
        return float('nan') if den == 0 else 1.0 - num / den
    ra = [sum(T[i]) / n for i in range(k)]
    rb = [sum(T[i][j] for i in range(k)) / n for j in range(k)]
    if kind == 'kappa':
        pe = sum(ra[i] * rb[i] for i in range(k))
        return float('nan') if pe >= 1.0 else (po - pe) / (1.0 - pe)
    if kind == 'ac1':
        used = [i for i in range(k) if ra[i] > 0 or rb[i] > 0]
        q = len(used)
        if q < 2:
            return 1.0
        pe = sum(((ra[i] + rb[i]) / 2.0) * (1 - (ra[i] + rb[i]) / 2.0) for i in used) / (q - 1)
        return (po - pe) / (1.0 - pe)
    raise ValueError(kind)


def stratified_agreement(inp, items, cats, stat_kinds=('kappa', 'ac1', 'raw'), tasks=None):
    """items: [(task_id, stratum, family code or None, code_1, code_2)]. The three agreement statistics with percentile intervals from
    the frozen stratified paired task-cluster bootstrap (stats.cluster_bootstrap_multi: tasks resampled with replacement within stratum
    and, within M, family; every task of tasks.json holds a slot; B and seed from the command line). Rule (iii) of LR82, S-2.
    -> {kind: {'estimate','lo','hi','dropped'}, 'n_items': n}."""
    out = {'n_items': len(items)}
    if not items:
        for kd in stat_kinds:
            out[kd] = {'estimate': None, 'lo': None, 'hi': None, 'dropped': None}
        return out
    cats = list(cats)
    rows = [agreement_item_row(t, s, f, a, b, cats) for (t, s, f, a, b) in items]
    fields = contingency_fields(cats)
    statistics = {kd: (lambda v, kd=kd: agreement_from_table(_table_from_view(v, cats), kd)) for kd in stat_kinds}
    res = inp.stats.cluster_bootstrap_multi(rows, statistics, fields, ('stratum', 'fam'), B=inp.B, seed=inp.seed,
                                            tasks=inp.tasks_univ if tasks is None else tasks)
    for kd in stat_kinds:
        r = res[kd]
        out[kd] = {'estimate': nn(r['estimate']), 'lo': nn(r['lo']), 'hi': nn(r['hi']), 'dropped': r['dropped']}
    return out


# ---------------------------------------------------------------------------------------------- test helper
_TMP_DIRS = []


def make_tmp(prefix='sectest_'):
    """A temporary folder that is removed when the process ends (LR82.2 item 8, D-2). Used by the unit tests."""
    import atexit
    import shutil
    import tempfile
    d = tempfile.mkdtemp(prefix=prefix)
    if not _TMP_DIRS:
        atexit.register(lambda: [shutil.rmtree(x, ignore_errors=True) for x in _TMP_DIRS])
    _TMP_DIRS.append(d)
    return d
