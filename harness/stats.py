# Statistics for the Born Legacy study (FULL_PREREG sections 7, 8, 10.4, 13).
# Written 2026-11-11 by pkg:HSTAT_GEN. Status: prepared.
#
# Host-side module: Python standard library only. If numpy is importable (study venv `envs/tools`), the bootstrap
# totals are computed by one matrix product per chunk of resamples; the random draws always come from
# random.Random(seed), so the result does not depend on whether numpy is present (tests compare both paths).
#
# What is here (all unit-tested against hand-computed values in harness/tests/stats/test_stats.py):
#   wilson, percentile, p_one_sided, holm, cp_upper, cp_upper_deff, icc_anova, deff, model_equal_mean,
#   pooled_fixed_weights, ipw_weights, cohen_kappa, gwet_ac1, bootstrap_agreement, log_rr, h3_log_rr,
#   build_cells / cluster_bootstrap_multi / cluster_bootstrap (stratified paired task-cluster bootstrap).
import math
import random

try:                                   # optional accelerator, never required
    import numpy as _np
except Exception:                      # pragma: no cover - depends on the interpreter
    _np = None

Z95 = 1.959963984540054
SEED = 20261111
B_DEFAULT = 10000
FIXED_WEIGHTS = {'M': 0.64, 'R': 0.20, 'A': 0.16}
ICC_FLOOR = 0.20                       # the pilot's ICC (section 7 framing rule: "at least the pilot's 0.20")
NAN = float('nan')


def isnan(x):
    return x is None or (isinstance(x, float) and math.isnan(x))


# ------------------------------------------------------------------------------------------------ Wilson
def wilson(k, n, z=Z95):
    """Wilson score interval for k events in n trials -> (p, lo, hi); (nan, nan, nan) if n == 0."""
    if n <= 0:
        return (NAN, NAN, NAN)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (p, max(0.0, c - h), min(1.0, c + h))


# ------------------------------------------------------------------------------------------------ percentiles, p
def percentile(sorted_vals, q):
    """Type-7 (linear interpolation, numpy default) percentile of an ascending list, q in [0, 1]. Handles +-inf."""
    n = len(sorted_vals)
    if n == 0:
        return NAN
    pos = q * (n - 1)
    i = int(math.floor(pos))
    f = pos - i
    lo = sorted_vals[i]
    if f == 0 or i + 1 >= n:
        return lo
    hi = sorted_vals[i + 1]
    if lo == hi:
        return lo
    return lo + (hi - lo) * f


def p_one_sided(draws, null):
    """One-sided bootstrap p-value for H1: stat > null:  (1 + #{b: stat_b <= null}) / (B + 1), B = number of valid
    (not dropped) resamples in `draws`."""
    valid = [d for d in draws if not isnan(d)]
    b = len(valid)
    if b == 0:
        return NAN
    return (1 + sum(1 for d in valid if d <= null)) / (b + 1)


# ------------------------------------------------------------------------------------------------ Holm
def holm(pvalues, conditions=None, not_testable=(), alpha=0.05):
    """Holm step-down over the testable hypotheses (FULL_PREREG section 7 decision rule).

    pvalues: {name: one-sided p}; conditions: {name: bool} separate point-estimate conditions (missing = no condition);
    not_testable: names removed from the family (H2b lifecycle rule, H4 rule, < 80% generated rule).
    A hypothesis is `supported` iff its Holm-adjusted p < alpha AND its point-estimate condition holds.
    Returns {'m', 'order', 'adjusted', 'alpha_step', 'reject', 'supported', 'not_testable'}.
    alpha_step[h] = alpha / (m - rank + 1) with rank 1 = smallest p: the level of the Holm step at which h is tested
    (used for the one-sided bound reported "at the Holm step's level")."""
    conditions = conditions or {}
    nt = [h for h in pvalues if h in set(not_testable) or isnan(pvalues[h])]
    for h in not_testable:
        if h not in nt:
            nt.append(h)
    names = [h for h in pvalues if h not in nt]
    order = sorted(names, key=lambda h: (pvalues[h], h))
    m = len(order)
    adjusted, alpha_step = {}, {}
    running = 0.0
    for i, h in enumerate(order):
        adj = min(1.0, (m - i) * pvalues[h])
        running = max(running, adj)
        adjusted[h] = running
        alpha_step[h] = alpha / (m - i)
    reject = {h: adjusted[h] < alpha for h in order}
    supported = {h: bool(reject[h] and conditions.get(h, True)) for h in order}
    return {'m': m, 'order': order, 'adjusted': adjusted, 'alpha_step': alpha_step, 'reject': reject,
            'supported': supported, 'not_testable': nt, 'alpha': alpha}


# ------------------------------------------------------------------------------------------------ Beta / Clopper-Pearson
def _betacf(a, b, x, max_iter=1000, eps=1e-15):
    """Continued fraction of the regularised incomplete beta function (modified Lentz)."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    d = tiny if abs(d) < tiny else d
    d = 1.0 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = tiny if abs(d) < tiny else d
        c = 1.0 + aa / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = tiny if abs(d) < tiny else d
        c = 1.0 + aa / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < eps:
            break
    return h


def betainc_reg(x, a, b):
    """Regularised incomplete beta function I_x(a, b)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def beta_ppf(q, a, b):
    """Quantile of Beta(a, b) by bisection on I_x(a, b) (60+ halvings, accurate to ~1e-16)."""
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if betainc_reg(mid, a, b) < q:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-16:
            break
    return 0.5 * (lo + hi)


def cp_upper(x, n, alpha=0.05):
    """Exact (Clopper-Pearson) one-sided 1-alpha upper bound for x events in n trials; x and n may be fractional
    (effective sample size). x = 0 uses the closed form 1 - alpha^(1/n); otherwise the Beta(x+1, n-x) quantile 1-alpha."""
    if n is None or n <= 0:
        return NAN
    if x >= n:
        return 1.0
    if x <= 0:
        return 1.0 - alpha ** (1.0 / n)
    return beta_ppf(1.0 - alpha, x + 1.0, n - x)


def deff(m, icc, floor=ICC_FLOOR):
    """Design effect 1 + (m - 1) * ICC with ICC truncated at 0 and at least `floor` (0.20, the pilot's)."""
    icc_used = max(floor, max(0.0, icc if not isnan(icc) else 0.0))
    return 1.0 + (m - 1.0) * icc_used


def cp_upper_deff(x, n, deff_value, alpha=0.05):
    """Design-effect-adjusted Clopper-Pearson upper bound: x_eff = x / DEFF, n_eff = n / DEFF (section 7)."""
    if deff_value < 1:
        deff_value = 1.0
    return cp_upper(x / deff_value, n / deff_value, alpha)


def icc_anova(rows_by_task):
    """One-way ANOVA intraclass correlation (unbalanced; Smith/Fleiss n0 form), truncated at 0.
    rows_by_task: {task: [0/1 outcomes of that task's clean programs]}. Tasks without programs are ignored.
    ICC = (MSB - MSW) / (MSB + (n0 - 1) MSW),  n0 = (N - sum n_i^2 / N) / (k - 1).  Returns 0.0 if undefined."""
    groups = [list(v) for v in rows_by_task.values() if len(v) > 0]
    k = len(groups)
    n_tot = sum(len(g) for g in groups)
    if k < 2 or n_tot - k <= 0:
        return 0.0
    grand = sum(sum(g) for g in groups) / n_tot
    ssb = sum(len(g) * (sum(g) / len(g) - grand) ** 2 for g in groups)
    ssw = sum(sum((y - sum(g) / len(g)) ** 2 for y in g) for g in groups)
    msb = ssb / (k - 1)
    msw = ssw / (n_tot - k)
    n0 = (n_tot - sum(len(g) ** 2 for g in groups) / n_tot) / (k - 1)
    den = msb + (n0 - 1.0) * msw
    if den <= 0:
        return 0.0
    return max(0.0, (msb - msw) / den)


def rare_bound(outcomes_by_task, alpha=0.05):
    """Rare-drift bound of the framing rule for one model (and stratum): outcomes_by_task {task: [0/1 silent flags of the
    model's clean programs]} -> dict(x, n, tasks, m, icc, icc_used, deff, n_eff, x_eff, upper)."""
    groups = {t: v for t, v in outcomes_by_task.items() if len(v) > 0}
    n = sum(len(v) for v in groups.values())
    x = sum(sum(v) for v in groups.values())
    tasks = len(groups)
    if n == 0:
        return {'x': 0, 'n': 0, 'tasks': 0, 'm': NAN, 'icc': NAN, 'icc_used': NAN, 'deff': NAN, 'n_eff': 0.0,
                'x_eff': 0.0, 'upper': NAN}
    m = n / tasks
    icc = icc_anova(groups)
    icc_used = max(ICC_FLOOR, icc)
    d = deff(m, icc)
    return {'x': x, 'n': n, 'tasks': tasks, 'm': m, 'icc': icc, 'icc_used': icc_used, 'deff': d, 'n_eff': n / d,
            'x_eff': x / d, 'upper': cp_upper_deff(x, n, d, alpha)}


# ------------------------------------------------------------------------------------------------ pooling, weights
def model_equal_mean(rates):
    """Unweighted mean of per-model rates; nan if any rate is undefined (the bootstrap then drops the resample)."""
    vals = list(rates.values()) if isinstance(rates, dict) else list(rates)
    if not vals or any(isnan(v) for v in vals):
        return NAN
    return sum(vals) / len(vals)


def pooled_fixed_weights(rates, weights=None):
    """Sensitivity pooling of per-stratum ratio estimators with fixed weights M 0.64, R 0.20, A 0.16 (section 7).
    rates: {'M': r, 'R': r, 'A': r}; nan if any weighted stratum is undefined."""
    weights = weights or FIXED_WEIGHTS
    if abs(sum(weights.values()) - 1.0) > 1e-9:
        raise ValueError('weights must sum to 1')
    tot = 0.0
    for s, w in weights.items():
        r = rates.get(s)
        if isnan(r):
            return NAN
        tot += w * r
    return tot


def ipw_weights(population_counts, sample_counts):
    """Inverse-probability weights per cell for the H5 coding sample (section 8): weight = population / sampled.
    Cells are e.g. (model, 'QF3'), (model, 'R'), (model, 'A'). A populated cell with 0 sampled programs gets None
    (the caller must report it); an empty cell gets no entry."""
    out = {}
    for cell, pop in population_counts.items():
        if pop <= 0:
            continue
        s = sample_counts.get(cell, 0)
        out[cell] = (pop / s) if s > 0 else None
    return out


# ------------------------------------------------------------------------------------------------ agreement
def _cats(a, b):
    return sorted(set(a) | set(b), key=lambda v: str(v))


def cohen_kappa(a, b):
    """Cohen's kappa for two raters over the same items."""
    n = len(a)
    if n == 0 or n != len(b):
        return NAN
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = sum((sum(1 for x in a if x == c) / n) * (sum(1 for y in b if y == c) / n) for c in _cats(a, b))
    if pe >= 1.0:
        return NAN
    return (po - pe) / (1.0 - pe)


def gwet_ac1(a, b):
    """Gwet's AC1 for two raters: pe = (1 / (q - 1)) * sum_k pi_k (1 - pi_k), pi_k = mean of the two raters' shares.
    q = number of categories observed in either rating; q = 1 -> agreement is complete, AC1 = 1."""
    n = len(a)
    if n == 0 or n != len(b):
        return NAN
    cats = _cats(a, b)
    q = len(cats)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    if q < 2:
        return 1.0
    pe = sum(pi * (1 - pi) for pi in (((sum(1 for x in a if x == c) + sum(1 for y in b if y == c)) / (2.0 * n))
                                      for c in cats)) / (q - 1)
    return (po - pe) / (1.0 - pe)


def bootstrap_agreement(a, b, statistic=cohen_kappa, B=B_DEFAULT, seed=SEED, clusters=None, alpha=0.05):
    """Percentile bootstrap interval of an agreement statistic. Items are resampled with replacement; if `clusters`
    (one label per item, e.g. the task id) is given, clusters are resampled instead. -> (estimate, lo, hi, dropped)."""
    n = len(a)
    est = statistic(a, b)
    rng = random.Random(seed)
    if clusters is None:
        units = [[i] for i in range(n)]
    else:
        by = {}
        for i, c in enumerate(clusters):
            by.setdefault(c, []).append(i)
        units = [by[c] for c in sorted(by, key=str)]
    draws, dropped = [], 0
    for _ in range(B):
        idx = [i for u in rng.choices(units, k=len(units)) for i in u]
        v = statistic([a[i] for i in idx], [b[i] for i in idx])
        if isnan(v):
            dropped += 1
        else:
            draws.append(v)
    draws.sort()
    return {'estimate': est, 'lo': percentile(draws, alpha / 2), 'hi': percentile(draws, 1 - alpha / 2),
            'dropped': dropped, 'B': B, 'raw_agreement': (sum(1 for x, y in zip(a, b) if x == y) / n) if n else NAN}


# ------------------------------------------------------------------------------------------------ H3
def log_rr(g1_mean, g2_mean):
    """log RR with the zero-denominator rules of section 8: G2 mean 0 and G1 mean > 0 -> +inf; both 0 -> nan (the
    bootstrap drops it); G1 mean 0 and G2 mean > 0 -> -inf (RR = 0)."""
    if isnan(g1_mean) or isnan(g2_mean):
        return NAN
    if g2_mean == 0:
        return math.inf if g1_mean > 0 else NAN
    if g1_mean == 0:
        return -math.inf
    return math.log(g1_mean / g2_mean)


def h3_group(fam):
    """G1 = QF1 + QF2, G2 = QF3..QF8; None for anything else."""
    if fam in ('QF1', 'QF2'):
        return 'G1'
    if fam in ('QF3', 'QF4', 'QF5', 'QF6', 'QF7', 'QF8'):
        return 'G2'
    return None


def h3_eligible_models(rows, models):
    """Models that enter H3: at least one clean program in each group (section 8). rows = flat rows of stratum M."""
    seen = {m: {'G1': 0, 'G2': 0} for m in models}
    for r in rows:
        g = h3_group(r.get('fam'))
        if g and r['model'] in seen:
            seen[r['model']][g] += r.get('clean', 0)
    return [m for m in models if seen[m]['G1'] > 0 and seen[m]['G2'] > 0]


def h3_log_rr(rows, models, silent_field='silent', clean_field='clean'):
    """H3 point estimate on flat per-program rows (stratum M): group rates are ratio estimators per model and group,
    RR = model-equal mean of G1 rates / model-equal mean of G2 rates; only models with a clean program in both groups
    enter. Returns log RR (may be +-inf; nan if no model enters or both means are 0)."""
    use = h3_eligible_models(rows, models)
    if not use:
        return NAN
    num = {(m, g): 0 for m in use for g in ('G1', 'G2')}
    den = dict(num)
    for r in rows:
        g = h3_group(r.get('fam'))
        if g and r['model'] in use:
            num[(r['model'], g)] += r.get(silent_field, 0)
            den[(r['model'], g)] += r.get(clean_field, 0)
    m1 = model_equal_mean([num[(m, 'G1')] / den[(m, 'G1')] for m in use])
    m2 = model_equal_mean([num[(m, 'G2')] / den[(m, 'G2')] for m in use])
    return log_rr(m1, m2)


# ------------------------------------------------------------------------------------------------ cluster bootstrap
def default_stratum_key(row):
    """Strata of the task-cluster bootstrap: the stratum (M, R, A) and, within M, the quota family (section 8)."""
    if row.get('stratum') == 'M':
        return ('M', row.get('fam') or row.get('family'))
    return (row.get('stratum'),)


class Cells:
    """Per-task sufficient statistics for the bootstrap. Every statistic of the study is a function of sums of
    per-program numbers over tasks, grouped by (model, stratum, family, ...), so a resample is described by how many
    times each task was drawn. rows: dicts with `task_key`, the `group_by` keys and the numeric `fields`."""

    def __init__(self, rows, fields, group_by, strata_key=default_stratum_key, task_key='task_id', tasks=None):
        self.fields = list(fields)
        self.group_by = tuple(group_by)
        self.fidx = {f: i for i, f in enumerate(self.fields)}
        self.task_key = task_key
        task_stratum = {}
        if tasks:
            for t in tasks:                      # {'task_id'|'id', 'stratum', 'fam'}
                tid = t[task_key] if task_key in t else t['id']
                task_stratum[tid] = strata_key({'stratum': t.get('stratum'), 'fam': t.get('fam')})
        cell_ids = {}
        per_task = {}
        for r in rows:
            t = r[task_key]
            if t not in task_stratum:
                task_stratum[t] = strata_key(r)
            g = tuple(r.get(k) for k in self.group_by)
            ci = cell_ids.setdefault(g, len(cell_ids))
            vec = per_task.setdefault(t, {}).setdefault(ci, [0.0] * len(self.fields))
            for f, i in self.fidx.items():
                v = r.get(f, 0)
                vec[i] += float(v) if v is not None else 0.0
        self.tasks = sorted(task_stratum, key=str)
        self.tindex = {t: i for i, t in enumerate(self.tasks)}
        self.strata = {}
        for t in self.tasks:
            self.strata.setdefault(task_stratum[t], []).append(self.tindex[t])
        self.cell_keys = [None] * len(cell_ids)
        for g, ci in cell_ids.items():
            self.cell_keys[ci] = g
        self.k = len(self.cell_keys) * len(self.fields)
        self.sparse = [[] for _ in self.tasks]            # per task: [(column, value)]
        for t, cells in per_task.items():
            for ci, vec in cells.items():
                for fi, v in enumerate(vec):
                    if v != 0.0:
                        self.sparse[self.tindex[t]].append((ci * len(self.fields) + fi, v))
        self._col_cache = {}

    def columns(self, field, where):
        key = (field, tuple(sorted((k, _as_key(v)) for k, v in where.items())))
        cols = self._col_cache.get(key)
        if cols is None:
            fi = self.fidx[field]
            pos = [(self.group_by.index(k), v) for k, v in where.items()]
            cols = [ci * len(self.fields) + fi for ci, g in enumerate(self.cell_keys)
                    if all(_match(g[p], v) for p, v in pos)]
            self._col_cache[key] = cols
        return cols

    def dense_matrix(self):
        rows = [[0.0] * self.k for _ in self.tasks]
        for ti, sp in enumerate(self.sparse):
            for c, v in sp:
                rows[ti][c] += v
        return rows


def _as_key(v):
    return tuple(sorted(v, key=str)) if isinstance(v, (set, frozenset, list, tuple)) else v


def _match(value, want):
    if isinstance(want, (set, frozenset, list, tuple)):
        return value in want
    return value == want


class View:
    """Totals of one resample (or of the observed data). sum(field, **where) adds the field over the cells whose
    group keys equal / belong to the given values; ratio() returns None (undefined) for a zero denominator."""

    def __init__(self, cells, totals):
        self._cells = cells
        self._tot = totals

    def sum(self, field, **where):
        return sum(self._tot[c] for c in self._cells.columns(field, where))

    def ratio(self, num, den, **where):
        d = self.sum(den, **where)
        if d == 0:
            return None
        return self.sum(num, **where) / d


def _resample_counts(cells, rng):
    """One resample: how many times each task was drawn, stratified (strata are resampled independently)."""
    counts = [0] * len(cells.tasks)
    for key in sorted(cells.strata, key=str):
        members = cells.strata[key]
        for i in rng.choices(members, k=len(members)):
            counts[i] += 1
    return counts


def _totals_pure(cells, counts):
    tot = [0.0] * cells.k
    for ti, w in enumerate(counts):
        if w:
            for c, v in cells.sparse[ti]:
                tot[c] += w * v
    return tot


def cluster_bootstrap_multi(rows, statistics, fields, group_by=('model', 'stratum', 'fam'), strata_key=default_stratum_key,
                            B=B_DEFAULT, seed=SEED, task_key='task_id', tasks=None, restrict=None, alpha=0.05,
                            use_numpy=None, chunk=500):
    """Stratified paired task-cluster bootstrap for several statistics on the SAME resamples (section 8).

    rows       per-program dicts (flat rows, see analyze_full.flatten) with `task_key`, the group_by keys, numeric fields
    statistics {name: f(view) -> float | None | nan}; None/nan = undefined -> that resample is dropped for that statistic
               and counted; +-inf is allowed (H3)
    fields     numeric row fields the statistics use
    strata_key row -> stratum key (default: stratum; within M also family); tasks are resampled with replacement inside
               each stratum, the same multiset for every model (the statistic reads all models from one resample)
    tasks      optional list of {'task_id'|'id', 'stratum', 'fam'} so that tasks without any row still occupy a slot
    restrict   optional row filter (e.g. stratum M only for H1-H3, strata R and A for H4)
    -> {name: {'estimate', 'draws' (valid ones, sorted), 'dropped', 'B', 'lo', 'hi', 'n_valid'}}
    Percentile intervals (two-sided 1 - alpha). Random seed 20261111 by default; Random(seed) is created per call."""
    if restrict is not None:
        rows = [r for r in rows if restrict(r)]
        if tasks:
            tasks = [t for t in tasks if restrict(t)]
    cells = Cells(rows, fields, group_by, strata_key, task_key, tasks)
    obs = View(cells, _totals_pure(cells, [1] * len(cells.tasks)))
    est = {n: _clean(f(obs)) for n, f in statistics.items()}
    rng = random.Random(seed)
    draws = {n: [] for n in statistics}
    dropped = {n: 0 for n in statistics}
    if use_numpy is None:
        use_numpy = _np is not None
    if use_numpy and _np is None:
        raise RuntimeError('numpy requested but not importable')
    dense = _np.array(cells.dense_matrix(), dtype=float) if use_numpy and cells.tasks else None
    done = 0
    while done < B:
        nb = min(chunk, B - done)
        counts_chunk = [_resample_counts(cells, rng) for _ in range(nb)]
        if use_numpy and dense is not None and dense.shape[1] > 0:
            tot_chunk = (_np.array(counts_chunk, dtype=float) @ dense).tolist()
        else:
            tot_chunk = [_totals_pure(cells, c) for c in counts_chunk]
        for tot in tot_chunk:
            view = View(cells, tot)
            for n, f in statistics.items():
                v = _clean(f(view))
                if isnan(v):
                    dropped[n] += 1
                else:
                    draws[n].append(v)
        done += nb
    out = {}
    for n in statistics:
        d = sorted(draws[n])
        out[n] = {'estimate': est[n], 'draws': d, 'dropped': dropped[n], 'B': B, 'n_valid': len(d),
                  'lo': percentile(d, alpha / 2), 'hi': percentile(d, 1 - alpha / 2)}
    return out


def _clean(v):
    if v is None:
        return NAN
    return float(v)


def cluster_bootstrap(rows, statistic, strata_key=default_stratum_key, B=B_DEFAULT, seed=SEED, **kw):
    """Single-statistic form of cluster_bootstrap_multi (INTERFACES.md signature). `statistic(view)`; extra keyword
    arguments (fields, group_by, tasks, restrict, ...) as in cluster_bootstrap_multi; `fields` defaults to every numeric
    key of the first row."""
    if 'fields' not in kw:
        first = rows[0] if rows else {}
        kw['fields'] = sorted(k for k, v in first.items() if isinstance(v, (int, float)) and not isinstance(v, bool)
                              or isinstance(v, bool))
    res = cluster_bootstrap_multi(rows, {'stat': statistic}, strata_key=strata_key, B=B, seed=seed, **kw)['stat']
    return res


def one_sided_bound(draws, level):
    """Lower one-sided bound at `level` (e.g. the Holm step's alpha): the `level` percentile of the draws."""
    return percentile(sorted(draws), level) if draws else NAN
