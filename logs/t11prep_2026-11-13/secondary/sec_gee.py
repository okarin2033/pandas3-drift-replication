# GEE family of the sensitivity analyses: B.19 (H2a with the ordinal cutoff covariate) and B.20 (GEE of silent drift on model, with H2a and
# H2b as linear contrasts; a second GEE with reasoning tokens when a token table is supplied).
# Written 2026-11-13 in the T11 preparation step. Status: draft; decides nothing.
#
# The GEE (logit link, binomial variance, exchangeable working correlation within task, robust sandwich covariance without small-sample
# correction, moment estimates of scale and correlation) is implemented here with numpy only; the unit test checks it against
# statsmodels (present in envs/tools) on hand-made data. Run with envs/tools/bin/python.
#   envs/tools/bin/python -I -B sec_gee.py --analysis B.19|B.20 --models-tsv models/models.tsv ... [--reasoning-tokens T.tsv]
import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sec_common as C  # noqa: E402
from sec_design_splits import parse_cutoffs  # noqa: E402

PAIR = 'E0a~E1'
POPULATION = 'M'                                  # C-14 default: stratum M only
LEVEL_STARTS = (('L1', '2025-06-05'), ('L2', '2025-12-03'), ('L3', '2026-01-21'))   # 4.1 l.153-158: L0 before 2.3.0, L1 to before 3.0.0rc0,
                                                                                    # L2 to before 3.0.0, L3 on or after 3.0.0
CUTOFF_BASIS_RUNS = ('training data', 'reliable')  # C-13: Haiku 4.5 at L1 (training data) first, then at L0 (reliable date)
ON_SEPARATION = 'not estimable'                   # C-14: no penalisation; alternative 'drop separated models' is implemented but not the default
H2B_OLD, H2B_NEW = 'anthropic__claude-haiku-4.5', 'anthropic__claude-haiku-5.5'
TOKENS_PER = 1000.0                               # reasoning tokens per 1,000; missing counted as 0 (count reported)
MAXITER, TOL = 200, 1e-9
BETA_LIMIT = 25.0                                 # |coefficient| above this after fitting = separation / divergence
CUTOFF_VS_COL = 'cutoff_vs_pandas3_0_0_(2026-01-21)'
# LR82.2 item 8 (S-4): every numerical constant of the GEE, listed with the choices and written into the meta block of B.19 and B.20.
NUMERICAL_CONSTANTS = {'MAXITER': MAXITER, 'TOL': TOL, 'BETA_LIMIT_separation': BETA_LIMIT, 'divergence_abs_beta': 1e3,
                       'mu_clip': [1e-10, 1 - 1e-10], 'linear_predictor_clip': [-35, 35], 'irls_weight_floor': 1e-10,
                       'exchangeable_alpha_range': '[-1/(n_max-1) + 1e-6, 0.999]', 'scale_and_alpha_ddof': 'p (as statsmodels)',
                       'covariance': 'robust sandwich', 'wald_z': 1.959963984540054}


def np_or_refuse():
    try:
        import numpy as np
        return np
    except Exception:
        raise C.Refuse('B.19 and B.20 need numpy: run with envs/tools/bin/python')


def level_of(cutoff):
    """Ordinal cutoff level 0-3 of one parsed cutoff (month-only cutoffs count from the first day of the month)."""
    iso = cutoff['iso'] if cutoff['kind'] == 'day' else cutoff['iso'] + '-01'
    lvl = 0
    for i, (name, start) in enumerate(LEVEL_STARTS, 1):
        if iso >= start:
            lvl = i
    return lvl


def model_levels(models_rows, basis):
    """{model key: level | None}; None = no documented cutoff (UNKNOWN: does not enter, 4.1 l.135). Models with two documented dates use
    the entry whose basis contains `basis` (else the first entry)."""
    out = {}
    for r in models_rows:
        cs = parse_cutoffs(r.get('vendor_knowledge_cutoff'))
        key = C.model_key(r['openrouter_id'])
        if not cs:
            out[key] = None
            continue
        pick = [c for c in cs if basis in c['basis'].split('/')] or cs[:1]
        out[key] = level_of(pick[0])
    return out


# ------------------------------------------------------------------------------------------------ GEE
def _expit(np, z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -35, 35)))


def _irls(np, y, X, iters=100):
    b = np.zeros(X.shape[1])
    for _ in range(iters):
        mu = _expit(np, X @ b)
        w = np.clip(mu * (1 - mu), 1e-10, None)
        z = X @ b + (y - mu) / w
        try:
            nb = np.linalg.solve(X.T @ (X * w[:, None]), X.T @ (w * z))
        except np.linalg.LinAlgError:
            return b
        if np.max(np.abs(nb - b)) < 1e-10:
            return nb
        b = nb
    return b


def gee_logit_exchangeable(y, X, groups, maxiter=MAXITER, tol=TOL):
    """Logit-link GEE with an exchangeable working correlation. y: 0/1 list, X: list of rows (include the intercept), groups: cluster
    labels. Returns dict(params, cov_robust, se_robust, alpha, scale, converged, n_iter, n_obs, n_groups, estimable, why)."""
    np = np_or_refuse()
    y = np.asarray(y, dtype=float)
    X = np.asarray(X, dtype=float)
    N, p = X.shape
    labels = {}
    gi = np.array([labels.setdefault(g, len(labels)) for g in groups])
    idx = [np.where(gi == k)[0] for k in range(len(labels))]
    res = {'n_obs': N, 'n_groups': len(idx), 'estimable': False, 'why': None}
    if N <= p or len(idx) < 2:
        res['why'] = 'fewer observations than parameters or fewer than two clusters'
        return res
    if y.min() == y.max():
        res['why'] = 'all outcomes equal (no events or all events)'
        return res
    beta = _irls(np, y, X)
    alpha, scale, converged, it = 0.0, 1.0, False, 0
    nmax = max(len(i) for i in idx)
    lo_a = (-1.0 / (nmax - 1) + 1e-6) if nmax > 1 else 0.0
    for it in range(1, maxiter + 1):
        mu = np.clip(_expit(np, X @ beta), 1e-10, 1 - 1e-10)
        a = mu * (1 - mu)
        resid = (y - mu) / np.sqrt(a)
        # moment estimates as statsmodels' Exchangeable.update (ddof = p)
        ssr = sum(float(np.sum(resid[i] ** 2)) for i in idx)
        pair_sum = sum(float((resid[i].sum() ** 2 - np.sum(resid[i] ** 2)) / 2.0) for i in idx)
        n_pairs = sum(0.5 * len(i) * (len(i) - 1) for i in idx)
        scale = ssr / (N - p)
        alpha = (pair_sum / scale) / (n_pairs - p) if (n_pairs - p) > 0 and scale > 0 else 0.0
        alpha = min(max(alpha, lo_a), 0.999)
        bread = np.zeros((p, p))
        score = np.zeros(p)
        for i in idx:
            n_i = len(i)
            sd = np.sqrt(a[i])
            D = X[i] * a[i][:, None]
            Rinv = (np.eye(n_i) - (alpha / (1 + (n_i - 1) * alpha)) * np.ones((n_i, n_i))) / (1 - alpha)
            Vinv = Rinv / sd[:, None] / sd[None, :]
            bread += D.T @ Vinv @ D
            score += D.T @ Vinv @ (y[i] - mu[i])
        try:
            step = np.linalg.solve(bread, score)
        except np.linalg.LinAlgError:
            res['why'] = 'singular information matrix'
            return res
        beta = beta + step
        if not np.all(np.isfinite(beta)) or np.max(np.abs(beta)) > 1e3:
            res['why'] = 'divergence (separation)'
            return res
        if np.max(np.abs(step)) < tol:
            converged = True
            break
    # sandwich at the final parameters, alpha and scale
    mu = np.clip(_expit(np, X @ beta), 1e-10, 1 - 1e-10)
    a = mu * (1 - mu)
    bread = np.zeros((p, p))
    meat = np.zeros((p, p))
    for i in idx:
        n_i = len(i)
        sd = np.sqrt(a[i])
        D = X[i] * a[i][:, None]
        Rinv = (np.eye(n_i) - (alpha / (1 + (n_i - 1) * alpha)) * np.ones((n_i, n_i))) / (1 - alpha)
        Vinv = Rinv / sd[:, None] / sd[None, :]
        bread += D.T @ Vinv @ D
        u = D.T @ Vinv @ (y[i] - mu[i])
        meat += np.outer(u, u)
    try:
        binv = np.linalg.inv(bread)
    except np.linalg.LinAlgError:
        res['why'] = 'singular information matrix'
        return res
    cov = binv @ meat @ binv
    res.update({'params': beta.tolist(), 'cov_robust': cov.tolist(), 'se_robust': np.sqrt(np.clip(np.diag(cov), 0, None)).tolist(),
                'alpha': float(alpha), 'scale': float(scale), 'converged': converged, 'n_iter': it, 'estimable': converged,
                'why': None if converged else 'no convergence in %d iterations' % maxiter})
    if converged and float(np.max(np.abs(beta))) > BETA_LIMIT:
        res['estimable'] = False
        res['why'] = 'coefficient beyond +-%g (separation)' % BETA_LIMIT
    return res


def wald(fit, c, z=1.959963984540054):
    """Linear combination c . beta with its robust Wald 95% interval."""
    np = np_or_refuse()
    b = np.asarray(fit['params'])
    cov = np.asarray(fit['cov_robust'])
    cv = np.asarray(c, dtype=float)
    est = float(cv @ b)
    se = float(math.sqrt(max(0.0, cv @ cov @ cv)))
    return {'estimate': est, 'se': se, 'lo': est - z * se, 'hi': est + z * se, 'odds_ratio': math.exp(est),
            'or_lo': math.exp(est - z * se), 'or_hi': math.exp(est + z * se)}


# ------------------------------------------------------------------------------------------------ data
def silent_rows(inp):
    return [r for r in C.flat_rows(inp.per_program, PAIR, inp.tmap, set(inp.models)) if r['stratum'] == POPULATION and r['clean']]


# ------------------------------------------------------------------------------------------------ B.19
def b19(inp, tool, outdir):
    if not inp.models_rows:
        raise C.Refuse('B.19 needs --models-tsv')
    rows = silent_rows(inp)
    runs, out_rows = [], []
    for basis in CUTOFF_BASIS_RUNS:
        lv = model_levels(inp.models_rows, basis)
        use = [r for r in rows if lv.get(r['model']) is not None]
        models_used = sorted({r['model'] for r in use})
        unknown = sorted(m for m in inp.models if lv.get(m) is None)
        by_level = {}
        for r in use:
            e = by_level.setdefault(lv[r['model']], {'n': 0, 'x': 0, 'models': set()})
            e['n'] += 1
            e['x'] += r['silent']
            e['models'].add(r['model'])
        run = {'cutoff_basis': basis, 'models_entering': models_used, 'models_not_entering': unknown,
               'levels': {m: lv[m] for m in models_used},
               'by_level': {str(k): {'n': v['n'], 'x': v['x'], 'models': sorted(v['models'])} for k, v in sorted(by_level.items())}}
        distinct = len(set(lv[m] for m in models_used))
        if len(use) == 0 or distinct < 2:
            run.update({'estimable': False, 'why': 'fewer than two cutoff levels among the entering models' if use else 'no entering model'})
        else:
            fit = gee_logit_exchangeable([r['silent'] for r in use], [[1.0, float(lv[r['model']])] for r in use], [r['task_id'] for r in use])
            run.update({'estimable': fit['estimable'], 'why': fit['why'], 'n_obs': fit['n_obs'], 'n_groups': fit['n_groups']})
            if fit['estimable']:
                w = wald(fit, [0.0, 1.0])
                run.update({'alpha': fit['alpha'], 'scale': fit['scale'], 'n_iter': fit['n_iter'], 'intercept': fit['params'][0],
                            'slope_per_level': w})
        runs.append(run)
        out_rows.append({'cutoff_basis': basis, 'models_entering': len(models_used), 'estimable': run['estimable'], 'why': run.get('why'),
                         'n_obs': run.get('n_obs'), 'n_clusters': run.get('n_groups'),
                         'log_odds_per_level': (run.get('slope_per_level') or {}).get('estimate'),
                         'lo': (run.get('slope_per_level') or {}).get('lo'), 'hi': (run.get('slope_per_level') or {}).get('hi'),
                         'odds_ratio_per_level': (run.get('slope_per_level') or {}).get('odds_ratio'),
                         'or_lo': (run.get('slope_per_level') or {}).get('or_lo'), 'or_hi': (run.get('slope_per_level') or {}).get('or_hi'),
                         'alpha': run.get('alpha')})
    cols = ['cutoff_basis', 'models_entering', 'estimable', 'why', 'n_obs', 'n_clusters', 'log_odds_per_level', 'lo', 'hi',
            'odds_ratio_per_level', 'or_lo', 'or_hi', 'alpha']
    meta = C.meta_block(inp, tool, ['B.19'], {'pair': PAIR, 'population': POPULATION, 'level_starts': dict(LEVEL_STARTS),
                                                   'numerical_constants': NUMERICAL_CONSTANTS})
    md = C.header_md(inp, 'B.19', 'H2a with the ordinal cutoff covariate (GEE, stratum M)', meta,
                     'GEE logistic, silent ~ ordinal level 0-3, exchangeable within task, robust Wald 95%% (C-13 (a)); run twice: '
                     'Haiku 4.5 at its training-data date (L1) and at its reliable date (L0). Models without a documented cutoff do not enter. '
                     'A cell without events is reported, not corrected.')
    md += ['', C.md_table(cols, out_rows), '']
    for r in runs:
        md.append('- %s: levels %s; observations by level %s.' % (r['cutoff_basis'], r['levels'], {k: (v['n'], v['x']) for k, v in r['by_level'].items()}))
    return C.emit(outdir, 'B.19', inp, meta, md, [('fit', cols, out_rows)], {'item': 'B.19', 'runs': runs})


# ------------------------------------------------------------------------------------------------ B.20
def read_tokens(path):
    t = {}
    for r in C.read_tsv(path):
        v = (r.get('reasoning_tokens') or '').strip()
        t[r['program_id']] = float(v) if v not in ('', 'NA', 'None') else None
    return t


def contrasts(models, groups):
    """Contrast vectors over (intercept, dummies of models[1:]) for H2a (mean log-odds BEFORE - mean AFTER) and H2b (old - new Haiku)."""
    def vec(w):
        v = [0.0] * (1 + len(models) - 1)
        for m, c in w.items():
            if m in models and models.index(m) > 0:
                v[models.index(m)] += c       # dummy of models[k] sits at column k
        return v
    out = {}
    bef = [m for m in models if groups.get(m) == 'before']
    aft = [m for m in models if groups.get(m) == 'after']
    if bef and aft:
        w = {m: 1.0 / len(bef) for m in bef}
        for m in aft:
            w[m] = w.get(m, 0.0) - 1.0 / len(aft)
        out['H2a (mean BEFORE - mean AFTER, log-odds)'] = vec(w)
    if H2B_OLD in models and H2B_NEW in models:
        out['H2b (haiku-4.5 - haiku-5.5, log-odds)'] = vec({H2B_OLD: 1.0, H2B_NEW: -1.0})
    return out


def fit_models(rows, models_rows, tokens=None):
    groups = {C.model_key(r['openrouter_id']): (r.get(CUTOFF_VS_COL) or '').strip() for r in models_rows} if models_rows else {}
    models = sorted({r['model'] for r in rows})
    sep = []
    for m in models:
        ys = [r['silent'] for r in rows if r['model'] == m]
        if sum(ys) == 0 or sum(ys) == len(ys):
            sep.append({'model': m, 'n': len(ys), 'x': sum(ys)})
    notes = {'separated_models': sep}
    if sep and ON_SEPARATION == 'not estimable':
        notes['estimable'] = False
        notes['why'] = 'separation: %s (no penalisation)' % ', '.join('%s %d/%d' % (s['model'], s['x'], s['n']) for s in sep)
        return None, models, groups, notes
    if sep:
        drop = {s['model'] for s in sep}
        rows = [r for r in rows if r['model'] not in drop]
        models = [m for m in models if m not in drop]
        notes['dropped_models'] = sorted(drop)
    if len(models) < 2:
        notes['estimable'] = False
        notes['why'] = 'fewer than two models'
        return None, models, groups, notes
    X = []
    miss = 0
    for r in rows:
        v = [1.0] + [1.0 if r['model'] == m else 0.0 for m in models[1:]]
        if tokens is not None:
            tk = tokens.get(r['program_id'])
            if tk is None:
                miss += 1
                tk = 0.0
            v.append(tk / TOKENS_PER)
        X.append(v)
    fit = gee_logit_exchangeable([r['silent'] for r in rows], X, [r['task_id'] for r in rows])
    notes['estimable'] = fit['estimable']
    notes['why'] = fit['why']
    if tokens is not None:
        notes['tokens_missing_counted_as_zero'] = miss
    return fit, models, groups, notes


def b20(inp, tool, outdir, tokens_path):
    if not inp.models_rows:
        raise C.Refuse('B.20 needs --models-tsv')
    rows = silent_rows(inp)
    tokens = read_tokens(tokens_path) if tokens_path else None
    variants = [('GEE silent ~ model', None)]
    if tokens is not None:
        variants.append(('GEE silent ~ model + reasoning tokens per 1,000', tokens))
    out, flat = [], []
    for name, tk in variants:
        fit, models, groups, notes = fit_models(rows, inp.models_rows, tk)
        e = {'model_name': name, 'models': models, 'notes': notes}
        if fit is not None and fit['estimable']:
            e.update({'n_obs': fit['n_obs'], 'n_clusters': fit['n_groups'], 'alpha': fit['alpha'], 'scale': fit['scale'],
                      'n_iter': fit['n_iter'], 'reference_model': models[0]})
            cons = contrasts(models, groups)
            e['contrasts'] = {}
            for cn, cv in cons.items():
                if tk is not None:
                    cv = cv + [0.0]
                w = wald(fit, cv)
                e['contrasts'][cn] = w
                flat.append(dict(w, fit=name, contrast=cn, estimable=True, why=None))
            if tk is not None:
                cv = [0.0] * (len(fit['params']) - 1) + [1.0]
                w = wald(fit, cv)
                e['tokens_per_1000'] = w
                flat.append(dict(w, fit=name, contrast='reasoning tokens per 1,000 (log-odds per 1,000)', estimable=True, why=None))
            if not cons:
                notes['contrasts'] = 'no contrast estimable: needs BEFORE and AFTER models, or both Haiku models'
        else:
            flat.append({'fit': name, 'contrast': 'all', 'estimable': False, 'why': notes.get('why') or (fit or {}).get('why')})
        out.append(e)
    tok_rows = []
    if tokens is not None:
        by = {}
        pm = {p['program_id']: p['model'] for p in inp.per_program}
        for pid, v in tokens.items():
            by.setdefault(pm.get(pid, '(not in per_program)'), []).append(v)
        for m, vs in sorted(by.items()):
            vals = sorted(x for x in vs if x is not None)
            tok_rows.append({'model': m, 'programs': len(vs), 'missing': len(vs) - len(vals),
                             'mean': (sum(vals) / len(vals)) if vals else None, 'median': C.median(vals),
                             'max': vals[-1] if vals else None})
    cols = ['fit', 'contrast', 'estimable', 'why', 'estimate', 'se', 'lo', 'hi', 'odds_ratio', 'or_lo', 'or_hi']
    meta = C.meta_block(inp, tool, ['B.20'], {'pair': PAIR, 'population': POPULATION, 'on_separation': ON_SEPARATION, 'numerical_constants': NUMERICAL_CONSTANTS,
                                              'tokens_file_sha256': C.sha256_file(tokens_path) if tokens_path else None})
    md = C.header_md(inp, 'B.20', 'GEE sensitivity models (stratum M)', meta,
                     'GEE logistic, silent ~ model, exchangeable within task, robust Wald 95%%; H2a and H2b as linear contrasts of the model '
                     'log-odds (C-14). Separation: %s. The second GEE (reasoning tokens) is run only when a token table is supplied.' % ON_SEPARATION)
    md += ['', C.md_table(cols, flat)]
    for e in out:
        md.append('- %s: models %s; notes %s' % (e['model_name'], len(e['models']), {k: v for k, v in e['notes'].items() if v}))
    tables = [('contrasts', cols, flat)]
    if tok_rows:
        tables.append(('tokens', ['model', 'programs', 'missing', 'mean', 'median', 'max'], tok_rows))
        md += ['', 'Reasoning tokens per model (from the supplied table):', '', C.md_table(['model', 'programs', 'missing', 'mean', 'median', 'max'], tok_rows)]
    return C.emit(outdir, 'B.20', inp, meta, md, tables, {'item': 'B.20', 'fits': out, 'tokens': tok_rows})


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--analysis', required=True, help='B.19 or B.20')
    C.add_common_args(ap, need_models=True)
    ap.add_argument('--reasoning-tokens', default=None, help='B.20 optional: TSV program_id, reasoning_tokens (built after T11 by the lead)')
    a = ap.parse_args(argv)
    if a.analysis not in ('B.19', 'B.20'):
        raise C.Refuse('unknown analysis %r' % a.analysis)
    np_or_refuse()
    inp = C.load_inputs(a, {'reasoning_tokens.tsv': a.reasoning_tokens} if a.reasoning_tokens else None)
    C.self_check(inp)
    tool = os.path.abspath(__file__)
    base = b19(inp, tool, a.out) if a.analysis == 'B.19' else b20(inp, tool, a.out, a.reasoning_tokens)
    print('wrote', os.path.basename(base) + '.{json,md,tsv}')
    return 0


if __name__ == '__main__':
    sys.exit(C.run_main(main))
