# HRUN: the oracle (FULL_PREREG section 3; STAGE2 T5.1, T5.7a). Written 2026-11-11 by pkg:HRUN. Standard library only.
# Copy-and-extend of the comparison layers of pilots/r3/harness/analyze.py (read-only there). Pure functions on run records whose
# canonical result is loaded under 'result', 'result_dt' and 'result_type' (runner_full / run_programs.load_record do that).
#
# Layers for baseline A against target B (first match wins; values: ints exact, floats rel 1e-11 or abs 1e-9, text exact, NaN/None/
# pd.NA/NaT all null in the canonical form; a completed run without `result` is drift):
#   IDENTICAL   values equal and dtypes and result class equal        DTYPE_ONLY  values equal (also treating bool as 0/1), dtype/class differ
#   ORDER_ONLY  equal as multisets of rows                            VALUE_DRIFT otherwise;  NO_RESULT: target completed without `result`
# Flags frozen on the card (section 3, review M2): order_significant (+ sort_keys): a row-order change that is not confined to ties of the
# keys is ORDER_DRIFT; dtype_significant: a dtype change is DTYPE_DRIFT. Unflagged: ORDER_ONLY / DTYPE_ONLY never drift. The pilot rule
# (order and dtype never drift) is returned as `class_pilot_rule`.
# Result types are compared by class name without module path (pilot CHANGES 23:47): pandas 3 reports 'pandas.DataFrame'.
import json, math, os, re, sys

HARNESS = os.path.dirname(os.path.abspath(__file__))
if HARNESS not in sys.path:
    sys.path.insert(0, HARNESS)
import configs as cfgmod
import warndef

REL, ABS = 1e-11, 1e-9
SMALL_REL = 1e-6                         # NUMERIC_SMALL threshold (section 3)
FAIL_LOUD = cfgmod.LOUD_STATUSES
DRIFT_CLASSES = ('ORDER_DRIFT', 'DTYPE_DRIFT', 'VALUE_DRIFT', 'NO_RESULT')
NO_CARD = {'order_significant': False, 'sort_keys': [], 'dtype_significant': False, 'label_spelling': True}


# ---------------------------------------------------------------- value equality (pilot eqv)
def isnum(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def eqv(a, b, loose):
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, bool) or isinstance(b, bool):
        if isinstance(a, bool) and isinstance(b, bool):
            return a == b
        if loose and (isnum(a) or isinstance(a, bool)) and (isnum(b) or isinstance(b, bool)):
            return math.isclose(float(a), float(b), rel_tol=REL, abs_tol=ABS)
        return False
    if isinstance(a, int) and isinstance(b, int):
        return a == b
    if isnum(a) and isnum(b):
        if math.isinf(a) or math.isinf(b):
            return a == b
        return math.isclose(a, b, rel_tol=REL, abs_tol=ABS)
    if isinstance(a, str) and isinstance(b, str):
        return a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(eqv(x, y, loose) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(eqv(a[k], b[k], loose) for k in a)
    return a == b


def canonical_equal(a, b, loose=False):
    """Value equality with the section 3 tolerances. Accepts canonical values or whole result records/files ({'result': ...})."""
    if isinstance(a, dict) and 'result' in a and 'k' not in a:
        a = a['result']
    if isinstance(b, dict) and 'result' in b and 'k' not in b:
        b = b['result']
    return eqv(a, b, loose)


# ---------------------------------------------------------------- unordered (multiset) equality
def _norm(x, digits=6):
    """Coarse normal form used only to ORDER rows for pairing; equality is then decided by eqv, not by this form."""
    if isinstance(x, bool):
        return int(x)
    if isinstance(x, float):
        if math.isinf(x) or math.isnan(x):
            return str(x)
        if x == int(x) and abs(x) < 1e15:
            return int(x)
        return float('%.*g' % (digits, x))
    if isinstance(x, list):
        return [_norm(u, digits) for u in x]
    return x


def _key(row):
    return json.dumps(_norm(row), default=str, sort_keys=True)


def rows_of(v):
    """(column keys, index labels, rows) with columns sorted by label, or None when the result has no row structure."""
    if not isinstance(v, dict):
        return None
    k = v.get('k')
    if k == 'df':
        cols = v['columns']
        order = sorted(range(len(cols)), key=lambda i: _key(cols[i]))
        idx = v['index']
        return ([_key(cols[i]) for i in order], idx, [[v['data'][i][r] for i in order] for r in range(len(idx))])
    if k == 's':
        return ([_key(v['name'])], v['index'], [[x] for x in v['data']])
    if k == 'idx':
        return (['_'], list(range(len(v['data']))), [[x] for x in v['data']])
    if k == 'list':
        return (['_'], list(range(len(v['items']))), [[x] for x in v['items']])
    if k == 'dict':
        return (['_'], [_key(kk) for kk, _ in v['items']], [[x] for _, x in v['items']])
    if k == 'nd' and len(v.get('shape', [])) == 1:
        return (['_'], list(range(len(v['data']))), [[x] for x in v['data']])
    return None


def _multiset_equal(rows_a, rows_b):
    if len(rows_a) != len(rows_b):
        return False
    sa, sb = sorted(rows_a, key=_key), sorted(rows_b, key=_key)
    return all(eqv(x, y, True) for x, y in zip(sa, sb))


def eq_unordered(a, b):
    ra, rb = rows_of(a), rows_of(b)
    if ra is None or rb is None or ra[0] != rb[0] or len(ra[1]) != len(rb[1]):
        return False
    if _multiset_equal([[i] + r for i, r in zip(ra[1], ra[2])], [[i] + r for i, r in zip(rb[1], rb[2])]):
        return True
    n = len(ra[1])
    rng = list(range(n))
    if ra[1] == rng and rb[1] == rng:            # default 0..n-1 index on both sides: ignore it
        return _multiset_equal(ra[2], rb[2])
    return False


# ---------------------------------------------------------------- tie-aware order (card sort_keys)
def _lab(x):
    return str(x)


def _lab_fuzzy(x):
    return re.sub(r'[\s_]+', '', str(x)).lower()


# REPAIR5 2026-11-11 (lead ruling LR1, FULL_PREREG_AMENDMENT_10.md; clarifies Amendment 3; review RV-2, RV-14). Copy before:
# logs/repair5_2026-11-11/backup/oracle_before.py. Row identity in the order rule:
#  1. a named key is looked up first among the result's column labels, then among the names of its index levels, with the card's
#     label-spelling tolerance (exact label first; with tolerance also a unique match ignoring case, spaces and underscores). Found in
#     neither: None (HRUN H1 stays: any change of row order is ORDER_DRIFT). A Series is a one-column table whose column label is its
#     name (as in rows_of below).
#  2. '__index__' = the index labels; if the index of EITHER result is a default position index (0..n-1 in steps of 1, one level),
#     which carries no identity, the key is the whole row (all values of the row, compared with the registered value tolerance). For a
#     result that is not a table or a Series, the key is the element at each position (a dict: its (key, value) item).
#  3. '__values__' is unchanged.
def is_default_index(v):
    """True for a DataFrame/Series whose single-level index is exactly 0, 1, ..., n-1 (a default position index)."""
    if not isinstance(v, dict) or v.get('k') not in ('df', 's'):
        return False
    if len(v.get('index_names') or [None]) != 1:
        return False
    idx = v.get('index') or []
    return all(isinstance(x, int) and not isinstance(x, bool) and x == i for i, x in enumerate(idx))


def _find_label(labels, key, tolerant):
    """Position of `key` among `labels`: exact match on the label text first; with tolerance, else the unique match ignoring case,
    spaces and underscores. -> (position, None), or (None, 'absent') / (None, 'ambiguous')."""
    for i, c in enumerate(labels):
        if c is not None and _lab(c) == _lab(key):
            return i, None
    if not tolerant:
        return None, 'absent'
    cand = [i for i, c in enumerate(labels) if c is not None and _lab_fuzzy(c) == _lab_fuzzy(key)]
    if len(cand) == 1:
        return cand[0], None
    return None, ('ambiguous' if cand else 'absent')


def _locate_named(v, key, tolerant):
    """Where a named key sits in a DataFrame or Series (LR1.1): ('col', position in v['columns']) or ('idx', index level), or None."""
    if not isinstance(v, dict):
        return None
    k = v.get('k')
    if k == 'df':
        cols = v['columns']
    elif k == 's':
        cols = [v.get('name')]
    else:
        return None
    i, why = _find_label(cols, key, tolerant)
    if i is not None:
        return ('col', i)
    if why == 'ambiguous':
        return None
    names = v.get('index_names') or [None]
    j, _ = _find_label(names, key, tolerant)
    return None if j is None else ('idx', j)


def _getter_at(v, loc):
    """Getter (row position -> key value) for a location from _locate_named, or None if `v` has no such column / index level."""
    k = v.get('k')
    data = v['data'] if k == 'df' else [v['data']]
    kind, p = loc
    if kind == 'col':
        return (lambda r, p=p: data[p][r]) if p < len(data) else None
    names = v.get('index_names') or [None]
    if p >= len(names):
        return None
    idx = v['index']
    if len(names) == 1:
        return lambda r: idx[r]
    return lambda r, p=p: (idx[r][p] if isinstance(idx[r], list) and p < len(idx[r]) else None)


def _named_getter(v, key, tolerant, loc=None):
    """Getter (row position -> key value) for a named key of a DataFrame or Series, or None if it cannot be located (LR1.1).
    `loc` (REPAIR5 fixes MF3): a location taken from the other result, used when this result does not name the key."""
    if loc is None:
        loc = _locate_named(v, key, tolerant)
    return None if loc is None else _getter_at(v, loc)


def _whole_rows(v):
    """All values of each row (columns in label order, as rows_of), for the identity key on a default position index."""
    ro = rows_of(v)
    return ro[2] if ro is not None else None


def key_sequence(v, keys, whole_row=False, tolerant=True, locs=None):
    """Per-row key tuples of a canonical result for the card's sort_keys, or None if a key cannot be found.
    Keys: a named key (column label, then index level name; LR1.1), '__index__' (index labels; the whole row when `whole_row`, i.e. when
    either result has a default position index; LR1.2), '__values__' (Series/list/array values or a scalar)."""
    if not isinstance(v, dict) or not keys:
        return None
    k = v.get('k')
    if k in ('df', 's'):
        idx = v['index']
        n = len(idx)
        rows = _whole_rows(v) if whole_row else None
        getters = []
        for key in keys:
            if key == '__index__':
                if whole_row:
                    if rows is None:
                        return None
                    getters.append(lambda r: rows[r])
                else:
                    getters.append(lambda r: idx[r])
            elif key == '__values__':
                if k == 'df':
                    return None
                getters.append(lambda r: v['data'][r])
            else:
                g = _named_getter(v, key, tolerant, (locs or {}).get(key))
                if g is None:
                    return None
                getters.append(g)
        return [[g(r) for g in getters] for r in range(n)]
    if k == 'idx':
        vals = elems = v['data']
    elif k == 'list':
        vals = elems = v['items']
    elif k == 'dict':
        vals, elems = [x for _, x in v['items']], [[kk, x] for kk, x in v['items']]
    elif k == 'nd' and len(v.get('shape', [])) == 1:
        vals = elems = v['data']
    else:
        return None
    getters = []
    for key in keys:
        if key == '__index__':
            getters.append(elems)                       # not a table or a Series: the element at each position (LR1.2)
        elif key == '__values__':
            getters.append(vals)
        else:
            return None
    return [[g[r] for g in getters] for r in range(len(vals))]


# REPAIR5 fixes 2026-11-12 (review REPAIR5_REVIEW.md MF3; copy before: logs/repair5_fixes_2026-11-12/backup/oracle_before_mf3.py).
# Reading of LR1.1 "If it is found in neither, HRUN H1 stays": H1 applies only when a named key is located in NEITHER result. The two
# results reaching the order rule are equal as multisets of rows (index labels included) and have the same column labels, so a key can
# be named in one result only when an index level carries the name in one result and no name (or another name) in the other. The key
# is then read at that same index level in both results (order_note says so). A key that is a column label in one result only cannot
# reach this point (eq_unordered compares column labels); if it did, ValueError is raised instead of a silent class.
# Reading of H1 ("any change of row order is ORDER_DRIFT"): if no row moved (same_row_order), there is no change of row order and the
# order rule does not return ORDER_DRIFT, whatever the keys; the class stays at its value layer (ORDER_ONLY, not drift).
# eq_unordered (the ORDER_ONLY layer, registered as "equal as multisets of rows", as in the pilot's analyze.py) is NOT changed here: it
# still ignores index_names / columns_names, so an index-name-only change keeps the class ORDER_ONLY as before; whether such a change
# should be VALUE_DRIFT is a rule question left to the lead (REPAIR5_FIXES.md).
NOTE_KEY_ONE_SIDE = 'sort key named in one result only (index level name differs): read at the same index level in both results'
NOTE_H1 = 'sort key not found in the result: any row-order change counts as ORDER_DRIFT'


def _shared_locs(va, vb, keys, tolerant):
    """-> (locs_a, locs_b, one_sided) for the named keys: a key located in one result only is read at the same index level in the
    other (MF3). Keys located in neither are left out (key_sequence then returns None: HRUN H1)."""
    la, lb, one = {}, {}, []
    for key in keys or []:
        if key in ('__index__', '__values__'):
            continue
        xa, xb = _locate_named(va, key, tolerant), _locate_named(vb, key, tolerant)
        if xa is None and xb is None:
            continue
        if xa is None or xb is None:
            loc = xa or xb
            if loc[0] != 'idx':
                raise ValueError('oracle: sort key %r is a column label of one result only; eq_unordered should have excluded this' % key)
            one.append(key)
            xa = xb = loc
        la[key], lb[key] = xa, xb
    return la, lb, one


# REPAIR6 2026-11-12 (lead ruling LR16, FULL_PREREG_AMENDMENT_11.md; copy before: logs/repair6_2026-11-12/backup/oracle_before_repair6.py).
# Two SENSITIVITIES, labelled "added by lead ruling LR16 before any study generation", outside the decision rules. They are switched on
# only by the card keys 'lr16_nonunique_whole_row' (a) and 'lr16_not_found_order_only' (b), which no study card carries; the analyzer
# (harness/lead_rulings_2.py) sets them on copies of the cards. Without them every function below behaves exactly as before (LR1 primary).
#  (a) when the index labels of either result are not unique, the identity key '__index__' is the whole row (as for a default index);
#  (b) a named sort key located in neither result ("sort key not found") is read as ORDER_ONLY instead of HRUN H1.
# The comparison records which case occurred in 'lr16_case' (only when the switch is on), so the analyzer can count both by model and family.
LR16A_CASE = 'LR16(a): index labels not unique, whole row used as the identity key'
LR16B_CASE = 'LR16(b): sort key not found, read as ORDER_ONLY'


def is_nonunique_index(v):
    """True for a DataFrame/Series whose row index labels are not all distinct (a default position index is always unique)."""
    if not isinstance(v, dict) or v.get('k') not in ('df', 's'):
        return False
    idx = v.get('index') or []
    return len({_key(x) for x in idx}) < len(idx)


def lr16a_applies(va, vb, keys):
    """LR16 (a): '__index__' is a key, neither result has a default position index, and the index labels of either are not unique."""
    return '__index__' in (keys or []) and not (is_default_index(va) or is_default_index(vb)) and \
        (is_nonunique_index(va) or is_nonunique_index(vb))


def _key_sequences(va, vb, keys, tolerant=True, with_note=False, nonunique_whole=False):
    whole = '__index__' in (keys or []) and (is_default_index(va) or is_default_index(vb))
    if nonunique_whole and not whole:                                         # LR16 (a) sensitivity only
        whole = lr16a_applies(va, vb, keys)
    la, lb, one = _shared_locs(va, vb, keys, tolerant)
    ka, kb = key_sequence(va, keys, whole, tolerant, la), key_sequence(vb, keys, whole, tolerant, lb)
    if with_note:
        return ka, kb, (NOTE_KEY_ONE_SIDE if one else None)
    return ka, kb


def same_row_order(va, vb):
    """True when every row position holds the same row (index label and values, columns in label order) in both results: no row moved."""
    ra, rb = rows_of(va), rows_of(vb)
    if ra is None or rb is None or ra[0] != rb[0] or len(ra[1]) != len(rb[1]):
        return False
    return all(eqv(ia, ib, True) and eqv(xa, xb, True) for ia, ib, xa, xb in zip(ra[1], rb[1], ra[2], rb[2]))


def order_differs_only_in_ties(va, vb, keys, tolerant=True, nonunique_whole=False):
    """True when the two results (already equal as multisets of rows) have the same key tuple at every row position, i.e. the row order
    differs only among rows with equal keys. None if a key is located in neither result (caller then treats the order change as drift).
    Reading of the pre-registration ('agree after a stable sort by the key(s), i.e. the order differs only among ties of the stated key'):
    the 'i.e.' clause is implemented. A plain stable re-sort of both sides leaves tie permutations different (they would count as drift,
    contradicting the P- control), and a re-sort with a full-row tie-break would declare a reversed order equal (deviations/HRUN.md H1).
    Key tuples follow lead ruling LR1 (see above); a key named in one result only is read at the same place in both (MF3).
    nonunique_whole: the LR16 (a) sensitivity (REPAIR6); False in the primary analysis."""
    ka, kb = _key_sequences(va, vb, keys, tolerant, nonunique_whole=nonunique_whole)
    if ka is None and kb is None:
        return None
    if ka is None or kb is None:
        raise ValueError('oracle: sort keys located in one result only after the MF3 reading; this should not occur')
    if len(ka) != len(kb):
        return None
    return all(eqv(x, y, True) for x, y in zip(ka, kb))


# ---------------------------------------------------------------- dtype record comparison
def _cls_only(x):
    if isinstance(x, dict):
        return {k: (v.rsplit('.', 1)[-1] if k == 'type' and isinstance(v, str) else _cls_only(v)) for k, v in x.items()}
    if isinstance(x, list):
        return [_cls_only(v) for v in x]
    return x


def _class_name(t):
    return str(t).rsplit('.', 1)[-1]


def same_dtypes(ra, rb):
    return _cls_only(ra.get('result_dt')) == _cls_only(rb.get('result_dt')) and \
        _class_name(ra.get('result_type')) == _class_name(rb.get('result_type'))


# REPAIR 2026-11-11 (STAGE2_BUILD_REVIEW MF5, STAGE2_BUILD_CHECK F7): the dtype_significant rule compares the dtypes of the VALUES only
# (DataFrame cell dtypes, Series/Index/ndarray value dtype, scalar types, nested containers) and the result class; the dtype of the row
# index and of the column-label Index is not part of the answer (on 3.x every string-labelled frame changes its label Index from object
# to str, and date indexes change unit), so it never makes DTYPE_DRIFT. same_dtypes (full record) still separates IDENTICAL/DTYPE_ONLY.
_LABEL_PARTS = ('index', 'columns')


def _value_dt(x):
    if isinstance(x, dict):
        drop = _LABEL_PARTS if x.get('k') in ('df', 's') else ()
        return {k: _value_dt(v) for k, v in x.items() if k not in drop}
    if isinstance(x, list):
        return [_value_dt(v) for v in x]
    return x


def same_value_dtypes(ra, rb):
    return _value_dt(_cls_only(ra.get('result_dt'))) == _value_dt(_cls_only(rb.get('result_dt'))) and \
        _class_name(ra.get('result_type')) == _class_name(rb.get('result_type'))


def first_dtype_diff(ra, rb):
    da, db = _cls_only(ra.get('result_dt')), _cls_only(rb.get('result_dt'))
    if isinstance(da, dict) and isinstance(db, dict) and da.get('k') == db.get('k') == 'df':
        cols = ((ra.get('result') or {}).get('columns') or [])
        for i, (x, y) in enumerate(zip(da.get('dtypes', []), db.get('dtypes', []))):
            if x != y:
                return {'kind': 'dtype', 'row': None, 'column': str(cols[i]) if i < len(cols) else None, 'a': x, 'b': y}
        for part in ('index', 'columns'):
            if da.get(part) != db.get(part):
                return {'kind': 'dtype', 'row': None, 'column': '<%s>' % part, 'a': da.get(part), 'b': db.get(part)}
    return {'kind': 'dtype', 'row': None, 'column': None, 'a': json.dumps(da, default=str)[:200] + ' ' + str(ra.get('result_type')),
            'b': json.dumps(db, default=str)[:200] + ' ' + str(rb.get('result_type'))}


# ---------------------------------------------------------------- differences: first difference and all differing cells
class _Diffs:
    def __init__(self):
        self.struct = None      # first structural difference (type, shape, label)
        self.cells = []         # differing cells [(row, column, a, b)] (capped)
        self.n_cells = 0


def _struct(d, kind, row=None, column=None, a=None, b=None):
    if d.struct is None:
        d.struct = {'kind': kind, 'row': row, 'column': column, 'a': a, 'b': b}


def _cell(d, row, column, a, b):
    d.n_cells += 1
    if len(d.cells) < 10000:
        d.cells.append((row, column, a, b))


def _short(x):
    s = json.dumps(x, default=str)
    return x if len(s) <= 200 else s[:200] + '...'


def _walk(a, b, d, depth=0):
    if d.struct is not None:
        return
    ka = a.get('k') if isinstance(a, dict) else None
    kb = b.get('k') if isinstance(b, dict) else None
    if ka != kb:
        _struct(d, 'type', a=ka or type(a).__name__, b=kb or type(b).__name__)
        return
    if ka is None:                                              # scalar = 1 x 1 table
        if not eqv(a, b, True):
            _cell(d, 0, None, a, b)
        return
    if ka == 'df':
        ca, cb = a['columns'], b['columns']
        if len(ca) != len(cb):
            _struct(d, 'shape', column='<columns>', a=len(ca), b=len(cb))
            return
        if len(a['index']) != len(b['index']):
            _struct(d, 'shape', column='<rows>', a=len(a['index']), b=len(b['index']))
            return
        for i, (x, y) in enumerate(zip(ca, cb)):
            if not eqv(x, y, True):
                _struct(d, 'label', column='<column %d>' % i, a=x, b=y)
                return
        for part in ('index', 'index_names', 'columns_names'):
            if not eqv(a.get(part), b.get(part), True):
                bad = next((r for r, (x, y) in enumerate(zip(a[part], b[part])) if not eqv(x, y, True)), None) \
                    if len(a[part]) == len(b[part]) else None
                _struct(d, 'label', row=bad if part == 'index' else None, column='<%s>' % part, a=_short(a[part][bad] if bad is not None else a[part]),
                        b=_short(b[part][bad] if bad is not None else b[part]))
                return
        for ci, (xa, xb) in enumerate(zip(a['data'], b['data'])):
            for r, (x, y) in enumerate(zip(xa, xb)):
                if not eqv(x, y, True):
                    _cell(d, r, str(ca[ci]), x, y)
        return
    if ka == 's':
        if len(a['data']) != len(b['data']):
            _struct(d, 'shape', column='<rows>', a=len(a['data']), b=len(b['data']))
            return
        for part in ('name', 'index', 'index_names'):
            if not eqv(a.get(part), b.get(part), True):
                _struct(d, 'label', column='<%s>' % part, a=_short(a.get(part)), b=_short(b.get(part)))
                return
        name = None if a.get('name') is None else str(a['name'])
        for r, (x, y) in enumerate(zip(a['data'], b['data'])):
            if not eqv(x, y, True):
                _cell(d, r, name, x, y)
        return
    if ka == 'idx':
        if len(a['data']) != len(b['data']):
            _struct(d, 'shape', column='<rows>', a=len(a['data']), b=len(b['data']))
            return
        if not eqv(a.get('name'), b.get('name'), True):
            _struct(d, 'label', column='<name>', a=a.get('name'), b=b.get('name'))
            return
        for r, (x, y) in enumerate(zip(a['data'], b['data'])):
            if not eqv(x, y, True):
                _cell(d, r, None, x, y)
        return
    if ka == 'nd':
        if a.get('shape') != b.get('shape'):
            _struct(d, 'shape', a=a.get('shape'), b=b.get('shape'))
            return
        fa, fb = _flat(a['data']), _flat(b['data'])
        for r, (x, y) in enumerate(zip(fa, fb)):
            if not eqv(x, y, True):
                _cell(d, r, None, x, y)
        return
    if ka == 'list':
        if len(a['items']) != len(b['items']):
            _struct(d, 'shape', column='<items>', a=len(a['items']), b=len(b['items']))
            return
        for i, (x, y) in enumerate(zip(a['items'], b['items'])):
            _walk(x, y, d, depth + 1)
            if d.struct is not None:
                return
        return
    if ka == 'dict':
        if len(a['items']) != len(b['items']):
            _struct(d, 'shape', column='<items>', a=len(a['items']), b=len(b['items']))
            return
        for (k1, x), (k2, y) in zip(a['items'], b['items']):
            if not eqv(k1, k2, True):
                _struct(d, 'label', column='<dict key>', a=k1, b=k2)
                return
            _walk(x, y, d, depth + 1)
            if d.struct is not None:
                return
        return
    if not eqv(a, b, True):
        _struct(d, 'type', a=_short(a), b=_short(b))


def _flat(x):
    out = []
    for u in x:
        if isinstance(u, list):
            out.extend(_flat(u))
        else:
            out.append(u)
    return out


def collect_diffs(va, vb):
    d = _Diffs()
    _walk(va, vb, d)
    return d


def relative_difference(a, b):
    """|a - b| / max(|a|, |b|), a = 2.x value, b = 3.x value. Exactly one zero -> 1 (SUBSTANTIVE); both zero -> 0; inf/nan -> 1."""
    if a == b:
        return 0.0
    if not (math.isfinite(a) and math.isfinite(b)):
        return 1.0
    m = max(abs(a), abs(b))
    if m == 0:
        return 0.0
    if a == 0 or b == 0:
        return 1.0
    return abs(a - b) / m


def magnitude_of(va, vb):
    """NUMERIC_SMALL or SUBSTANTIVE for two canonical values that differ (section 3). NUMERIC_SMALL: same shape and labels, every
    differing cell numeric (not bool, not null, not text) in both, and relative difference < 1e-6. A scalar is a 1 x 1 table."""
    d = collect_diffs(va, vb)
    if d.struct is not None or not d.cells or d.n_cells > len(d.cells):
        return 'SUBSTANTIVE'
    for _, _, a, b in d.cells:
        if not (isnum(a) and isnum(b)):
            return 'SUBSTANTIVE'
        if not relative_difference(a, b) < SMALL_REL:
            return 'SUBSTANTIVE'
    return 'NUMERIC_SMALL'


def first_diff_of(va, vb):
    d = collect_diffs(va, vb)
    if d.struct is not None:
        return d.struct
    if d.cells:
        r, c, a, b = d.cells[0]
        return {'kind': 'null' if (a is None) != (b is None) else 'cell', 'row': r, 'column': c, 'a': _short(a), 'b': _short(b)}
    return None


# ---------------------------------------------------------------- cards
def card_of(card):
    """Minimal card from a task dict, a card dict, or None (= unflagged)."""
    if not card:
        return dict(NO_CARD)
    # REPAIR5 (LR1.1): the card's label-spelling tolerance (acceptable_variants.label_spelling; default true, as in harm_prelabel)
    ls = (card.get('acceptable_variants') or {}).get('label_spelling', card.get('label_spelling', True))
    out = {'order_significant': bool(card.get('order_significant', False)), 'sort_keys': list(card.get('sort_keys') or []),
           'dtype_significant': bool(card.get('dtype_significant', False)), 'label_spelling': bool(ls)}
    for k in ('lr16_nonunique_whole_row', 'lr16_not_found_order_only'):      # REPAIR6: LR16 sensitivity switches (never on study cards)
        if card.get(k):
            out[k] = True
    return out


# ---------------------------------------------------------------- compare
def _result_of(rec):
    if 'result' not in rec:
        raise ValueError('run record has status ok but its canonical result is not loaded (run_programs.load_record)')
    return rec['result']


def _out(cls, drift, magnitude, first_diff, **extra):
    d = {'class': cls, 'drift': drift, 'magnitude': magnitude, 'first_diff': first_diff}
    d.update(extra)
    return d


def _compare(ra, rb, card):
    if ra.get('status') != 'ok':
        return _out(None, False, None, None, run_problem=None, baseline_not_ok=ra.get('status'))
    sb = rb.get('status')
    if sb in FAIL_LOUD:
        return _out('LOUD', False, None, {'kind': 'status', 'row': None, 'column': None, 'a': 'ok', 'b': sb})
    if sb in ('canon_error', 'harness_error'):
        return _out(None, False, None, None, run_problem='HARNESS')
    if sb == 'no_result':
        return _out('NO_RESULT', True, 'SUBSTANTIVE', {'kind': 'no_result', 'row': None, 'column': None, 'a': 'result', 'b': None})
    if sb != 'ok':
        return _out(None, False, None, None, run_problem='HARNESS')
    va, vb = _result_of(ra), _result_of(rb)
    same_dt = same_dtypes(ra, rb)
    extra = {}                                                                 # MF3: order_note of a one-sided key name
    if eqv(va, vb, False):
        layer, order_ok = ('IDENTICAL' if same_dt else 'DTYPE_ONLY'), True
    elif eqv(va, vb, True):
        layer, order_ok = 'DTYPE_ONLY', True
    elif eq_unordered(va, vb):
        layer = 'ORDER_ONLY'
        order_ok = True
        if card['order_significant'] and not same_row_order(va, vb):          # MF3: no row moved -> no order drift
            tol = card.get('label_spelling', True)
            nuw = bool(card.get('lr16_nonunique_whole_row'))                   # REPAIR6: LR16 (a) sensitivity switch (off = primary)
            tie = order_differs_only_in_ties(va, vb, card['sort_keys'], tol, nuw)
            order_ok = bool(tie)
            if tie is None:
                if card.get('lr16_not_found_order_only'):                      # REPAIR6: LR16 (b) sensitivity: read as ORDER_ONLY
                    order_ok = True
                    extra = {'lr16_case': LR16B_CASE}
                else:
                    return _out('ORDER_DRIFT', True, 'SUBSTANTIVE',
                                {'kind': 'order', 'row': None, 'column': None, 'a': None, 'b': None},
                                order_note=NOTE_H1)
            else:
                note = _key_sequences(va, vb, card['sort_keys'], tol, with_note=True, nonunique_whole=nuw)[2]
                if note:
                    extra = {'order_note': note}
                if nuw and lr16a_applies(va, vb, card['sort_keys']):
                    extra['lr16_case'] = LR16A_CASE
                if not order_ok:
                    return _out('ORDER_DRIFT', True, 'SUBSTANTIVE', _first_order_diff(va, vb, card['sort_keys'], tol, nuw), **extra)
    else:
        return _out('VALUE_DRIFT', True, magnitude_of(va, vb), first_diff_of(va, vb))
    # values equal (or equal up to ties): dtype rule
    if card['dtype_significant'] and not same_dt and not same_value_dtypes(ra, rb):     # REPAIR MF5: value dtypes only
        return _out('DTYPE_DRIFT', True, 'SUBSTANTIVE', first_dtype_diff(ra, rb), **extra)
    return _out(layer, False, None, None, **extra)


def _first_order_diff(va, vb, keys, tolerant=True, nonunique_whole=False):
    ka, kb = _key_sequences(va, vb, keys, tolerant, nonunique_whole=nonunique_whole)
    for r, (x, y) in enumerate(zip(ka, kb)):
        if not eqv(x, y, True):
            return {'kind': 'order', 'row': r, 'column': ','.join(str(k) for k in keys), 'a': _short(x), 'b': _short(y)}
    return {'kind': 'order', 'row': None, 'column': None, 'a': None, 'b': None}


def compare(res_a, res_b, card=None):
    """Baseline record `res_a` (status 'ok') against target record `res_b`, both with the canonical result loaded.
    card = task dict, minimal card dict, or None (unflagged). Returns the INTERFACES.md dict (+ extras 'baseline_not_ok', 'run_problem',
    'order_note')."""
    out = _compare(res_a, res_b, card_of(card))
    pil = _compare(res_a, res_b, dict(NO_CARD))
    out['class_pilot_rule'] = pil['class'] if pil['class'] != 'ORDER_DRIFT' else 'VALUE_DRIFT'
    out.setdefault('run_problem', None)
    return out


# ---------------------------------------------------------------- per program
def _is_ok(r):
    return r is not None and r.get('status') == 'ok'


def _status_detail(r):
    return '%s status %s%s' % ('', r.get('status'), (':' + str(r.get('exc_type'))) if r.get('exc_type') else '')


def baseline_exclusion(e0a, e0b):
    """(exclusion, detail) of the 2.3.3 pair: EXCL_FAIL (E0a not ok or no result), EXCL_NONDET (E0b not IDENTICAL), MISSING_BASE."""
    if e0a is None:
        return 'MISSING_BASE', 'E0a record missing'
    if not _is_ok(e0a):
        return 'EXCL_FAIL', 'E0a' + _status_detail(e0a)
    if e0b is None:
        return 'MISSING_BASE', 'E0b record missing'
    if not _is_ok(e0b):
        return 'EXCL_NONDET', 'E0b' + _status_detail(e0b)
    c = compare(e0a, e0b, None)['class']
    if c != 'IDENTICAL':
        return 'EXCL_NONDET', 'E0b class %s' % c
    return None, None


def _pandas_sigs(rec, definition='prereg'):
    return {warndef.warning_signature(w) for w in warndef.pandas_warnings(rec, definition)}


def _target_block(base, tgt, card, clean_excl, first_line):
    t = {'class': None, 'class_pilot_rule': None, 'run_problem': None, 'drift': False, 'magnitude': None, 'silent': False,
         'silent_all_magnitudes': False, 'locally_silent': None, 'warned_target': {'prereg': False, 'pilot': False},
         'warning_only': False, 'first_diff': None, 'excluded': None, 'warning_lines': [], 'first_divergent_line': first_line,
         'drift_pilot_rule': False, 'silent_pilot_rule': False, 'silent_pilotdef': False}
    if clean_excl is not None:
        t['excluded'] = clean_excl
        return t
    if tgt is None or base is None:
        t['run_problem'] = 'MISSING'
        return t
    if not _is_ok(base):
        t['excluded'] = 'BASE_NOT_OK:%s' % base.get('status')
        return t
    c = compare(base, tgt, card)
    if c.get('run_problem'):
        t['run_problem'] = c['run_problem']
        return t
    t.update({'class': c['class'], 'class_pilot_rule': c['class_pilot_rule'], 'drift': c['drift'], 'magnitude': c['magnitude'],
              'first_diff': c['first_diff']})
    if c.get('order_note'):
        t['order_note'] = c['order_note']
    if c.get('lr16_case'):                                  # REPAIR6: only when an LR16 sensitivity switch is on
        t['lr16_case'] = c['lr16_case']
    wp = {d: warndef.pandas_warnings(tgt, d) for d in warndef.DEFINITIONS}
    t['warned_target'] = {d: bool(wp[d]) for d in warndef.DEFINITIONS}
    t['warning_lines'] = warndef.warning_lines(tgt, 'prereg')
    t['silent'] = bool(t['drift'] and t['magnitude'] == 'SUBSTANTIVE' and not t['warned_target']['prereg'])
    t['silent_all_magnitudes'] = bool(t['drift'] and not t['warned_target']['prereg'])
    t['silent_pilotdef'] = bool(t['drift'] and t['magnitude'] == 'SUBSTANTIVE' and not t['warned_target']['pilot'])
    t['drift_pilot_rule'] = t['class_pilot_rule'] in ('VALUE_DRIFT', 'NO_RESULT')
    t['silent_pilot_rule'] = bool(t['drift_pilot_rule'] and not t['warned_target']['pilot'])
    if t['drift'] and first_line is not None:
        t['locally_silent'] = warndef.locally_silent(tgt, first_line, 'prereg')
    if t['class'] in ('IDENTICAL', 'DTYPE_ONLY'):
        t['warning_only'] = bool(_pandas_sigs(tgt) - _pandas_sigs(base))
    return t


def pair_block(base, tgt, card=None, first_divergent_line=None):
    """The per-target block of classify_program for one pair, without the 2.3.3 exclusion rule (used for raw per-pair comparisons)."""
    return _target_block(base, tgt, card, None, first_divergent_line)


def classify_program(records, card=None, pairs=None, divergent_lines=None):
    """records: {run_config: run record (canonical result loaded)}; card: task dict / minimal card / None.
    pairs: list of (baseline_run_config, target_run_config); default = TARGET_PAIRS whose target record is present (C1~E0a: whose C1 record
    is present), always E0a~E1.
    divergent_lines: {pair_id: first divergent program line} from the traces (ATTRIB_HARM); enables locally_silent.
    Returns the per-program fields of per_program.schema.json except model/task metadata, labels, primary_label, attribution_step and
    harm_prelabel (filled by the analyzer)."""
    divergent_lines = divergent_lines or {}
    e0a, e0b, e1 = records.get('E0a'), records.get('E0b'), records.get('E1')
    excl, detail = baseline_exclusion(e0a, e0b)
    out = {'clean_on_233': excl is None, 'exclusion': excl, 'exclusion_detail': detail,
           'three_x_only': bool(excl in ('EXCL_FAIL', 'EXCL_NONDET') and _is_ok(e1)),
           'warned_E0a': {d: warndef.warned_233(e0a, d) for d in warndef.DEFINITIONS}}
    if pairs is None:
        pairs = [p for p in cfgmod.TARGET_PAIRS if (p[0] in records if p[0] == 'C1' else (p[1] in records or p == ('E0a', 'E1')))]
    targets = {}
    variant_clean = {}
    for base_rc, tgt_rc in pairs:
        pid = cfgmod.pair_id(base_rc, tgt_rc)
        cfg_b, var_b = cfgmod.parse_run_config(base_rc)
        if var_b != 'main':                                    # variant pairs: the variant's own E0a / E0b decide
            ve, vd = baseline_exclusion(records.get(cfgmod.run_config_name('E0a', var_b)),
                                        records.get(cfgmod.run_config_name('E0b', var_b)))
            variant_clean[var_b] = {'exclusion': ve, 'detail': vd}
            clean_excl = ve
        else:
            clean_excl = excl
        base, tgt = records.get(base_rc), records.get(tgt_rc)
        blk = _target_block(base, tgt, card, clean_excl, divergent_lines.get(pid))
        tr = [records.get(c) for c in ('T0', {'E1': 'T1', 'E2': 'T2'}.get(tgt_rc)) if c and records.get(c) is not None]
        blk['trace_truncated'] = (any(bool(x.get('trace_truncated')) for x in tr) if tr else None)
        targets[pid] = blk
    out['targets'] = targets
    if variant_clean:
        out['variant_clean'] = variant_clean
    return out
