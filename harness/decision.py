# Decision output of the Born Legacy study: hypothesis table (H1, H2a, H2b, H3, H4), Holm decision rule, H5 interpretation
# rule and the framing outcome (gradient / model-specific / rare-drift / otherwise). FULL_PREREG sections 7, 8, 13.
# Written 2026-11-11 by pkg:HSTAT_GEN. Status: prepared.
#
# usage: python3 -I harness/decision.py --summary results/summary.json
# decide(summary, plan=None) -> dict; prints INCOMPLETE while any planned model is neither complete nor stopped by a
# section 13 rule (stop rules: a = cost cap or $40 total, b = endpoint unavailable 7 consecutive days, c = harness or
# generator bug), and while the run records contain MISSING/HARNESS problems. Nothing is decided on incomplete data.
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import stats  # noqa: E402

PRIMARY_PAIR = 'E0a~E1'
STOP_RULES = ('a', 'b', 'c')
MIN_SHARE = 0.80            # section 13: less than 80% of planned programs generated -> descriptive only, not testable
RARE_LIMIT = 0.02           # section 7 framing rule: exact one-sided 95% upper bound below 2%
H4_MIN_DRIFT, H4_MIN_TASKS = 20, 5
H5_MIN_CODED = 20


def model_status(summary, plan):
    """-> {model: {'closed': bool, 'why': str, 'share': float|None, 'under80': bool}} for every planned model."""
    out = {}
    for m, pm in plan['models'].items():
        sm = summary.get('models', {}).get(m, {})
        state = sm.get('state') or pm.get('state') or 'not_started'
        rule = sm.get('stop_rule') or pm.get('stop_rule')
        planned = sm.get('planned') if sm.get('planned') is not None else pm.get('planned')
        generated = sm.get('generated') if sm.get('generated') is not None else pm.get('generated', 0)
        share = (generated / planned) if planned else None
        if state == 'complete':
            closed, why = True, 'complete'
        elif state == 'stopped' and rule in STOP_RULES:
            closed, why = True, 'stopped by rule %s' % rule
        else:
            closed, why = False, 'state %s (%s of %s programs generated)' % (state, generated, planned)
        out[m] = {'closed': closed, 'why': why, 'share': share, 'under80': bool(closed and share is not None and share < MIN_SHARE),
                  'generated': generated, 'planned': planned, 'state': state, 'stop_rule': rule}
    return out


def _fmt_pp(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return 'n/a'
    if x in (math.inf, -math.inf) or x in ('Infinity', '-Infinity'):
        return str(x)
    return '%+.2f pp' % (100 * float(x))


def _fmt_p(p):
    return 'n/a' if p is None or (isinstance(p, float) and math.isnan(p)) else '%.4f' % p


def _num(v):
    if v == 'Infinity':
        return math.inf
    if v == '-Infinity':
        return -math.inf
    return v


def h5_headline(h5):
    """Pre-set H5 interpretation (section 7): applies to the R estimate; fallback R+A; else descriptive only."""
    if not h5:
        return {'basis': None, 'summary_sentence': 'H5 not available (no coded programs).', 'rule': 'none', 'allowed': None}
    bg = h5.get('by_group', {})
    sel, name = None, None
    for g in ('R', 'R+A'):
        if bg.get(g, {}).get('n_coded', 0) >= H5_MIN_CODED:
            sel, name = bg[g], g
            break
    caveat = '' if h5.get('basis') == 'coded' else ' [%s]' % h5.get('basis')
    if sel is None:
        return {'basis': None, 'rule': 'none', 'allowed': None,
                'summary_sentence': 'Fewer than %d coded drift programs in R and in R+A: no summary sentence is allowed; shares are '
                                    'reported descriptively.%s' % (H5_MIN_CODED, caveat)}
    h3 = sel['shares'].get('HARM_3X')
    lo, hi = (h3 or {}).get('lo'), (h3 or {}).get('hi')
    if hi is None or lo is None:
        return {'basis': name, 'rule': 'none', 'allowed': None, 'summary_sentence': 'H5 interval undefined.' + caveat}
    note = '' if name == 'R' else ' (R has fewer than %d coded drift programs, so R and A pooled are used)' % H5_MIN_CODED
    if hi < 0.10:
        sent = ('Upper bound of h3 (3.x harms) %.1f%% < 10%%: drift may be described as mostly corrective or neutral; it may not be '
                'called harmful in general%s.' % (100 * hi, note))
        allowed = 'mostly_corrective_or_neutral'
    elif lo > 0.25:
        sent = ('Lower bound of h3 (3.x harms) %.1f%% > 25%%: the paper may say a substantial share of drift makes results '
                'wrong%s.' % (100 * lo, note))
        allowed = 'substantial_share_wrong'
    else:
        sent = ('h3 interval %.1f%%-%.1f%% straddles the 10%% / 25%% limits: shares are reported without either summary%s.'
                % (100 * lo, 100 * hi, note))
        allowed = None
    return {'basis': name, 'rule': 'applied', 'allowed': allowed, 'h3_lo': lo, 'h3_hi': hi, 'n_coded': sel['n_coded'],
            'summary_sentence': sent + caveat}


def decide(summary, plan=None, pair=PRIMARY_PAIR):
    plan = plan or summary['plan']
    ms = model_status(summary, plan)
    open_models = {m: s['why'] for m, s in ms.items() if not s['closed']}
    blocking = []
    probs = summary.get('problems', {}).get(pair) or {}
    if any(v for v in probs.values()):
        blocking.append('run records with problems on %s: %s (MISSING/HARNESS must be 0 at T10)' % (pair, probs))
    if open_models or blocking:
        lines = ['INCOMPLETE']
        for m, why in open_models.items():
            lines.append('  open model %s: %s' % (m, why))
        for b in blocking:
            lines.append('  blocking: %s' % b)
        lines.append('  (sections 13 and 16 W7: no decision is printed until every planned model is complete or stopped by a '
                     'rule, and no run problems remain)')
        return {'status': 'INCOMPLETE', 'open_models': open_models, 'blocking': blocking, 'model_status': ms,
                'text': '\n'.join(lines)}
    tg = summary['targets'][pair]
    tests = tg['tests']
    roles = plan['roles']
    groups = {g: [m for m, d in plan['models'].items() if d['group'] == g] for g in ('BEFORE', 'AFTER', 'UNKNOWN')}
    scope = {'H1': [roles['h1_high'], roles['h1_low']], 'H2a': groups['BEFORE'] + groups['AFTER'],
             'H2b': [roles['h2b_old'], roles['h2b_new']], 'H3': list(plan['models']), 'H4': list(plan['models'])}
    nt, why_nt = [], {}
    for h, models in scope.items():
        reasons = []
        for m in models:
            if m not in ms:
                reasons.append('model %s not in the plan' % m)
            elif ms[m]['under80']:
                reasons.append('model %s has %.0f%% of planned programs (< 80%%; section 13)' % (m, 100 * ms[m]['share']))
        if h == 'H2b' and not plan.get('h2b_available', True):
            reasons.append('Haiku 4.5 unavailable before its first main-run call (section 4.1 lifecycle rule)')
        if h == 'H4':
            nd, nt_ = tests['H4'].get('n_drift_programs', 0), tests['H4'].get('n_drift_tasks', 0)
            if nd < H4_MIN_DRIFT or nt_ < H4_MIN_TASKS:
                reasons.append('R+A hold %d drift programs from %d tasks (< %d programs or < %d tasks; section 7)'
                               % (nd, nt_, H4_MIN_DRIFT, H4_MIN_TASKS))
        if reasons:
            nt.append(h)
            why_nt[h] = '; '.join(reasons)
    pvals = {h: tests[h]['p'] for h in ('H1', 'H2a', 'H2b', 'H3', 'H4')}
    conds = {h: tests[h].get('condition') for h in tests if tests[h].get('condition') is not None}
    hol = stats.holm(pvals, conds, nt, plan.get('alpha', 0.05))
    for h in hol['not_testable']:
        if h not in nt:                      # p-value undefined: every resample was dropped (zero events, zero denominators)
            nt.append(h)
            why_nt[h] = 'p-value undefined (every bootstrap resample dropped: zero denominators)'
    table = []
    for h in ('H1', 'H2a', 'H2b', 'H3', 'H4'):
        t = tests[h]
        if h == 'H3':
            est_text = 'RR %s' % ('n/a' if _isn(t.get('rr')) else ('inf' if t['rr'] in (math.inf, 'Infinity') else '%.2f' % t['rr']))
            iv = '[%s, %s] (log RR)' % (_g(t['lo']), _g(t['hi']))
        elif h == 'H4':
            est_text = 'share unwarned on 2.3.3 = %s' % _pct(t['estimate'])
            iv = '[%s, %s]' % (_pct(t['lo']), _pct(t['hi']))
        else:
            est_text = _fmt_pp(t['estimate'])
            iv = '[%s, %s]' % (_fmt_pp(t['lo']), _fmt_pp(t['hi']))
        if h in hol['adjusted']:
            step = hol['alpha_step'][h]
            osl = t.get('one_sided_lower', {}).get(str(round(step, 6)))
            iv += '; one-sided lower at alpha %.4f: %s' % (step, _fmt_pp(osl) if h not in ('H3', 'H4') else
                                                         (_g(osl) if h == 'H3' else _pct(osl)))
        cond = t.get('condition_text') or '-'
        if t.get('condition') is not None:
            cond += ' (%s)' % ('met' if t['condition'] else 'not met')
        if h in nt:
            res = 'NOT TESTABLE: ' + why_nt[h]
        else:
            res = 'SUPPORTED' if hol['supported'][h] else ('not supported' + (' (point-estimate condition not met)'
                                                                              if hol['reject'][h] and not conds.get(h, True) else ''))
        table.append({'hypothesis': h, 'estimate': t['estimate'], 'estimate_text': est_text, 'interval_text': iv,
                      'p': t['p'], 'p_text': _fmt_p(t['p']), 'p_adj': hol['adjusted'].get(h),
                      'p_adj_text': _fmt_p(hol['adjusted'].get(h)) if h in hol['adjusted'] else '-', 'condition_text': cond,
                      'result': res, 'dropped_resamples': t.get('dropped'), 'testable': h not in nt})
    sup = hol['supported']
    # rare-drift branch: every model's stratum-M silent-drift upper bound (CP on n_eff) below 2%
    rare = {}
    for m in plan['models']:
        r = tg.get('rare_M', {}).get(m) or {}
        rare[m] = {'upper': r.get('cp_deff_upper'), 'n': r.get('n'), 'x': r.get('x'), 'deff': r.get('deff'),
                   'n_eff': r.get('n_eff'), 'excluded_under80': ms[m]['under80']}
    judged = {m: r for m, r in rare.items() if not r['excluded_under80']}
    rare_ok = bool(judged) and all(r['upper'] is not None and r['upper'] < RARE_LIMIT for r in judged.values())
    if sup.get('H1') and (sup.get('H2a') or sup.get('H2b')):
        outcome, reason = 'gradient', 'H1 supported and at least one of H2a, H2b supported.'
    elif sup.get('H1'):
        outcome, reason = 'model-specific', 'H1 supported, neither H2 supported (the gap exists but is not tied to cutoff in this set).'
    elif rare_ok:
        outcome = 'rare-drift'
        reason = ('every model in stratum M has an exact one-sided 95%% upper bound (design-effect adjusted Clopper-Pearson) '
                  'below 2%%; largest %.2f%%.' % (100 * max(r['upper'] for r in judged.values())))
        if len(judged) < len(rare):
            reason += ' Models under 80%% generated were left out of the condition: %s.' % sorted(set(rare) - set(judged))
    else:
        outcome = 'otherwise'
        reason = 'neither the gradient / model-specific nor the rare-drift condition holds: estimates are reported with the hypotheses as tested.'
    h5 = h5_headline(tg.get('h5'))
    dec = {'status': 'COMPLETE', 'pair': pair, 'table': table, 'holm': hol, 'not_testable': why_nt, 'model_status': ms,
           'framing': {'outcome': outcome, 'reason': reason, 'rare_drift_condition': rare_ok, 'rare': rare},
           'h5': h5, 'open_models': {}, 'blocking': []}
    dec['text'] = render_text(dec)
    return dec


def _isn(x):
    return x is None or (isinstance(x, float) and math.isnan(x))


def _g(x):
    return 'n/a' if _isn(x) else (str(x) if isinstance(x, str) else '%.3f' % x)


def _pct(x):
    return 'n/a' if _isn(x) else '%.1f%%' % (100 * x)


def render_text(dec):
    L = ['DECISION (%s): %s' % (dec['pair'], dec['framing']['outcome'].upper())]
    L.append('  ' + dec['framing']['reason'])
    L.append('')
    for r in dec['table']:
        L.append('  %-4s %-34s p=%s  Holm p=%s  %s' % (r['hypothesis'], r['estimate_text'], r['p_text'], r['p_adj_text'], r['result']))
        L.append('       interval %s ; condition %s ; dropped resamples %s' % (r['interval_text'], r['condition_text'], r['dropped_resamples']))
    L.append('')
    L.append('  H5: ' + dec['h5']['summary_sentence'])
    return '\n'.join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--summary', required=True)
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    with open(a.summary, encoding='utf-8') as f:
        summary = json.load(f)
    # summary.json is strict JSON (inf as strings); convert the few numbers decide() compares
    for pair, tg in summary.get('targets', {}).items():
        for t in tg.get('tests', {}).values():
            for k in ('estimate', 'lo', 'hi', 'rr'):
                t[k] = _num(t.get(k))
    dec = decide(summary)
    print(json.dumps(dec, indent=1, default=str) if a.json else dec['text'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
