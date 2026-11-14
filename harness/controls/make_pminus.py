# [REPAIR5 2026-11-11: REPAIR5_NATURAL block added (lead ruling LR1.4); copy before: logs/repair5_2026-11-11/backup/make_pminus_before.py]
# [REPAIR6 2026-11-12: REPAIR6_NATURAL block added (lead ruling LR16); copy before: logs/repair6_2026-11-12/backup/make_pminus_before_repair6.py]
# VERIFY (T5.11, P-): writes the hand-written negative / matching-positive oracle control programs and their manifest.
# Written 2026-11-11 by pkg:VERIFY. Standard library only. Run: python3 -I -B harness/controls/make_pminus.py
# Output: harness/controls/programs/<name>.py, harness/controls/controls.json (expectations written BEFORE any run, from the
# pre-registration FULL_PREREG section 3 and section 9, not from what the harness printed).
# All data are the synthetic CSVs in harness/controls/data/. 'natural' controls differ between pandas versions because of a
# documented behaviour change (dtype strings, row order of DataFrame.value_counts(sort=False), concat of date indexes);
# 'switch' controls read the major version of the running pandas and build two known results, so the oracle is tested on an
# exactly known difference (tolerances, magnitude class, shape, nulls, NO_RESULT, LOUD).
import json, os, sys, textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
PROG_DIR = os.path.join(HERE, 'programs')

HDR = '# VERIFY control %s (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: %s.\n'
V = 'import pandas as pd\nV = int(pd.__version__.split(".")[0])   # 2 = baseline (2.3.3), 3 = target (3.x)\n'

# ---- natural controls -------------------------------------------------------------------------------------------------
NATURAL = [
    # name, category, flags, expected classes (any of), drift, magnitude, pilot-rule class, rationale, source
    ('dt_text_frame', 'P-', {}, ['DTYPE_ONLY'], False, None, 'DTYPE_ONLY',
     'text columns are object on 2.3.3 and str on 3.x; values equal; unflagged -> DTYPE_ONLY',
     'import pandas as pd\ndf = pd.read_csv("people.csv")\nresult = df[["name", "city", "plan"]]\n'),
    ('dt_groupby_sum', 'P-', {}, ['DTYPE_ONLY'], False, None, 'DTYPE_ONLY',
     'group keys end up in an object (2.3.3) or str (3.x) index; sums equal',
     'import pandas as pd\ndf = pd.read_csv("people.csv")\nresult = df.groupby("city")["amount"].sum()\n'),
    ('dt_datetime_frame', 'P-', {}, ['DTYPE_ONLY'], False, None, 'DTYPE_ONLY',
     'parsed dates are datetime64[ns] on 2.3.3 and a coarser unit on 3.x; canonical timestamps equal',
     'import pandas as pd\ndf = pd.read_csv("people.csv", parse_dates=["signup"])\nresult = df[["id", "signup"]]\n'),
    ('dt_column_labels', 'P-', {}, ['DTYPE_ONLY'], False, None, 'DTYPE_ONLY',
     'result is the Index of column labels: object on 2.3.3, str on 3.x; labels equal',
     'import pandas as pd\ndf = pd.read_csv("people.csv")\nresult = df.columns\n'),
    ('dt_value_counts_series', 'P-', {}, ['DTYPE_ONLY'], False, None, 'DTYPE_ONLY',
     'distinct counts, so order is fixed; only the index dtype differs',
     'import pandas as pd\ndf = pd.read_csv("people.csv")\nresult = df["city"].value_counts()\n'),
    ('dt_pivot_table', 'P-', {}, ['DTYPE_ONLY'], False, None, 'DTYPE_ONLY',
     'row and column labels are text; dtype of the label indexes differs, values equal',
     'import pandas as pd\ndf = pd.read_csv("people.csv")\nresult = pd.pivot_table(df, index="city", columns="plan", values="amount", aggfunc="sum", fill_value=0)\n'),
    ('dt_to_dict_keys', 'P-', {}, ['IDENTICAL'], False, None, 'IDENTICAL',
     'a plain dict of Python strings and floats cannot differ by dtype: IDENTICAL (guards against calling every program DTYPE_ONLY)',
     'import pandas as pd\ndf = pd.read_csv("people.csv")\nresult = df.groupby("city")["amount"].sum().to_dict()\n'),
    ('ord_dataframe_value_counts', 'P-', {}, ['ORDER_ONLY'], False, None, 'ORDER_ONLY',
     'DataFrame.value_counts(sort=False) lists groups sorted on 2.3.3 and in first-appearance order on 3.x; unflagged -> ORDER_ONLY',
     'import pandas as pd\ndf = pd.read_csv("people.csv")\nresult = df[["plan", "city"]].value_counts(sort=False)\n'),
    ('ord_dataframe_value_counts_frame', 'P-', {}, ['ORDER_ONLY'], False, None, 'ORDER_ONLY',
     'the same as a DataFrame with a default index (index ignored by the oracle)',
     'import pandas as pd\ndf = pd.read_csv("people.csv")\nresult = df[["plan", "city"]].value_counts(sort=False).reset_index(name="n")\n'),
    ('ord_concat_dates', 'P-', {}, ['ORDER_ONLY'], False, None, 'ORDER_ONLY',
     'concat(axis=1, sort=False) of date-indexed frames: index sorted on 2.3.3, first appearance on 3.x',
     'import pandas as pd\na = pd.read_csv("left.csv", parse_dates=["date"], index_col="date").rename(columns={"value": "left"})\n'
     'b = pd.read_csv("right.csv", parse_dates=["date"], index_col="date").rename(columns={"value": "right"})\n'
     'result = pd.concat([a, b], axis=1, sort=False)\n'),
    ('ord_and_dtype_unflagged', 'P-', {}, ['ORDER_ONLY'], False, None, 'ORDER_ONLY',
     'order and index dtype both change; unflagged -> not drift (ORDER_ONLY; DTYPE_ONLY would also be non-drift)',
     'import pandas as pd\ndf = pd.read_csv("people.csv")\nresult = df[["plan", "city"]].value_counts(sort=False)\n'),
    # flagged, ties only
    ('tie_stable_sorted_counts_series', 'P-', {'order_significant': True, 'sort_keys': ['__values__']}, ['ORDER_ONLY'], False, None, 'ORDER_ONLY',
     'sorted by count; every group has count 2, so the order differs only among ties of the key',
     'import pandas as pd\ndf = pd.read_csv("people.csv")\nresult = df[["plan", "city"]].value_counts(sort=False).sort_values(ascending=False, kind="stable")\n'),
    ('tie_stable_sorted_counts_frame', 'P-', {'order_significant': True, 'sort_keys': ['n']}, ['ORDER_ONLY'], False, None, 'ORDER_ONLY',
     'same, as a DataFrame with key column n',
     'import pandas as pd\ndf = pd.read_csv("people.csv")\nresult = df[["plan", "city"]].value_counts(sort=False).sort_values(ascending=False, kind="stable").reset_index(name="n")\n'),
    ('tie_partial_ties_frame', 'P-', {'order_significant': True, 'sort_keys': ['n']}, ['ORDER_ONLY'], False, None, 'ORDER_ONLY',
     'one group has count 3, four have count 2, one has count 1: after a stable descending sort the count column is equal at every row, only the cities inside the count-2 block change places',
     'import pandas as pd\ndf = pd.read_csv("people2.csv")\nresult = df[["city"]].value_counts(sort=False).sort_values(ascending=False, kind="stable").reset_index(name="n")\n'),
    # matching positives
    ('pos_order_beyond_ties_index', 'P+', {'order_significant': True, 'sort_keys': ['__index__']}, ['ORDER_DRIFT'], True, 'SUBSTANTIVE', 'ORDER_ONLY',
     'flagged on the (distinct) group labels: any reordering is beyond ties',
     'import pandas as pd\ndf = pd.read_csv("people.csv")\nresult = df[["plan", "city"]].value_counts(sort=False)\n'),
    ('pos_order_beyond_ties_frame', 'P+', {'order_significant': True, 'sort_keys': ['city']}, ['ORDER_DRIFT'], True, 'SUBSTANTIVE', 'ORDER_ONLY',
     'flagged on city; the same frame lists the groups in a different order, cities all distinct per row',
     'import pandas as pd\ndf = pd.read_csv("people2.csv")\nresult = df[["city"]].value_counts(sort=False).reset_index(name="n")\n'),
    ('pos_order_beyond_ties_partial_key', 'P+', {'order_significant': True, 'sort_keys': ['n']}, ['ORDER_DRIFT'], True, 'SUBSTANTIVE', 'ORDER_ONLY',
     'same data as tie_partial_ties_frame but the frame is not sorted by n: the n column itself changes order (3,2,2,2,2,1 vs 2,2,2,2,1,3), so the change is beyond ties of the key',
     'import pandas as pd\ndf = pd.read_csv("people2.csv")\nresult = df[["city"]].value_counts(sort=False).reset_index(name="n")\n'),
    ('pos_order_concat_dates', 'P+', {'order_significant': True, 'sort_keys': ['__index__']}, ['ORDER_DRIFT'], True, 'SUBSTANTIVE', 'ORDER_ONLY',
     'date index in a different order, flagged on the index',
     'import pandas as pd\na = pd.read_csv("left.csv", parse_dates=["date"], index_col="date").rename(columns={"value": "left"})\n'
     'b = pd.read_csv("right.csv", parse_dates=["date"], index_col="date").rename(columns={"value": "right"})\n'
     'result = pd.concat([a, b], axis=1, sort=False)\n'),
    ('pos_dtype_text_frame', 'P+', {'dtype_significant': True}, ['DTYPE_DRIFT'], True, 'SUBSTANTIVE', 'DTYPE_ONLY',
     'dtype_significant card, text columns change dtype (object -> str)',
     'import pandas as pd\ndf = pd.read_csv("people.csv")\nresult = df[["name", "city", "plan"]]\n'),
    ('pos_dtype_datetime_frame', 'P+', {'dtype_significant': True}, ['DTYPE_DRIFT'], True, 'SUBSTANTIVE', 'DTYPE_ONLY',
     'dtype_significant card, datetime unit changes',
     'import pandas as pd\ndf = pd.read_csv("people.csv", parse_dates=["signup"])\nresult = df[["id", "signup"]]\n'),
    ('flag_dtype_on_order_only', 'P-', {'dtype_significant': True}, ['ORDER_ONLY', 'DTYPE_DRIFT'], None, None, 'ORDER_ONLY',
     'dtype_significant card on a program whose result changes order and index dtype: both ORDER_ONLY and DTYPE_DRIFT are defensible readings; recorded, not scored',
     'import pandas as pd\ndf = pd.read_csv("people.csv")\nresult = df[["plan", "city"]].value_counts(sort=False)\n'),
]


# REPAIR 2026-11-11 (STAGE2_BUILD_REVIEW MF5, STAGE2_BUILD_CHECK F7), added in the repair step. Expectations written here before
# any run, from FULL_PREREG section 3 ("a dtype change" of an answer whose dtype is part of the answer) as repaired in harness/oracle.py:
# with dtype_significant set, only the dtypes of the values count; the dtype of the row index or of the column-label Index does not.
HDR_REPAIR = '# REPAIR control %s (hand-written, synthetic data; 2026-11-11, review MF5). Expected class: %s.\n'
REPAIR_NATURAL = [
    ('dtsig_float_frame_text_labels', 'P-', {'dtype_significant': True}, ['DTYPE_ONLY'], False, None, 'DTYPE_ONLY',
     'dtype_significant card; float cells are float64 on both sides, only the text row index and the column-label Index change object -> str: not DTYPE_DRIFT',
     'import pandas as pd\ndf = pd.read_csv("people.csv")\nresult = df.groupby("city")[["amount"]].sum()\n'),
    ('dtsig_series_date_index', 'P-', {'dtype_significant': True}, ['DTYPE_ONLY'], False, None, 'DTYPE_ONLY',
     'dtype_significant card; integer values unchanged, only the unit of the parsed date index changes: not DTYPE_DRIFT',
     'import pandas as pd\nresult = pd.read_csv("left.csv", parse_dates=["date"], index_col="date")["value"]\n'),
    ('dtsig_value_counts_series', 'P-', {'dtype_significant': True}, ['DTYPE_ONLY'], False, None, 'DTYPE_ONLY',
     'dtype_significant card; distinct counts (int64 on both sides), only the dtype of the text index changes: not DTYPE_DRIFT',
     'import pandas as pd\ndf = pd.read_csv("people.csv")\nresult = df["city"].value_counts()\n'),
    ('dtsig_index_result', 'P+', {'dtype_significant': True}, ['DTYPE_DRIFT'], True, 'SUBSTANTIVE', 'DTYPE_ONLY',
     'dtype_significant card; the result is an Index of text labels, so its dtype is the dtype of its values (object -> str): DTYPE_DRIFT',
     'import pandas as pd\ndf = pd.read_csv("people.csv")\nresult = df.columns\n'),
]
# REPAIR2 2026-11-11 (FULL_PREREG_AMENDMENT_3, review MF3), added after Amendment 3 and BEFORE the
# P- re-run. Expectations written here from the amended section 3 wording: with sort_keys ['__index__'] (identity key for a requested
# non-sorted order), a result whose rows keep the same index label at every position is not ORDER_DRIFT; only dtypes differ.
HDR_REPAIR2 = '# REPAIR2 control %s (hand-written, synthetic data; 2026-11-11, Amendment 3). Expected class: %s.\n'
REPAIR2_NATURAL = [
    ('idkey_same_order_groupby', 'P-', {'order_significant': True, 'sort_keys': ['__index__']}, ['DTYPE_ONLY'], False, None, 'DTYPE_ONLY',
     'order_significant with the identity key __index__; groupby sorts its text keys on every version, so the index label at every row position is the same; only the label and text dtypes change: not ORDER_DRIFT',
     'import pandas as pd\ndf = pd.read_csv("people.csv")\nresult = df.groupby("city")[["amount"]].sum()\n'),
    ('idkey_same_order_file_rows', 'P-', {'order_significant': True, 'sort_keys': ['__index__']}, ['DTYPE_ONLY'], False, None, 'DTYPE_ONLY',
     'order_significant with the identity key __index__ on a file-order result (default row labels 0..n-1 kept in file order on every version); text columns change dtype only: not ORDER_DRIFT',
     'import pandas as pd\ndf = pd.read_csv("people.csv")\nresult = df[["name", "city"]]\n'),
]
# REPAIR5 2026-11-11 (lead ruling LR1.4, FULL_PREREG_AMENDMENT_10.md; review RV-2, RV-14), added after the
# rulings and BEFORE the first run of these controls. Expectations written here from LR1 (row identity in the order rule) and sealed
# in logs/repair5_2026-11-11/lr1_controls_expectations.sha256 before the run. Natural difference used: DataFrame.value_counts(sort=False)
# lists groups sorted on 2.3.3 and in first-appearance order on 3.x (as in the VERIFY controls above; people2.csv: counts 3/2/2/2/2/1).
HDR_REPAIR5 = '# REPAIR5 control %s (hand-written, synthetic data; 2026-11-11, lead ruling LR1.4). Expected class: %s.\n'
REPAIR5_NATURAL = [
    ('lr1_idkey_column_default_index_frame', 'P+', {'order_significant': True, 'sort_keys': ['__index__']}, ['ORDER_DRIFT'], True, 'SUBSTANTIVE', 'ORDER_ONLY',
     'LR1.4 must be ORDER_DRIFT (table form): identity key __index__, the key (city) held as a column, default index 0..n-1, rows reordered beyond ties (cities distinct); LR1.2 uses the whole row as the key',
     'import pandas as pd\ndf = pd.read_csv("people2.csv")\nresult = df[["city"]].value_counts(sort=False).reset_index(name="n")\n'),
    ('lr1_idkey_column_default_index_list', 'P+', {'order_significant': True, 'sort_keys': ['__index__']}, ['ORDER_DRIFT'], True, 'SUBSTANTIVE', 'ORDER_ONLY',
     'LR1.4 must be ORDER_DRIFT (list form): the same rows as a Python list of (city, n) tuples, reordered beyond ties; LR1.2 uses the element at each position',
     'import pandas as pd\ndf = pd.read_csv("people2.csv")\nresult = list(df[["city"]].value_counts(sort=False).reset_index(name="n").itertuples(index=False, name=None))\n'),
    ('lr1_idkey_series_default_index', 'P+', {'order_significant': True, 'sort_keys': ['__index__']}, ['ORDER_DRIFT'], True, 'SUBSTANTIVE', 'ORDER_ONLY',
     'Series form (LR1.2, review RV-2(c); added next to the two LR1.4 forms): the counts as a Series with a default index, values reordered beyond ties (3 moves from first to last); the whole row is the key',
     'import pandas as pd\ndf = pd.read_csv("people2.csv")\nresult = df[["city"]].value_counts(sort=False).reset_index(name="n")["n"]\n'),
    ('lr1_namedkey_index_ties_only', 'P-', {'order_significant': True, 'sort_keys': ['n']}, ['ORDER_ONLY'], False, None, 'ORDER_ONLY',
     'LR1.4 must be ORDER_ONLY: named key n held in the index (not a column), rows permuted among ties only (stable descending sort by n; only the cities inside the count-2 block change places); LR1.1 finds n among the index level names',
     'import pandas as pd\ndf = pd.read_csv("people2.csv")\nresult = df[["city"]].value_counts(sort=False).sort_values(ascending=False, kind="stable").reset_index(name="n").set_index("n")\n'),
]
# REPAIR6 2026-11-12 (lead ruling LR16, FULL_PREREG_AMENDMENT_11.md), added BEFORE the first run of these controls.
# One control per LR16 case. The primary expectation (LR1 primary) is scored by pminus_eval.py like every control; the expectation under
# the LR16 sensitivity switch is checked by harness/controls/lr16_eval.py. Both are sealed in logs/repair6_2026-11-12/
# lr16_controls_expectations.sha256 before the first run. Natural difference used: DataFrame.value_counts(sort=False) lists groups
# sorted on 2.3.3 and in first-appearance order on 3.x (people.csv; as in ord_dataframe_value_counts above, all counts 2).
HDR_REPAIR6 = '# REPAIR6 control %s (hand-written, synthetic data; 2026-11-12, lead ruling LR16). Expected class: %s.\n'
REPAIR6_NATURAL = [
    # name, category, flags, expected (primary), drift, magnitude, pilot-rule class, rationale, source, LR16 switch, expected under it
    ('lr16_nonunique_index_ties_label', 'P-', {'order_significant': True, 'sort_keys': ['__index__']}, ['ORDER_ONLY'], False, None, 'ORDER_ONLY',
     'LR16 (a) case: identity key __index__ on a non-unique index (plan; two rows per plan after a stable sort by plan); only rows that share a plan label change places, so under LR1 (key = index labels) the order differs only in ties: ORDER_ONLY; under the LR16 (a) sensitivity (whole row as key) ORDER_DRIFT',
     'import pandas as pd\ndf = pd.read_csv("people.csv")\nresult = df[["plan", "city"]].value_counts(sort=False).reset_index(name="n").set_index("plan").sort_index(kind="stable")\n',
     'lr16_nonunique_whole_row', ['ORDER_DRIFT']),
    ('lr16_key_not_found_reordered', 'P+', {'order_significant': True, 'sort_keys': ['total']}, ['ORDER_DRIFT'], True, 'SUBSTANTIVE', 'ORDER_ONLY',
     'LR16 (b) case: named sort key total is neither a column nor an index level name of the result; rows reordered: under LR1 HRUN H1 ("sort key not found") ORDER_DRIFT; under the LR16 (b) sensitivity ORDER_ONLY',
     'import pandas as pd\ndf = pd.read_csv("people.csv")\nresult = df[["plan", "city"]].value_counts(sort=False).reset_index(name="n")\n',
     'lr16_not_found_order_only', ['ORDER_ONLY']),
]
# ---- switch controls: (name, expression for result on V=2, on V=3, flags, expected classes, drift, magnitude, rationale) ---
SW = [
    ('num_identical_float', 'float64', '2.5', '2.5', ['IDENTICAL'], False, None, 'same value'),
    ('num_below_relative_tol', 'float64', '2.5', '2.5 * (1 + 1e-12)', ['IDENTICAL'], False, None, 'relative difference 1e-12 < 1e-11'),
    ('num_below_absolute_tol', 'float64', '0.0', '1e-12', ['IDENTICAL'], False, None, 'one zero but absolute difference 1e-12 < 1e-9: equal by the oracle tolerance'),
    ('num_small_scalar', 'float64', '2.5', '2.5 * (1 + 1e-8)', ['VALUE_DRIFT'], True, 'NUMERIC_SMALL', 'relative difference 1e-8 < 1e-6'),
    ('num_small_just_under', 'float64', '1.0', '1.0 + 5e-7', ['VALUE_DRIFT'], True, 'NUMERIC_SMALL', 'relative difference 5e-7 < 1e-6'),
    ('num_substantive_just_over', 'float64', '1.0', '1.0 + 2e-6', ['VALUE_DRIFT'], True, 'SUBSTANTIVE', 'relative difference 2e-6 >= 1e-6'),
    ('num_substantive_scalar', 'float64', '2.5', '2.5 * (1 + 1e-4)', ['VALUE_DRIFT'], True, 'SUBSTANTIVE', 'relative difference 1e-4'),
    ('num_zero_vs_nonzero', 'float64', '0.0', '1e-7', ['VALUE_DRIFT'], True, 'SUBSTANTIVE', 'exactly one of a, b is 0 -> relative difference 1 -> SUBSTANTIVE (absolute 1e-7 > 1e-9, so it is drift)'),
    ('num_sign_flip_tiny', 'float64', '1e-8', '-1e-8', ['VALUE_DRIFT'], True, 'SUBSTANTIVE', 'relative difference 2 (opposite signs), absolute 2e-8 > 1e-9'),
    ('num_integer_off_by_one', 'int64', '100', '101', ['VALUE_DRIFT'], True, 'SUBSTANTIVE', 'integers are compared exactly'),
    ('num_text_differs', 'str', '"abc"', '"abd"', ['VALUE_DRIFT'], True, 'SUBSTANTIVE', 'text compared exactly'),
    ('num_frame_all_small', 'frame', 'pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [10.0, 20.0, 30.0]})',
     'pd.DataFrame({"a": [1.0 * (1 + 1e-8), 2.0 * (1 + 2e-8), 3.0], "b": [10.0, 20.0 * (1 + 1e-7), 30.0 * (1 - 1e-8)]})',
     ['VALUE_DRIFT'], True, 'NUMERIC_SMALL', 'same shape and labels, every differing cell numeric and below 1e-6 relative'),
    ('num_frame_one_large_cell', 'frame', 'pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [10.0, 20.0, 30.0]})',
     'pd.DataFrame({"a": [1.0 * (1 + 1e-8), 2.0, 3.0], "b": [10.0, 20.0, 30.0 * 1.01]})',
     ['VALUE_DRIFT'], True, 'SUBSTANTIVE', 'one cell differs by 1%: SUBSTANTIVE although another cell differs by 1e-8'),
    ('num_frame_extra_row', 'frame', 'pd.DataFrame({"a": [1.0, 2.0, 3.0]})', 'pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0]})',
     ['VALUE_DRIFT'], True, 'SUBSTANTIVE', 'shape differs'),
    ('num_frame_label_differs', 'frame', 'pd.DataFrame({"a": [1.0, 2.0]})', 'pd.DataFrame({"b": [1.0, 2.0]})',
     ['VALUE_DRIFT'], True, 'SUBSTANTIVE', 'column label differs'),
    ('num_null_pattern', 'frame', 'pd.DataFrame({"a": [1.0, float("nan"), 3.0]})', 'pd.DataFrame({"a": [1.0, 2.0, 3.0]})',
     ['VALUE_DRIFT'], True, 'SUBSTANTIVE', 'null pattern differs'),
    ('num_null_kinds_equal', 'frame', 'pd.DataFrame({"a": [1.0, None, 3.0]}, dtype="float64")',
     'pd.DataFrame({"a": pd.array([1.0, pd.NA, 3.0], dtype="Float64")})', ['IDENTICAL', 'DTYPE_ONLY'], False, None,
     'None, NaN and pd.NA are all null (section 3): no value difference'),
    ('num_bool_vs_int', 'frame', 'pd.DataFrame({"a": [True, False, True]})', 'pd.DataFrame({"a": [1, 0, 1]})',
     ['DTYPE_ONLY'], False, None, 'booleans treated as 0/1: dtype difference only'),
    ('num_no_result_on_target', 'noresult', '1', '1', ['NO_RESULT'], True, 'SUBSTANTIVE',
     'the 3.x run completes without defining result: drift (NO_RESULT, section 3)'),
    ('loud_raise_on_target', 'raise', '1', '1', ['LOUD'], False, None, 'the 3.x run raises: LOUD, never drift'),
]


def write(name, text):
    os.makedirs(PROG_DIR, exist_ok=True)
    with open(os.path.join(PROG_DIR, name + '.py'), 'w', encoding='utf-8') as f:
        f.write(text)


def main():
    controls = []
    for name, cat, flags, exp, drift, mag, pil, why, src in NATURAL:
        write(name, HDR % (name, '/'.join(exp)) + '# ' + why + '\n' + src)
        controls.append({'name': name, 'kind': 'natural', 'category': cat, 'card': flags, 'expect_class': exp,
                         'expect_drift': drift, 'expect_magnitude': mag, 'expect_class_pilot_rule': pil, 'why': why,
                         'scored': name != 'flag_dtype_on_order_only'})
    for name, cat, flags, exp, drift, mag, pil, why, src in REPAIR_NATURAL:
        write(name, HDR_REPAIR % (name, '/'.join(exp)) + '# ' + why + '\n' + src)
        controls.append({'name': name, 'kind': 'natural', 'category': cat, 'card': flags, 'expect_class': exp,
                         'expect_drift': drift, 'expect_magnitude': mag, 'expect_class_pilot_rule': pil, 'why': why,
                         'scored': True, 'added': 'REPAIR 2026-11-11 (review MF5)'})
    for name, cat, flags, exp, drift, mag, pil, why, src in REPAIR2_NATURAL:
        write(name, HDR_REPAIR2 % (name, '/'.join(exp)) + '# ' + why + '\n' + src)
        controls.append({'name': name, 'kind': 'natural', 'category': cat, 'card': flags, 'expect_class': exp,
                         'expect_drift': drift, 'expect_magnitude': mag, 'expect_class_pilot_rule': pil, 'why': why,
                         'scored': True, 'added': 'REPAIR2 2026-11-11 (FULL_PREREG_AMENDMENT_3, review MF3)'})
    for name, cat, flags, exp, drift, mag, pil, why, src in REPAIR5_NATURAL:
        write(name, HDR_REPAIR5 % (name, '/'.join(exp)) + '# ' + why + '\n' + src)
        controls.append({'name': name, 'kind': 'natural', 'category': cat, 'card': flags, 'expect_class': exp,
                         'expect_drift': drift, 'expect_magnitude': mag, 'expect_class_pilot_rule': pil, 'why': why,
                         'scored': True, 'added': 'REPAIR5 2026-11-11 (lead ruling LR1.4, FULL_PREREG_AMENDMENT_10)'})
    for name, cat, flags, exp, drift, mag, pil, why, src, switch, exp_sw in REPAIR6_NATURAL:
        write(name, HDR_REPAIR6 % (name, '/'.join(exp)) + '# ' + why + '\n' + src)
        controls.append({'name': name, 'kind': 'natural', 'category': cat, 'card': flags, 'expect_class': exp,
                         'expect_drift': drift, 'expect_magnitude': mag, 'expect_class_pilot_rule': pil, 'why': why,
                         'scored': True, 'added': 'REPAIR6 2026-11-12 (lead ruling LR16, FULL_PREREG_AMENDMENT_11)',
                         'lr16_switch': switch, 'expect_class_under_lr16_switch': exp_sw})
    for name, kind, a, b, exp, drift, mag, why in SW:
        if kind == 'noresult':
            body = V + 'if V < 3:\n    result = 1\n'
        elif kind == 'raise':
            body = V + 'if V >= 3:\n    raise ValueError("control: target raises")\nresult = 1\n'
        else:
            body = V + 'result = (%s) if V < 3 else (%s)\n' % (a, b)
        write(name, HDR % (name, '/'.join(exp)) + '# ' + why + '\n' + body)
        controls.append({'name': name, 'kind': 'switch', 'category': 'P-' if not drift else 'P+', 'card': {},
                         'expect_class': exp, 'expect_drift': drift, 'expect_magnitude': mag,
                         'expect_class_pilot_rule': None, 'why': why, 'scored': True})
    with open(os.path.join(HERE, 'controls.json'), 'w', encoding='utf-8') as f:
        json.dump({'written': '2026-11-11', 'by': 'pkg:VERIFY (4 dtype_significant controls added 2026-11-11 in the repair step, review MF5; 2 identity-key controls added 2026-11-11, Amendment 3; 4 row-identity controls added 2026-11-11, lead ruling LR1.4; 2 LR16 controls added 2026-11-12, lead ruling LR16)',
                   'note': 'expectations written from FULL_PREREG sections 3 and 9 before any run', 'controls': controls}, f, indent=1)
    print('wrote %d programs' % len(controls))


if __name__ == '__main__':
    sys.exit(main())
