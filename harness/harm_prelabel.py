# ATTRIB_HARM: reference-based automatic harm pre-label (FULL_PREREG section 10.2; STAGE2 T5.7; CONVENTIONS sections 5.2, 5.4, 12).
# Written 2026-11-11 by pkg:ATTRIB_HARM (drafted_by: pkg:ATTRIB_HARM; status: prepared).
# Standard library only. Pure functions on canonical results ({'result', 'result_dt', 'result_type'}, as run_programs.load_record returns
# them) and task cards (task.json dicts).
#
# harm_prelabel(e0a, target, reference, card): each of the 2.x (E0a) and 3.x (target) results is "acceptable" when it matches the
# reference under the card's acceptable variants AND passes every property check; then
#   only E0a acceptable -> HARM_3X; only target -> FIX_3X; both -> BOTH_ACCEPTABLE; neither -> NEITHER;
#   comparison impossible -> UNDETERMINABLE (no card, reference missing / not ok / failing its own property checks, a result whose
#   canonical form has no table reading, e.g. an opaque object).
# A side whose run did not complete with a result (LOUD, no_result) is not acceptable.
#
# Acceptable variants implemented (section 10.1, CONVENTIONS 5.2):
#   row_order 'any' -> rows compared as multisets; 'ties_only' -> rows in order, permutations only among rows with equal sort-key tuples
#     (keys not found -> the exact order is required);
#   label_spelling -> column/index labels match ignoring case, spaces and underscores;
#   missing_value_representation -> NaN/None/pd.NA/NaT (already null in the canonical form) and the empty string are the same;
#   rounding_sig_digits (6) -> numbers compared after rounding to that many significant digits; bool compared as 0/1;
#   representation (always): an unnamed default 0..n-1 row index is ignored; a named or non-default index counts as key column(s), so
#     "the key may be the index instead of a column" holds; unnamed columns pair with the remaining reference columns in order;
#     timestamps/dates compare as ISO text with a 'T00:00:00' time dropped (a date as datetime or as 'YYYY-MM-DD' text is the same).
import math, re

CODES = ('HARM_3X', 'FIX_3X', 'BOTH_ACCEPTABLE', 'NEITHER', 'UNDETERMINABLE')
NULL_TEXT = ('nan', 'None', 'NaT', '<NA>')
DEFAULT_VARIANTS = {'row_order': 'any', 'label_spelling': True, 'missing_value_representation': True, 'rounding_sig_digits': 6}


class NotComparable(Exception):
    pass


# ------------------------------------------------------------------------------------------------ table view of a canonical result
class Table:
    """labels: one label per column (None = unnamed); rows: list of row lists; n_index: leading columns that came from the index;
    kind: 'dataframe' | 'series' | 'index' | 'scalar' | 'other'."""

    def __init__(self, labels, rows, n_index, kind):
        self.labels, self.rows, self.n_index, self.kind = labels, rows, n_index, kind

    def column(self, j):
        return [r[j] for r in self.rows]

    def __repr__(self):
        return 'Table(%s, %d rows, n_index=%d, %s)' % (self.labels, len(self.rows), self.n_index, self.kind)


def _canon(x):
    """Canonical value of a run record / result file / bare canonical value."""
    if isinstance(x, dict) and 'result' in x and 'k' not in x:
        return x.get('result')
    return x


def _is_default_index(idx, names):
    return all(n is None for n in (names or [None])) and list(idx) == list(range(len(idx)))


def _index_columns(idx, names):
    """(labels, columns) of a row index; MultiIndex entries are lists."""
    n = len(idx)
    if n and all(isinstance(v, list) for v in idx):
        depth = max(len(v) for v in idx)
        names = list(names or []) + [None] * depth
        return names[:depth], [[(v[k] if k < len(v) else None) for v in idx] for k in range(depth)]
    nm = (names or [None])[0] if names else None
    return [nm], [list(idx)]


def _label(c):
    if isinstance(c, list):
        return '|'.join('' if x is None else str(x) for x in c)
    return c


def to_table(value):
    v = _canon(value)
    if not isinstance(v, dict) or 'k' not in v:
        if isinstance(v, (dict, list)):
            raise NotComparable('unsupported canonical value')
        if isinstance(v, str) and (v.startswith('OBJ:') or v == '<deep>'):
            raise NotComparable('opaque object result')
        return Table([None], [[v]], 0, 'scalar')
    k = v.get('k')
    if k == 'df':
        idx, names = v.get('index') or [], v.get('index_names')
        labels, cols = [], []
        n_index = 0
        if not _is_default_index(idx, names):
            il, ic = _index_columns(idx, names)
            labels += il
            cols += ic
            n_index = len(il)
        labels += [_label(c) for c in v.get('columns') or []]
        cols += [list(c) for c in v.get('data') or []]
        n = len(idx)
        return Table(labels, [[c[r] for c in cols] for r in range(n)], n_index, 'dataframe')
    if k == 's':
        idx, names = v.get('index') or [], v.get('index_names')
        labels, cols, n_index = [], [], 0
        if not _is_default_index(idx, names):
            il, ic = _index_columns(idx, names)
            labels, cols, n_index = il, ic, len(il)
        labels.append(v.get('name'))
        cols.append(list(v.get('data') or []))
        return Table(labels, [[c[r] for c in cols] for r in range(len(idx))], n_index, 'series')
    if k == 'idx':
        return Table([v.get('name')], [[x] for x in v.get('data') or []], 0, 'index')
    if k == 'list':
        items = v.get('items') or []
        if any(isinstance(x, dict) and 'k' in x for x in items):
            raise NotComparable('list of pandas objects')
        return Table([None], [[x if not isinstance(x, list) else tuple(x)] for x in items], 0, 'other')
    if k == 'dict':
        items = v.get('items') or []
        if any(isinstance(x[1], dict) and 'k' in x[1] for x in items):
            return _dict_long_table(items)          # REPAIR6 (LR19 (3), review SF5): a dict holding a Series or other pandas object
        return Table([None, None], [[a, b] for a, b in items], 1, 'other')
    if k == 'nd':
        shape = v.get('shape') or []
        data = v.get('data') or []
        if len(shape) == 1:
            return Table([None], [[x] for x in data], 0, 'other')
        if len(shape) == 2:
            return Table([None] * (shape[1] if shape else 0), [list(r) for r in data], 0, 'other')
        raise NotComparable('array with %d dimensions' % len(shape))
    raise NotComparable('unknown canonical kind %r' % k)


# REPAIR6 2026-11-12 (lead ruling LR19 (3), review SF5; copy before: logs/repair6_2026-11-12/backup/harm_prelabel_before_repair6.py).
# A dict whose values include a pandas object (e.g. R_09: {"total": x, "row_count": n, "per_rider": <Series>}) was NotComparable, so its
# harm pre-label was UNDETERMINABLE and its property checks could not run. It is now read as a long table with two columns, the path of
# each leaf value and the value (kind 'other', one key column): a scalar item gives the path (key,); a Series gives (key, index label(s))
# per row (its name is not part of the path; a default index gives the row position); a DataFrame gives (key, row label(s) or position,
# column label) per cell; a dict gives (key, dict key) and is read recursively; a list, Index or 1-D array gives (key, position). Paths
# are tuples, so a Series indexed by rider_id and a dict keyed by rider_id give the same rows. A dict without pandas objects is read as
# before (two columns key, value), so no earlier pre-label changes.
def _leaves(prefix, x):
    if not (isinstance(x, dict) and 'k' in x):
        yield prefix, (tuple(x) if isinstance(x, list) else x)
        return
    k = x.get('k')
    if k in ('df', 's'):
        t = to_table(x)
        for pos, r in enumerate(t.rows):
            keys = tuple(_label(c) if isinstance(c, list) else c for c in r[:t.n_index]) if t.n_index else (pos,)
            if k == 's':
                yield from _leaves(prefix + keys, r[-1])
            else:
                for j in range(t.n_index, len(t.labels)):
                    yield from _leaves(prefix + keys + (t.labels[j],), r[j])
        return
    if k == 'dict':
        for a, b in x.get('items') or []:
            yield from _leaves(prefix + ((tuple(a) if isinstance(a, list) else a),), b)
        return
    if k in ('list', 'idx') or (k == 'nd' and len(x.get('shape') or []) == 1):
        for i, u in enumerate((x.get('items') if k == 'list' else x.get('data')) or []):
            yield from _leaves(prefix + (i,), u)
        return
    raise NotComparable('dict holding a %r object' % k)


def _dict_long_table(items):
    rows = []
    for a, b in items:
        for path, val in _leaves(((tuple(a) if isinstance(a, list) else a),), b):
            rows.append([path, val])
    return Table([None, None], rows, 1, 'other')


# ------------------------------------------------------------------------------------------------ value normal form
def _variants(card):
    out = dict(DEFAULT_VARIANTS)
    out.update((card or {}).get('acceptable_variants') or {})
    if (card or {}).get('order_significant'):
        out['row_order'] = 'ties_only'
    return out


def _round(x, digits):
    if x == 0 or math.isinf(x) or math.isnan(x):
        return float(x)
    return float('%.*g' % (digits, x))


def norm_value(x, var):
    if x is None:
        return None
    if isinstance(x, bool):
        return float(int(x))
    if isinstance(x, (int, float)):
        if isinstance(x, float) and math.isnan(x):
            return None
        return _round(float(x), int(var.get('rounding_sig_digits') or 6))
    if isinstance(x, str):
        if x == '' and var.get('missing_value_representation'):
            return None
        m = re.match(r'^(TS|D):(.*)$', x)
        if m:
            s = m.group(2)
            s = re.sub(r'T00:00:00(\.0+)?$', '', s)
            return 'DATE:' + s
        if re.match(r'^\d{4}-\d{2}-\d{2}$', x):
            return 'DATE:' + x
        if re.match(r'^\d{4}-\d{2}-\d{2}[T ]00:00:00$', x):
            return 'DATE:' + x[:10]
        return x
    if isinstance(x, (list, tuple)):
        return tuple(norm_value(u, var) for u in x)
    return str(x)


def _sort_key(row):
    return tuple((0, '') if v is None else ((1, v) if isinstance(v, float) else (2, str(v))) for v in row)


def label_key(lab, fuzzy):
    if lab is None:
        return None
    s = str(lab)
    return re.sub(r'[\s_]+', '', s).lower() if fuzzy else s


# ------------------------------------------------------------------------------------------------ matching
def _align_columns(tx, tref, fuzzy):
    """Column permutation p with tx column p[j] matching reference column j, or None."""
    if len(tx.labels) != len(tref.labels):
        return None
    kx = [label_key(l, fuzzy) for l in tx.labels]
    kr = [label_key(l, fuzzy) for l in tref.labels]
    used, perm = set(), [None] * len(kr)
    for j, k in enumerate(kr):
        if k is None:
            continue
        cand = [i for i, kk in enumerate(kx) if kk == k and i not in used]
        if cand:
            perm[j] = cand[0]
            used.add(cand[0])
    rest_x = [i for i in range(len(kx)) if i not in used]
    rest_r = [j for j in range(len(kr)) if perm[j] is None]
    if len(rest_x) != len(rest_r):
        return None
    if rest_r and not (all(kx[i] is None for i in rest_x) or all(kr[j] is None for j in rest_r)):
        return None
    for i, j in zip(rest_x, rest_r):
        perm[j] = i
    return perm


def _key_positions(tref, keys, fuzzy):
    out = []
    for key in keys or []:
        if key == '__index__':
            if tref.n_index == 0:
                return None
            out.extend(range(tref.n_index))
        elif key == '__values__':
            out.append(len(tref.labels) - 1)
        else:
            cand = [j for j, l in enumerate(tref.labels) if label_key(l, fuzzy) == label_key(key, fuzzy)]
            if len(cand) != 1:
                return None
            out.append(cand[0])
    return out or None


def _runs(rows, pos):
    """Consecutive runs of equal key tuples: [(key, [rows])]."""
    out = []
    for r in rows:
        k = tuple(r[p] for p in pos)
        if out and out[-1][0] == k:
            out[-1][1].append(r)
        else:
            out.append((k, [r]))
    return out


def matches_reference(canonical, reference, card):
    """True when `canonical` equals the reference result under the card's acceptable variants (see the module header).
    Raises NotComparable when either result has no table reading."""
    var = _variants(card)
    fuzzy = bool(var.get('label_spelling'))
    tx, tr = to_table(canonical), to_table(reference)
    if tx.kind == 'scalar' or tr.kind == 'scalar':
        if len(tx.rows) != 1 or len(tr.rows) != 1 or len(tx.labels) != 1 or len(tr.labels) != 1:
            return False
        return norm_value(tx.rows[0][0], var) == norm_value(tr.rows[0][0], var)
    perm = _align_columns(tx, tr, fuzzy)
    if perm is None or len(tx.rows) != len(tr.rows):
        return False
    rx = [[norm_value(r[perm[j]], var) for j in range(len(perm))] for r in tx.rows]
    rr = [[norm_value(v, var) for v in r] for r in tr.rows]
    if var.get('row_order') == 'ties_only':
        pos = _key_positions(tr, (card or {}).get('sort_keys'), fuzzy)
        if pos is None:
            return rx == rr
        ra, rb = _runs(rx, pos), _runs(rr, pos)
        if [k for k, _ in ra] != [k for k, _ in rb]:
            return False
        return all(sorted(a, key=_sort_key) == sorted(b, key=_sort_key) for (_, a), (_, b) in zip(ra, rb))
    return sorted(rx, key=_sort_key) == sorted(rr, key=_sort_key)


# ------------------------------------------------------------------------------------------------ property checks (CONVENTIONS 5.4)
def _target_cols(t, target, fuzzy):
    """Column indexes of a check target: a label, '__index__' (index columns) or '__values__' (Series values / scalar / single column)."""
    if target == '__index__':
        return list(range(t.n_index))
    if target == '__values__':
        return [len(t.labels) - 1] if t.labels else []
    hits = [j for j, l in enumerate(t.labels) if label_key(l, fuzzy) == label_key(target, fuzzy)]
    return hits


def _values(t, cols):
    return [r[j] for r in t.rows for j in cols]


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and not (isinstance(x, float) and math.isnan(x))


_YEAR = re.compile(r'^(?:TS:|D:)?(-?\d{4})-\d{2}-\d{2}')


def _year(x):
    if isinstance(x, str):
        m = _YEAR.match(x.strip())
        if m:
            return int(m.group(1))
    return None


def _flat(v):
    if isinstance(v, (list, tuple)):
        for u in v:
            yield from _flat(u)
    else:
        yield v


def _cmp(a, b):
    """-1/0/1 for two non-missing values (numbers numerically, everything else as text)."""
    if _num(a) and _num(b):
        return (a > b) - (a < b)
    a, b = str(a), str(b)
    return (a > b) - (a < b)


def _pairs_sorted(rows, pos, asc):
    """Rows sorted by the key columns (ties in any order; missing values last, as pandas na_position='last')."""
    for i in range(1, len(rows)):
        for p, up in zip(pos, asc):
            x, y = rows[i - 1][p], rows[i][p]
            if x is None and y is None:
                continue
            if x is None:
                return False
            if y is None:
                break
            c = _cmp(x, y)
            if c == 0:
                continue
            if (c > 0) == bool(up):
                return False
            break
    return True


def check_properties(canonical, property_checks, card):
    """Failed checks of `canonical` as [{'check', 'detail'}] (empty = all pass). A check whose target column is absent fails."""
    var = _variants(card)
    fuzzy = bool(var.get('label_spelling'))
    t = to_table(canonical)
    failed = []

    def fail(name, detail):
        failed.append({'check': name, 'detail': detail})

    def cols_or_fail(name, targets):
        out = []
        for tg in targets:
            c = _target_cols(t, tg, fuzzy)
            if not c:
                fail(name, 'target %r not found' % (tg,))
                return None
            out.extend(c)
        return out

    for chk in property_checks or []:
        name, args = chk.get('check'), chk.get('args') or {}
        if name == 'no_null_text':
            bad = [x for x in list(_flat([r for r in t.rows])) + [l for l in t.labels if l is not None]
                   if isinstance(x, str) and x.strip() in NULL_TEXT]
            if bad:
                fail(name, '%d value(s)/label(s) are null text, e.g. %r' % (len(bad), bad[0]))
        elif name == 'no_all_missing_column':
            if t.kind != 'scalar' and t.rows:
                empty = [t.labels[j] for j in range(t.n_index, len(t.labels)) if all(r[j] is None for r in t.rows)]
                if empty:
                    fail(name, 'all-missing column(s) %r' % (empty,))
        elif name == 'date_year_in_range':
            cols = cols_or_fail(name, args.get('columns') or [])
            if cols is not None:
                bad = [x for x in _values(t, cols) if _year(x) is not None and not (args['min_year'] <= _year(x) <= args['max_year'])]
                if bad:
                    fail(name, '%d date(s) outside %s-%s, e.g. %r' % (len(bad), args['min_year'], args['max_year'], bad[0]))
        elif name == 'counts_sum_to_rows':
            cols = cols_or_fail(name, [args.get('column')])
            if cols is not None:
                vals = [x for x in _values(t, cols) if x is not None]
                if any(not _num(x) for x in vals):
                    fail(name, 'non-numeric count')
                elif not math.isclose(sum(vals), args['expected'], rel_tol=0, abs_tol=1e-9):
                    fail(name, 'sum %r != %r' % (sum(vals), args['expected']))
        elif name == 'rate_in_unit_interval':
            cols = cols_or_fail(name, args.get('columns') or [])
            if cols is not None:
                bad = [x for x in _values(t, cols) if x is not None and (not _num(x) or not (0 <= x <= 1))]
                if bad:
                    fail(name, '%d value(s) not a number in [0, 1], e.g. %r' % (len(bad), bad[0]))
        elif name == 'n_groups_equals':
            n = 1 if t.kind == 'scalar' else len(t.rows)
            if n != args.get('n'):
                fail(name, '%d rows, expected %r' % (n, args.get('n')))
        elif name == 'no_nulls':
            targets = args.get('columns') or []
            cols = cols_or_fail(name, targets) if targets else list(range(len(t.labels)))
            if cols is not None:
                k = sum(1 for x in _values(t, cols) if x is None)
                if k:
                    fail(name, '%d missing value(s)' % k)
        elif name == 'numeric_in_range':
            cols = cols_or_fail(name, args.get('columns') or [])
            if cols is not None:
                lo, hi = args.get('min'), args.get('max')
                bad = [x for x in _values(t, cols) if x is not None and
                       (not _num(x) or (lo is not None and x < lo) or (hi is not None and x > hi))]
                if bad:
                    fail(name, '%d value(s) outside [%r, %r], e.g. %r' % (len(bad), lo, hi, bad[0]))
        elif name == 'values_in_set':
            cols = cols_or_fail(name, [args.get('column')])
            if cols is not None:
                allowed = set(args.get('values') or [])
                bad = [x for x in _values(t, cols) if x is not None and x not in allowed]
                if bad:
                    fail(name, '%d value(s) not in the set, e.g. %r' % (len(bad), bad[0]))
        elif name == 'columns_present':
            have = {label_key(l, fuzzy) for l in t.labels if l is not None}
            miss = [c for c in args.get('columns') or [] if label_key(c, fuzzy) not in have]
            if miss:
                fail(name, 'missing column(s) %r' % (miss,))
        elif name == 'result_kind':
            if t.kind != args.get('kind'):
                fail(name, 'kind %s, expected %s' % (t.kind, args.get('kind')))
        elif name == 'sorted_by':
            keys = args.get('keys') or []
            asc = list(args.get('ascending') or [True] * len(keys))
            pos = []
            for k in keys:
                c = _target_cols(t, k, fuzzy)
                if not c:
                    fail(name, 'key %r not found' % (k,))
                    pos = None
                    break
                pos.append(c[0])
            if pos is not None and not _pairs_sorted(t.rows, pos, asc):
                fail(name, 'rows not sorted by %r' % (keys,))
        else:
            fail(str(name), 'unknown check')
    return failed


# ------------------------------------------------------------------------------------------------ pre-label
def _ok(rec):
    if rec is None:
        return False
    st = rec.get('status') if isinstance(rec, dict) else None
    return st in (None, 'ok') and (not isinstance(rec, dict) or 'result' in rec)


def _side(rec, ref, card):
    """(acceptable: bool, detail dict); raises NotComparable."""
    if not _ok(rec):
        return False, {'status': (rec or {}).get('status')}
    m = matches_reference(rec, ref, card)
    failed = check_properties(rec, (card or {}).get('property_checks') or [], card)
    return (m and not failed), {'matches_reference': m, 'failed_checks': failed}


def harm_prelabel(e0a, target, reference, card):
    """-> {'label', 'e0a_ok', 'target_ok', 'failed': {...}} (INTERFACES.md section 4)."""
    out = {'label': 'UNDETERMINABLE', 'e0a_ok': None, 'target_ok': None, 'failed': {}}
    if not card:
        out['failed']['reason'] = 'no specification card'
        return out
    if not _ok(reference):
        out['failed']['reason'] = 'reference result unavailable'
        return out
    try:
        to_table(reference)
        ref_failed = check_properties(reference, card.get('property_checks') or [], card)
        if ref_failed:
            out['failed']['reason'] = 'reference fails its own property checks'
            out['failed']['reference'] = ref_failed
            return out
        a_ok, a_det = _side(e0a, reference, card)
        b_ok, b_det = _side(target, reference, card)
    except NotComparable as e:
        out['failed']['reason'] = 'not comparable: %s' % e
        return out
    out.update(e0a_ok=a_ok, target_ok=b_ok)
    out['failed'] = {'e0a': a_det, 'target': b_det}
    out['label'] = ('BOTH_ACCEPTABLE' if a_ok and b_ok else 'HARM_3X' if a_ok else 'FIX_3X' if b_ok else 'NEITHER')
    return out
