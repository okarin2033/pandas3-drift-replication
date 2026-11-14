# Task specifications for family QF7_INDEX_REDUCE (package TASKS_M2). Written 2026-11-11 by pkg:TASKS_M2.
# Status: prepared. Consumed by build.py (writes tasks/M2/<id>/).
# Rows and slots from mechanisms/confirm/quota_allocation.tsv: I01 -> 01 05 09 13; I02 -> 02 06 10 14; I05 -> 03 07 11 15;
# I06 -> 04 08 12 16. I06 was confirmed on E1 (3.1.x) only.

OL = 'QF7_INDEX_REDUCE/order_lines.csv'
PR = 'QF7_INDEX_REDUCE/parcel_rates.csv'
CC = 'QF7_INDEX_REDUCE/code_changes.csv'
SQ = 'QF7_INDEX_REDUCE/storage_quota.csv'

G = [{'check': 'no_null_text', 'args': {}}, {'check': 'no_all_missing_column', 'args': {}}]

REF_OL = '''import csv
import numpy as np
import pandas as pd

with open("order_lines.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))


def col(rs, name):
    return np.array([float(r[name]) for r in rs if r[name].strip() != ""], dtype="float64")
'''

REF_PR = '''import csv
import numpy as np
import pandas as pd

with open("parcel_rates.csv", encoding="utf-8", newline="") as f:
    rows = [(float(r["weight_kg"]), int(r["zones"]), float(r["fee"]) if r["fee"].strip() != "" else None)
            for r in csv.DictReader(f)]
'''

REF_CC = '''import csv
import numpy as np
import pandas as pd

with open("code_changes.csv", encoding="utf-8", newline="") as f:
    rows = [(r["product"], int(r["stock_qty"]), int(r["old_code"]), int(r["new_code"])) for r in csv.DictReader(f)]
'''

REF_SQ = '''import csv
import numpy as np
import pandas as pd

with open("storage_quota.csv", encoding="utf-8", newline="") as f:
    rows = [(int(r["account_id"]), r["active"] == "True", int(r["quota_bytes"]), int(r["used_bytes"]))
            for r in csv.DictReader(f)]
# exact Python integers: active counts 1 or 0
control = [(a, int(act) + q + u) for a, act, q, u in rows]
'''

NAIVE_OL = '''import numpy as np
import pandas as pd

df = pd.read_csv("order_lines.csv")
'''

NAIVE_PR = '''import pandas as pd

df = pd.read_csv("parcel_rates.csv")
'''

NAIVE_CC = '''import pandas as pd

df = pd.read_csv("code_changes.csv")
lookup = df.set_index("old_code")
'''

NAIVE_SQ = '''import pandas as pd

df = pd.read_csv("storage_quota.csv")
control = df[["active", "quota_bytes", "used_bytes"]].sum(axis=1)
'''

SQ_TEXT = ("Each account gets a control total: its active flag counted as 1 (True) or 0 (False), plus quota_bytes, plus "
           "used_bytes. ")

SPECS = [
    # ------------------------------------------------------------ I01 (numpy reductions on a DataFrame reduce over both axes)
    dict(
        id='M_QF7_01', row='I01', files=[OL],
        text=("Give the total quantity and the total amount over all order lines, ignoring empty cells. `result` should be "
              "a Series with the two totals, indexed by quantity and amount."),
        allowed=[], invited=['I01'], order=False, keys=[], dtype=False,
        intended="Column sums of quantity and amount over the non-empty cells of all 300 lines; two values.",
        av_notes="totals to 6 significant digits; a two-entry dict or one-row table is acceptable.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 2}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': None}}],
        direction='HARM',
        reason="np.sum on a DataFrame gave per-column totals on 2.x; on 3.x it adds up both columns into one number.",
        naive=NAIVE_OL + '''result = np.sum(df[["quantity", "amount"]])
''',
        ref=REF_OL + '''result = pd.Series(np.array([float(np.sum(col(rows, "quantity"))), float(np.sum(col(rows, "amount")))],
                            dtype="float64"), index=["quantity", "amount"])
'''),
    dict(
        id='M_QF7_05', row='I01', files=[OL],
        text=("Give the population standard deviation (dividing by the number of values) of quantity and of amount over all "
              "order lines, ignoring empty cells. `result` should be a Series indexed by quantity and amount."),
        allowed=[], invited=['I01'], order=False, keys=[], dtype=False,
        intended="For each of quantity and amount separately: standard deviation with divisor n over its non-empty cells.",
        av_notes="values to 6 significant digits.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 2}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': None}}],
        direction='HARM',
        reason=("np.std on a DataFrame gave one value per column on 2.x; on 3.x it pools both columns into one standard "
                "deviation."),
        naive=NAIVE_OL + '''result = np.std(df[["quantity", "amount"]])
''',
        ref=REF_OL + '''result = pd.Series(np.array([float(np.std(col(rows, "quantity"))), float(np.std(col(rows, "amount")))],
                            dtype="float64"), index=["quantity", "amount"])
'''),
    dict(
        id='M_QF7_09', row='I01', files=[OL],
        text=("Tidy the product names (remove surrounding spaces, lower case). For the lines of product blender, give the "
              "total quantity and the total amount, ignoring empty cells. `result` should be a Series with the two totals, "
              "indexed by quantity and amount."),
        allowed=[], invited=['I01'], order=False, keys=[], dtype=False,
        intended="Restrict to the 36 lines whose tidied product is 'blender'; column sums of quantity and amount.",
        av_notes="totals to 6 significant digits.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 2}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': None}}],
        direction='HARM',
        reason="np.sum on the filtered DataFrame returned per-column totals on 2.x; on 3.x a single grand total.",
        naive=NAIVE_OL + '''df["product"] = df["product"].str.strip().str.lower()
blender = df[df["product"] == "blender"]
result = np.sum(blender[["quantity", "amount"]])
''',
        ref=REF_OL + '''sub = [r for r in rows if r["product"].strip().lower() == "blender"]
result = pd.Series(np.array([float(np.sum(col(sub, "quantity"))), float(np.sum(col(sub, "amount")))], dtype="float64"),
                   index=["quantity", "amount"])
'''),
    dict(
        id='M_QF7_13', row='I01', files=[OL],
        text=("For the order lines with an amount above 100, give the population variance (dividing by the number of values) "
              "of quantity and of amount, ignoring empty cells. `result` should be a Series indexed by quantity and amount."),
        allowed=[], invited=['I01'], order=False, keys=[], dtype=False,
        intended=("Restrict to the 223 lines with amount > 100; for quantity and amount separately the variance with divisor "
                  "n over the non-empty cells."),
        av_notes="values to 6 significant digits.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 2}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': None}}],
        direction='HARM',
        reason="np.var on a DataFrame gave a variance per column on 2.x; on 3.x one variance of all cells together.",
        naive=NAIVE_OL + '''big = df[df["amount"] > 100]
result = np.var(big[["quantity", "amount"]])
''',
        ref=REF_OL + '''sub = [r for r in rows if r["amount"].strip() != "" and float(r["amount"]) > 100]
result = pd.Series(np.array([float(np.var(col(sub, "quantity"))), float(np.var(col(sub, "amount")))], dtype="float64"),
                   index=["quantity", "amount"])
'''),
    # ------------------------------------------------------------ I02 (integer slice on a float index is positional)
    dict(
        id='M_QF7_02', row='I02', files=[PR],
        text=("Give the fee for every weight from 10 kg up to 30 kg. `result` should be a Series of fees indexed by "
              "weight_kg, in the order of the file."),
        allowed=[], invited=['I02'], order=False, keys=[], dtype=False,
        intended="The 44 rows with 10 <= weight_kg <= 30 (weights are never whole numbers): fee indexed by weight_kg.",
        av_notes="weight_kg may be a column; empty fees stay missing.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 44}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['weight_kg'], 'min': 10, 'max': 30}}],
        direction='HARM',
        reason=("s[10:30] on a float index selected weights 10-30 by label on 2.x; on 3.x it selects rows 10 to 29 by "
                "position."),
        naive=NAIVE_PR + '''fees = df.set_index("weight_kg")["fee"]
result = fees[10:30]
''',
        ref=REF_PR + '''sel = [r for r in rows if 10 <= r[0] <= 30]
result = pd.Series(np.array([np.nan if r[2] is None else r[2] for r in sel], dtype="float64"),
                   index=pd.Index(np.array([r[0] for r in sel], dtype="float64"), name="weight_kg"))
'''),
    dict(
        id='M_QF7_06', row='I02', files=[PR],
        text=("What is the average fee for parcels weighing from 5 kg up to 15 kg (empty fees ignored)? `result` should be "
              "that number."),
        allowed=[], invited=['I02'], order=False, keys=[], dtype=False,
        intended="Mean of the non-empty fees of the 22 rows with 5 <= weight_kg <= 15.",
        av_notes="to 6 significant digits.",
        checks=G + [{'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': None}},
                    {'check': 'result_kind', 'args': {'kind': 'scalar'}}],
        direction='HARM',
        reason=("The integer slice on the weight index meant weights 5-15 on 2.x; on 3.x it is positions 5-14, so other "
                "parcels are averaged."),
        naive=NAIVE_PR + '''fees = df.set_index("weight_kg")["fee"]
result = float(fees[5:15].mean())
''',
        ref=REF_PR + '''vals = [r[2] for r in rows if 5 <= r[0] <= 15 and r[2] is not None]
result = float(sum(vals) / len(vals))
'''),
    dict(
        id='M_QF7_10', row='I02', files=[PR],
        text=("What is the highest fee for parcels weighing up to 12 kg? `result` should be that number."),
        allowed=[], invited=['I02'], order=False, keys=[], dtype=False,
        intended="Maximum non-empty fee among the 26 rows with weight_kg <= 12.",
        av_notes="to 6 significant digits.",
        checks=G + [{'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': None}},
                    {'check': 'result_kind', 'args': {'kind': 'scalar'}}],
        direction='HARM',
        reason="fees[:12] was label-based (weights up to 12 kg) on 2.x; on 3.x it is the first 12 rows only.",
        naive=NAIVE_PR + '''fees = df.set_index("weight_kg")["fee"]
result = float(fees[:12].max())
''',
        ref=REF_PR + '''result = float(max(r[2] for r in rows if r[0] <= 12 and r[2] is not None))
'''),
    dict(
        id='M_QF7_14', row='I02', files=[PR],
        text=("For the parcels weighing from 20 kg up to 40 kg, count the price rows for each zones value. `result` should be "
              "a Series of counts indexed by zones, ordered by zones from 1 to 5."),
        allowed=[], invited=['I02'], order=True, keys=['zones'], dtype=False,
        intended="Among the 46 rows with 20 <= weight_kg <= 40, the number of rows per zones value (1-5), ascending by zones.",
        av_notes="zones may be a column; a zones value with no row may be omitted or shown as 0.",
        checks=G + [{'check': 'counts_sum_to_rows', 'args': {'column': '__values__', 'expected': 46}},
                    {'check': 'sorted_by', 'args': {'keys': ['zones'], 'ascending': [True]}},
                    {'check': 'values_in_set', 'args': {'column': 'zones', 'values': [1, 2, 3, 4, 5]}}],
        direction='HARM',
        reason=("table[20:40] on the float weight index selected 20-40 kg by label on 2.x; on 3.x it takes rows 20-39 by "
                "position, so the counts describe other parcels."),
        naive=NAIVE_PR + '''table = df.set_index("weight_kg")
result = table[20:40]["zones"].value_counts().sort_index()
''',
        ref=REF_PR + '''sel = [r[1] for r in rows if 20 <= r[0] <= 40]
zs = sorted(set(sel))
result = pd.Series(np.array([sel.count(z) for z in zs], dtype="int64"), index=pd.Index(np.array(zs, dtype="int64"), name="zones"))
'''),
    # ------------------------------------------------------------ I05 (Index vs Series comparison returns a Series)
    dict(
        id='M_QF7_03', row='I05', files=[CC],
        text=("Index the table by old_code so that it can be used as a lookup of the new code. Then add a column unchanged "
              "to the original table, True where new_code equals old_code. `result` should be the original table (same "
              "rows, same order) with the added column unchanged."),
        allowed=[], invited=['I05'], order=False, keys=[], dtype=False,
        intended=("The 150 rows of code_changes.csv with columns product, stock_qty, old_code, new_code and a boolean column "
                  "unchanged = (new_code == old_code); 100 rows are True."),
        av_notes="row order and row labels are free; unchanged may be True/False or 1/0.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 150}},
                    {'check': 'columns_present', 'args': {'columns': ['product', 'old_code', 'new_code', 'unchanged']}},
                    {'check': 'no_nulls', 'args': {'columns': ['unchanged']}},
                    {'check': 'values_in_set', 'args': {'column': 'unchanged', 'values': [True, False]}}],
        direction='HARM',
        reason=("Comparing the old_code index with the new_code column gave a plain array on 2.x, assigned by position; on "
                "3.x it is a Series labelled by old codes, which aligns to nothing in the original table and fills the "
                "column with missing values."),
        naive=NAIVE_CC + '''df["unchanged"] = lookup.index == lookup["new_code"]
result = df
''',
        ref=REF_CC + '''result = pd.DataFrame({"product": [r[0] for r in rows], "stock_qty": np.array([r[1] for r in rows], dtype="int64"),
                       "old_code": np.array([r[2] for r in rows], dtype="int64"),
                       "new_code": np.array([r[3] for r in rows], dtype="int64"),
                       "unchanged": np.array([r[2] == r[3] for r in rows], dtype="bool")})
'''),
    dict(
        id='M_QF7_07', row='I05', files=[CC],
        text=("Index the table by old_code so that it can be used as a lookup of the new code. Build a table with one row "
              "per product row of the file: the column product and a column changed that is True where new_code differs "
              "from old_code. `result` should be this two-column table, in file order."),
        allowed=[], invited=['I05'], order=False, keys=[], dtype=False,
        intended="150 rows: product and changed = (new_code != old_code); 50 rows are True.",
        av_notes="row labels are free; changed may be True/False or 1/0.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 150}},
                    {'check': 'columns_present', 'args': {'columns': ['product', 'changed']}},
                    {'check': 'no_nulls', 'args': {'columns': ['changed']}},
                    {'check': 'values_in_set', 'args': {'column': 'changed', 'values': [True, False]}}],
        direction='HARM',
        reason=("The index-vs-column comparison is a plain array on 2.x; on 3.x it is a Series labelled by old codes, so the "
                "DataFrame constructor aligns it against the product column's row numbers and doubles the rows with "
                "missing values."),
        naive=NAIVE_CC + '''changed = lookup.index != lookup["new_code"]
result = pd.DataFrame({"product": df["product"], "changed": changed})
''',
        ref=REF_CC + '''result = pd.DataFrame({"product": [r[0] for r in rows], "changed": np.array([r[2] != r[3] for r in rows], dtype="bool")})
'''),
    dict(
        id='M_QF7_11', row='I05', files=[CC],
        text=("Index the table by old_code so that it can be used as a lookup of the new code. What is the total stock_qty "
              "of the product rows whose code did not change (new_code equal to old_code)? `result` should be that number."),
        allowed=[], invited=['I05'], order=False, keys=[], dtype=False,
        intended="Sum of stock_qty over the 100 rows with new_code == old_code.",
        av_notes="a whole number.",
        checks=G + [{'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 1, 'max': None}},
                    {'check': 'result_kind', 'args': {'kind': 'scalar'}}],
        direction='HARM',
        reason=("Multiplying stock_qty by the index-vs-column comparison worked by position on 2.x; on 3.x the comparison "
                "is a Series labelled by old codes, the product aligns on labels and the sum collapses to 0."),
        naive=NAIVE_CC + '''same = lookup.index == lookup["new_code"]
result = int((df["stock_qty"] * same).sum())
''',
        ref=REF_CC + '''result = int(sum(r[1] for r in rows if r[2] == r[3]))
'''),
    dict(
        id='M_QF7_15', row='I05', files=[CC],
        text=("Index the table by old_code so that it can be used as a lookup of the new code. For every row, in file order, "
              "tell whether the new code is higher than the old code. `result` should be the sequence of True/False values."),
        allowed=[], invited=['I05'], order=False, keys=[], dtype=False,
        intended="150 booleans in file order: new_code > old_code.",
        av_notes="a list, array or Series of 150 booleans is acceptable; labels of a Series are free.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 150}},
                    {'check': 'no_nulls', 'args': {'columns': []}}],
        direction='BOTH',
        reason=("The values are the same on both versions; only the container changes (NumPy array on 2.x, Series labelled "
                "by old codes on 3.x), and the task accepts either."),
        naive=NAIVE_CC + '''result = lookup.index < lookup["new_code"]
''',
        ref=REF_CC + '''result = np.array([r[3] > r[2] for r in rows], dtype="bool")
'''),
    # ------------------------------------------------------------ I06 (row-wise sum of bool + int64 at the int64 limit, 3.1)
    dict(
        id='M_QF7_04', row='I06', files=[SQ],
        text=(SQ_TEXT + "`result` should be a Series of control totals indexed by account_id, with exact whole numbers."),
        allowed=[], invited=['I06'], order=False, keys=[], dtype=False,
        intended=("For each of the 150 accounts: (1 if active else 0) + quota_bytes + used_bytes as an exact integer (the "
                  "23 unlimited accounts exceed the 64-bit range)."),
        av_notes="account_id may be a column; totals must be exact integers.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 150}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': None}}],
        direction='HARM',
        reason=("The row-wise sum over a frame mixing a true/false column and integers used exact Python integers on 2.x; on "
                "3.1 it uses 64-bit integers and the unlimited accounts wrap around to negative totals."),
        naive=NAIVE_SQ + '''control.index = df["account_id"]
result = control
''',
        ref=REF_SQ + '''result = pd.Series([c for _, c in control], index=pd.Index(np.array([a for a, _ in control], dtype="int64"),
                   name="account_id"), dtype="object")
'''),
    dict(
        id='M_QF7_08', row='I06', files=[SQ],
        text=(SQ_TEXT + "How many accounts have a control total above 1,000,000,000,000? `result` should be that number."),
        allowed=[], invited=['I06'], order=False, keys=[], dtype=False,
        intended="Number of accounts whose exact control total exceeds 10**12.",
        av_notes="a whole number.",
        checks=G + [{'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': 150}},
                    {'check': 'result_kind', 'args': {'kind': 'scalar'}}],
        direction='HARM',
        reason=("On 3.1 the row-wise sum of a true/false column with 64-bit integers wraps around for the unlimited accounts, "
                "so their totals become negative and are not counted; 2.x summed exactly."),
        naive=NAIVE_SQ + '''result = int((control > 10**12).sum())
''',
        ref=REF_SQ + '''result = int(sum(1 for _, c in control if c > 10**12))
'''),
    dict(
        id='M_QF7_12', row='I06', files=[SQ],
        text=(SQ_TEXT + "Give the grand total of the control totals over all accounts, as an exact whole number. `result` "
              "should be that number."),
        allowed=[], invited=['I06'], order=False, keys=[], dtype=False,
        intended="Exact integer sum of the 150 control totals (larger than the 64-bit range).",
        av_notes="must be exact; a Python int is expected.",
        checks=G + [{'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': None}},
                    {'check': 'result_kind', 'args': {'kind': 'scalar'}}],
        direction='HARM',
        reason=("The per-account totals overflow 64-bit integers on 3.1 (exact Python integers on 2.x), so the grand total "
                "is wrong on 3.1."),
        naive=NAIVE_SQ + '''result = int(control.sum())
''',
        ref=REF_SQ + '''result = int(sum(c for _, c in control))
'''),
    dict(
        id='M_QF7_16', row='I06', files=[SQ],
        text=(SQ_TEXT + "Add up the control totals separately for the active and the inactive accounts. `result` should be a "
              "Series indexed by the active value (False, True) with exact whole numbers."),
        allowed=[], invited=['I06'], order=False, keys=[], dtype=False,
        intended="Exact integer sums of the control totals for active == False and for active == True.",
        av_notes="active may be a column; sums must be exact.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 2}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': None}}],
        direction='HARM',
        reason=("The control totals of unlimited accounts wrap around in 64-bit integers on 3.1 (exact on 2.x), so both "
                "group sums are wrong on 3.1."),
        naive=NAIVE_SQ + '''result = control.groupby(df["active"]).sum()
''',
        ref=REF_SQ + '''keys = [False, True]
sums = [sum(c for (a, act, q, u), (_, c) in zip(rows, control) if act == k) for k in keys]
result = pd.Series(sums, index=pd.Index(np.array(keys, dtype="bool"), name="active"), dtype="object")
'''),
]
