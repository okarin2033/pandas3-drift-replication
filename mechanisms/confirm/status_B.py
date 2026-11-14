# Written 2026-11-11 by pkg:MECH_B (STAGE2 T2.3). Builds mechanisms/confirm/status_B.tsv and attempts_B.json from the harness
# outputs (via summarize_B.attempt) with a fixed rule, then checks both TSVs of MECH_B against their conventions schemas.
#   status: CONFIRMED if an attempt drifts (oracle 'drift' true) on E0a~E1 or E0a~E2; the deciding attempt is the first one that
#           drifts in the order a, b (attempt b exists only because attempt a did not drift). NOT_REPRODUCED after two attempts
#           without drift on E1/E2. Drift on E3/E4 only (pyarrow) never confirms; it is reported in the note.
#   warn_233_measured / _pilotdef: warned_E0a of the deciding attempt (CONFIRMED) or of the last attempt (NOT_REPRODUCED);
#           every attempt's value is in the note.
#   warn_3x: any pandas warning (section 3 definition) in the E1 or E2 run of that attempt; loud: that attempt LOUD on E1.
# The interpretive text per row (MANUAL below) was written after reading the run outputs; it never changes a status.
# Usage (from the study folder): python3 -I -B mechanisms/confirm/status_B.py
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import summarize_B as sb  # noqa: E402

YESPRIOR = {'YES_DEFAULT': 'yes', 'YES_PARTIAL': 'yes', 'BY_ENFORCEMENT': 'yes', 'NO_NOTE': 'no', 'NOT_STATED': 'no'}

MANUAL = {
    'G01': 'Empty age bins appear (count 0) on 2.3.3 and vanish on 3.x (shape 5 -> 3 rows).',
    'G02': 'Unobserved category combination: NaN on 2.3.3, 0 on 3.x.',
    'G03': 'Grouping column summed into the result on 2.3.3, absent on 3.x (3 -> 2 columns).',
    'G04': 'Series key not in the frame: excluded from the result on 2.3.3, included on 3.x (1 -> 2 columns).',
    'G05': 'agg(np.std): pandas std (ddof=1) on 2.3.3, NumPy std (ddof=0) on 3.x.',
    'G06': 'Attempt a (column list of length 1) IDENTICAL on all targets, no 2.3.3 warning. Attempt b (level list of length 1): dict keys scalar on 2.3.3, 1-tuples on 3.x.',
    'G07': 'Both attempts IDENTICAL up to oracle tolerance; DTYPE_ONLY comes from the str index dtype of the group keys on 3.x, not from the sums. Attempt a: 500 mixed-magnitude values; attempt b: 1e16, 1, 1, 1, 1, -1e16 in one group (sum 4.0 on 2.3.3 and 3.1.1).',
    'G08': 'Attempt a (int64 group sums that overflow) DTYPE_ONLY, same wrapped values on all versions. Attempt b (groupby any/median on datetimes with NaT): LOUD on 3.x (TypeError for any on datetime64), FutureWarning on 2.3.3.',
    'R01': 'Row-order change only (pilot-rule class ORDER_ONLY): rows sorted by date on 2.3.3, first-appearance order on 3.x; drift only under an order_significant card (sort key __index__), so it matters only for order_significant tasks.',
    'R02': 'The row order of value_counts(sort=False) changes (sorted by labels on 2.3.3, first appearance on 3.x); because the idea takes head(3), different rows are selected, so it is value drift even without the order flag. Without head() it would be a row-order change only.',
    'R03': 'Both attempts select the same rows in the same order on every version. Attempt a: DataFrame.nlargest(2) with 5 tied maxima; attempt b: Series.nlargest(5) on 60 rows with many ties.',
    'R04': 'stack() without arguments: rows with NaN dropped on 2.3.3 (4 rows), kept on 3.x (8 rows); not a row-order change.',
    'R05': 'concat with a header-only frame, then describe(): numeric statistics for 1 column (amount) on 2.3.3, count/unique/top/freq for 3 columns on 3.x (all three columns non-numeric after concat); not a row-order change.',
    'R06': 'Both attempts give equal values on every version (DTYPE_ONLY from the str column-label dtype). Attempt a: qcut quartiles on values at the bin edges; attempt b: pivot_table with margins and dropna=False.',
    'R07': 'Both attempts DTYPE_ONLY: the joined index is object on 2.3.3 and int64 on 3.1.1 (as the 3.1 note says), but the values agree; in attempt b describe() did not change either. Would count only for a dtype_significant task.',
    'N01': 'Attempt a (sorted codes) DTYPE_ONLY: int64 on 2.3.3, object on 3.x. Attempt b: the object-dtype code column is dropped by mean(numeric_only=True) on 3.x (2 -> 1 columns).',
    'N02': 'convert_dtypes then 0/0: isna().sum() is 1 on 2.3.3 and 2 on 3.x (0/0 counted as missing).',
    'N03': 'Both attempts DTYPE_ONLY (label dtype object vs str); 2.3.3 did not infer int64 from the object input in either program (no warning either), so the constructor/Index-setting change was not exercised.',
    'N04': 'Attempt a (object column of ints): IDENTICAL, index object on 2.3.3 too, no warning. Attempt b (object column of Timestamps): 2.3.3 warns and infers datetime64, 3.x keeps object, but the describe() values agree (DTYPE_ONLY).',
    'N05': 'Attempt a (frame already nullable) DTYPE_ONLY. Attempt b (NumPy-backed frame with NaN vs Int64 Series): False on 2.3.3 and 3.0.6, NA on 3.1.1, so drift on E1 only (3.1 change).',
    'N06': 'rank() on a convert_dtypes column with NA: on 2.3.3 the missing value gets rank 1.0 and the others shift (5.0, 1.0, 2.5, 4.0, 2.5); on 3.x the missing value stays NA (4.0, NA, 1.5, 3.0, 1.5).',
    'N07': 'Attempt a (Categorical.map with a NaN-aware function): same values on all versions (DTYPE_ONLY). Attempt b (replace adding a new category): LOUD on 3.x (TypeError), FutureWarning on 2.3.3.',
    'I01': 'np.sum on a frame: Series on 2.3.3, scalar on 3.x (type change).',
    'I02': 'Integer slice on a float index: label-based on 2.3.3 (labels 10-30), positional on 3.x (rows 10-29).',
    'I03': 'Attempt a (text index, s[0]): LOUD on 3.x (KeyError). Attempt b (mixed text/integer labels with label 0 present): label-based on 2.3.3 as well, IDENTICAL; the silent case was not produced.',
    'I04': 'Attempt a (mask & list): LOUD on 3.x (TypeError). Attempt b (& between Series with mismatched indexes): IDENTICAL.',
    'I05': 'Attempt a (Series * list) IDENTICAL. Attempt b (Index == Series): NumPy array on 2.3.3, Series on 3.x (type change; values equal element-wise).',
    'I06': 'Attempt a (small counts) DTYPE_ONLY on E1 (object -> int64), IDENTICAL on E2. Attempt b (counts at the int64 limit): exact Python-int sum on 2.3.3 and 3.0.6, int64 overflow on 3.1.1 (E1 only); the data are unrealistic (counts near 9.2e18).',
    'X01': 'rolling(7).sem() changes (first non-null value 1.2586 on 2.3.3, 1.1653 on 3.x); rolling std agrees within tolerance.',
    'X02': 'groupby quantile(0.5, interpolation=nearest) on an even-sized group: 2.0 on 2.3.3, 3.0 on 3.x.',
}

SCHEMA_DIR = os.path.join(S, 'conventions', 'schema')


def yn(b):
    return 'na' if b is None else ('yes' if b else 'no')


def load_catalogue():
    with open(os.path.join(S, 'mechanisms', 'catalogue.tsv'), encoding='utf-8') as f:
        return {r['id']: r for r in csv.DictReader(f, delimiter='\t')}


def drifts(att, pair):
    c = att.get(pair)
    return bool(c and c.get('drift'))


def build():
    cat = load_catalogue()
    attempts = []
    rows = []
    for cid in sb.IDS:
        atts = [a for a in (sb.attempt(cid, 'a'), sb.attempt(cid, 'b')) if a is not None]
        attempts.extend(atts)
        decide = next((a for a in atts if drifts(a, 'E0a~E1') or drifts(a, 'E0a~E2')), None)
        if decide is not None:
            status = 'CONFIRMED'
        elif len(atts) >= 2:
            status, decide = 'NOT_REPRODUCED', atts[-1]
        else:
            raise SystemExit('%s: only one attempt and no drift; a second attempt is required' % cid)
        c1, c2 = decide.get('E0a~E1') or {}, decide.get('E0a~E2') or {}
        w_pre = (c1.get('warned_E0a') or {}).get('prereg')
        w_pil = (c1.get('warned_E0a') or {}).get('pilot')
        w3 = bool((c1.get('warned_target') or {}).get('prereg')) or bool((c2.get('warned_target') or {}).get('prereg'))
        prior = cat[cid]['py2x_warned']
        notes = [MANUAL[cid]]
        notes.append('deciding attempt %s; magnitude E1 %s, E2 %s; silent E1 %s, E2 %s' % (
            decide['attempt'], c1.get('magnitude'), c2.get('magnitude'), c1.get('silent'), c2.get('silent')))
        per = []
        for a in atts:
            ca, cb = a.get('E0a~E1') or {}, a.get('E0a~E2') or {}
            e3, e4 = a.get('E0pa~E3') or {}, a.get('E0pa~E4') or {}
            det = (a.get('E0a~E0b') or {}).get('class')
            per.append('%s: E1 %s E2 %s E3 %s E4 %s, E0a~E0b %s, warn233 %s/%s' % (
                a['attempt'], ca.get('class'), cb.get('class'), e3.get('class'), e4.get('class'), det,
                yn((ca.get('warned_E0a') or {}).get('prereg')), yn((ca.get('warned_E0a') or {}).get('pilot'))))
            if not (drifts(a, 'E0a~E1') or drifts(a, 'E0a~E2')) and (drifts(a, 'E0pa~E3') or drifts(a, 'E0pa~E4')):
                notes.append('attempt %s drifts only with pyarrow (E3/E4): does not confirm (section 4.3)' % a['attempt'])
        notes.append('attempts [' + '; '.join(per) + ']')
        if cid.startswith('R'):
            order_only = c1.get('class') == 'ORDER_DRIFT' and c1.get('class_pilot_rule') == 'ORDER_ONLY'
            order_only2 = c2.get('class') == 'ORDER_DRIFT' and c2.get('class_pilot_rule') == 'ORDER_ONLY'
            notes.append('row-order change only: %s (E1), %s (E2)' % (yn(order_only), yn(order_only2)))
        exp = YESPRIOR.get(prior)
        if exp is not None and exp != yn(w_pre):
            notes.append('DISAGREEMENT with prior %s: measured 2.3.3 warning (section 3) = %s on the deciding attempt' % (prior, yn(w_pre)))
        if yn(w_pre) != yn(w_pil):
            notes.append('section 3 and pilot warning definitions disagree on 2.3.3')
        rows.append({
            'id': cid, 'family': cat[cid]['quota_family'], 'scope': cat[cid]['scope'],
            'programs': ';'.join(a['program'] for a in atts), 'attempts': str(len(atts)),
            'drift_E1': yn(drifts(decide, 'E0a~E1')), 'drift_E2': yn(drifts(decide, 'E0a~E2')),
            'warn_233_measured': yn(w_pre), 'warn_233_pilotdef': yn(w_pil), 'warn_3x': yn(w3),
            'loud': yn(c1.get('class') == 'LOUD'), 'status': status, 'prior_py2x_warned': prior,
            'note': ' | '.join(notes).replace('\t', ' ').replace('\n', ' '),
            'class_E1': c1.get('class') or 'NA', 'class_E2': c2.get('class') or 'NA',
        })
    return rows, attempts


def check_tsv(path, schema_name):
    with open(os.path.join(SCHEMA_DIR, schema_name), encoding='utf-8') as f:
        schema = json.load(f)
    cols = [c['name'] for c in schema['columns']]
    errs = []
    with open(path, encoding='utf-8') as f:
        rd = csv.reader(f, delimiter='\t')
        header = next(rd)
        if header != cols:
            errs.append('header %s != %s' % (header, cols))
        for i, r in enumerate(rd, 2):
            if len(r) != len(cols):
                errs.append('line %d: %d fields' % (i, len(r)))
                continue
            for c, v in zip(schema['columns'], r):
                if not re.search(c['pattern'], v):
                    errs.append('line %d col %s: %r' % (i, c['name'], v[:60]))
    return errs


def main():
    rows, attempts = build()
    with open(os.path.join(SCHEMA_DIR, 'confirm_status.tsv.schema.json'), encoding='utf-8') as f:
        cols = [c['name'] for c in json.load(f)['columns']]
    out = os.path.join(HERE, 'status_B.tsv')
    with open(out, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar='\\')
        w.writerow(cols)
        for r in rows:
            w.writerow([r[c] for c in cols])
    with open(os.path.join(HERE, 'attempts_B.json'), 'w', encoding='utf-8') as f:
        json.dump(attempts, f, indent=1, sort_keys=True, default=str)
        f.write('\n')
    fams = {}
    for r in rows:
        fams.setdefault(r['family'], {}).setdefault(r['status'], []).append(r['id'])
    print('rows:', len(rows))
    for fam in sorted(fams):
        print(fam, {k: len(v) for k, v in sorted(fams[fam].items())}, fams[fam].get('CONFIRMED', []))
    print('E0a~E0b classes:', sorted({(a.get('E0a~E0b') or {}).get('class') for a in attempts}))
    errs = check_tsv(out, 'confirm_status.tsv.schema.json')
    print('status_B.tsv schema check:', 'OK' if not errs else errs)
    dn = os.path.join(HERE, 'data_needs_B.tsv')
    if os.path.exists(dn):
        errs = check_tsv(dn, 'data_needs.tsv.schema.json')
        conf = {r['id'] for r in rows if r['status'] == 'CONFIRMED'}
        with open(dn, encoding='utf-8') as f:
            have = {r['id'] for r in csv.DictReader(f, delimiter='\t')}
        print('data_needs_B.tsv schema check:', 'OK' if not errs else errs,
              '| confirmed rows without data needs:', sorted(conf - have), '| non-confirmed listed:', sorted(have - conf))


if __name__ == '__main__':
    main()
