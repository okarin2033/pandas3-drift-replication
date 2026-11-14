# Added report of lead rulings LR42 and LR61 (LEAD_RULINGS_LR42-LR56_2026-11-13.md, LEAD_RULINGS_LR57-LR63_2026-11-13.md; Amendment 12):
# every result that is reported for stratum R is computed a second time without the tasks listed in tasks/RULED_FIDELITY_FAILS.tsv
# (today one task, R_08). Registered before any study generation; decides nothing. Written 2026-11-13 (T8 preparation, LR61). Standard library only (+ the study's analyze_full / decision / validate_tasks).
#
# One place: without_ruled() reads the ruled list (validate_tasks.load_ruled_fidelity_fails with an explicit path: the sha256 must equal
# the file's MANIFEST.sha256 line, header and rows must be well formed; an unreadable, unpinned, changed or malformed file raises
# RuledListError, never an empty list), drops the listed tasks from the per-program rows and from the task list, and calls the SAME code
# that computes the result for stratum R (a callable handed in by the caller). Each added result carries LABEL and is written beside the
# primary result (key ADDED_KEY), never in its place; nothing here is read by decision.decide() or by any decision rule.
# The primary analysis (build_per_program, flatten, run_tests, rate_tables, h5_tables, summarize, the registered sensitivities, the
# lead-ruling additions) and per_program.jsonl are not changed; the inputs handed in are not mutated.
#
# Places that report a result for stratum R and receive the added report (deviation T8P-LR61-1 of deviations/T8PREP.md):
#  analyze_full.main -> primary_report(): per target pair the per-model rates of stratum R (rate_tables: x, n, rate, Wilson,
#      task-cluster bootstrap, rare-event bound), the registered secondary H4_stratum_R_only (run_tests); on the primary pair the H5
#      shares of the groups R and R+A (h5_tables) and the H5 interpretation rule with its fallback R -> R+A (decision.h5_headline),
#      all computed by analyze_full.summarize() on the data without the listed tasks.
#  lead_rulings.lr2_flags_sensitivity (LR2.4) and lead_rulings_2.alt_analysis (LR13 a/b, LR14, LR16 a/b, LR17): H4_stratum_R_only.
#  lead_rulings_2: LR16 case counts of family R; LR17 RQ5 stratum R rates (both columns); LR18 H5 automatic pre-label groups R and
#      R+A; LR26 H5 groups R and R+A; LR15 name-only counts of family R.
# T8 apply 2026-11-13 (lead ruling LR70, LEAD_RULINGS_LR69-LR76_2026-11-13.md; deviation T8A-LR70-1 of deviations/T8APPLY.md): the
#  added report is given for every result whose definition names stratum R, alone or pooled with stratum A. primary_report() also
#  carries, from the same summarize() call on the data without the listed tasks, the confirmatory H4 on R+A (tests H4), its companion
#  (secondary H4_companion_drift_plus_loud_warned_on_233) and the R+A testability count of H4 (n_drift_programs, n_drift_tasks, which
#  decision.py compares with its minimum on the full strata); labelled as before; no decision rule reads them (md_h4_ra: hypotheses.md).
# T8 apply 2 2026-11-13 (lead ruling LR70; deviation T8A2-LR70-1 of deviations/T8APPLY.md): the H4 on R+A that the sensitivities report
#  (lead_rulings.lr2_flags_sensitivity LR2.4; lead_rulings_2.alt_analysis LR13 a/b, LR14, LR16 a/b, LR17), with its companion and the
#  R+A testability count, also gets the added report: lead_rulings.added_h4_ra, one without_ruled call per sensitivity and pair (key
#  H4_RA_added_report_LR42_LR61). This file: comment lines only.
import collections
import copy
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
STUDY = os.path.dirname(HERE)
RULED_FILE_REL = 'tasks/RULED_FIDELITY_FAILS.tsv'
LABEL = ('added report of lead rulings LR42 and LR61: stratum R without the tasks of tasks/RULED_FIDELITY_FAILS.tsv; registered before '
         'any study generation; decides nothing')
ADDED_KEY = 'added_report_LR42_LR61'
R_GROUPS = ('R', 'R+A')                       # H5 groups that hold stratum R (R+A is the registered fallback of the H5 rule)
MD_START = '<!-- LR61 added report start -->'
MD_END = '<!-- LR61 added report end -->'

RuledList = collections.namedtuple('RuledList', 'ids sha256 rel rows')


class RuledListError(Exception):
    pass


def load_ruled(study=None, path=None):
    """-> RuledList of tasks/RULED_FIDELITY_FAILS.tsv (or `path`), its sha256 checked against its line in study/MANIFEST.sha256.
    Raises RuledListError when the file cannot be read, is not pinned, does not match its manifest line or is malformed."""
    import validate_tasks as vt
    study = os.path.abspath(study or STUDY)
    p = os.path.abspath(path or os.path.join(study, *RULED_FILE_REL.split('/')))
    try:
        with open(p, 'rb') as f:
            data = f.read()
        rows, errs = vt.load_ruled_fidelity_fails(study, p)
    except (OSError, UnicodeDecodeError) as e:
        raise RuledListError('LR61: ruled list %s cannot be read: %s' % (os.path.basename(p), e.__class__.__name__))
    if errs:
        raise RuledListError('; '.join(errs))
    rel = os.path.relpath(p, study).replace(os.sep, '/')
    return RuledList(tuple(sorted(rows)), hashlib.sha256(data).hexdigest(), rel, rows)


def _tid(t):
    return t.get('id') or t.get('task_id')


def without_ruled(compute, per_program, tasks, extract=None, ruled=None, study=None, path=None):
    """The one function of LR61: read the ruled list (unless a RuledList from load_ruled() is handed in), drop the listed tasks from
    `per_program` and `tasks`, call compute(per_program_kept, tasks_kept) (the same code that computes the result for stratum R) and
    return the labelled added result (extract(result) when extract is given)."""
    r = ruled if ruled is not None else load_ruled(study, path)
    if not isinstance(r, RuledList):
        raise RuledListError('LR61: the ruled list must come from load_ruled()')
    ex = set(r.ids)
    pp = [p for p in per_program if p.get('task_id') not in ex]
    tk = [t for t in (tasks or []) if _tid(t) not in ex]
    present = {p.get('task_id') for p in per_program} | {_tid(t) for t in (tasks or [])}
    res = compute(pp, tk)
    return {'label': LABEL, 'rulings': ['LR42', 'LR61'], 'outside_decision_rules': True, 'decides_nothing': True,
            'ruled_file': r.rel, 'ruled_file_sha256': r.sha256, 'listed_tasks': list(r.ids),
            'tasks_left_out': sorted(ex & present), 'n_tasks_kept': len(tk), 'n_programs_left_out': len(per_program) - len(pp),
            'result': extract(res) if extract is not None else res}


# ------------------------------------------------------------------------------------------------ extractors
def h5_r_groups(h5):
    """The parts of an h5_tables() result that report stratum R: groups R and R+A, with the basis and the R cells without codes."""
    if not h5:
        return None
    return {'basis': h5.get('basis'), 'by_group': {g: h5['by_group'][g] for g in R_GROUPS if g in h5.get('by_group', {})},
            'uncovered_cells_R': [c for c in h5.get('uncovered_cells', []) if c.endswith('|R')],
            'weights': h5.get('weights')}


def secondary_h4_r(res_tests_secondary, summ=None):
    v = res_tests_secondary.get('H4_stratum_R_only')
    return summ({'H4_stratum_R_only': v})['H4_stratum_R_only'] if summ else v


def case_counts_r(cc):
    """{pair: counts of family R} from a lead_rulings_2._case_counts() / lr15 'counts' dict."""
    return {pair: {'total_R': e['by_family'].get('R', 0),
                   'by_model_R': {k.rsplit('|', 1)[0]: v for k, v in e['by_model_family'].items() if k.endswith('|R')}}
            for pair, e in cc.items()}


# ------------------------------------------------------------------------------------------------ primary analysis
def primary_report(per_program, plan, tasks, B, seed, targets, codes, use_numpy=None, ruled=None, study=None, path=None):
    """{pair: added entry} for the results of the primary analysis that are reported for stratum R, computed by
    analyze_full.summarize() (sensitivities off: no registered sensitivity reports stratum R alone) on the data without the listed
    tasks; the H5 rule (decision.h5_headline, with its fallback R -> R+A) applied to that H5 table. The primary summary is not read."""
    import analyze_full as af
    import decision
    r = ruled if ruled is not None else load_ruled(study, path)

    def compute(pp, tk):
        return af.summarize(pp, copy.deepcopy(plan), tk if tasks else None, B, seed, list(targets), codes, None, use_numpy=use_numpy,
                            sensitivities_on=False)

    full = without_ruled(compute, per_program, tasks, ruled=r)
    s = full.pop('result')
    out = {}
    for pair in targets:
        tg = s['targets'].get(pair) or {}
        res = {'rates_R': {m: d['R'] for m, d in (tg.get('rates') or {}).items() if 'R' in d},
               'H4_stratum_R_only': (tg.get('secondary') or {}).get('H4_stratum_R_only')}
        h4 = (tg.get('tests') or {}).get('H4')                # LR70: the confirmatory H4 on R+A, its companion, its testability count
        if h4 is not None:
            res['H4_RA'] = h4
            res['H4_companion_drift_plus_loud_warned_on_233'] = (tg.get('secondary') or {}).get(
                'H4_companion_drift_plus_loud_warned_on_233')
            res['H4_testability_RA'] = {'n_drift_programs': h4.get('n_drift_programs'), 'n_drift_tasks': h4.get('n_drift_tasks'),
                                        'registered_minimum': {'n_drift_programs': decision.H4_MIN_DRIFT,
                                                               'n_drift_tasks': decision.H4_MIN_TASKS}}
            res['H4_RA_note'] = ('LR70: the confirmatory H4 on R+A, its companion and the R+A testability count computed by the same '
                                 'code without the listed tasks; the primary H4, its Holm step and its testability are decided on the '
                                 'full strata R and A as registered')
        if 'h5' in tg:
            res['h5'] = h5_r_groups(tg['h5'])
            res['h5_rule'] = decision.h5_headline(tg['h5'])
            res['h5_rule_note'] = ('the registered H5 rule (section 7: R headline, fallback R+A at fewer than %d coded drift programs) '
                                   'applied to the H5 table without the listed tasks; the primary H5 rule is computed on the full '
                                   'stratum as registered' % decision.H5_MIN_CODED)
        out[pair] = dict(full, result=res)
    return out


# ------------------------------------------------------------------------------------------------ report text
def _pct(x, d=1):
    return 'n/a' if x is None else '%.*f%%' % (d, 100 * x)


def _head(L, e):
    L += [MD_START, '', '**%s.** Listed tasks: %s; left out of this run: %s (%d programs).' % (
        e['label'][0].upper() + e['label'][1:], ', '.join(e['listed_tasks']) or 'none', ', '.join(e['tasks_left_out']) or 'none',
        e['n_programs_left_out']), '']


def md_rates(L, e):
    """Rows of the per-model rate table for stratum R without the listed tasks (hypotheses.md, after the primary table)."""
    _head(L, e)
    L.append('| Model | Stratum | silent / clean | rate | Wilson | bootstrap | CP+DEFF upper bound | generated |')
    L.append('|---|---|---|---|---|---|---|---|')
    for m, x in e['result']['rates_R'].items():
        L.append('| %s | R without the listed tasks | %d / %d | %s | %s-%s | %s-%s | %s | %d |' % (
            m, x['x'], x['n'], _pct(x['rate']), _pct(x['wilson_lo']), _pct(x['wilson_hi']), _pct(x['boot_lo']), _pct(x['boot_hi']),
            _pct(x['cp_deff_upper'], 2) if x['rare_event'] else '-', x['generated']))
    h = e['result'].get('H4_stratum_R_only')
    if h:
        L += ['', 'Secondary H4 on stratum R only, without the listed tasks: %s [%s, %s].' % (_pct(h.get('estimate')), _pct(h.get('lo')),
                                                                                           _pct(h.get('hi')))]
    L += ['', MD_END]


def md_h5(L, e, codes):
    h = e['result'].get('h5')
    if not h:
        return
    _head(L, e)
    L.append('| Group | coded | weighted n | ' + ' | '.join(codes) + ' |')
    L.append('|---|---|---|' + '---|' * len(codes))
    for g, x in h['by_group'].items():
        cells = []
        for c in codes:
            sh = x['shares'].get(c)
            cells.append('n/a' if not sh else '%s [%s, %s]' % (_pct(sh['est']), _pct(sh['lo']), _pct(sh['hi'])))
        L.append('| %s without the listed tasks | %d | %.1f | %s |' % (g, x['n_coded'], x['weighted_n'], ' | '.join(cells)))
    L += ['', MD_END]


def md_h4_ra(L, e):
    """LR70: the confirmatory H4 on R+A, its companion and the R+A testability count without the listed tasks (hypotheses.md, right
    after the hypothesis table, which is written only when the decision is complete)."""
    r = e['result']
    h = r.get('H4_RA')
    if not h:
        return
    c = r.get('H4_companion_drift_plus_loud_warned_on_233') or {}
    n = r.get('H4_testability_RA') or {}
    mn = n.get('registered_minimum') or {}
    _head(L, e)
    L += ['H4 on R+A without the listed tasks (share of drift programs without a pandas warning on 2.3.3): %s [%s, %s]; companion '
          '(drift plus LOUD, warned on 2.3.3): %s [%s, %s]; testability count on R+A without the listed tasks: %s drift programs in %s '
          'tasks (registered minimum %s and %s; the primary testability is decided on the full strata).' % (
              _pct(h.get('estimate')), _pct(h.get('lo')), _pct(h.get('hi')), _pct(c.get('estimate')), _pct(c.get('lo')),
              _pct(c.get('hi')), n.get('n_drift_programs'), n.get('n_drift_tasks'), mn.get('n_drift_programs'),
              mn.get('n_drift_tasks')), '', MD_END]


def md_rule(L, e):
    rule = e['result'].get('h5_rule')
    if not rule:
        return
    L += [MD_START, '', '%s: the same H5 rule without the listed tasks (%s): %s' % (
        e['label'][0].upper() + e['label'][1:], ', '.join(e['tasks_left_out']) or 'none present', rule['summary_sentence']), '', MD_END]


def strip_md(text):
    """Text without the added blocks (for the byte-identity check of the primary report)."""
    out, skip = [], False
    for ln in text.split('\n'):
        if ln == MD_START:
            skip = True
            continue
        if ln == MD_END:
            skip = False
            continue
        if not skip:
            out.append(ln)
    return '\n'.join(out)
