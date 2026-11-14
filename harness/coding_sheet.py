# ATTRIB_HARM: blind A/B harm-coding sheets, samplers and decoding (FULL_PREREG sections 8 "H5 weights", 10.3, 10.4; STAGE2 T5.7, T12.1).
# Written 2026-11-11 by pkg:ATTRIB_HARM (drafted_by: pkg:ATTRIB_HARM; status: prepared).
# Standard library only; no LLM is called here. Coder B may be a person (human form) or an LLM from outside the study set (machine form:
# items JSONL + harm/coder_llm/PROMPT.txt + harm/coder_llm/answer.schema.json); both see exactly the same blind content.
#
# What a coder sees (section 10.3): the task statement, the fixture description, the acceptable variants, the property checks, the program,
# and the two results labelled A and B in seeded random order (seed 20261111) with the differing cells highlighted.
# What a coder NEVER sees: the intended-computation paragraph, the reference solution or its result, the automatic pre-label, the predicted
# direction, catalogue ids, family, stratum, task id, model, dtypes, result class paths, or any version / environment label. Only
# BLIND_TASK_FIELDS of the card are read; the A/B -> environment key is written to a separate file (--key) that coders never get.
#
# Subcommands (python3 -I -B harness/coding_sheet.py <cmd> ...; with no subcommand the arguments are those of `build`):
#   sample  --per-program results/per_program.jsonl --out harm/coding_sample.tsv [--pair E0a~E1] [--n-max 400] [--seed 20261111]
#   double  --sample harm/coding_sample.tsv --out harm/double_sample.tsv [--share 0.25] [--n-min 80] [--exclude PREV.tsv] [--seed ...]
#   build   --per-program ... --runs runs/ --tasks tasks/tasks.json --out harm/sheets/ --key harm/_private/sheet_key.json
#           [--sample harm/coding_sample.tsv] [--double harm/double_sample.tsv] [--gen-dir generations] [--pair E0a~E1] [--seed ...]
#   render  --specs SPECS.json --out DIR --key KEY.json [--seed ...]      (explicit items, e.g. the coding manual's worked examples)
#   decode  --answers answers.csv|answers.jsonl --key KEY.json --out codes.tsv [--coder NAME]   (A/B codes -> HARM_3X / FIX_3X / ...)
import argparse, collections, csv, datetime, gzip, hashlib, html, json, math, os, random, re, sys

HARNESS = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HARNESS)
if HARNESS not in sys.path:
    sys.path.insert(0, HARNESS)
import harm_prelabel as hp  # noqa: E402

SEED = 20261111
CODER_CODES = ('A_ONLY_CORRECT', 'B_ONLY_CORRECT', 'BOTH_ACCEPTABLE', 'NEITHER', 'UNDETERMINABLE')
HARM_CODES = ('HARM_3X', 'FIX_3X', 'BOTH_ACCEPTABLE', 'NEITHER', 'UNDETERMINABLE')
BLIND_TASK_FIELDS = ('task_text', 'files', 'acceptable_variants', 'property_checks', 'order_significant', 'sort_keys')
PROMPT_PATH = os.path.join(STUDY, 'harm', 'coder_llm', 'PROMPT.txt')
HUMAN_MAX_ROWS = 2000      # human pages show results with at most this many rows in full
MACHINE_MAX_ROWS = 100     # the machine form / LLM prompt shows results with at most this many rows in full
HEAD_ROWS = 10             # otherwise: the first rows ...
MAX_DIFF_ROWS = 40         # ... plus rows with a difference, up to this many (plus a per-column summary of the whole result)
MAX_DIFF_LIST = 40         # differences listed one by one (the total count is always given)
# Harness-authored text must never carry these (version / environment / design labels). Program text, task text and result values are
# shown verbatim and are checked separately in the tests on synthetic data.
FORBIDDEN_RE = re.compile(r'\bpandas\s*[23](\.\d+)*\b|\b[23]\.[0-3]\.\d+\b|\bE0a\b|\bE0b\b|\bE0pa\b|\bE[1-4]\b|\bpd(223|233|30x|31x)(pa)?\b|'
                          r'\bHARM_3X\b|\bFIX_3X\b|\bQF[1-8]\b|\bpyarrow\b|\bdtype\b|\bversion\b|\bintended computation\b|\breference\b',
                          re.IGNORECASE)


def _read(path, errors='strict'):
    with open(path, encoding='utf-8', errors=errors) as f:
        return f.read()


def now_iso():
    return datetime.datetime.now().astimezone().isoformat(timespec='seconds')


# ================================================================================================ samplers (sections 8, 10.3, 10.4)
def family_code(fam):
    return fam.split('_')[0] if fam else None


def cell_of(p):
    """Stratification cell model x {QF1..QF8, R, A} (section 8, H5 weights)."""
    st = p.get('stratum')
    return (p.get('model'), family_code(p.get('family')) if st == 'M' else st)


def allocate(counts, n, min_one=True):
    """Proportional allocation (largest remainder) of n draws over cells {cell: N}; with min_one every non-empty cell gets >= 1 draw
    (requires n >= number of cells). Deterministic: ties broken by sorted cell order."""
    cells = sorted(c for c, k in counts.items() if k > 0)
    total = sum(counts[c] for c in cells)
    if n >= total:
        return {c: counts[c] for c in cells}
    if min_one and n < len(cells):
        raise ValueError('cannot give each of %d cells a draw with n = %d' % (len(cells), n))
    quota = {c: n * counts[c] / total for c in cells}
    alloc = {c: min(counts[c], max(1 if min_one else 0, int(math.floor(quota[c])))) for c in cells}
    while sum(alloc.values()) < n:
        cand = [c for c in cells if alloc[c] < counts[c]]
        c = max(cand, key=lambda c: (quota[c] - alloc[c], -cells.index(c)))
        alloc[c] += 1
    while sum(alloc.values()) > n:
        cand = [c for c in cells if alloc[c] > (1 if min_one else 0)]
        c = min(cand, key=lambda c: (quota[c] - alloc[c], cells.index(c)))
        alloc[c] -= 1
    return alloc


def _stratified(items, n, seed, min_one):
    by = collections.defaultdict(list)
    for p in items:
        by[cell_of(p)].append(p)
    counts = {c: len(v) for c, v in by.items()}
    alloc = allocate(counts, n, min_one)
    rng = random.Random(seed)
    out = []
    for c in sorted(by):
        pool = sorted(by[c], key=lambda p: p['program_id'])
        k = alloc.get(c, 0)
        take = pool if k >= len(pool) else rng.sample(pool, k)
        for p in sorted(take, key=lambda p: p['program_id']):
            out.append((c, len(pool), k, p))
    return out


def coding_sample(drift_programs, n_max=400, seed=SEED):
    """All drift programs if there are at most n_max; else a stratified random sample of n_max (cells model x {QF1..QF8,R,A},
    proportional allocation with at least one per non-empty cell) with inverse-probability weight N_cell / n_cell.
    Returns dicts with program_id, model, stratum, family, cell, weight (sum of weights = number of drift programs)."""
    progs = [dict(p) for p in drift_programs]
    if len(progs) <= n_max:
        out = []
        for p in sorted(progs, key=lambda p: p['program_id']):
            q = dict(p)
            q.update(cell='%s|%s' % cell_of(p), weight=1.0)
            out.append(q)
        return out
    out = []
    for c, N, k, p in _stratified(progs, n_max, seed, True):
        q = dict(p)
        q.update(cell='%s|%s' % c, weight=N / k)
        out.append(q)
    return out


def double_coding_sample(coded, share=0.25, n_min=80, seed=SEED, exclude=()):
    """Coder B's sample (section 10.4): ceil(share x n) but at least min(n_min, n) of the coded programs, stratified like the coding
    sample (proportional; at least one per cell when the sample is at least as large as the number of cells). `exclude` (program ids
    double-coded in an earlier round) makes the 'fresh 25%' of a second round. Each row keeps its coding weight and gets
    'double_weight' = n_coded_cell / n_double_cell."""
    pool = [dict(p) for p in coded if p['program_id'] not in set(exclude)]
    n_base = len(coded)
    n = max(int(math.ceil(share * n_base)), min(n_min, n_base))
    n = min(n, len(pool))
    cells = {cell_of(p) for p in pool}
    out = []
    for c, N, k, p in _stratified(pool, n, seed, n >= len(cells)):
        q = dict(p)
        q.update(cell='%s|%s' % c, double_weight=N / k)
        out.append(q)
    return out


SAMPLE_FIELDS = ['program_id', 'model', 'task_id', 'stratum', 'family', 'cell', 'weight']


def write_tsv(path, rows, fields):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write('\t'.join(fields) + '\n')
        for r in rows:
            f.write('\t'.join('' if r.get(k) is None else str(r.get(k)) for k in fields) + '\n')


def read_tsv(path):
    with open(path, encoding='utf-8') as f:
        lines = [ln.rstrip('\n') for ln in f if ln.strip() and not ln.startswith('#')]
    hdr = lines[0].split('\t')
    return [dict(zip(hdr, ln.split('\t'))) for ln in lines[1:]]


def drift_programs(per_program, pair='E0a~E1'):
    return [p for p in per_program if p.get('clean_on_233') and ((p.get('targets') or {}).get(pair) or {}).get('drift')]


# ================================================================================================ blind content
def blind_view(task):
    """The only card fields a coder may see (BLIND_TASK_FIELDS)."""
    return {k: (task or {}).get(k) for k in BLIND_TASK_FIELDS}


def variants_text(task):
    av = (task or {}).get('acceptable_variants') or {}
    out = []
    if (task or {}).get('order_significant') or av.get('row_order') == 'ties_only':
        keys = ', '.join(str(k).replace('__index__', 'the row labels').replace('__values__', 'the values') for k in task.get('sort_keys') or [])
        out.append('Row order matters: rows must be ordered by %s; rows with equal values of %s may appear in any order.'
                   % (keys or 'the key the task names', 'that key' if len(task.get('sort_keys') or []) <= 1 else 'those keys'))
    else:
        out.append('Row order does not matter.')
    if av.get('label_spelling'):
        out.append('Column and row labels may differ in letter case, spaces and underscores.')
    if av.get('missing_value_representation'):
        out.append('Every way of writing a missing value is the same (NaN, None, NA, NaT, an empty cell).')
    if av.get('rounding_sig_digits'):
        out.append('Numbers that agree to %d significant digits are equal.' % int(av['rounding_sig_digits']))
    if av.get('notes'):
        out.append('Also acceptable: %s' % av['notes'])
    return out


def _tg(t):
    return {'__index__': 'the row labels', '__values__': 'the values'}.get(t, '"%s"' % t)


def check_text(chk):
    n, a = chk.get('check'), chk.get('args') or {}
    cols = ', '.join(_tg(c) for c in a.get('columns') or [])
    if n == 'no_null_text':
        return 'No value or label is the text nan, None, NaT or <NA>.'
    if n == 'no_all_missing_column':
        return 'No column is entirely missing.'
    if n == 'date_year_in_range':
        return 'Every date in %s has a year from %s to %s.' % (cols, a.get('min_year'), a.get('max_year'))
    if n == 'counts_sum_to_rows':
        return 'The values of %s add up to %s.' % (_tg(a.get('column')), a.get('expected'))
    if n == 'rate_in_unit_interval':
        return 'Every value of %s is a number between 0 and 1.' % cols
    if n == 'n_groups_equals':
        return 'The result has exactly %s rows.' % a.get('n')
    if n == 'no_nulls':
        return 'No missing values%s.' % ((' in ' + cols) if cols else '')
    if n == 'numeric_in_range':
        lo, hi = a.get('min'), a.get('max')
        rng = ('from %s to %s' % (lo, hi) if lo is not None and hi is not None else 'at least %s' % lo if lo is not None
               else 'at most %s' % hi)
        return 'Every value of %s is a number %s.' % (cols, rng)
    if n == 'values_in_set':
        return 'Every value of %s is one of: %s.' % (_tg(a.get('column')), ', '.join(json.dumps(v, ensure_ascii=False) for v in a.get('values') or []))
    if n == 'columns_present':
        return 'The result has the column(s) %s.' % ', '.join('"%s"' % c for c in a.get('columns') or [])
    if n == 'result_kind':
        return 'The result is a %s.' % {'dataframe': 'table', 'series': 'single column with row labels (Series)', 'scalar': 'single value',
                                        'index': 'list of labels (Index)'}.get(a.get('kind'), a.get('kind'))
    if n == 'sorted_by':
        ks = a.get('keys') or []
        asc = a.get('ascending') or [True] * len(ks)
        return 'Rows are sorted by %s (ties in any order).' % ', '.join('%s %s' % (_tg(k), 'ascending' if u else 'descending')
                                                                        for k, u in zip(ks, asc))
    return '%s %s' % (n, json.dumps(a, ensure_ascii=False))


def show(v):
    """Display form of one canonical cell: text in double quotes, numbers bare, missing as <missing>."""
    if v is None:
        return '<missing>'
    if isinstance(v, bool):
        return 'True' if v else 'False'
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, (list, tuple)):
        return '(' + ', '.join(show(u) for u in v) + ')'
    if isinstance(v, str):
        for pre, fmt in (('TS:', lambda s: s.replace('T', ' ')), ('D:', lambda s: s), ('TD:', lambda s: 'duration %s s' % s),
                         ('IV:', lambda s: 'interval %s' % s), ('PE:', lambda s: 'period %s' % s), ('C:', lambda s: s),
                         ('OBJ:', lambda s: '<object %s>' % s)):
            if v.startswith(pre):
                return fmt(v[len(pre):])
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def show_label(lab):
    return '(unnamed)' if lab is None else (lab if isinstance(lab, str) else show(lab))


class View:
    """Display table of one result: labels, rows, n_index; opaque results keep a text dump."""

    def __init__(self, rec):
        self.status = (rec or {}).get('status', 'ok') if isinstance(rec, dict) else 'ok'
        self.text = None
        self.table = None
        if self.status not in (None, 'ok'):
            self.text = 'The program stopped without a result (%s).' % ('no `result` variable' if self.status == 'no_result' else 'it raised an error')
            return
        try:
            self.table = hp.to_table(rec)
        except hp.NotComparable:
            self.text = json.dumps(hp._canon(rec), ensure_ascii=False, default=str)[:4000]

    def shape(self):
        if self.table is None:
            return None
        return (len(self.table.rows), len(self.table.labels))


def _eq(a, b):
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), rel_tol=1e-11, abs_tol=1e-9)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_eq(x, y) for x, y in zip(a, b))
    return a == b


def _key_alignment(ta, tb, cmap):
    """Rows matched by the first shared column whose values are unique and non-missing in both results (a natural key such as an
    id or a group label), when the row counts or the key orders differ; {} if there is no such column."""
    for ca, cb in sorted(cmap.items()):
        ka = [json.dumps(r[ca], default=str) for r in ta.rows]
        kb = [json.dumps(r[cb], default=str) for r in tb.rows]
        if 'null' in ka or 'null' in kb or len(set(ka)) != len(ka) or len(set(kb)) != len(kb):
            continue
        if ka == kb:
            return {}
        pos_b = {k: j for j, k in enumerate(kb)}
        m = {i: pos_b[k] for i, k in enumerate(ka) if k in pos_b}
        if m:
            return m
    return {}


def diff_views(va, vb):
    """-> (marks_a, marks_b, differences). marks: {(row, col)} positions to highlight (col None = whole row); differences:
    [{'row', 'column', 'A', 'B'}] in display form (row = 1-based position; capped at 500)."""
    ma, mb, diffs = set(), set(), []
    ta, tb = va.table, vb.table
    if ta is None or tb is None:
        if not (va.text is not None and vb.text is not None and va.text == vb.text):
            diffs.append({'row': None, 'column': None, 'A': va.text or 'a table', 'B': vb.text or 'a table'})
        return ma, mb, diffs
    la, lb = [show_label(x) for x in ta.labels], [show_label(x) for x in tb.labels]
    cmap = {}
    used = set()
    for i, l in enumerate(la):
        for j, m in enumerate(lb):
            if j not in used and l == m:
                cmap[i] = j
                used.add(j)
                break
    for i in range(len(la)):
        if i not in cmap:
            ma.update((r, i) for r in range(len(ta.rows)))
            diffs.append({'row': None, 'column': la[i], 'A': 'column present', 'B': 'column absent'})
    for j in range(len(lb)):
        if j not in used:
            mb.update((r, j) for r in range(len(tb.rows)))
            diffs.append({'row': None, 'column': lb[j], 'A': 'column absent', 'B': 'column present'})
    # rows: by index key when both have unique non-default row labels, else by position
    rmap = {}
    if ta.n_index and tb.n_index and ta.n_index == tb.n_index:
        ka = [json.dumps(r[:ta.n_index], default=str) for r in ta.rows]
        kb = [json.dumps(r[:tb.n_index], default=str) for r in tb.rows]
        if len(set(ka)) == len(ka) and len(set(kb)) == len(kb):
            pos_b = {k: j for j, k in enumerate(kb)}
            rmap = {i: pos_b[k] for i, k in enumerate(ka) if k in pos_b}
    if not rmap:
        rmap = _key_alignment(ta, tb, cmap)
    if not rmap:
        rmap = {i: i for i in range(min(len(ta.rows), len(tb.rows)))}
    for i in range(len(ta.rows)):
        if i not in rmap:
            ma.add((i, None))
            if len(diffs) < 500:
                diffs.append({'row': i + 1, 'column': None, 'A': 'row present', 'B': 'no matching row'})
    hit_b = set(rmap.values())
    for j in range(len(tb.rows)):
        if j not in hit_b:
            mb.add((j, None))
            if len(diffs) < 500:
                diffs.append({'row': j + 1, 'column': None, 'A': 'no matching row', 'B': 'row present'})
    for i, j in sorted(rmap.items()):
        for ca, cb in cmap.items():
            x, y = ta.rows[i][ca], tb.rows[j][cb]
            if not _eq(x, y):
                ma.add((i, ca))
                mb.add((j, cb))
                if len(diffs) < 500:
                    diffs.append({'row': i + 1 if i == j else '%d (A) / %d (B)' % (i + 1, j + 1), 'column': la[ca], 'A': show(x), 'B': show(y)})
    return ma, mb, diffs


def rows_to_show(view, marks, max_all, max_diff=MAX_DIFF_ROWS):
    if view.table is None:
        return []
    n = len(view.table.rows)
    if n <= max_all:
        return list(range(n))
    marked = sorted({r for r, _ in marks})
    keep = set(range(min(HEAD_ROWS, n))) | set(marked[:max_diff])
    return sorted(keep)


def column_summary(view):
    """Neutral per-column description of the WHOLE result (so a coder can judge rows that are not shown): number of values,
    missing values, and min/max for numbers or the number of distinct values and the most common ones for text."""
    t = view.table
    if t is None:
        return []
    out = []
    for j, lab in enumerate(t.labels):
        col = [r[j] for r in t.rows]
        miss = sum(1 for v in col if v is None)
        nums = [v for v in col if isinstance(v, (int, float)) and not isinstance(v, bool)]
        s = '%s%s: %d values, %d missing' % ('[row label] ' if j < t.n_index else '', show_label(lab), len(col), miss)
        if nums and len(nums) == len(col) - miss:
            s += ', min %s, max %s' % (show(min(nums)), show(max(nums)))
        else:
            vals = [show(v) for v in col if v is not None]
            cnt = collections.Counter(vals)
            s += (', %d distinct; most common: %s' % (len(cnt), ', '.join('%s (%d)' % kv for kv in cnt.most_common(3)))) if cnt else ', no values'
        out.append(s)
    return out


# ------------------------------------------------------------------------------------------------ text and HTML rendering
LEGEND = ('Text values are shown in double quotes, numbers without quotes, and a missing value as <missing>. '
          'Cells that differ between result A and result B are marked. Long results show only their first rows and some rows with '
          'a difference; the column summaries describe every row.')


def table_text(view, marks, rows, mark=('«', '»')):
    if view.table is None:
        return view.text or ''
    t = view.table
    hdr = ['row'] + [('[row label] ' if j < t.n_index else '') + show_label(l) for j, l in enumerate(t.labels)]
    out = [' | '.join(hdr)]
    prev = -1
    for r in rows:
        if r != prev + 1:
            out.append('... (%d row(s) not shown)' % (r - prev - 1))
        cells = [str(r + 1)]
        whole = (r, None) in marks
        for j, v in enumerate(t.rows[r]):
            s = show(v)
            cells.append(mark[0] + s + mark[1] if (whole or (r, j) in marks) else s)
        out.append(' | '.join(cells))
        prev = r
    if prev < len(t.rows) - 1:
        out.append('... (%d row(s) not shown)' % (len(t.rows) - 1 - prev))
    return '\n'.join(out)


def table_html(view, marks, rows):
    if view.table is None:
        return '<pre class="opaque">%s</pre>' % html.escape(view.text or '')
    t = view.table
    h = ['<table><thead><tr><th>row</th>']
    for j, l in enumerate(t.labels):
        h.append('<th>%s%s</th>' % ('<span class="ix">row label</span> ' if j < t.n_index else '', html.escape(show_label(l))))
    h.append('</tr></thead><tbody>')
    prev = -1
    for r in rows:
        if r != prev + 1:
            h.append('<tr class="gap"><td colspan="%d">&hellip; %d row(s) not shown</td></tr>' % (len(t.labels) + 1, r - prev - 1))
        whole = (r, None) in marks
        h.append('<tr><td class="rn">%d</td>' % (r + 1))
        for j, v in enumerate(t.rows[r]):
            s = html.escape(show(v))
            h.append('<td><mark>%s</mark></td>' % s if (whole or (r, j) in marks) else '<td>%s</td>' % s)
        h.append('</tr>')
        prev = r
    if prev < len(t.rows) - 1:
        h.append('<tr class="gap"><td colspan="%d">&hellip; %d row(s) not shown</td></tr>' % (len(t.labels) + 1, len(t.rows) - 1 - prev))
    h.append('</tbody></table>')
    return ''.join(h)


def make_item(item_id, task, program_text, rec_a, rec_b):
    """One blind item (machine form) from a card and the two run records already placed as A and B."""
    bv = blind_view(task)
    va, vb = View(rec_a), View(rec_b)
    ma, mb, diffs = diff_views(va, vb)
    ra, rb = rows_to_show(va, ma, MACHINE_MAX_ROWS), rows_to_show(vb, mb, MACHINE_MAX_ROWS)
    ha, hb = rows_to_show(va, ma, HUMAN_MAX_ROWS, 500), rows_to_show(vb, mb, HUMAN_MAX_ROWS, 500)
    shape = lambda v: ({'rows': v.shape()[0], 'columns': v.shape()[1]} if v.shape() else None)
    return {
        'schema': 'harm_item/1', 'item_id': item_id,
        'task_statement': bv['task_text'] or '',
        'files': ['%s: %s' % (os.path.basename(f.get('path', '')), f.get('description', '')) for f in bv['files'] or []],
        'acceptable_variants': variants_text(bv),
        'property_checks': [check_text(c) for c in bv['property_checks'] or []],
        'program': program_text or '',
        'result_A': {'shape': shape(va), 'table': table_text(va, ma, ra), 'summary': column_summary(va)},
        'result_B': {'shape': shape(vb), 'table': table_text(vb, mb, rb), 'summary': column_summary(vb)},
        'n_differences': len(diffs), 'differences': diffs[:MAX_DIFF_LIST],
        'legend': LEGEND,
        '_html': {'A': table_html(va, ma, ha), 'B': table_html(vb, mb, hb)},
    }


def item_text(it):
    """Plain-text rendering of one item (used in the LLM prompt and for the guard test)."""
    L = ['ITEM %s' % it['item_id'], '', 'TASK', it['task_statement'], '', 'FILES']
    L += ['- ' + f for f in it['files']] + ['', 'ACCEPTABLE VARIANTS'] + ['- ' + v for v in it['acceptable_variants']]
    L += ['', 'PROPERTY CHECKS (a correct result passes all of them)'] + ['- ' + c for c in it['property_checks'] or ['(none listed)']]
    L += ['', 'PROGRAM', '```python', it['program'].rstrip('\n'), '```', '', it['legend'], '']
    for side in ('A', 'B'):
        r = it['result_' + side]
        L.append('RESULT %s%s' % (side, (' (%d rows x %d columns)' % (r['shape']['rows'], r['shape']['columns'])) if r['shape'] else ''))
        L += [r['table'], 'Summary of every column of result %s:' % side] + ['  ' + x for x in r['summary']] + ['']
    L.append('DIFFERENCES BETWEEN A AND B (%d in total%s)' % (it['n_differences'], ', first %d listed' % MAX_DIFF_LIST
                                                               if it['n_differences'] > MAX_DIFF_LIST else ''))
    for d in it['differences']:
        L.append('- row %s, column %s: A = %s ; B = %s' % (d['row'] if d['row'] is not None else '-', d['column'] if d['column'] is not None else '-',
                                                          d['A'], d['B']))
    return '\n'.join(L)


CSS = ('body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:16px;max-width:1100px;color:#111;background:#fff}'
       'h1{font-size:20px}h2{font-size:16px;margin-top:22px}pre{background:#f4f4f4;padding:8px;overflow-x:auto;font-size:12px}'
       'table{border-collapse:collapse;font-size:12px;display:block;overflow-x:auto}td,th{border:1px solid #ccc;padding:2px 6px;'
       'white-space:nowrap}th{background:#eee}mark{background:#ffd54f;font-weight:600}.rn{color:#777}.gap td{color:#777;font-style:italic}'
       '.ix{font-size:10px;color:#555}.codes li{margin:2px 0}')


def item_html(it, codes_help):
    e = html.escape
    H = ['<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
         '<title>Coding item %s</title><style>%s</style></head><body>' % (e(it['item_id']), CSS),
         '<h1>Coding item %s</h1>' % e(it['item_id']),
         '<h2>Task</h2><p>%s</p>' % e(it['task_statement']),
         '<h2>Files</h2><ul>%s</ul>' % ''.join('<li>%s</li>' % e(f) for f in it['files']),
         '<h2>Acceptable variants</h2><ul>%s</ul>' % ''.join('<li>%s</li>' % e(v) for v in it['acceptable_variants']),
         '<h2>Property checks</h2><p>A correct result passes all of them.</p><ul>%s</ul>' % (
             ''.join('<li>%s</li>' % e(c) for c in it['property_checks']) or '<li>(none listed)</li>'),
         '<h2>Program</h2><pre>%s</pre>' % e(it['program']),
         '<p>%s</p>' % e(it['legend'])]
    for side in ('A', 'B'):
        r = it['result_' + side]
        sh = (' (%d rows &times; %d columns)' % (r['shape']['rows'], r['shape']['columns'])) if r['shape'] else ''
        H.append('<h2>Result %s%s</h2>%s' % (side, sh, it['_html'][side]))
        if r['summary']:
            H.append('<p>Summary of every column:</p><ul>%s</ul>' % ''.join('<li>%s</li>' % e(x) for x in r['summary']))
    H.append('<h2>Differences between A and B (%d%s)</h2><ul>%s</ul>' % (it['n_differences'], ', first %d listed' % MAX_DIFF_LIST
                                                                       if it['n_differences'] > MAX_DIFF_LIST else '', ''.join(
        '<li>row %s, column %s: A = %s ; B = %s</li>' % (e(str(d['row'] if d['row'] is not None else '-')),
                                                         e(str(d['column'] if d['column'] is not None else '-')), e(str(d['A'])), e(str(d['B'])))
        for d in it['differences'])))
    H.append('<h2>Your code</h2><p>Enter one code for this item in the answer sheet (CSV):</p><ul class="codes">%s</ul>' % ''.join(
        '<li><b>%s</b>: %s</li>' % (e(c), e(t)) for c, t in codes_help))
    H.append('</body></html>')
    return '\n'.join(H)


CODES_HELP = [('A_ONLY_CORRECT', 'result A is a correct answer to the task and result B is not'),
              ('B_ONLY_CORRECT', 'result B is a correct answer to the task and result A is not'),
              ('BOTH_ACCEPTABLE', 'both results are correct answers (the difference is allowed by the task and the acceptable variants)'),
              ('NEITHER', 'neither result is a correct answer'),
              ('UNDETERMINABLE', 'the information shown does not allow a decision')]


def assert_blind(it):
    """Guard: harness-authored parts of an item carry no version, environment or design label."""
    authored = [it['legend']] + it['acceptable_variants'] + it['property_checks'] + [str(it['result_A']['shape']), str(it['result_B']['shape'])]
    authored += [re.sub(r'(most common: |, min |, max ).*$', '', x) for x in it['result_A']['summary'] + it['result_B']['summary']]
    for s in authored:
        m = FORBIDDEN_RE.search(s or '')
        if m:
            raise ValueError('blindness guard: %r in harness-authored text of item %s' % (m.group(0), it['item_id']))


def assign(program_ids, seed=SEED):
    """Seeded item order and A/B assignment: [(item_id, program_id, a_is_base)]; ids C0001... in shuffled order."""
    pids = sorted(program_ids)
    rng = random.Random(seed)
    rng.shuffle(pids)
    return [('C%04d' % (i + 1), pid, rng.random() < 0.5) for i, pid in enumerate(pids)]


def write_items(entries, out_dir, key_path, seed=SEED, double_ids=(), base_label='E0a', target_label='E1', meta=None):
    """entries: [{'program_id', 'task', 'program_text', 'base', 'target', 'weight', 'cell'}]. Writes the human form (items/*.html,
    INDEX.html, answers_coderA.csv, answers_coderB.csv), the machine form (machine/items*.jsonl, machine/prompts/*.txt) and the key."""
    by = {e['program_id']: e for e in entries}
    plan = assign(by, seed)
    if os.path.abspath(key_path).startswith(os.path.abspath(out_dir) + os.sep):
        raise ValueError('the key file must not be inside the coders\' folder')
    for sub in ('items', 'machine', os.path.join('machine', 'prompts')):
        os.makedirs(os.path.join(out_dir, sub), exist_ok=True)
    template = _read(PROMPT_PATH) if os.path.exists(PROMPT_PATH) else None
    key = {'schema': 'harm_key/1', 'created': now_iso(), 'seed': seed, 'note': 'NEVER give this file to a coder.', 'meta': meta or {},
           'items': {}}
    items = []
    for item_id, pid, a_is_base in plan:
        e = by[pid]
        ra, rb = (e['base'], e['target']) if a_is_base else (e['target'], e['base'])
        it = make_item(item_id, e['task'], e['program_text'], ra, rb)
        assert_blind(it)
        items.append(it)
        key['items'][item_id] = {'program_id': pid, 'A': base_label if a_is_base else target_label,
                                 'B': target_label if a_is_base else base_label, 'weight': e.get('weight', 1.0), 'cell': e.get('cell'),
                                 'double_coded': pid in set(double_ids)}
        with open(os.path.join(out_dir, 'items', item_id + '.html'), 'w', encoding='utf-8') as f:
            f.write(item_html(it, CODES_HELP))
        if template:
            with open(os.path.join(out_dir, 'machine', 'prompts', item_id + '.txt'), 'w', encoding='utf-8') as f:
                f.write(render_prompt(template, it))
    dbl = [it for it in items if key['items'][it['item_id']]['double_coded']]
    for name, subset in (('items.jsonl', items), ('items_coderB.jsonl', dbl)):
        with open(os.path.join(out_dir, 'machine', name), 'w', encoding='utf-8') as f:
            for it in subset:
                f.write(json.dumps({k: v for k, v in it.items() if not k.startswith('_')}, ensure_ascii=False) + '\n')
    for name, subset in (('answers_coderA.csv', items), ('answers_coderB.csv', dbl)):
        with open(os.path.join(out_dir, name), 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            w.writerow(['item_id', 'code', 'note'])
            for it in subset:
                w.writerow([it['item_id'], '', ''])
    with open(os.path.join(out_dir, 'INDEX.html'), 'w', encoding='utf-8') as f:
        f.write('<!doctype html><html><head><meta charset="utf-8"><title>Coding items</title><style>%s</style></head><body>' % CSS)
        f.write('<h1>Coding items (%d)</h1><p>Codes: %s. Answer sheets: answers_coderA.csv (all items), answers_coderB.csv '
                '(second coder, %d items).</p><ul>' % (len(items), ', '.join(c for c, _ in CODES_HELP), len(dbl)))
        for it in items:
            f.write('<li><a href="items/%s.html">%s</a>%s</li>' % (it['item_id'], it['item_id'],
                                                                     ' (second coder)' if key['items'][it['item_id']]['double_coded'] else ''))
        f.write('</ul></body></html>')
    os.makedirs(os.path.dirname(os.path.abspath(key_path)), exist_ok=True)
    with open(key_path, 'w', encoding='utf-8') as f:
        json.dump(key, f, indent=1, ensure_ascii=False)
    return items, key


# ================================================================================================ LLM coder (machine form)
def render_prompt(template, it):
    if '{{ITEM}}' not in template:
        raise ValueError('PROMPT template has no {{ITEM}} placeholder')
    return template.replace('{{ITEM}}', item_text(it)).replace('{{ITEM_ID}}', it['item_id'])


def validate_answer(obj):
    """Errors of one coder answer against harm/coder_llm/answer.schema.json (implemented here without a JSON-Schema library)."""
    errs = []
    if not isinstance(obj, dict):
        return ['answer is not a JSON object']
    extra = set(obj) - {'item_id', 'code', 'reason'}
    if extra:
        errs.append('unexpected keys %s' % sorted(extra))
    if not isinstance(obj.get('item_id'), str) or not re.match(r'^C\d{4}$', obj.get('item_id') or ''):
        errs.append('item_id must look like C0001')
    if obj.get('code') not in CODER_CODES:
        errs.append('code must be one of %s' % (CODER_CODES,))
    if not isinstance(obj.get('reason'), str) or not (1 <= len(obj.get('reason') or '') <= 600):
        errs.append('reason must be a string of 1-600 characters')
    return errs


def study_vendors(models_tsv=os.path.join(STUDY, 'models', 'models.tsv'), extra_models=()):
    """Vendor prefixes (the part before '/') of the study models (models.tsv rows selected=yes, plus substitutes in extra_models)."""
    vend = set()
    with open(models_tsv, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if (r.get('selected') or '').strip().lower() == 'yes':
                vend.add(r['openrouter_id'].split('/')[0])
    vend.update(m.split('/')[0] for m in extra_models)
    return vend


def outside_study_set(model_id, models_tsv=os.path.join(STUDY, 'models', 'models.tsv'), extra_models=()):
    """Section 10.4: an LLM coder B must come from a model family outside the study set; operationalised as a vendor prefix that no
    study model (or substitute actually used) has. True/False."""
    return model_id.split('/')[0] not in study_vendors(models_tsv, extra_models)


# ================================================================================================ decode (after coding)
def map_code(code, a_label, b_label, base_label='E0a'):
    """Coder code -> harm code: 'only the 2.x result correct' = HARM_3X, 'only the 3.x result correct' = FIX_3X."""
    if code not in CODER_CODES:
        raise ValueError('unknown coder code %r' % code)
    if code == 'A_ONLY_CORRECT':
        return 'HARM_3X' if a_label == base_label else 'FIX_3X'
    if code == 'B_ONLY_CORRECT':
        return 'HARM_3X' if b_label == base_label else 'FIX_3X'
    return code


def read_answers(path):
    if path.endswith('.csv'):
        with open(path, encoding='utf-8') as f:
            return [{'item_id': r['item_id'].strip(), 'code': r['code'].strip(), 'reason': r.get('note', '')} for r in csv.DictReader(f)
                    if (r.get('code') or '').strip()]
    out = []
    with open(path, encoding='utf-8') as f:
        txt = f.read().strip()
    objs = json.loads(txt) if txt.startswith('[') else [json.loads(ln) for ln in txt.splitlines() if ln.strip()]
    for o in objs:
        errs = validate_answer(o)
        if errs:
            raise ValueError('invalid answer %r: %s' % (o, '; '.join(errs)))
        out.append(o)
    return out


def decode(answers, key, coder=''):
    rows = []
    for a in answers:
        k = key['items'].get(a['item_id'])
        if k is None:
            raise ValueError('item %s not in key' % a['item_id'])
        rows.append({'program_id': k['program_id'], 'code': map_code(a['code'], k['A'], k['B']), 'weight': k.get('weight', 1.0),
                     'coder': coder, 'coder_code': a['code'], 'item_id': a['item_id']})
    return rows


# ================================================================================================ building from study files
def _load_json_any(path):
    op = gzip.open if path.endswith('.gz') else open
    with op(path, 'rt', encoding='utf-8') as f:
        return json.load(f)


def load_record(runs_root, run_config, pid):
    try:
        import run_programs
        return run_programs.load_record(runs_root, run_config, pid)
    except ImportError:
        p = os.path.join(runs_root, run_config, pid + '.json.gz')
        if not os.path.exists(p):
            return None
        rec = _load_json_any(p)
        if rec.get('result_path'):
            rec.update(_load_json_any(os.path.join(runs_root, rec['result_path'])))
        return rec


def load_tasks(path):
    d = json.loads(_read(path))
    return {t['id']: t for t in (d['tasks'] if isinstance(d, dict) else d)}


def build_entries(sample_rows, runs_root, tasks, gen_dir, pair='E0a~E1'):
    base, target = pair.split('~')
    out = []
    for s in sample_rows:
        pid = s['program_id']
        rel = pid[len('gen/'):] if pid.startswith('gen/') else pid
        src_path = os.path.join(gen_dir, rel + '.py')
        program_text = _read(src_path, 'replace') if os.path.exists(src_path) else ''
        out.append({'program_id': pid, 'task': tasks[s['task_id']], 'program_text': program_text,
                    'base': load_record(runs_root, base, pid), 'target': load_record(runs_root, target, pid),
                    'weight': float(s.get('weight') or 1.0), 'cell': s.get('cell')})
    return out, base, target


def _abs(p):
    return p if os.path.isabs(p) else os.path.join(STUDY, p)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cmds = ('sample', 'double', 'build', 'render', 'decode')
    if not argv or argv[0] not in cmds:
        argv = ['build'] + argv
    ap = argparse.ArgumentParser(description='Blind A/B harm-coding sheets (ATTRIB_HARM).')
    sp = ap.add_subparsers(dest='cmd')
    a = sp.add_parser('sample')
    a.add_argument('--per-program', required=True)
    a.add_argument('--out', required=True)
    a.add_argument('--pair', default='E0a~E1')
    a.add_argument('--n-max', type=int, default=400)
    a.add_argument('--seed', type=int, default=SEED)
    a = sp.add_parser('double')
    a.add_argument('--sample', required=True)
    a.add_argument('--out', required=True)
    a.add_argument('--share', type=float, default=0.25)
    a.add_argument('--n-min', type=int, default=80)
    a.add_argument('--exclude')
    a.add_argument('--seed', type=int, default=SEED)
    a = sp.add_parser('build')
    a.add_argument('--per-program', required=True)
    a.add_argument('--runs', required=True)
    a.add_argument('--tasks', required=True)
    a.add_argument('--out', required=True)
    a.add_argument('--key', default='harm/_private/sheet_key.json')
    a.add_argument('--sample')
    a.add_argument('--double')
    a.add_argument('--gen-dir', default='generations')
    a.add_argument('--pair', default='E0a~E1')
    a.add_argument('--seed', type=int, default=SEED)
    a = sp.add_parser('render')
    a.add_argument('--specs', required=True)
    a.add_argument('--out', required=True)
    a.add_argument('--key', required=True)
    a.add_argument('--seed', type=int, default=SEED)
    a = sp.add_parser('decode')
    a.add_argument('--answers', required=True)
    a.add_argument('--key', required=True)
    a.add_argument('--out', required=True)
    a.add_argument('--coder', default='')
    o = ap.parse_args(argv)

    if o.cmd == 'sample':
        pp = [json.loads(ln) for ln in _read(_abs(o.per_program)).splitlines() if ln.strip()]
        rows = coding_sample(drift_programs(pp, o.pair), o.n_max, o.seed)
        write_tsv(_abs(o.out), rows, SAMPLE_FIELDS)
        print('%d drift programs on %s; %d in the coding sample; sum of weights %.3f' % (len(drift_programs(pp, o.pair)), o.pair, len(rows),
                                                                                         sum(r['weight'] for r in rows)))
    elif o.cmd == 'double':
        rows = read_tsv(_abs(o.sample))
        for r in rows:
            r['weight'] = float(r['weight'])
            r['family'] = r.get('family') or None
        excl = [r['program_id'] for r in read_tsv(_abs(o.exclude))] if o.exclude else ()
        d = double_coding_sample(rows, o.share, o.n_min, o.seed, excl)
        write_tsv(_abs(o.out), d, SAMPLE_FIELDS + ['double_weight'])
        print('%d coded; %d in the double-coding sample' % (len(rows), len(d)))
    elif o.cmd == 'build':
        pp = [json.loads(ln) for ln in _read(_abs(o.per_program)).splitlines() if ln.strip()]
        rows = read_tsv(_abs(o.sample)) if o.sample else coding_sample(drift_programs(pp, o.pair), 400, o.seed)
        dbl = [r['program_id'] for r in read_tsv(_abs(o.double))] if o.double else ()
        entries, base, target = build_entries(rows, _abs(o.runs), load_tasks(_abs(o.tasks)), _abs(o.gen_dir), o.pair)
        items, _ = write_items(entries, _abs(o.out), _abs(o.key), o.seed, dbl, base, target,
                               meta={'pair': o.pair, 'per_program': o.per_program})
        print('%d items written to %s (%d for the second coder); key: %s' % (len(items), o.out, len(dbl), o.key))
    elif o.cmd == 'render':
        spec = json.loads(_read(_abs(o.specs)))
        entries = []
        for s in spec['items']:
            rec = lambda p: _load_json_any(_abs(p))
            entries.append({'program_id': s['source_id'], 'task': s['task'],
                            'program_text': _read(_abs(s['program_path']), 'replace'),
                            'base': rec(s['base_record']), 'target': rec(s['target_record']), 'weight': s.get('weight', 1.0),
                            'cell': s.get('cell')})
        items, _ = write_items(entries, _abs(o.out), _abs(o.key), o.seed, [e['program_id'] for e in entries],
                               spec.get('base_label', 'E0a'), spec.get('target_label', 'E1'), meta={'specs': o.specs})
        print('%d items written to %s; key: %s' % (len(items), o.out, o.key))
    elif o.cmd == 'decode':
        key = json.loads(_read(_abs(o.key)))
        rows = decode(read_answers(_abs(o.answers)), key, o.coder)
        write_tsv(_abs(o.out), rows, ['program_id', 'code', 'weight', 'coder', 'coder_code', 'item_id'])
        print('%d codes written to %s: %s' % (len(rows), o.out, dict(collections.Counter(r['code'] for r in rows))))
    return 0


if __name__ == '__main__':
    sys.exit(main())
