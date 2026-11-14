# Agreement family of the secondary analyses (T12, after harm coding): B.32 (coder agreement), B.33 (each coder against the automatic
# pre-label), B.25 (H5 predicted-direction agreement on M), B.22 (weighted kappa of the two invitation-strength ratings).
# Written 2026-11-13 in the T11 preparation step. Status: draft; decides nothing.
#
# Inputs besides the common ones: decoded coding files in the format harness/coding_sheet.py `decode` writes (TSV: program_id, code,
# weight, coder, coder_code, item_id), joined on program_id; for B.25 the resolved codes (TSV: program_id, code[, weight]; no producer
# exists yet, REVIEW X-6); for B.22 the second rating (TSV: task_id, invitation_strength).
#   python3 -I -B sec_agreement.py --analysis B.32 --coder-a A.tsv --coder-b B.tsv --coder-a-kind model|human --coder-b-kind model|human ...
#     (LR84.2, Amendment 15 item 7: the kind of each coder is a required option; two model coders give the label "model vs model")
#   python3 -I -B sec_agreement.py --analysis B.33 --coder-a A.tsv [--coder-b B.tsv] ...
#   python3 -I -B sec_agreement.py --analysis B.25 --resolved harm/codes_resolved.tsv ...
#   python3 -I -B sec_agreement.py --analysis B.22 --second-rating R2.tsv --pairs-table R2_pairs.tsv ...
# B.22 (LR83.2): weighted kappa (linear weights) of the two invitation-strength ratings on the 128 tasks (quota-row strength) and, beside it,
# on the 130 (task, invited idiom) pairs; the descriptive part-1 count (is the invited idiom among the first-choice codes / among the listed
# codes) for both ratings. Inputs: second_rating.tsv and second_rating_pairs.tsv written by logs/t11prep_2026-11-13/second_rating/
# convert_second_rating.py (which checks the seals and applies the quota-row rule).
import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sec_common as C  # noqa: E402

HARM_CODES = ('HARM_3X', 'FIX_3X', 'BOTH_ACCEPTABLE', 'NEITHER', 'UNDETERMINABLE')
KAPPA_THRESHOLD = 0.60                    # 10.4
BOOTSTRAP_UNIT = 'task, stratified by stratum and, within M, family (LR82 general rule (iii), item 7)'   # C-20 (b) + S-2
IPW_APPLIED_TO_AGREEMENT = False          # C-20: not applied
PRELABEL_PAIR = 'E0a~E1'
NO_PRELABEL_CODE = 'UNDETERMINABLE'       # LR82.2 item 7 (S-5): a program without a pre-label is UNDETERMINABLE, as in the frozen H5 table
H5_PAIR = 'E0a~E1'
B25_AGREEMENT_DEFINITION = ('(HARM with HARM_3X + FIX with FIX_3X) / (programs predicted HARM or FIX and coded HARM_3X or FIX_3X); '
                            'BOTH only in the cross-table')          # C-16 default
B25_ALT_DEFINITION = 'BOTH_ACCEPTABLE counts as agreeing with BOTH (denominator: predicted HARM, FIX or BOTH, coded HARM_3X, FIX_3X or BOTH_ACCEPTABLE)'
KAPPA_WEIGHTS = 'linear'                  # C-15: 'linear' (default) or 'quadratic'
B22_UNIT = 'task (M tasks, strength of the quota row) and, beside it, the 130 (task, invited idiom) pairs (LR83.2)'
LEVELS = (1, 2, 3)


def read_codes_file(path, require_coder_cols=False):
    """{program_id: {'code', 'weight'}} from a decoded coding TSV; duplicates and unknown codes are refused."""
    rows = C.read_tsv(path)
    out = {}
    for r in rows:
        pid = r['program_id']
        if pid in out:
            raise C.Refuse('%s: duplicate program_id %s' % (os.path.basename(path), pid))
        if r['code'] not in HARM_CODES:
            raise C.Refuse('%s: unknown harm code %r for %s' % (os.path.basename(path), r['code'], pid))
        w = r.get('weight')
        out[pid] = {'code': r['code'], 'weight': float(w) if w not in (None, '') else None}
    return out


def raw_agree(a, b):
    return (sum(1 for x, y in zip(a, b) if x == y) / len(a)) if a else float('nan')


def agreement_block(inp, items):
    """kappa, AC1, raw agreement with percentile intervals from the stratified paired task-cluster bootstrap of the frozen engine
    (rule (iii) of LR82; B and seed from the command line). items: [(task_id, stratum, family code, code_1, code_2)]."""
    r = C.stratified_agreement(inp, items, HARM_CODES)
    out = {'n_items': r['n_items']}
    for name, key in (('kappa', 'kappa'), ('ac1', 'ac1'), ('raw_agreement', 'raw')):
        e = r[key]
        out.update({name: e['estimate'], name + '_lo': e['lo'], name + '_hi': e['hi'], name + '_dropped': e['dropped']})
    return out


def item_of(p, a, b):
    fam = C.family_code(p.get('family')) if p['stratum'] == 'M' else None
    return (p['task_id'], p['stratum'], fam, a, b)


AG_COLS = ['n_items', 'kappa', 'kappa_lo', 'kappa_hi', 'kappa_dropped', 'ac1', 'ac1_lo', 'ac1_hi', 'ac1_dropped', 'raw_agreement',
           'raw_agreement_lo', 'raw_agreement_hi']


# ------------------------------------------------------------------------------------------------ B.32
STAT_LABELS = {
    ('model', 'model'): 'model vs model (agreement between two model coders; not inter-rater reliability of people)',
    ('human', 'model'): 'author vs model (not inter-rater reliability; the second coder was a model)',
    ('model', 'human'): 'model vs human (not inter-rater reliability; the first coder was a model)',
    ('human', 'human'): 'two human coders',
}


def stat_label(kind_a, kind_b):
    if (kind_a, kind_b) not in STAT_LABELS:
        raise C.Refuse('the kind of each coder is model or human (got %r and %r)' % (kind_a, kind_b))
    return STAT_LABELS[(kind_a, kind_b)]


def b32(inp, tool, outdir, ca, cb, kind_a, kind_b):
    A, Bc = read_codes_file(ca), read_codes_file(cb)
    by_id = {p['program_id']: p for p in inp.per_program}
    extra = sorted(set(Bc) - set(A))
    if extra:
        raise C.Refuse('coder B has %d items that coder A has not coded (first: %s); B.32 is defined on the double-coded sample' % (len(extra), extra[0]))
    ids = sorted(Bc)
    unknown = [i for i in ids if i not in by_id]
    if unknown:
        raise C.Refuse('%d coded program ids are not in per_program.jsonl (first: %s)' % (len(unknown), unknown[0]))

    def core(sub):
        sub_by = {p['program_id']: p for p in sub.per_program}
        kept = [i for i in ids if i in sub_by]
        items = [item_of(sub_by[i], A[i]['code'], Bc[i]['code']) for i in kept]
        res = agreement_block(sub, items)
        res['items_left_out_ruled'] = len(ids) - len(kept)
        res['threshold_kappa'] = KAPPA_THRESHOLD
        res['kappa_meets_threshold'] = (res['kappa'] is not None and res['kappa'] >= KAPPA_THRESHOLD)
        res['label_of_statistic'] = stat_label(kind_a, kind_b)
        conf = collections.Counter((A[i]['code'], Bc[i]['code']) for i in kept)
        return [dict(res, table='agreement')] + [{'table': 'confusion', 'stratum': 'M', 'coder_a': x, 'coder_b': y, 'count': n}
                                                 for (x, y), n in sorted(conf.items())]
    allr, mr = C.row_variants(inp, core)
    rows = [r for r in allr if r['table'] == 'agreement']
    conf = [r for r in allr if r['table'] == 'confusion' and r['variant'] == 'all tasks']
    res = rows[0]
    wo = [r for r in rows if r['variant'] != 'all tasks']
    meta = C.meta_block(inp, tool, ['B.32'], {'coder_a_file_sha256': C.sha256_file(ca), 'coder_b_file_sha256': C.sha256_file(cb),
                                              'bootstrap_unit': BOOTSTRAP_UNIT, 'coder_a_kind': kind_a, 'coder_b_kind': kind_b, 'lr61': mr})
    md = C.header_md(inp, 'B.32', 'Coder agreement (double-coded sample)', meta,
                     'Statistic label: %s. Bootstrap: %s (rule (iii)); IPW not applied. Threshold kappa >= %.2f: %s. A second row repeats the '
                     'statistic without the programs of the ruled R tasks (LR61/LR70, rule (vi)) when the tasks hold stratum R.' % (
                         res['label_of_statistic'], BOOTSTRAP_UNIT, KAPPA_THRESHOLD, 'met' if res['kappa_meets_threshold'] else 'not met'))
    acols = ['variant'] + AG_COLS + ['items_left_out_ruled', 'threshold_kappa', 'kappa_meets_threshold', 'label_of_statistic']
    md += ['', C.md_table(AG_COLS + ['variant'], rows), '', 'Code cross-table (coder A x coder B), all tasks:', '',
           C.md_table(['coder_a', 'coder_b', 'count'], conf)]
    return C.emit(outdir, 'B.32', inp, meta, md, [('agreement', acols, rows), ('confusion', ['coder_a', 'coder_b', 'count'], conf)],
                  {'item': 'B.32', 'result': res, 'result_without_ruled': wo[0] if wo else None,
                   'confusion': [{k: v for k, v in c.items() if k in ('coder_a', 'coder_b', 'count')} for c in conf], 'lr61_without_ruled': mr})


# ------------------------------------------------------------------------------------------------ B.33
def b33(inp, tool, outdir, files):
    by_id = {p['program_id']: p for p in inp.per_program}
    loaded = []
    for name, path in files:
        codes = read_codes_file(path)
        for pid in codes:
            if pid not in by_id:
                raise C.Refuse('%s: program id %s not in per_program.jsonl' % (os.path.basename(path), pid))
        loaded.append((name, path, codes))

    def core(sub):
        sub_by = {p['program_id']: p for p in sub.per_program}
        out = []
        for name, path, codes in loaded:
            items, no_label = [], 0
            for pid in sorted(codes):
                p = sub_by.get(pid)
                if p is None:
                    continue
                t = (p.get('targets') or {}).get(PRELABEL_PAIR) or {}
                pre = t.get('harm_prelabel')
                if pre is None:
                    no_label += 1
                    pre = NO_PRELABEL_CODE         # LR82.2 item 7 (S-5): as in the frozen H5 table (analyze_full.py: `or 'UNDETERMINABLE'`)
                items.append(item_of(p, codes[pid]['code'], pre))
            res = agreement_block(sub, items)
            res.update({'coder': name, 'items_without_prelabel': no_label, 'file_sha256': C.sha256_file(path)})
            out.append(res)
        return out
    out, mr = C.row_variants(inp, core)
    cols = ['variant', 'coder'] + AG_COLS + ['items_without_prelabel']
    meta = C.meta_block(inp, tool, ['B.33'], {'pair': PRELABEL_PAIR, 'bootstrap_unit': BOOTSTRAP_UNIT, 'prelabel_missing_code': NO_PRELABEL_CODE,
                                              'lr61': mr})
    md = C.header_md(inp, 'B.33', 'Each coder against the automatic pre-label', meta,
                     'Same intervals as B.32. An item whose pre-label is empty is entered as %s, as in the frozen H5 table, and counted '
                     '(items_without_prelabel). Rows with variant "without ruled R tasks" leave out the programs of the ruled tasks (LR61/LR70).' % NO_PRELABEL_CODE)
    md += ['', C.md_table(cols, out)]
    return C.emit(outdir, 'B.33', inp, meta, md, [('agreement', cols, out)], {'item': 'B.33', 'results': out, 'lr61_without_ruled': mr})


# ------------------------------------------------------------------------------------------------ B.25
def b25(inp, tool, outdir, resolved_path):
    stats = inp.stats
    codes = read_codes_file(resolved_path)
    by_id = {p['program_id']: p for p in inp.per_program}
    rows, skipped = [], collections.Counter()
    for pid, c in sorted(codes.items()):
        p = by_id.get(pid)
        if p is None:
            raise C.Refuse('resolved codes: program id %s not in per_program.jsonl' % pid)
        if p['stratum'] != 'M':
            skipped['not stratum M'] += 1
            continue
        kind, t = C.pair_status(p, H5_PAIR)
        if kind != 'CLEAN' or not t.get('drift'):
            skipped['not a pair-clean drift program of %s' % H5_PAIR] += 1
            continue
        task = inp.tmap.get(p['task_id'], {})
        d = ((task.get('predicted_direction') or {}).get('direction'))
        if d not in ('HARM', 'FIX', 'BOTH'):
            skipped['no predicted direction'] += 1
            continue
        fam = C.family_code(p.get('family')) or C.family_code(task.get('family'))
        code = c['code']
        w = c['weight'] if c['weight'] is not None else 1.0
        den = 1 if (d in ('HARM', 'FIX') and code in ('HARM_3X', 'FIX_3X')) else 0
        num = 1 if ((d == 'HARM' and code == 'HARM_3X') or (d == 'FIX' and code == 'FIX_3X')) else 0
        den_alt = 1 if (d in ('HARM', 'FIX', 'BOTH') and code in ('HARM_3X', 'FIX_3X', 'BOTH_ACCEPTABLE')) else 0
        num_alt = 1 if (num or (d == 'BOTH' and code == 'BOTH_ACCEPTABLE')) else 0
        rows.append({'model': p['model'], 'task_id': p['task_id'], 'stratum': 'M', 'fam': fam, 'direction': d, 'code': code, 'w': w,
                     'num': num, 'den': den, 'num_alt': num_alt, 'den_alt': den_alt})
    cross = collections.defaultdict(lambda: {'n': 0, 'w': 0.0})
    for r in rows:
        for fam in (r['fam'], 'ALL'):
            k = (fam, r['direction'], r['code'])
            cross[k]['n'] += 1
            cross[k]['w'] += r['w']
    cross_rows = []
    row_tot = collections.defaultdict(lambda: {'n': 0, 'w': 0.0})
    for (fam, d, code), v in cross.items():
        row_tot[(fam, d)]['n'] += v['n']
        row_tot[(fam, d)]['w'] += v['w']
    for (fam, d, code), v in sorted(cross.items(), key=lambda kv: (kv[0][0] != 'ALL', str(kv[0][0]), kv[0][1], kv[0][2])):
        rt = row_tot[(fam, d)]
        cross_rows.append({'family': fam, 'predicted_direction': d, 'code': code, 'count': v['n'], 'share_unweighted': v['n'] / rt['n'],
                           'weighted_count': v['w'], 'share_ipw': (v['w'] / rt['w']) if rt['w'] else None})
    agree = []
    tk = [t for t in inp.tasks_univ if t['stratum'] == 'M']
    for name, nf, df in (('default', 'num', 'den'), ('BOTH_ACCEPTABLE agrees with BOTH', 'num_alt', 'den_alt')):
        stat = {'ALL': (lambda v, nf=nf, df=df: (None if v.sum(df) == 0 else v.sum(nf) / v.sum(df)))}
        for q in C.QFS:
            stat[q] = (lambda v, q=q, nf=nf, df=df: (None if v.sum(df, fam=q) == 0 else v.sum(nf, fam=q) / v.sum(df, fam=q)))
        res = stats.cluster_bootstrap_multi(rows, stat, [nf, df], ('model', 'stratum', 'fam'), B=inp.B, seed=inp.seed, tasks=tk) if rows else {}
        for q in ['ALL'] + C.QFS:
            sub = rows if q == 'ALL' else [r for r in rows if r['fam'] == q]
            nn_, dd = sum(r[nf] for r in sub), sum(r[df] for r in sub)
            if q != 'ALL' and not sub:
                continue
            p_, lo, hi = C.wilson(stats, nn_, dd)
            b = res.get(q)
            agree.append({'definition': name, 'family': q, 'agree': nn_, 'of': dd, 'rate': p_, 'wilson_lo': lo, 'wilson_hi': hi,
                          'boot_lo': C.nn(b['lo']) if b else None, 'boot_hi': C.nn(b['hi']) if b else None,
                          'boot_dropped': b['dropped'] if b else None})
    meta = C.meta_block(inp, tool, ['B.25'], {'resolved_file_sha256': C.sha256_file(resolved_path), 'pair': H5_PAIR,
                                              'definition': B25_AGREEMENT_DEFINITION, 'alternative': B25_ALT_DEFINITION})
    acols = ['definition', 'family', 'agree', 'of', 'rate', 'wilson_lo', 'wilson_hi', 'boot_lo', 'boot_hi', 'boot_dropped']
    ccols = ['family', 'predicted_direction', 'code', 'count', 'share_unweighted', 'weighted_count', 'share_ipw']
    md = C.header_md(inp, 'B.25', 'H5 predicted-direction agreement (stratum M)', meta,
                     'Agreement = %s. Alternative: %s. Task-cluster bootstrap over M by family. Secondary check; no test.' % (
                         B25_AGREEMENT_DEFINITION, B25_ALT_DEFINITION))
    md += ['', C.md_table(acols, agree), '', 'Cross-table, all families (predicted direction by resolved code):', '',
           C.md_table(ccols, [r for r in cross_rows if r['family'] == 'ALL']), '',
           'Left out: ' + ('; '.join('%s: %d' % kv for kv in sorted(skipped.items())) or 'nothing') + '.']
    return C.emit(outdir, 'B.25', inp, meta, md, [('agreement', acols, agree), ('crosstable', ccols, cross_rows)],
                  {'item': 'B.25', 'agreement': agree, 'crosstable': cross_rows, 'left_out': dict(skipped)})


# ------------------------------------------------------------------------------------------------ B.22
def weighted_kappa(a, b, levels=LEVELS, weights=KAPPA_WEIGHTS):
    """Weighted Cohen's kappa for two ordinal ratings: 1 - sum w_ij O_ij / sum w_ij E_ij with disagreement weights w (linear: |i-j|,
    quadratic: (i-j)^2). nan when the expected weighted disagreement is 0."""
    n = len(a)
    if n == 0 or n != len(b):
        return float('nan')
    k = len(levels)
    idx = {v: i for i, v in enumerate(levels)}
    O = [[0.0] * k for _ in range(k)]
    for x, y in zip(a, b):
        O[idx[x]][idx[y]] += 1.0 / n
    ra = [sum(O[i]) for i in range(k)]
    rb = [sum(O[i][j] for i in range(k)) for j in range(k)]

    def w(i, j):
        d = abs(i - j)
        return d if weights == 'linear' else d * d
    num = sum(w(i, j) * O[i][j] for i in range(k) for j in range(k))
    den = sum(w(i, j) * ra[i] * rb[j] for i in range(k) for j in range(k))
    if den == 0:
        return float('nan')
    return 1.0 - num / den


def read_pairs_table(path, allow_empty=False):
    """Rows of second_rating_pairs.tsv (convert_second_rating.py): task_id, quota_row, strength_first, strength_second and the four
    part-1 marks. Levels outside 1..3, marks outside 0/1 and a duplicated (task, idiom) pair are refused."""
    with open(path, encoding='utf-8') as f:
        header = [ln.rstrip('\n') for ln in f if ln.strip() and not ln.startswith('#')][:1]
    rows = C.read_tsv(path)
    if allow_empty and not rows and header:
        return []              # test data without an M stratum (pilot wiring): a header-only table
    need = ['task_id', 'idiom_id', 'quota_row', 'strength_first', 'strength_second', 'p1_first_choice_first', 'p1_listed_first',
            'p1_first_choice_second', 'p1_listed_second']
    if not rows or any(k not in rows[0] for k in need):
        raise C.Refuse('pairs table: columns %s needed' % need)
    seen = set()
    for r in rows:
        if (r['task_id'], r['idiom_id']) in seen:
            raise C.Refuse('pairs table: a (task, idiom) pair twice')
        seen.add((r['task_id'], r['idiom_id']))
        for k in ('strength_first', 'strength_second'):
            if r[k].strip() not in ('1', '2', '3'):
                raise C.Refuse('pairs table: level %r outside %s' % (r[k], LEVELS))
        for k in ('quota_row', 'p1_first_choice_first', 'p1_listed_first', 'p1_first_choice_second', 'p1_listed_second'):
            if r[k].strip() not in ('0', '1'):
                raise C.Refuse('pairs table: %s must be 0 or 1' % k)
    return rows


def kappa_row(inp, unit, items, missing=None):
    """One row of the kappa table: items [(task_id, 'M', family code, rating 1, rating 2)]."""
    a, b = [x[3] for x in items], [x[4] for x in items]
    est = weighted_kappa(a, b)
    kind = 'wkappa_' + KAPPA_WEIGHTS
    bs = C.stratified_agreement(inp, items, LEVELS, stat_kinds=(kind,), tasks=[t for t in inp.tasks_univ if t['stratum'] == 'M'])[kind]
    return {'unit': unit, 'n_items': len(items), 'weights': KAPPA_WEIGHTS, 'weighted_kappa': C.nn(est), 'lo': bs['lo'], 'hi': bs['hi'],
            'dropped': bs['dropped'], 'tasks_without_both_ratings': missing, 'raw_agreement': raw_agree(a, b) if a else None}


def part1_rows(inp, pairs):
    """Descriptive part-1 count of each rating (Amendment 7 item 4): the share of units whose invited idiom is among the first-choice
    codes, and among the listed codes (first-choice and possible), with Wilson intervals (rule (iii)). Units: the 128 quota-row pairs
    (one per task) and all 130 pairs."""
    out = []
    for rating in ('first', 'second'):
        for unit, sel in (('quota-row pairs (tasks)', [r for r in pairs if r['quota_row'] == '1']), ('all pairs', pairs)):
            n = len(sel)
            row = {'rating': rating, 'unit': unit, 'n': n}
            for key, col in (('first_choice', 'p1_first_choice_%s' % rating), ('listed', 'p1_listed_%s' % rating)):
                x = sum(1 for r in sel if r[col] == '1')
                p, lo, hi = C.wilson(inp.stats, x, n)
                row.update({key + '_n': x, key + '_share': C.nn(p), key + '_lo': C.nn(lo), key + '_hi': C.nn(hi)})
            out.append(row)
    return out


def b22(inp, tool, outdir, second_path, pairs_path=None):
    second = {}
    for r in C.read_tsv(second_path):
        v = (r.get('invitation_strength') or '').strip()
        if v:
            if int(v) not in LEVELS:
                raise C.Refuse('second rating: level %s outside %s' % (v, LEVELS))
            second[r['task_id']] = int(v)
    items, missing = [], 0
    for t in inp.tasks:
        if t.get('stratum') != 'M':
            continue
        f = t.get('invitation_strength')
        if f is None or t['id'] not in second:
            missing += 1
            continue
        if int(f) not in LEVELS:
            raise C.Refuse('first rating of %s: level %s outside %s' % (t['id'], f, LEVELS))
        items.append((t['id'], 'M', C.family_code(inp.tmap[t['id']].get('family')), int(f), second[t['id']]))
    res = kappa_row(inp, 'tasks (quota row)', items, missing)
    res['n_tasks'] = res['n_items']
    kappa_rows = [res]
    a, b = [x[3] for x in items], [x[4] for x in items]
    cross = collections.Counter(zip(a, b))
    conf = [{'unit': 'tasks (quota row)', 'first_rating': x, 'second_rating': y, 'count': n} for (x, y), n in sorted(cross.items())]
    extra_meta = {'second_rating_sha256': C.sha256_file(second_path), 'unit': B22_UNIT}
    part1 = []
    if pairs_path:
        pairs = read_pairs_table(pairs_path, allow_empty=inp.test_mode)
        pitems = []
        for r in pairs:
            t = inp.tmap.get(r['task_id'])
            if t is None or t.get('stratum') != 'M':
                raise C.Refuse('pairs table: %s is not an M task of tasks.json' % r['task_id'])
            pitems.append((r['task_id'], 'M', C.family_code(t.get('family')), int(r['strength_first']), int(r['strength_second'])))
            if r['quota_row'] == '1':          # consistency with the two task-level tables
                if second.get(r['task_id']) != int(r['strength_second']) or t.get('invitation_strength') != int(r['strength_first']):
                    raise C.Refuse('pairs table: the quota row of %s differs from the task-level tables' % r['task_id'])
        kappa_rows.append(kappa_row(inp, 'pairs (task, invited idiom)', pitems, None))
        pc = collections.Counter((x[3], x[4]) for x in pitems)
        conf += [{'unit': 'pairs (task, invited idiom)', 'first_rating': x, 'second_rating': y, 'count': n} for (x, y), n in sorted(pc.items())]
        part1 = part1_rows(inp, pairs)
        extra_meta['pairs_table_sha256'] = C.sha256_file(pairs_path)
    cols = ['unit', 'n_items', 'weights', 'weighted_kappa', 'lo', 'hi', 'dropped', 'tasks_without_both_ratings', 'raw_agreement']
    ccols = ['unit', 'first_rating', 'second_rating', 'count']
    pcols = ['rating', 'unit', 'n', 'first_choice_n', 'first_choice_share', 'first_choice_lo', 'first_choice_hi',
             'listed_n', 'listed_share', 'listed_lo', 'listed_hi']
    meta = C.meta_block(inp, tool, ['B.22'], extra_meta)
    md = C.header_md(inp, 'B.22', 'Weighted kappa of the two invitation-strength ratings (LR4, LR83.2)', meta,
                     'First rating = tasks.json invitation_strength (its sealed part-2 quota-row rating); second rating = its sealed part-2 '
                     'rating of the quota row (INTEGRATE I2), converted by convert_second_rating.py. Unit: %s; %s weights; stratified '
                     'task-cluster bootstrap by family within M (rule (iii)); a task with two pairs is one cluster. The LR3 table on the '
                     'second rating is produced by the frozen analyzer (--second-rating). The part-1 table is descriptive (Amendment 7 '
                     'item 4): the invited idiom among the first-choice codes / among the listed codes; Wilson intervals.' % (
                         B22_UNIT, KAPPA_WEIGHTS))
    md += ['', C.md_table(cols, kappa_rows), '', C.md_table(ccols, conf)]
    tables = [('kappa', cols, kappa_rows), ('crosstable', ccols, conf)]
    if part1:
        md += ['', 'Part 1 (descriptive):', '', C.md_table(pcols, part1)]
        tables.append(('part1', pcols, part1))
    return C.emit(outdir, 'B.22', inp, meta, md, tables,
                  {'item': 'B.22', 'result': res, 'result_pairs': kappa_rows[1] if pairs_path else None, 'crosstable': conf,
                   'part1_descriptive': part1})


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--analysis', required=True, help='B.32, B.33, B.25 or B.22')
    C.add_common_args(ap)
    ap.add_argument('--ruled-path', default=None)
    ap.add_argument('--coder-a')
    ap.add_argument('--coder-b')
    ap.add_argument('--coder-a-kind', choices=('human', 'model'), help='B.32: required')
    ap.add_argument('--coder-b-kind', choices=('human', 'model'), help='B.32: required')
    ap.add_argument('--resolved')
    ap.add_argument('--second-rating')
    ap.add_argument('--pairs-table', help='B.22: second_rating_pairs.tsv of convert_second_rating.py (130 pairs)')
    a = ap.parse_args(argv)
    need = {'B.32': ('coder_a', 'coder_b', 'coder_a_kind', 'coder_b_kind'), 'B.33': ('coder_a',), 'B.25': ('resolved',), 'B.22': ('second_rating', 'pairs_table')}
    if a.analysis not in need:
        raise C.Refuse('unknown analysis %r' % a.analysis)
    for k in need[a.analysis]:
        if not getattr(a, k):
            raise C.Refuse('%s needs --%s' % (a.analysis, k.replace('_', '-')))
    extra = {}
    for k in ('coder_a', 'coder_b', 'resolved', 'second_rating', 'pairs_table'):
        if getattr(a, k):
            extra[k + '.tsv'] = getattr(a, k)
    inp = C.load_inputs(a, extra)
    C.self_check(inp)
    tool = os.path.abspath(__file__)
    if a.analysis == 'B.32':
        base = b32(inp, tool, a.out, a.coder_a, a.coder_b, a.coder_a_kind, a.coder_b_kind)
    elif a.analysis == 'B.33':
        files = [('coder A', a.coder_a)] + ([('coder B', a.coder_b)] if a.coder_b else [])
        base = b33(inp, tool, a.out, files)
    elif a.analysis == 'B.25':
        base = b25(inp, tool, a.out, a.resolved)
    else:
        base = b22(inp, tool, a.out, a.second_rating, a.pairs_table)
    print('wrote', os.path.basename(base) + '.{json,md,tsv}')
    return 0


if __name__ == '__main__':
    sys.exit(C.run_main(main))
