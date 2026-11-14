# Analyzer for the Born Legacy study: run records -> per_program.jsonl -> summary.json and hypotheses.md.
# Written 2026-11-11 by pkg:HSTAT_GEN. Status: prepared.
# Implements FULL_PREREG sections 7 (hypotheses, Holm, framing, H5), 8 (statistics), 10.3 (coding weights), 13 (stop rules).
#
# usage: python3 -I harness/analyze_full.py --runs runs/ --tasks tasks/tasks.json --models <model_key,...> --out results/
#            [--label 'pilot regression, not study data'] [--targets E0a~E1,E0a~E2] [--gen-dir generations/]
#            [--codes harm/codes_resolved.tsv] [--plan plan.json] [--B 10000] [--seed 20261111] [--study DIR]
#            [--flags-before F|none] [--h3-subset-lr2 F|none] [--second-rating F]   (lead rulings LR2.4, LR2.5, LR3; harness/lead_rulings.py)
#            [--oracle-pre-lr1 F] [--flags-before-lr2-3 F|none] [--card-variants-before-lr18 F|none]   (REPAIR6: lead rulings LR13 to
#            LR22, harness/lead_rulings_2.py, summary key lead_ruling_additions_2; LR22 (3) exclusions table, key exclusions_table_LR22)
# T8 preparation 2026-11-13 (lead rulings LR42, LR61; deviation T8P-LR61-1 of deviations/T8PREP.md): main() adds, beside each primary
# result reported for stratum R, the added report of harness/lr61_report.py (key added_report_LR42_LR61 of summary['targets'][pair];
# marked blocks in hypotheses.md); the primary analysis, per_program.jsonl and the decision are not changed.
# T8 apply 2026-11-13 (lead ruling LR70; deviation T8A-LR70-1 of deviations/T8APPLY.md): the added report also carries the confirmatory
# H4 on R+A, its companion and the R+A testability count (lr61_report.primary_report); one marked block after the hypothesis table.
# Use envs/tools/bin/python for the full B = 10,000 (numpy makes the bootstrap seconds instead of minutes).
# T11 prep 2026-11-13 (audit finding M-9): flatten() also requires the pair block's `excluded` to be null.
#
# The oracle (HRUN: oracle.classify_program, warndef, exposure_scan, run_programs.load_record) and the attribution /
# harm pre-label (ATTRIB_HARM) are called ONLY through the signatures of conventions/INTERFACES.md. `Deps` lets tests
# inject stubs; `load_deps()` imports the real modules (VERIFY wires them for the regression).
#
# The analyzer is not meant to be run on study data until every planned model is complete or stopped by a section 13
# rule: decision.py prints INCOMPLETE otherwise, and this script still writes the files but marks them INCOMPLETE.
import argparse
import collections
import datetime
import gzip
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import stats  # noqa: E402

PRIMARY_PAIR = 'E0a~E1'
CODES = ('HARM_3X', 'FIX_3X', 'BOTH_ACCEPTABLE', 'NEITHER', 'UNDETERMINABLE')
QFS = ['QF%d' % i for i in range(1, 9)]
RUN_CONFIGS = ['E0a', 'E0b', 'E1', 'E2', 'E0pa', 'E3', 'E4', 'A1', 'A2', 'A3', 'A4', 'T0', 'T1', 'T2', 'C1',
               'V-clean__E0a', 'V-clean__E0b', 'V-clean__E1', 'V-dirty__E0a', 'V-dirty__E0b', 'V-dirty__E1']
ATTRIB_TARGET = {'E0a~E1': ('E1', 'T1'), 'E0a~E2': ('E2', 'T2')}
FLAT_FIELDS = ['gen', 'clean', 'silent', 'drift', 'drift_any', 'drift_unwarned', 'drift_warned', 'loud', 'vs', 'vs_warned',
               'silent_all', 'silent_pilotrule', 'silent_pilotwarn', 'clean_nd', 'silent_nd', 'clean_exp', 'silent_exp',
               'clean_alt', 'three_x_only']
GROUP_BY = ('model', 'stratum', 'fam', 'grp', 'strength')


def now_iso():
    return datetime.datetime.now().astimezone().isoformat(timespec='seconds')


# ------------------------------------------------------------------------------------------------ plan
def read_tsv(path):
    with open(path, encoding='utf-8') as f:
        lines = [ln.rstrip('\n') for ln in f if ln.strip()]
    head = lines[0].split('\t')
    return [dict(zip(head, ln.split('\t'))) for ln in lines[1:]]


def model_key(openrouter_id):
    return openrouter_id.replace('/', '__')


def default_plan(study, n_tasks=None, k=5):
    """The 10 planned models from models/models.tsv (selected = yes): cutoff group by the vendor-documented cutoff
    (column cutoff_vs_pandas3_0_0_(2026-01-21): before/after/unknown), open/closed, hypothesis roles (section 7)."""
    rows = [r for r in read_tsv(os.path.join(study, 'models', 'models.tsv')) if r.get('selected') == 'yes']
    models = {}
    for r in rows:
        key = model_key(r['openrouter_id'])
        grp = {'before': 'BEFORE', 'after': 'AFTER'}.get(r['cutoff_vs_pandas3_0_0_(2026-01-21)'], 'UNKNOWN')
        models[key] = {'openrouter_id': r['openrouter_id'], 'group': grp, 'open': r['open_weights'] == 'yes', 'k': k}
    return {'models': models, 'k': k, 'n_tasks': n_tasks, 'alpha': 0.05,
            'roles': {'h1_high': 'qwen__qwen3.5-9b', 'h1_low': 'anthropic__claude-sonnet-5.5',
                      'h2b_old': 'anthropic__claude-haiku-4.5', 'h2b_new': 'anthropic__claude-haiku-5.5'},
            'h2b_available': True,           # set False by amendment if Haiku 4.5 is retired before its first main-run call
            'targets': [PRIMARY_PAIR]}


def generation_state(gen_dir, key, planned):
    """-> {'generated', 'planned', 'state', 'stop_rule'}: complete when every planned program exists; otherwise the state
    written by gen_full.py in <gen_dir>/<key>/status.json ('stopped' with rule a|b|c is a section 13 stop)."""
    d = os.path.join(gen_dir, key)
    n = len([f for f in os.listdir(d) if re.match(r'.+__s\d+\.py$', f)]) if os.path.isdir(d) else 0
    st = {}
    try:
        with open(os.path.join(d, 'status.json')) as f:
            st = json.load(f)
    except Exception:
        pass
    if planned and n >= planned:
        state, rule = 'complete', None
    elif st.get('state') == 'stopped':
        state, rule = 'stopped', st.get('stop_rule')
    else:
        state, rule = st.get('state') or ('not_started' if n == 0 else 'running'), None
    return {'generated': n, 'planned': planned, 'state': state, 'stop_rule': rule}


def fill_generation(plan, gen_dir):
    n_tasks = plan.get('n_tasks') or 0
    for key, m in plan['models'].items():
        planned = n_tasks * m.get('k', plan.get('k', 5))
        m.update(generation_state(gen_dir, key, planned))
    return plan


# ------------------------------------------------------------------------------------------------ dependencies
class Deps:
    """The modules the analyzer calls. Attributes: classify_program(records, card), attribute(program, records, traces,
    card, target), harm_prelabel(e0a, target, reference, card), scan(text, rows), load_record(root, run_config, pid),
    exposure_rows. Tests pass stubs; load_deps() loads the real ones."""

    def __init__(self, classify_program, attribute, harm_prelabel, scan, load_record, exposure_rows=None, load_trace=None,
                 first_divergent_line=None):
        self.classify_program = classify_program
        self.first_divergent_line = first_divergent_line
        self.attribute = attribute
        self.harm_prelabel = harm_prelabel
        self.scan = scan
        self.load_record = load_record
        self.exposure_rows = exposure_rows or []
        self.load_trace = load_trace or _load_trace


def load_deps(study, exposure=None):
    """exposure: path of the exposure-regex table; None = <study>/tasks/exposure_regex.tsv (must exist: INTEGRATE writes it);
    'none' = no exposure scan (controls and the pilot regression, which have no exposure table). VERIFY fix F1."""
    import importlib
    sys.path.insert(0, HERE)
    oracle = importlib.import_module('oracle')
    attribution = importlib.import_module('attribution')
    harm = importlib.import_module('harm_prelabel')
    expo = importlib.import_module('exposure_scan')
    runp = importlib.import_module('run_programs')
    if exposure == 'none':
        rows = []
    else:
        path = exposure or os.path.join(study, 'tasks', 'exposure_regex.tsv')
        if not os.path.exists(path):
            raise SystemExit('analyze_full: exposure table %s not found (INTEGRATE writes tasks/exposure_regex.tsv); '
                             'pass --exposure none for controls and the pilot regression' % path)
        rows = expo.load(path)
    return Deps(oracle.classify_program, attribution.attribute, harm.harm_prelabel, expo.scan, runp.load_record, rows,
                first_divergent_line=attribution.first_divergent_line)


def _load_trace(runs_root, rec):
    p = rec.get('trace_path') if rec else None
    if not p:
        return None
    full = os.path.join(runs_root, p)
    if not os.path.exists(full):
        return None
    with gzip.open(full, 'rt', encoding='utf-8') as f:
        return json.load(f)


# ------------------------------------------------------------------------------------------------ per_program
def family_code(task):
    fam = task.get('family')
    return fam.split('_')[0] if fam else None


def blank_target():
    return {'class': None, 'class_pilot_rule': None, 'run_problem': None, 'drift': False, 'magnitude': None, 'silent': False,
            'silent_all_magnitudes': False, 'locally_silent': None, 'warned_target': {'prereg': False, 'pilot': False},
            'warning_only': False, 'first_diff': None, 'labels': [], 'primary_label': None, 'attribution_step': None,
            'trace_truncated': None, 'harm_prelabel': None}


def body_key(src):
    return ' '.join((src or '').split())


def build_per_program(runs_root, tasks, models, deps, gen_dir, samples=None):
    """One dict per generated program (schema per_program.schema.json). tasks: list of task dicts (tasks.json);
    models: model keys. Programs are the files <gen_dir>/<model>/<task>__s<k>.py."""
    tmap = {t['id']: t for t in tasks}
    out = []
    for model in models:
        mdir = os.path.join(gen_dir, model)
        if not os.path.isdir(mdir):
            continue
        seen_bodies = {}
        files = sorted(f for f in os.listdir(mdir) if re.match(r'.+__s\d+\.py$', f))
        files.sort(key=lambda f: (re.match(r'(.+)__s(\d+)\.py$', f).group(1), int(re.match(r'(.+)__s(\d+)\.py$', f).group(2))))
        for fn in files:
            tid, k = re.match(r'(.+)__s(\d+)\.py$', fn).groups()
            k = int(k)
            if samples is not None and k not in samples:
                continue
            task = tmap.get(tid)
            if task is None:
                continue
            pid = 'gen/%s/%s__s%d' % (model, tid, k)
            with open(os.path.join(mdir, fn), encoding='utf-8', errors='replace') as f:
                src = f.read()
            records = {}
            for rc in RUN_CONFIGS:
                rec = deps.load_record(runs_root, rc, pid)
                if rec is not None:
                    records[rc] = rec
            base = deps.classify_program(records, task)
            traces = {}
            for tname in ('T0', 'T1', 'T2'):
                if tname in records:
                    traces[tname] = deps.load_trace(runs_root, records[tname])
            lines = {}
            if deps.first_divergent_line is not None and traces.get('T0') is not None:
                for pair, (tgt, tr) in ATTRIB_TARGET.items():
                    if (base.get('targets') or {}).get(pair, {}).get('drift') and traces.get(tr) is not None:
                        ln = deps.first_divergent_line(traces['T0'], traces[tr])
                        if ln is not None:
                            lines[pair] = ln
            if lines:                                   # locally-silent outcome needs the first divergent line (review m2)
                base = deps.classify_program(records, task, divergent_lines=lines)
            row = {'schema_version': 'per_program/1', 'program_id': pid, 'model': model, 'task_id': tid, 'sample': k,
                   'stratum': task['stratum'], 'family': task.get('family'), 'generic_family': task.get('generic_family'),
                   'clean_on_233': bool(base.get('clean_on_233')), 'exclusion': base.get('exclusion'),
                   'exclusion_detail': base.get('exclusion_detail'), 'three_x_only': bool(base.get('three_x_only')),
                   'warned_E0a': base.get('warned_E0a') or {'prereg': False, 'pilot': False},
                   'exposure_match': deps.scan(src, deps.exposure_rows) if src.strip() else [],
                   'duplicate_body_of': None, 'empty_source': not src.strip(), 'targets': {}}
            bk = (tid, body_key(src))
            if bk in seen_bodies:
                row['duplicate_body_of'] = seen_bodies[bk]
            else:
                seen_bodies[bk] = pid
            for pair, t in (base.get('targets') or {}).items():
                tt = blank_target()
                tt.update(t)
                row['targets'][pair] = tt
                if pair in ATTRIB_TARGET and tt['drift'] and row['clean_on_233']:
                    tgt, tr = ATTRIB_TARGET[pair]
                    base_traces = {n: traces[n] for n in ('T0', tr) if traces.get(n) is not None}
                    a = deps.attribute({'program_id': pid, 'source': src}, records, base_traces or None, task, tgt)
                    tt['labels'] = list(a.get('labels') or [])
                    tt['primary_label'] = a.get('primary')
                    tt['attribution_step'] = a.get('step')
                    # a trace run that was made but produced no trace (CPU/wall/memory limit hit while tracing) is a truncated trace too
                    # (VERIFY fix F2; the pilot's t08__s1 case); a trace run that was not made leaves the flag as attribute() gave it
                    lost = any(records.get(n) is not None and not records[n].get('trace_path') for n in ('T0', tr))
                    tt['trace_truncated'] = bool(a.get('truncated')) or lost
                    ref = deps.load_record(runs_root, 'E0a', 'ref/' + tid)
                    if ref is not None and 'E0a' in records and tgt in records:
                        hp = deps.harm_prelabel(records['E0a'], records[tgt], ref, task)
                        tt['harm_prelabel'] = hp.get('label')
            out.append(row)
    out.sort(key=lambda r: r['program_id'])
    return out


# ------------------------------------------------------------------------------------------------ flat rows
DRIFT_PILOT = ('VALUE_DRIFT', 'NO_RESULT')


def flatten(pp, pair, tmap=None):
    """Numeric per-program row for the statistics. clean = clean on 2.3.3 and the target run exists; every outcome is 0
    for programs that are not clean (denominators are clean programs, section 3)."""
    t = pp['targets'].get(pair)
    task = (tmap or {}).get(pp['task_id'], {})
    fam = family_code(pp) or family_code(task)
    ok = bool(pp['clean_on_233']) and t is not None and t.get('run_problem') is None
    ok = ok and t.get('excluded') is None      # M-9 (T11 prep 2026-11-13): honour the pair block's own-baseline exclusion
    c = 1 if ok else 0
    drift_any = c and t['drift']
    subst = c and t['drift'] and t.get('magnitude') == 'SUBSTANTIVE'
    warned233 = bool(pp['warned_E0a']['prereg'])
    loud = c and t.get('class') == 'LOUD'
    invited = set([task.get('catalogue_row')] if task.get('catalogue_row') else task.get('invited_ids_author') or [])
    exposed = 1 if (invited & set(pp.get('exposure_match') or [])) else 0
    nd = 1 if pp.get('duplicate_body_of') is None else 0
    silent = 1 if (c and t['silent']) else 0
    st = task.get('invitation_strength')
    return {
        'model': pp['model'], 'task_id': pp['task_id'], 'program_id': pp['program_id'], 'stratum': pp['stratum'], 'fam': fam,
        'grp': stats.h3_group(fam) if pp['stratum'] == 'M' else None, 'strength': st if pp['stratum'] == 'M' else None,
        'gen': 1, 'clean': c, 'silent': silent, 'drift': 1 if subst else 0, 'drift_any': 1 if drift_any else 0,
        'drift_unwarned': 1 if (subst and not warned233) else 0, 'drift_warned': 1 if (subst and warned233) else 0,
        'loud': 1 if loud else 0, 'vs': 1 if (subst or loud) else 0, 'vs_warned': 1 if ((subst or loud) and warned233) else 0,
        'silent_all': 1 if (c and t['silent_all_magnitudes']) else 0,
        'silent_pilotrule': 1 if (silent and t.get('class_pilot_rule') in DRIFT_PILOT) else 0,
        'silent_pilotwarn': 1 if (subst and not t['warned_target']['pilot']) else 0,
        'clean_nd': c * nd, 'silent_nd': silent * nd, 'clean_exp': c * exposed, 'silent_exp': silent * exposed,
        'clean_alt': 1 if (c or pp.get('three_x_only')) else 0, 'three_x_only': 1 if pp.get('three_x_only') else 0,
        'exclusion': pp.get('exclusion'), 'run_problem': (t or {}).get('run_problem') if t else 'NO_TARGET',
    }


def outcome_label(pp, pair):
    """Exclusive outcome category per generated program (exclusion-aware reporting, section 8)."""
    if not pp['clean_on_233']:
        return pp.get('exclusion') or 'EXCL_FAIL'
    t = pp['targets'].get(pair)
    if t is None or t.get('run_problem'):
        return 'RUN_PROBLEM'
    if t.get('class') == 'LOUD':
        return 'LOUD'
    if t['drift']:
        small = t.get('magnitude') == 'NUMERIC_SMALL'
        return ('NUMERIC_SMALL_' if small else 'DRIFT_') + ('SILENT' if t['silent_all_magnitudes'] else 'WARNED')
    if t.get('warning_only'):
        return 'WARNING_ONLY'
    return t.get('class') or 'UNCLASSIFIED'


# ------------------------------------------------------------------------------------------------ tests (statistics)
def _rate(v, m, **where):
    return v.ratio('silent', 'clean', model=m, **where)


def _mean_rates(v, models, field_num='silent', field_den='clean', **where):
    rs = [v.ratio(field_num, field_den, model=m, **where) for m in models]
    if not rs or any(r is None for r in rs):
        return None
    return sum(rs) / len(rs)


def pooled_rate(v, m, num='silent', den='clean'):
    rs = {s: v.ratio(num, den, model=m, stratum=s) for s in ('M', 'R', 'A')}
    return stats.pooled_fixed_weights({s: (stats.NAN if r is None else r) for s, r in rs.items()})


def hypothesis_statistics(plan, models_present, num='silent', den='clean', pooled=False):
    """{name: f(view)}: d1 (H1), d2 (H2a), d3 (H2b) on stratum M; for pooled=True the fixed-weight pooled rates (M .64,
    R .20, A .16) replace the stratum-M rates (sensitivity)."""
    roles = plan['roles']
    before = [m for m in models_present if plan['models'][m]['group'] == 'BEFORE']
    after = [m for m in models_present if plan['models'][m]['group'] == 'AFTER']
    closed_b = [m for m in before if not plan['models'][m]['open']]
    closed_a = [m for m in after if not plan['models'][m]['open']]

    def r(v, m):
        if pooled:
            x = pooled_rate(v, m, num, den)
            return None if stats.isnan(x) else x
        return v.ratio(num, den, model=m, stratum='M')

    def diff(a, b):
        def f(v):
            x, y = r(v, a), r(v, b)
            return None if x is None or y is None else x - y
        return f

    def groupdiff(bl, al):
        def f(v):
            xs = [r(v, m) for m in bl]
            ys = [r(v, m) for m in al]
            if not xs or not ys or any(z is None for z in xs + ys):
                return None
            return sum(xs) / len(xs) - sum(ys) / len(ys)
        return f
    return {'d1': diff(roles['h1_high'], roles['h1_low']), 'd2': groupdiff(before, after),
            'd3': diff(roles['h2b_old'], roles['h2b_new']), 'd2_closed': groupdiff(closed_b, closed_a)}


def h3_statistic(models, field_num='silent', field_den='clean', extra=None):
    extra = extra or {}

    def f(v):
        g1 = [v.ratio(field_num, field_den, model=m, stratum='M', grp='G1', **extra) for m in models]
        g2 = [v.ratio(field_num, field_den, model=m, stratum='M', grp='G2', **extra) for m in models]
        if not models or any(x is None for x in g1 + g2):
            return None
        return stats.log_rr(sum(g1) / len(g1), sum(g2) / len(g2))
    return f


def h4_statistic(num='drift_unwarned', den='drift', strata=('R', 'A')):
    def f(v):
        d = v.sum(den, stratum=set(strata))
        return None if d == 0 else v.sum(num, stratum=set(strata)) / d
    return f


def _rr(logrr):
    if stats.isnan(logrr):
        return None
    return math.inf if logrr > 700 else math.exp(logrr)


def _summ(res, null=None, extra=None):
    d = {k: res[k] for k in ('estimate', 'lo', 'hi', 'dropped', 'n_valid', 'B')}
    # one-sided lower bounds at the Holm step levels alpha/1 ... alpha/5 (section 7: reported, they do not decide)
    d['one_sided_lower'] = {str(round(0.05 / j, 6)): _nn(stats.percentile(res['draws'], 0.05 / j)) for j in range(1, 6)}
    d['p'] = stats.p_one_sided(res['draws'], null) if null is not None else None
    d['null'] = null
    if extra:
        d.update(extra)
    return d


def run_tests(flat, plan, models, tasks_univ, B, seed, use_numpy=None):
    """The five confirmatory statistics on one target (rows `flat` already built for that pair). Returns
    {'tests': {...}, 'models_used': {...}} with p-values, estimates, bootstrap bounds and point-estimate conditions.
    Holm and the decision are applied in decision.py."""
    kw = dict(fields=FLAT_FIELDS, group_by=GROUP_BY, B=B, seed=seed, use_numpy=use_numpy)
    inscope = [m for m in models if m in plan['models']]
    flat_in = [r for r in flat if r['model'] in inscope]
    m_rows = [r for r in flat_in if r['stratum'] == 'M']
    elig = stats.h3_eligible_models(m_rows, inscope)
    hs = hypothesis_statistics(plan, inscope)
    resM = stats.cluster_bootstrap_multi(
        flat_in, {'d1': hs['d1'], 'd2': hs['d2'], 'd3': hs['d3'], 'd2_closed': hs['d2_closed'],
                  'h3': h3_statistic(elig)},
        restrict=lambda r: r.get('stratum') == 'M', tasks=[t for t in tasks_univ if t.get('stratum') == 'M'], **kw)
    ra_tasks = [t for t in tasks_univ if t.get('stratum') in ('R', 'A')]
    resRA = stats.cluster_bootstrap_multi(
        flat_in, {'h4': h4_statistic(), 'h4_R': h4_statistic(strata=('R',)), 'h4_vs': h4_statistic('vs_warned', 'vs')},
        restrict=lambda r: r.get('stratum') in ('R', 'A'), tasks=ra_tasks, **kw)
    drift_ra = [r for r in flat_in if r['stratum'] in ('R', 'A') and r['drift']]
    tests = {
        'H1': _summ(resM['d1'], 0.02, {'condition': None}),
        'H2a': _summ(resM['d2'], 0.0, {'condition': (resM['d2']['estimate'] >= 0.02) if not stats.isnan(resM['d2']['estimate']) else False,
                                       'condition_text': 'point estimate >= 2 pp'}),
        'H2b': _summ(resM['d3'], 0.0, {'condition': None}),
        'H3': _summ(resM['h3'], 0.0, {'condition': (resM['h3']['estimate'] >= math.log(2.0)) if not stats.isnan(resM['h3']['estimate']) else False,
                                      'condition_text': 'point estimate RR >= 2', 'models_entering': elig,
                                      'rr': _rr(resM['h3']['estimate']),
                                      'n_dropped_both_zero': resM['h3']['dropped'],
                                      'n_plus_inf': sum(1 for d in resM['h3']['draws'] if d == math.inf)}),
        'H4': _summ(resRA['h4'], 0.5, {'condition': None, 'n_drift_programs': len(drift_ra),
                                       'n_drift_tasks': len({r['task_id'] for r in drift_ra})}),
    }
    secondary = {'H2a_closed_only': _summ(resM['d2_closed'], 0.0),
                 'H4_stratum_R_only': _summ(resRA['h4_R'], 0.5),
                 'H4_companion_drift_plus_loud_warned_on_233': _summ(resRA['h4_vs'], None)}
    return {'tests': tests, 'secondary': secondary, 'draws': {k: resM[k]['draws'] for k in resM},
            'draws_RA': {k: resRA[k]['draws'] for k in resRA}}


# ------------------------------------------------------------------------------------------------ descriptive tables
def rate_tables(flat, models, tasks_univ, B, seed, use_numpy=None):
    """Per model x stratum: x, n, rate, Wilson (program level), task-cluster bootstrap interval, rare-event bound when
    x < 5; per model x family for stratum M (Wilson and rare bound)."""
    out = {m: {} for m in models}
    for s in ('M', 'R', 'A'):
        rows = [r for r in flat if r['model'] in models and r['stratum'] == s]
        if not rows:
            continue
        stat = {m: (lambda v, m=m: v.ratio('silent', 'clean', model=m, stratum=s)) for m in models}
        res = stats.cluster_bootstrap_multi(rows, stat, FLAT_FIELDS, GROUP_BY, B=B, seed=seed, use_numpy=use_numpy,
                                            tasks=[t for t in tasks_univ if t.get('stratum') == s])
        for m in models:
            mr = [r for r in rows if r['model'] == m]
            x, n = sum(r['silent'] for r in mr), sum(r['clean'] for r in mr)
            p, lo, hi = stats.wilson(x, n)
            ent = {'x': x, 'n': n, 'generated': sum(r['gen'] for r in mr), 'rate': None if n == 0 else p,
                   'wilson_lo': None if n == 0 else lo, 'wilson_hi': None if n == 0 else hi,
                   'boot_lo': _nn(res[m]['lo']), 'boot_hi': _nn(res[m]['hi']), 'boot_dropped': res[m]['dropped']}
            by_task = collections.defaultdict(list)
            for r in mr:
                if r['clean']:
                    by_task[r['task_id']].append(r['silent'])
            rb = stats.rare_bound(by_task)
            ent['cp_deff_upper'] = _nn(rb['upper'])
            ent['deff'] = _nn(rb['deff'])
            ent['icc'] = _nn(rb['icc'])
            ent['n_eff'] = _nn(rb['n_eff'])
            ent['rare_event'] = bool(n > 0 and x < 5)
            out[m][s] = ent
    fam = {m: {} for m in models}
    for m in models:
        for q in QFS:
            mr = [r for r in flat if r['model'] == m and r['stratum'] == 'M' and r['fam'] == q]
            if not mr:
                continue
            x, n = sum(r['silent'] for r in mr), sum(r['clean'] for r in mr)
            p, lo, hi = stats.wilson(x, n)
            by_task = collections.defaultdict(list)
            for r in mr:
                if r['clean']:
                    by_task[r['task_id']].append(r['silent'])
            rb = stats.rare_bound(by_task)
            fam[m][q] = {'x': x, 'n': n, 'rate': None if n == 0 else p, 'wilson_lo': None if n == 0 else lo,
                         'wilson_hi': None if n == 0 else hi, 'rare_event': bool(n > 0 and x < 5),
                         'cp_deff_upper': _nn(rb['upper'])}
    return out, fam


def _nn(v):
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else v


def sensitivities(flat, plan, models, tasks_univ, B, seed, use_numpy=None, h3_subset=None):
    """Pre-declared sensitivities (section 8), reported as sensitivities with point estimate and percentile interval:
    d1/d2a/d3 under all-magnitude drift, the pilot order/dtype rule, the pilot warning definition, within-task
    de-duplication, the 'at least one of E0a/E1' denominator, per generated program rate, fixed-weight pooled strata;
    H3 without QF5, under the pilot rule, exposure-conditional and per invitation strength."""
    inscope = [m for m in models if m in plan['models']]
    flat_in = [r for r in flat if r['model'] in inscope]
    variants = {
        'all_magnitudes': ('silent_all', 'clean'),
        'pilot_order_dtype_rule': ('silent_pilotrule', 'clean'),
        'pilot_warning_definition': ('silent_pilotwarn', 'clean'),
        'dedup_within_task': ('silent_nd', 'clean_nd'),
        'unconditional_per_generated': ('silent', 'gen'),
        'denominator_clean_or_3x_only': ('silent', 'clean_alt'),
    }
    stat = {}
    for name, (num, den) in variants.items():
        hs = hypothesis_statistics(plan, inscope, num, den)
        stat.update({name + '|d1': hs['d1'], name + '|d2': hs['d2'], name + '|d3': hs['d3']})
    hsp = hypothesis_statistics(plan, inscope, pooled=True)
    stat.update({'fixed_weight_pooled|d1': hsp['d1'], 'fixed_weight_pooled|d2': hsp['d2'], 'fixed_weight_pooled|d3': hsp['d3']})
    kw = dict(fields=FLAT_FIELDS, group_by=GROUP_BY, B=B, seed=seed, use_numpy=use_numpy)
    res_m = stats.cluster_bootstrap_multi(flat_in, {k: v for k, v in stat.items() if not k.startswith('fixed_weight')},
                                          restrict=lambda r: r['stratum'] == 'M',
                                          tasks=[t for t in tasks_univ if t.get('stratum') == 'M'], **kw)
    res_p = stats.cluster_bootstrap_multi(flat_in, {k: v for k, v in stat.items() if k.startswith('fixed_weight')},
                                          tasks=tasks_univ, **kw)
    out = {}
    for res in (res_m, res_p):
        for k, r in res.items():
            out[k] = {'estimate': _nn(r['estimate']), 'lo': _nn(r['lo']), 'hi': _nn(r['hi']), 'dropped': r['dropped']}
    # H3 variants
    m_rows = [r for r in flat_in if r['stratum'] == 'M']
    h3s = {}
    base_models = stats.h3_eligible_models(m_rows, inscope)
    h3s['H3_primary_recomputed'] = h3_statistic(base_models)

    def h3_without_qf5(v):
        g1 = [v.ratio('silent', 'clean', model=m, stratum='M', grp='G1') for m in base_models]
        g2 = [_ratio_excl(v, m, 'QF5') for m in base_models]
        if not base_models or any(x is None for x in g1 + g2):
            return None
        return stats.log_rr(sum(g1) / len(g1), sum(g2) / len(g2))

    def _ratio_excl(v, m, drop):
        fams = {f for f in QFS[2:] if f != drop}
        return v.ratio('silent', 'clean', model=m, stratum='M', fam=fams)
    h3s['H3_without_QF5'] = h3_without_qf5
    h3s['H3_pilot_order_dtype_rule'] = h3_statistic(base_models, 'silent_pilotrule')
    h3s['H3_exposure_conditional'] = h3_statistic(stats.h3_eligible_models(
        [dict(r, clean=r['clean_exp']) for r in m_rows], inscope), 'silent_exp', 'clean_exp')
    for lvl in (1, 2, 3):
        h3s['H3_invitation_strength_%d' % lvl] = h3_statistic(base_models, extra={'strength': lvl})
    res_h3 = stats.cluster_bootstrap_multi(flat_in, h3s, restrict=lambda r: r['stratum'] == 'M',
                                           tasks=[t for t in tasks_univ if t.get('stratum') == 'M'], **kw)
    for k, r in res_h3.items():
        out[k] = {'estimate': _nn(r['estimate']) if r['estimate'] not in (math.inf, -math.inf) else str(r['estimate']),
                  'lo': _nn(r['lo']), 'hi': _nn(r['hi']), 'dropped': r['dropped'], 'n_valid': r['n_valid']}
    # REPAIR4 2026-11-11 (review RV-4; Amendment 2(b)): H3 statistic, rule and threshold of section 8 unchanged, computed on the
    # frozen subset of M tasks whose naive drift is silent on E1 (tasks/H3_NAIVE_SILENT_SUBSET.tsv). Reported next to the primary H3.
    subset = h3_subset if h3_subset is not None else load_h3_subset()
    if subset:
        def _in(r):
            return r.get('stratum') == 'M' and (r.get('task_id') or r.get('id')) in subset
        sub_rows = [r for r in m_rows if _in(r)]
        res_sub = stats.cluster_bootstrap_multi(
            flat_in, {'H3_naive_silent_subset': h3_statistic(stats.h3_eligible_models(sub_rows, inscope))},
            restrict=_in, tasks=[t for t in tasks_univ if _in(t)], **kw)
        r = res_sub['H3_naive_silent_subset']
        out['H3_naive_silent_subset'] = {
            'estimate': _nn(r['estimate']) if r['estimate'] not in (math.inf, -math.inf) else str(r['estimate']),
            'lo': _nn(r['lo']), 'hi': _nn(r['hi']), 'dropped': r['dropped'], 'n_valid': r['n_valid'],
            'n_tasks_in_subset': len(subset), 'n_tasks_present': len({t.get('task_id') or t.get('id') for t in tasks_univ if _in(t)})}
    return out


H3_SUBSET_FILE = os.path.join(os.path.dirname(HERE), 'tasks', 'H3_NAIVE_SILENT_SUBSET.tsv')


def load_h3_subset(path=H3_SUBSET_FILE):
    """Frozen task ids of the Amendment 2(b) H3 sensitivity (REPAIR4 2026-11-11). Empty set if the file does not exist."""
    if not os.path.exists(path):
        return set()
    with open(path, encoding='utf-8') as f:
        lines = [ln.strip() for ln in f if ln.strip() and not ln.startswith('#')]
    return set(lines[1:]) if lines and lines[0] == 'task_id' else set(lines)


# ------------------------------------------------------------------------------------------------ H5
def read_codes(path):
    """Resolved harm codes (T12): TSV with header program_id, code[, weight]. Returns {program_id: (code, weight|None)}."""
    codes = {}
    for r in read_tsv(path):
        code = r['code']
        if code not in CODES:
            raise ValueError('unknown harm code %r for %s' % (code, r['program_id']))
        w = r.get('weight')
        codes[r['program_id']] = (code, float(w) if w not in (None, '') else None)
    return codes


def h5_tables(per_program, tasks_univ, plan, codes, B, seed, use_numpy=None, pair=PRIMARY_PAIR):
    """Shares of HARM_3X / FIX_3X / BOTH_ACCEPTABLE / NEITHER / UNDETERMINABLE among E1 drift programs, per stratum R, A, M,
    M per family and R+A pooled, each with a task-cluster bootstrap 95% interval. basis = 'coded' (resolved human/LLM
    codes with inverse-probability weights model x {QF1..QF8,R,A}) or 'automatic pre-label' (no codes file; NOT the
    confirmatory H5)."""
    drift = [p for p in per_program if p['clean_on_233'] and (p['targets'].get(pair) or {}).get('drift')]
    basis = 'coded' if codes is not None else 'automatic pre-label (not coded; not the confirmatory H5)'

    def cell(p):
        return (p['model'], family_code(p) if p['stratum'] == 'M' else p['stratum'])
    pop = collections.Counter(cell(p) for p in drift)
    items = []
    for p in drift:
        if codes is not None:
            if p['program_id'] not in codes:
                continue
            code, w = codes[p['program_id']]
        else:
            code, w = (p['targets'][pair].get('harm_prelabel') or 'UNDETERMINABLE'), 1.0
        items.append((p, code, w))
    samp = collections.Counter(cell(p) for p, _, _ in items)
    ipw = stats.ipw_weights(pop, samp)
    uncovered = sorted('%s|%s' % c for c, w in ipw.items() if w is None)
    rows = []
    for p, code, w in items:
        weight = w if w is not None else (ipw.get(cell(p)) or 0.0)
        r = {'model': p['model'], 'task_id': p['task_id'], 'stratum': p['stratum'], 'fam': family_code(p), 'w': weight,
             'n_coded': 1}
        for c in CODES:
            r['w_' + c] = weight if c == code else 0.0
        rows.append(r)
    fields = ['w', 'n_coded'] + ['w_' + c for c in CODES]
    groups = {'R': lambda r: r['stratum'] == 'R', 'A': lambda r: r['stratum'] == 'A', 'M': lambda r: r['stratum'] == 'M',
              'R+A': lambda r: r['stratum'] in ('R', 'A')}
    for q in QFS:
        groups['M:' + q] = (lambda q: lambda r: r['stratum'] == 'M' and r['fam'] == q)(q)
    out = {}
    for g, sel in groups.items():
        grows = [r for r in rows if sel(r)]
        tasks = [t for t in tasks_univ if sel({'stratum': t.get('stratum'), 'fam': t.get('fam')})]
        ent = {'n_coded': len(grows), 'weighted_n': sum(r['w'] for r in grows), 'shares': {}}
        if grows:
            stat = {c: (lambda v, c=c: (None if v.sum('w') == 0 else v.sum('w_' + c) / v.sum('w'))) for c in CODES}
            res = stats.cluster_bootstrap_multi(grows, stat, fields, ('stratum',), B=B, seed=seed, use_numpy=use_numpy,
                                                tasks=tasks)
            for c in CODES:
                ent['shares'][c] = {'est': _nn(res[c]['estimate']), 'lo': _nn(res[c]['lo']), 'hi': _nn(res[c]['hi']),
                                    'dropped': res[c]['dropped']}
        out[g] = ent
    return {'basis': basis, 'by_group': out, 'uncovered_cells': uncovered, 'n_drift_programs': len(drift),
            'n_coded_total': len(items), 'weights': 'inverse probability within model x {QF1..QF8,R,A}'}


# ------------------------------------------------------------------------------------------------ summary
def summarize(per_program, plan, tasks=None, B=stats.B_DEFAULT, seed=stats.SEED, targets=None, codes=None, label=None,
              use_numpy=None, sensitivities_on=True, tmap=None):
    """summary.json content. per_program: list of per-program dicts; plan: see default_plan (+ generation state);
    tasks: task dicts of tasks.json (defines the task universe per stratum, incl. tasks without programs)."""
    targets = targets or plan.get('targets') or [PRIMARY_PAIR]
    tmap = tmap or {t['id']: t for t in (tasks or [])}
    models = [m for m in plan['models']]
    present = sorted({p['model'] for p in per_program})
    models_all = [m for m in models if m in present] + [m for m in present if m not in models]
    univ = [{'task_id': t['id'], 'stratum': t['stratum'], 'fam': family_code(t)} for t in (tasks or [])]
    if not univ:
        seen = {}
        for p in per_program:
            seen[p['task_id']] = {'task_id': p['task_id'], 'stratum': p['stratum'], 'fam': family_code(p)}
        univ = list(seen.values())
    summary = {'schema_version': 'summary/1', 'created': now_iso(), 'label': label, 'B': B, 'seed': seed,
               'python': sys.version.split()[0],
               'plan': plan, 'numpy_used': (stats._np is not None) if use_numpy is None else use_numpy,
               'n_programs': len(per_program), 'models': {}, 'targets': {}, 'problems': {},
               'not_implemented_here': ['GEE logistic sensitivity models and the ordinal cutoff covariate (T11, statsmodels)',
                                        'hand attribution agreement (T12)']}
    # per-model descriptives (primary pair)
    for m in models_all:
        mp = [p for p in per_program if p['model'] == m]
        gs = plan['models'].get(m, {})
        oc = collections.Counter(outcome_label(p, PRIMARY_PAIR) for p in mp)
        summary['models'][m] = {
            'group': gs.get('group'), 'open': gs.get('open'), 'planned': gs.get('planned'), 'generated': len(mp),
            'state': gs.get('state'), 'stop_rule': gs.get('stop_rule'),
            'generated_share': (len(mp) / gs['planned']) if gs.get('planned') else None,
            'outcomes_E0a~E1': dict(oc), 'three_x_only': sum(1 for p in mp if p['three_x_only']),
            'empty_source': sum(1 for p in mp if p.get('empty_source')),
            'duplicate_body_rate': (sum(1 for p in mp if p['duplicate_body_of']) / len(mp)) if mp else None,
            'warned_E0a_prereg_rate_of_clean': None}
        cl = [p for p in mp if p['clean_on_233']]
        if cl:
            summary['models'][m]['warned_E0a_prereg_rate_of_clean'] = sum(1 for p in cl if p['warned_E0a']['prereg']) / len(cl)
    for pair in targets:
        flat = [flatten(p, pair, tmap) for p in per_program]
        probs = collections.Counter(r['run_problem'] for r in flat if r['run_problem'] and r['clean'] == 0
                                    and r['exclusion'] is None)
        summary['problems'][pair] = dict(probs)
        tt = {}
        res = run_tests(flat, plan, models_all, univ, B, seed, use_numpy)
        tt['tests'] = res['tests']
        tt['secondary'] = res['secondary']
        rates, fam = rate_tables(flat, models_all, univ, B, seed, use_numpy)
        tt['rates'] = rates
        tt['family_rates'] = fam
        tt['rare_M'] = {m: {k: rates[m].get('M', {}).get(k) for k in ('x', 'n', 'deff', 'icc', 'n_eff', 'cp_deff_upper')}
                        for m in models_all}
        # H4 by family (descriptive), M per family
        mfam = {}
        for q in QFS:
            rows = [r for r in flat if r['stratum'] == 'M' and r['fam'] == q]
            d = sum(r['drift'] for r in rows)
            mfam[q] = {'drift': d, 'drift_unwarned': sum(r['drift_unwarned'] for r in rows),
                       'share_unwarned_on_233': (sum(r['drift_unwarned'] for r in rows) / d) if d else None}
        dM = sum(r['drift'] for r in flat if r['stratum'] == 'M')
        tt['h4_stratum_M'] = {'drift': dM, 'share_unwarned_on_233': (sum(r['drift_unwarned'] for r in flat if r['stratum'] == 'M') / dM) if dM else None,
                              'per_family': mfam}
        if pair == PRIMARY_PAIR:
            tt['h5'] = h5_tables(per_program, univ, plan, codes, B, seed, use_numpy, pair)
            if sensitivities_on:
                tt['sensitivities'] = sensitivities(flat, plan, models_all, univ, B, seed, use_numpy)
        summary['targets'][pair] = tt
    return summary


# ------------------------------------------------------------------------------------------------ report
def fmt_pct(x, d=1):
    return 'n/a' if x is None else '%.*f%%' % (d, 100 * x)


def write_hypotheses_md(summary, decision, path):
    L = []
    L.append('# Hypotheses (generated by analyze_full.py)')
    L.append('')
    L.append('Generated %s. Seed %s, B = %s, numpy accelerator: %s.' % (summary['created'], summary['seed'], summary['B'],
                                                                      summary['numpy_used']))
    if summary.get('label'):
        L.append('')
        L.append('**LABEL: %s**' % summary['label'])
    L.append('')
    L.append('## Decision: %s' % decision['status'])
    if decision['status'] == 'INCOMPLETE':
        L.append('')
        L.append('Hypothesis table not produced (section 13 and review m3: the analyzer is not read on study data until every '
                 'planned model is complete or stopped by a rule).')
        for m, why in decision['open_models'].items():
            L.append('- open model `%s`: %s' % (m, why))
        for why in decision.get('blocking', []):
            L.append('- blocking: %s' % why)
    else:
        L.append('')
        L.append('| Hypothesis | Estimate | 95% interval | p (one-sided) | Holm-adjusted p | Condition | Result |')
        L.append('|---|---|---|---|---|---|---|')
        for r in decision['table']:
            L.append('| %s | %s | %s | %s | %s | %s | %s |' % (r['hypothesis'], r['estimate_text'], r['interval_text'],
                                                               r['p_text'], r['p_adj_text'], r['condition_text'], r['result']))
        import lr61_report                         # T8 apply 2026-11-13 (LR70): H4 on R+A, companion, testability count without the list
        added_h4 = summary['targets'].get(PRIMARY_PAIR, {}).get(lr61_report.ADDED_KEY)
        if added_h4:
            lr61_report.md_h4_ra(L, added_h4)
        L.append('')
        L.append('Framing outcome: **%s**. %s' % (decision['framing']['outcome'], decision['framing']['reason']))
        L.append('')
        L.append('H5 headline: %s' % decision['h5']['summary_sentence'])
        import lr61_report                         # T8 preparation 2026-11-13 (LR42, LR61): the same rule without the listed tasks
        added_p = summary['targets'].get(PRIMARY_PAIR, {}).get(lr61_report.ADDED_KEY)
        if added_p:
            lr61_report.md_rule(L, added_p)
    L.append('')
    L.append('## Per-model silent-drift rate on E1 (clean programs; Wilson 95% and task-cluster bootstrap 95%)')
    L.append('')
    L.append('| Model | Stratum | silent / clean | rate | Wilson | bootstrap | CP+DEFF upper bound | generated |')
    L.append('|---|---|---|---|---|---|---|---|')
    prim = summary['targets'].get(PRIMARY_PAIR, {})
    for m, d in prim.get('rates', {}).items():
        for s, e in d.items():
            L.append('| %s | %s | %d / %d | %s | %s-%s | %s-%s | %s | %d |' % (
                m, s, e['x'], e['n'], fmt_pct(e['rate']), fmt_pct(e['wilson_lo']), fmt_pct(e['wilson_hi']),
                fmt_pct(e['boot_lo']), fmt_pct(e['boot_hi']), fmt_pct(e['cp_deff_upper'], 2) if e['rare_event'] else '-',
                e['generated']))
    import lr61_report                             # T8 preparation 2026-11-13 (LR42, LR61): added report beside the primary rows
    added = prim.get(lr61_report.ADDED_KEY)
    if added:
        lr61_report.md_rates(L, added)
    L.append('')
    L.append('## H4 companions and design-implied value (stratum M, descriptive)')
    h4m = prim.get('h4_stratum_M')
    if h4m:
        L.append('')
        L.append('Observed stratum M: %s drift programs, share without a pandas warning on 2.3.3 = %s.' % (
            h4m['drift'], fmt_pct(h4m['share_unwarned_on_233'])))
        di = summary.get('h4_design_implied')
        L.append('Design-implied value (h4_design.py, recorded at the freeze): %s.' % (
            fmt_pct((di or {}).get('prereg_definition', {}).get('design_implied_H4_M')) if di else 'not supplied (run h4_design.py at T8)'))
        sec = prim.get('tests', {})
        L.append('')
        L.append('| Family | drift programs | share unwarned on 2.3.3 |')
        L.append('|---|---|---|')
        for q, e in h4m['per_family'].items():
            L.append('| %s | %d | %s |' % (q, e['drift'], fmt_pct(e['share_unwarned_on_233'])))
    h5 = prim.get('h5')
    if h5:
        L.append('')
        L.append('## H5 shares (%s)' % h5['basis'])
        L.append('')
        L.append('| Group | coded | weighted n | HARM_3X | FIX_3X | BOTH_ACCEPTABLE | NEITHER | UNDETERMINABLE |')
        L.append('|---|---|---|---|---|---|---|---|')
        for g, e in h5['by_group'].items():
            cells = []
            for c in CODES:
                sh = e['shares'].get(c)
                cells.append('n/a' if not sh else '%s [%s, %s]' % (fmt_pct(sh['est']), fmt_pct(sh['lo']), fmt_pct(sh['hi'])))
            L.append('| %s | %d | %.1f | %s |' % (g, e['n_coded'], e['weighted_n'], ' | '.join(cells)))
        if h5['uncovered_cells']:
            L.append('')
            L.append('Cells with drift programs but none coded (no weight can be formed): %s' % ', '.join(h5['uncovered_cells']))
        if added:                                  # T8 preparation 2026-11-13 (LR42, LR61)
            lr61_report.md_h5(L, added, CODES)
    L.append('')
    L.append('Not computed in this script (T11): GEE sensitivity models, ordinal cutoff covariate, hand-attribution agreement.')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')


# ------------------------------------------------------------------------------------------------ main
def jsonable(o):
    """Strict-JSON copy: nan -> null, +-inf -> the strings 'Infinity' / '-Infinity'."""
    if isinstance(o, float):
        if math.isnan(o):
            return None
        if math.isinf(o):
            return 'Infinity' if o > 0 else '-Infinity'
        return o
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    return o


def load_tasks(path):
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    return d['tasks'] if isinstance(d, dict) else d


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0] if __doc__ else None)
    ap.add_argument('--runs', required=True)
    ap.add_argument('--tasks', required=True)
    ap.add_argument('--models', required=True, help='comma-separated model keys (openrouter id with / replaced by __)')
    ap.add_argument('--out', required=True)
    ap.add_argument('--study', default=os.path.dirname(HERE))
    ap.add_argument('--gen-dir', default=None)
    ap.add_argument('--label', default=None)
    ap.add_argument('--targets', default=PRIMARY_PAIR)
    ap.add_argument('--codes', default=None)
    ap.add_argument('--plan', default=None)
    ap.add_argument('--B', type=int, default=stats.B_DEFAULT)
    ap.add_argument('--seed', type=int, default=stats.SEED)
    ap.add_argument('--no-sensitivities', action='store_true')
    ap.add_argument('--exposure', default=None, help="exposure-regex table (default tasks/exposure_regex.tsv); 'none' for controls and the pilot regression")
    ap.add_argument('--dtype-signal', choices=('default', 'on', 'off'), default='default',
                    help='REPAIR2 2026-11-11: attribution dtype-propagation signal; default = attribution.DTYPE_SIGNAL_DEFAULT (Amendment 4)')
    ap.add_argument('--h4-design', default=None, help='JSON written by h4_design.py --out (design-implied H4, recorded at the freeze)')
    # LR2 step 2026-11-11: additions of lead rulings LR2.4, LR2.5 and LR3 (harness/lead_rulings.py; outside the decision rules)
    ap.add_argument('--flags-before', default=None, help="LR2.4 flags before LR2 (default tasks/FLAGS_BEFORE_LR2.tsv; 'none' = skip)")
    ap.add_argument('--h3-subset-lr2', default=None, help="LR2.5 new naive-silent list (default tasks/H3_NAIVE_SILENT_SUBSET_LR2.tsv if it exists)")
    ap.add_argument('--second-rating', default=None, help='LR3/LR4 second blind invitation rating, TSV task_id<TAB>invitation_strength')
    # REPAIR6 2026-11-12: additions of lead rulings LR13 to LR22 (harness/lead_rulings_2.py; Amendment 11; outside the decision rules)
    ap.add_argument('--oracle-pre-lr1', default=None, help='LR13: pre-LR1 oracle copy (default the sealed logs/repair5_2026-11-11/backup/oracle_before.py)')
    ap.add_argument('--flags-before-lr2-3', default=None, help="LR14: flag snapshot (default tasks/FLAGS_BEFORE_LR2_3.tsv; 'none' = skip)")
    ap.add_argument('--card-variants-before-lr18', default=None, help="LR18: earlier card notes (default tasks/CARD_VARIANTS_BEFORE_LR18.json; 'none' = skip)")
    a = ap.parse_args(argv)
    import decision
    study = a.study
    gen_dir = a.gen_dir or os.path.join(study, 'generations')
    tasks = load_tasks(a.tasks)
    plan = json.load(open(a.plan)) if a.plan else default_plan(study)
    plan['n_tasks'] = len(tasks)
    fill_generation(plan, gen_dir)
    plan['targets'] = a.targets.split(',')
    models = [m for m in a.models.split(',') if m]
    deps = load_deps(study, a.exposure)
    if a.dtype_signal != 'default':                # REPAIR2 2026-11-11 (review MF6): one-analysis override of the module switch
        import attribution as _attr
        _attr.DTYPE_SIGNAL_DEFAULT = (a.dtype_signal == 'on')
    pp = build_per_program(a.runs, tasks, models, deps, gen_dir)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, 'per_program.jsonl'), 'w', encoding='utf-8') as f:
        for r in pp:
            f.write(json.dumps(r, default=str) + '\n')
    codes = read_codes(a.codes) if a.codes else None
    summary = summarize(pp, plan, tasks, a.B, a.seed, plan['targets'], codes, a.label, sensitivities_on=not a.no_sensitivities)
    # T8 preparation 2026-11-13 (lead rulings LR42, LR61): every result reported for stratum R also without the tasks of
    # tasks/RULED_FIDELITY_FAILS.tsv (hash checked against MANIFEST.sha256 of --study; an unreadable or changed list stops the run),
    # written beside the primary result; decides nothing (decision.decide reads none of it).
    import lr61_report
    ruled61 = lr61_report.load_ruled(study)
    for pair, ent in lr61_report.primary_report(pp, plan, tasks, a.B, a.seed, plan['targets'], codes, ruled=ruled61).items():
        summary['targets'][pair][lr61_report.ADDED_KEY] = ent
    if a.h4_design:
        with open(a.h4_design, encoding='utf-8') as f:
            summary['h4_design_implied'] = json.load(f)
    if not a.no_sensitivities:                     # LR2 step 2026-11-11: lead rulings LR2.4, LR2.5, LR3 (not the primary analysis)
        import lead_rulings
        summary['lead_ruling_additions'] = lead_rulings.compute_all(
            a.runs, tasks, models, deps, gen_dir, pp, plan, plan['targets'], a.B, a.seed, summary,
            flags_before_path=a.flags_before or lead_rulings.FLAGS_BEFORE_FILE,
            h3_subset_lr2_path=a.h3_subset_lr2 or lead_rulings.H3_SUBSET_LR2_FILE, second_rating_path=a.second_rating,
            ruled=ruled61)                         # T8 preparation 2026-11-13 (LR42, LR61)
        lead_rulings.write_md(jsonable(summary['lead_ruling_additions']), os.path.join(a.out, 'lead_ruling_additions.md'))
    # REPAIR6 2026-11-12 (lead ruling LR22 (3), review SF11): exclusions table with external-SIGKILL harness errors as their own row
    # (always; the primary per-program rows and statistics are not changed)
    import lead_rulings_2
    summary['exclusions_table_LR22'] = lead_rulings_2.exclusions_table(pp, a.runs, deps.load_record, plan['targets'])
    if not a.no_sensitivities:                     # REPAIR6 2026-11-12: lead rulings LR13 to LR18 (not the primary analysis)
        kw = {}
        if a.oracle_pre_lr1:
            kw.update(oracle_pre_lr1_path=os.path.abspath(a.oracle_pre_lr1))
        if a.flags_before:
            kw.update(flags_before_lr2_path=a.flags_before)
        if a.flags_before_lr2_3:
            kw.update(flags_before_lr2_3_path=a.flags_before_lr2_3)
        if a.card_variants_before_lr18:
            kw.update(card_variants_path=a.card_variants_before_lr18)
        kw.update(ruled=ruled61)                   # T8 preparation 2026-11-13 (LR42, LR61)
        kw.update(codes=codes)                     # REPAIR8 2026-11-13 (LR26): the added H5 report uses the same codes as the primary H5
        summary['lead_ruling_additions_2'] = lead_rulings_2.compute_all(
            a.runs, tasks, models, deps, gen_dir, pp, plan, plan['targets'], a.B, a.seed, summary, **kw)
        lead_rulings_2.write_md(jsonable(summary['lead_ruling_additions_2']), os.path.join(a.out, 'lead_ruling_additions_2.md'),
                                jsonable(summary['exclusions_table_LR22']))
    else:
        L = []
        lead_rulings_2.write_exclusions(L, jsonable(summary['exclusions_table_LR22']))
        with open(os.path.join(a.out, 'exclusions_LR22.md'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(L) + '\n')
    dec = decision.decide(summary, plan)
    summary['decision'] = {k: v for k, v in dec.items() if k != 'text'}
    if dec['status'] == 'COMPLETE':
        summary['decision_by_target'] = {pair: {k: v for k, v in decision.decide(summary, plan, pair).items() if k != 'text'}
                                         for pair in plan['targets'] if pair in summary['targets']}
    with open(os.path.join(a.out, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(jsonable(summary), f, indent=1, default=str)
    write_hypotheses_md(summary, dec, os.path.join(a.out, 'hypotheses.md'))
    print(dec['text'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
