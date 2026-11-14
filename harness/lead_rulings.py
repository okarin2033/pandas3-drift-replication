# Additions of the lead's rulings LR2 and LR3 to the analyzer (FULL_PREREG_AMENDMENT_10.md; LEAD_RULINGS_LR1-LR12_2026-11-11.md).
# Written 2026-11-11 (LR2 step). Standard library only (+ the study's stats / analyze_full).
#
# Nothing here changes the primary analysis: analyze_full.build_per_program, flatten, run_tests, the registered sensitivities and
# per_program.jsonl are untouched. analyze_full.main() calls compute_all() after summarize() and stores the result under the
# top-level key 'lead_ruling_additions' of summary.json (and writes lead_ruling_additions.md); the registered keys are not changed.
#
#  - LR2.4  sensitivity, label "added by lead ruling LR2 before any study generation", outside the decision rules: every confirmatory
#           statistic (H1, H2a, H2b, H3, H4 and the registered secondary ones of run_tests) recomputed with the flags as hashed before
#           LR2 for the tasks that existed then (tasks/FLAGS_BEFORE_LR2.tsv, rows existed_before_rulings = yes; the other tasks keep
#           their current flags), with the number of results (program x target pair) whose class differs.
#  - LR2.5  second sensitivity, same label: the H3 statistic of the Amendment 2(b) sensitivity on the NEW naive-silent list
#           (tasks/H3_NAIVE_SILENT_SUBSET_LR2.tsv), computed only when that file exists (it is written only if the naive re-run
#           under LR1 and LR2 gives other figures than Amendment 2); the frozen list keeps its registered key H3_naive_silent_subset.
#  - LR3    descriptive table: the H3 statistic by invitation level (1, 2, 3, all) with the cell counts (M tasks and clean
#           programs per level and group), for the primary rating (card field invitation_strength) and, when present, the
#           second rating of LR4 (a TSV task_id<TAB>invitation_strength, or the card field invitation_strength_second).
#  - T8 preparation 2026-11-13 (lead rulings LR42, LR61; deviation T8P-LR61-1 of deviations/T8PREP.md): in the LR2.4 sensitivity the
#           result reported for stratum R (secondary H4_stratum_R_only) is also given without the tasks of tasks/RULED_FIDELITY_FAILS.tsv
#           (harness/lr61_report.py, key added_report_LR42_LR61 beside it); nothing else changes.
#  - T8 apply 2 2026-11-13 (lead ruling LR70, LEAD_RULINGS_LR69-LR76_2026-11-13.md; deviation T8A2-LR70-1 of deviations/T8APPLY.md):
#           the H4 on R+A that a sensitivity reports (tests H4, its companion H4_companion_drift_plus_loud_warned_on_233 and the R+A
#           testability count n_drift_programs / n_drift_tasks) is also given without the tasks of tasks/RULED_FIDELITY_FAILS.tsv:
#           added_h4_ra(), one lr61_report.without_ruled call per sensitivity and pair, key H4_RA_added_report_LR42_LR61 beside the
#           sensitivity's own results; in lead_ruling_additions.md one marked block after each pair's table (md_h4_ra_added). Labelled as
#           LR61 labels it; no decision rule reads it; the sensitivity's own results are not changed.
import copy
import csv
import json
import math
import os

import analyze_full as af
import decision
import lr61_report as lr61
import stats

LABEL_LR2 = 'added by lead ruling LR2 before any study generation'
LABEL_LR3 = 'added by lead ruling LR3: descriptive table, no rule changes'
FLAGS_BEFORE_FILE = os.path.join(os.path.dirname(af.HERE), 'tasks', 'FLAGS_BEFORE_LR2.tsv')
H3_SUBSET_LR2_FILE = os.path.join(os.path.dirname(af.HERE), 'tasks', 'H3_NAIVE_SILENT_SUBSET_LR2.tsv')
CLASS_FIELDS = ('class', 'drift', 'silent', 'magnitude')


def _est(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    return str(x) if x in (math.inf, -math.inf) else x


# ------------------------------------------------------------------------------------------------ inputs
def load_flags_before(path):
    """{task_id: {'order_significant', 'sort_keys', 'row_order'}} for the rows with existed_before_rulings = yes (all rows if the
    column is absent). Empty dict if the file does not exist."""
    if not path or not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        lines = [ln for ln in f if not ln.startswith('#')]
    out = {}
    for r in csv.DictReader(lines, delimiter='\t'):
        if r.get('existed_before_rulings', 'yes') != 'yes':
            continue
        out[r['task_id']] = {'order_significant': r['order_significant'].strip().lower() == 'true',
                             'sort_keys': json.loads(r['sort_keys']), 'row_order': r['row_order']}
    return out


def tasks_with_flags(tasks, flags):
    """-> (copy of tasks with the given flags put in, sorted ids whose flags differ from the current card)."""
    alt, changed = [], []
    for t in tasks:
        f = flags.get(t['id'])
        if f is None:
            alt.append(t)
            continue
        cur = {'order_significant': bool(t.get('order_significant')), 'sort_keys': list(t.get('sort_keys') or []),
               'row_order': (t.get('acceptable_variants') or {}).get('row_order')}
        if cur == f:
            alt.append(t)
            continue
        u = copy.deepcopy(t)
        u['order_significant'] = f['order_significant']
        u['sort_keys'] = list(f['sort_keys'])
        u.setdefault('acceptable_variants', {})['row_order'] = f['row_order']
        alt.append(u)
        changed.append(t['id'])
    return alt, sorted(changed)


def load_rating(path):
    """{task_id: level} from a TSV with columns task_id and invitation_strength. Empty dict if no path."""
    if not path:
        return {}
    with open(path, encoding='utf-8') as f:
        lines = [ln for ln in f if not ln.startswith('#')]
    out = {}
    for r in csv.DictReader(lines, delimiter='\t'):
        v = (r.get('invitation_strength') or '').strip()
        if v:
            out[r['task_id']] = int(v)
    return out


def _models_all(plan, per_program):
    present = sorted({p['model'] for p in per_program})
    models = list(plan['models'])
    return [m for m in models if m in present] + [m for m in present if m not in models]


def _univ(tasks):
    return [{'task_id': t['id'], 'stratum': t['stratum'], 'fam': af.family_code(t)} for t in tasks]


def _summ_tests(res):
    keep = ('estimate', 'lo', 'hi', 'p', 'null', 'dropped', 'n_valid', 'condition')
    return {k: {f: _est(v.get(f)) for f in keep if f in v} for k, v in res.items()}


# ------------------------------------------------------------------------------------------------ LR2.4
def lr2_flags_sensitivity(runs, tasks, models, deps, gen_dir, per_program, plan, targets, B, seed, flags, use_numpy=None,
                          primary_tests=None, ruled=None):
    ruled = lr61.load_ruled() if ruled is None else ruled       # T8 preparation 2026-11-13 (LR42, LR61)
    alt_tasks, changed = tasks_with_flags(tasks, flags)
    out = {'label': LABEL_LR2, 'ruling': 'LR2.4', 'outside_decision_rules': True,
           'flags_source': 'flags as hashed before lead ruling LR2 (tasks/FLAGS_BEFORE_LR2.tsv, existed_before_rulings = yes)',
           'n_tasks_with_pre_LR2_flags': len(flags), 'n_tasks_in_run_with_pre_LR2_flags': sum(1 for t in tasks if t['id'] in flags),
           'tasks_whose_flags_differ': changed}
    rebuilt = af.build_per_program(runs, [t for t in alt_tasks if t['id'] in set(changed)], models, deps, gen_dir) if changed else []
    rb = {p['program_id']: p for p in rebuilt}
    alt_pp = [rb.get(p['program_id'], p) for p in per_program]
    diffs = []
    for p in per_program:
        q = rb.get(p['program_id'])
        if q is None:
            continue
        for pair in targets:
            a, b = p['targets'].get(pair) or {}, q['targets'].get(pair) or {}
            va, vb = tuple(a.get(k) for k in CLASS_FIELDS), tuple(b.get(k) for k in CLASS_FIELDS)
            if va != vb or p['clean_on_233'] != q['clean_on_233']:
                diffs.append({'program_id': p['program_id'], 'pair': pair, 'with_current_flags': dict(zip(CLASS_FIELDS, va)),
                              'with_pre_LR2_flags': dict(zip(CLASS_FIELDS, vb))})
    out['n_programs_reclassified'] = len(rebuilt)
    out['n_results_class_differs'] = len(diffs)
    out['n_results_class_differs_by_pair'] = {pair: sum(1 for d in diffs if d['pair'] == pair) for pair in targets}
    out['results_class_differs'] = diffs
    amap = {t['id']: t for t in alt_tasks}
    univ = _univ(alt_tasks)
    models_all = _models_all(plan, alt_pp)
    out['targets'] = {}
    for pair in targets:
        flat = [af.flatten(p, pair, amap) for p in alt_pp]
        res = af.run_tests(flat, plan, models_all, univ, B, seed, use_numpy)
        ent = {'tests': _summ_tests(res['tests']), 'secondary': _summ_tests(res['secondary'])}
        if primary_tests and pair in primary_tests:
            ent['estimate_differs_from_primary'] = {
                k: _est(ent['tests'][k].get('estimate')) != _est(primary_tests[pair].get(k, {}).get('estimate'))
                for k in ent['tests']}
        ent[lr61.ADDED_KEY] = added_h4_r(alt_pp, alt_tasks, pair, plan, B, seed, use_numpy, ruled)   # T8 preparation (LR42, LR61)
        ent[H4_RA_KEY] = added_h4_ra(alt_pp, alt_tasks, pair, plan, B, seed, use_numpy, ruled)      # T8 apply 2 (LR70)
        out['targets'][pair] = ent
    return out


def added_h4_r(pp_all, tasks_all, pair, plan, B, seed, use_numpy, ruled):
    """T8 preparation 2026-11-13 (LR42, LR61): the secondary H4_stratum_R_only of af.run_tests, as in the sensitivity, on the rows and
    tasks without the listed tasks (lr61_report.without_ruled)."""
    def compute(pp, tk):
        tm = {t['id']: t for t in tk}
        return af.run_tests([af.flatten(p, pair, tm) for p in pp], plan, _models_all(plan, pp), _univ(tk), B, seed, use_numpy)
    return lr61.without_ruled(compute, pp_all, tasks_all, ruled=ruled,
                              extract=lambda res: _summ_tests({'H4_stratum_R_only': res['secondary']['H4_stratum_R_only']})[
                                  'H4_stratum_R_only'])


H4_COMP = 'H4_companion_drift_plus_loud_warned_on_233'
H4_RA_KEY = 'H4_RA_' + lr61.ADDED_KEY            # T8 apply 2 2026-11-13 (LR70): holds ADDED_KEY, so every strip of the added keys removes it


def added_h4_ra(pp_all, tasks_all, pair, plan, B, seed, use_numpy, ruled):
    """T8 apply 2 2026-11-13 (LR70): the H4 on R+A of af.run_tests as the sensitivity reports it (tests H4, summarised by _summ_tests),
    its companion (secondary H4_companion_drift_plus_loud_warned_on_233) and the R+A testability count of H4 (n_drift_programs,
    n_drift_tasks; the registered minimum of decision.py beside it for reference), computed by the same code on the rows and tasks without
    the listed tasks: one lr61_report.without_ruled call. Decides nothing."""
    def compute(pp, tk):
        tm = {t['id']: t for t in tk}
        return af.run_tests([af.flatten(p, pair, tm) for p in pp], plan, _models_all(plan, pp), _univ(tk), B, seed, use_numpy)

    def extract(res):
        h4 = res['tests']['H4']
        return {'H4_RA': _summ_tests({'H4': h4})['H4'],
                H4_COMP: _summ_tests({H4_COMP: res['secondary'][H4_COMP]})[H4_COMP],
                'H4_testability_RA': {'n_drift_programs': h4.get('n_drift_programs'), 'n_drift_tasks': h4.get('n_drift_tasks'),
                                      'registered_minimum': {'n_drift_programs': decision.H4_MIN_DRIFT,
                                                             'n_drift_tasks': decision.H4_MIN_TASKS}},
                'H4_RA_note': ('LR70: the H4 on R+A of this sensitivity, its companion and the R+A testability count computed by the same '
                               'code without the listed tasks; the sensitivity\'s own values are computed on the full strata R and A')}
    return lr61.without_ruled(compute, pp_all, tasks_all, ruled=ruled, extract=extract)


def md_h4_ra_added(L, e, pair):
    """T8 apply 2 2026-11-13 (LR70): one marked block with the added H4 on R+A of a sensitivity (after the sensitivity's table)."""
    r = e['result']
    h, c, n = r.get('H4_RA') or {}, r.get(H4_COMP) or {}, r.get('H4_testability_RA') or {}
    mn = n.get('registered_minimum') or {}
    L += [lr61.MD_START, '', '**%s.** Left out: %s (%d programs).' % (e['label'], ', '.join(e['tasks_left_out']) or 'none',
                                                                        e['n_programs_left_out']), '',
          '- %s, H4 on R+A without the listed tasks: estimate %s, lo %s, hi %s, p %s; companion (drift plus LOUD, warned on 2.3.3): '
          'estimate %s, lo %s, hi %s; testability count on R+A without the listed tasks: %s drift programs in %s tasks (registered '
          'minimum %s and %s)' % (pair, h.get('estimate'), h.get('lo'), h.get('hi'), h.get('p'), c.get('estimate'), c.get('lo'),
                                  c.get('hi'), n.get('n_drift_programs'), n.get('n_drift_tasks'), mn.get('n_drift_programs'),
                                  mn.get('n_drift_tasks')), '', lr61.MD_END]


# ------------------------------------------------------------------------------------------------ LR2.5
def h3_on_subset(flat, plan, models_all, univ, B, seed, subset, use_numpy=None):
    """The Amendment 2(b) computation (analyze_full.sensitivities, key H3_naive_silent_subset) on another task list."""
    inscope = [m for m in models_all if m in plan['models']]
    flat_in = [r for r in flat if r['model'] in inscope]

    def _in(r):
        return r.get('stratum') == 'M' and (r.get('task_id') or r.get('id')) in subset
    sub_rows = [r for r in flat_in if _in(r)]
    kw = dict(fields=af.FLAT_FIELDS, group_by=af.GROUP_BY, B=B, seed=seed, use_numpy=use_numpy)
    res = stats.cluster_bootstrap_multi(flat_in, {'h3': af.h3_statistic(stats.h3_eligible_models(sub_rows, inscope))},
                                        restrict=_in, tasks=[t for t in univ if _in(t)], **kw)['h3']
    return {'estimate': _est(res['estimate']), 'lo': _est(res['lo']), 'hi': _est(res['hi']), 'dropped': res['dropped'],
            'n_valid': res['n_valid'], 'n_tasks_in_subset': len(subset),
            'n_tasks_present': len({t.get('task_id') or t.get('id') for t in univ if _in(t)})}


def lr2_naive_subset_sensitivity(per_program, tasks, plan, B, seed, subset_path, frozen_subset, use_numpy=None):
    out = {'label': LABEL_LR2, 'ruling': 'LR2.5', 'outside_decision_rules': True, 'pair': af.PRIMARY_PAIR}
    if not subset_path or not os.path.exists(subset_path):
        out.update(applicable=False, reason='no new naive-silent list: the naive re-run under LR1 and LR2 gave the Amendment 2 '
                                            'figures, so only the frozen list (H3_naive_silent_subset) is reported')
        return out
    new = af.load_h3_subset(subset_path)
    tmap = {t['id']: t for t in tasks}
    flat = [af.flatten(p, af.PRIMARY_PAIR, tmap) for p in per_program]
    out.update(applicable=True, list_file=os.path.basename(subset_path), n_tasks_new_list=len(new),
               n_tasks_frozen_list=len(frozen_subset), only_in_new=sorted(new - frozen_subset),
               only_in_frozen=sorted(frozen_subset - new),
               H3_naive_silent_subset_LR2=h3_on_subset(flat, plan, _models_all(plan, per_program), _univ(tasks), B, seed, new,
                                                       use_numpy))
    return out


# ------------------------------------------------------------------------------------------------ LR3
def lr3_table(per_program, tasks, plan, B, seed, ratings, use_numpy=None, pair=af.PRIMARY_PAIR):
    """ratings: {name: {task_id: level}}; the primary rating is normally the card field invitation_strength."""
    tmap = {t['id']: t for t in tasks}
    models_all = _models_all(plan, per_program)
    inscope = [m for m in models_all if m in plan['models']]
    flat0 = [af.flatten(p, pair, tmap) for p in per_program]
    univ = _univ(tasks)
    m_tasks = [t for t in tasks if t['stratum'] == 'M']
    kw = dict(fields=af.FLAT_FIELDS, group_by=af.GROUP_BY, B=B, seed=seed, use_numpy=use_numpy)
    out = {'label': LABEL_LR3, 'ruling': 'LR3', 'pair': pair, 'ratings': {}}
    for name, rating in ratings.items():
        if not rating:
            out['ratings'][name] = {'present': False}
            continue
        flat = [dict(r, strength=rating.get(r['task_id']) if r['stratum'] == 'M' else None) for r in flat0
                if r['model'] in inscope]
        m_rows = [r for r in flat if r['stratum'] == 'M']
        base_models = stats.h3_eligible_models(m_rows, inscope)
        st = {'all': af.h3_statistic(base_models)}
        for lvl in (1, 2, 3):
            st[str(lvl)] = af.h3_statistic(base_models, extra={'strength': lvl})
        res = stats.cluster_bootstrap_multi(flat, st, restrict=lambda r: r['stratum'] == 'M',
                                            tasks=[t for t in univ if t.get('stratum') == 'M'], **kw)
        rows = {}
        for lvl in ('1', '2', '3', 'all'):
            def _lv(tid):
                return lvl == 'all' or rating.get(tid) == int(lvl)
            g = {grp: [t['id'] for t in m_tasks if stats.h3_group(af.family_code(t)) == grp and _lv(t['id'])] for grp in ('G1', 'G2')}
            prog = {grp: sum(r['clean'] for r in m_rows if r['grp'] == grp and _lv(r['task_id'])) for grp in ('G1', 'G2')}
            r = res[lvl]
            rows[lvl] = {'tasks_G1': len(g['G1']), 'tasks_G2': len(g['G2']), 'clean_programs_G1': prog['G1'],
                         'clean_programs_G2': prog['G2'],
                         'mean_level_G1': None, 'mean_level_G2': None,
                         'h3_log_rr': _est(r['estimate']), 'lo': _est(r['lo']), 'hi': _est(r['hi']), 'dropped': r['dropped'],
                         'n_valid': r['n_valid']}
            if lvl == 'all':
                for grp in ('G1', 'G2'):
                    lv = [rating[t] for t in g[grp] if t in rating]
                    rows[lvl]['mean_level_' + grp] = (sum(lv) / len(lv)) if lv else None
        out['ratings'][name] = {'present': True, 'n_rated_M_tasks': sum(1 for t in m_tasks if t['id'] in rating),
                                'models_entering': base_models, 'levels': rows}
    return out


# ------------------------------------------------------------------------------------------------ all
def compute_all(runs, tasks, models, deps, gen_dir, per_program, plan, targets, B, seed, summary, flags_before_path=FLAGS_BEFORE_FILE,
                h3_subset_lr2_path=H3_SUBSET_LR2_FILE, second_rating_path=None, use_numpy=None, ruled=None):
    ruled = lr61.load_ruled() if ruled is None else ruled       # T8 preparation 2026-11-13 (LR42, LR61)
    primary_tests = {pair: (summary['targets'].get(pair) or {}).get('tests') or {} for pair in targets}
    flags = load_flags_before(flags_before_path) if flags_before_path not in (None, 'none') else {}
    out = {'note': 'lead rulings LR2 and LR3 (Amendment 10); not part of the primary analysis or the decision rules'}
    out['LR2_4_flags_before_LR2'] = lr2_flags_sensitivity(runs, tasks, models, deps, gen_dir, per_program, plan, targets, B, seed,
                                                          flags, use_numpy, primary_tests, ruled)
    out['LR2_4_flags_before_LR2']['flags_file'] = None if not flags else os.path.basename(flags_before_path)
    out['LR2_5_new_naive_silent_list'] = lr2_naive_subset_sensitivity(
        per_program, tasks, plan, B, seed, None if h3_subset_lr2_path in (None, 'none') else h3_subset_lr2_path, af.load_h3_subset(),
        use_numpy)
    primary = {t['id']: t['invitation_strength'] for t in tasks if t['stratum'] == 'M' and t.get('invitation_strength') is not None}
    second = load_rating(second_rating_path) if second_rating_path else \
        {t['id']: t['invitation_strength_second'] for t in tasks if t['stratum'] == 'M' and t.get('invitation_strength_second') is not None}
    out['LR3_h3_by_invitation_level'] = lr3_table(per_program, tasks, plan, B, seed,
                                                  {'primary_rating': primary, 'second_rating': second}, use_numpy)
    return out


def write_md(add, path):
    L = ['# Additions of lead rulings LR2 and LR3 (not the primary analysis; outside the decision rules)', '']
    s = add['LR2_4_flags_before_LR2']
    L += ['## LR2.4 sensitivity: "%s"' % s['label'], '',
          '- tasks with pre-LR2 flags in this run: %d; tasks whose flags differ: %d; programs reclassified: %d; '
          'results (program x pair) whose class differs: %d' % (s['n_tasks_in_run_with_pre_LR2_flags'], len(s['tasks_whose_flags_differ']),
                                                               s['n_programs_reclassified'], s['n_results_class_differs']), '']
    for pair, ent in s['targets'].items():
        L.append('| %s | estimate | lo | hi | p |' % pair)
        L.append('|---|---|---|---|---|')
        for k, v in ent['tests'].items():
            L.append('| %s | %s | %s | %s | %s |' % (k, v.get('estimate'), v.get('lo'), v.get('hi'), v.get('p')))
        L.append('')
        if ent.get(H4_RA_KEY):                              # T8 apply 2 2026-11-13 (LR70)
            md_h4_ra_added(L, ent[H4_RA_KEY], pair)
    s = add['LR2_5_new_naive_silent_list']
    L += ['## LR2.5 sensitivity: "%s"' % s['label'], '']
    if not s.get('applicable'):
        L += ['- not applicable: %s' % s['reason'], '']
    else:
        r = s['H3_naive_silent_subset_LR2']
        L += ['- new list %s: %d tasks (frozen list %d); H3 log RR %s [%s, %s], %d of %d tasks present'
              % (s['list_file'], s['n_tasks_new_list'], s['n_tasks_frozen_list'], r['estimate'], r['lo'], r['hi'],
                 r['n_tasks_present'], r['n_tasks_in_subset']), '']
    t = add['LR3_h3_by_invitation_level']
    L += ['## LR3: H3 statistic by invitation level (%s)' % t['label'], '']
    for name, ent in t['ratings'].items():
        if not ent.get('present'):
            L += ['- %s: not present' % name, '']
            continue
        L += ['%s (%d rated M tasks)' % (name, ent['n_rated_M_tasks']), '',
              '| level | G1 tasks | G2 tasks | G1 clean programs | G2 clean programs | H3 log RR | lo | hi |', '|---|---|---|---|---|---|---|---|']
        for lvl, r in ent['levels'].items():
            L.append('| %s | %d | %d | %d | %d | %s | %s | %s |' % (lvl, r['tasks_G1'], r['tasks_G2'], r['clean_programs_G1'],
                                                                 r['clean_programs_G2'], r['h3_log_rr'], r['lo'], r['hi']))
        L.append('')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
