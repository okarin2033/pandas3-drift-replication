# Task specifications for family QF1_STRING (stratum M, package TASKS_M1).
# Written 2026-11-11 by pkg:TASKS_M1; drafted_by pkg:TASKS_M1, status prepared.
# Each entry is turned into tasks/M1/<id>/{task.json, naive.py, reference.py} by build_tasks.py.
# 'checks' lists the task-specific property checks; the two generic checks are added by the builder.

FAMILY = 'QF1_STRING'

TASKS = [
# ------------------------------------------------------------------ S01 (slots 01, 06, 11, 16)
dict(
 id='M_QF1_01', row='S01', invited=['S01'], files=['QF1_STRING/members.csv'],
 text=("Tidy the members file: in every text column remove the spaces around the values and write each word with a leading "
       "capital letter (for example 'ZÜRICH  ' becomes 'Zürich'). Then, for each home city, count the members and add up their "
       "fees. Leave out members whose city is empty or '-'. `result` should be a table with the columns home_city, members and "
       "total_fee, one row per city."),
 allowed=['text column'], order=False, keys=[],
 intended=("Read members.csv, strip surrounding spaces and title-case the text columns (home_city is the one that matters), drop "
           "rows whose city is missing or '-', then group by the tidied city and report the number of members and the sum of fee "
           "per city: 8 cities, 226 members in total."),
 notes='home_city may be the index instead of a column; fee totals may be rounded to 2 decimals.',
 checks=[('n_groups_equals', {'n': 8}), ('counts_sum_to_rows', {'column': 'members', 'expected': 226}),
         ('columns_present', {'columns': ['home_city', 'members', 'total_fee']})],
 direction='HARM', reason='on 3.x the text columns are no longer detected by the type test, so city names stay untidied and split into many groups',
 naive='''import pandas as pd

df = pd.read_csv("members.csv")
for col in df.columns:
    if df[col].dtype == object:
        df[col] = df[col].str.strip().str.title()
df = df[df["home_city"].notna() & (df["home_city"] != "-")]
result = (df.groupby("home_city")
            .agg(members=("member_id", "count"), total_fee=("fee", "sum"))
            .reset_index())
''',
 ref='''import pandas as pd

df = pd.read_csv("members.csv")
city = df["home_city"].str.strip().str.title()
keep = city.notna() & (city != "-")
d = pd.DataFrame({"home_city": city[keep].tolist(), "fee": df.loc[keep, "fee"].tolist()})
g = d.groupby("home_city")["fee"]
out = pd.DataFrame({"members": g.size(), "total_fee": g.sum().round(2)})
out = out.sort_index().reset_index()
out["members"] = out["members"].astype("int64")
result = out
'''),
dict(
 id='M_QF1_06', row='S01', invited=['S01'], files=['QF1_STRING/price_list.csv'],
 text=("Clean the price list: in every text column remove the spaces around the values and convert the text to lower case. "
       "Then compute the average price per section, rounded to two decimals. `result` should be a Series indexed by section."),
 allowed=['text column'], order=False, keys=[],
 intended=("Read price_list.csv, strip and lower-case the text columns (section is the one that matters: dairy, pantry, drinks, "
           "bakery), group by the cleaned section and return the mean price per section rounded to 2 decimals (4 sections)."),
 notes='section may be a column instead of the index.',
 checks=[('n_groups_equals', {'n': 4}), ('numeric_in_range', {'columns': ['__values__'], 'min': 0, 'max': None})],
 direction='HARM', reason='on 3.x the type test finds no text column, so section labels keep their spaces and capitals and split into 12 groups',
 naive='''import pandas as pd

df = pd.read_csv("price_list.csv")
for c in df.columns:
    if df[c].dtype == "O":
        df[c] = df[c].str.strip().str.lower()
result = df.groupby("section")["price"].mean().round(2)
''',
 ref='''import pandas as pd

df = pd.read_csv("price_list.csv")
section = df["section"].str.strip().str.lower()
d = pd.DataFrame({"section": section.tolist(), "price": df["price"].tolist()})
result = d.groupby("section")["price"].mean().round(2).sort_index()
'''),
dict(
 id='M_QF1_11', row='S01', invited=['S01'], files=['QF1_STRING/members.csv'],
 text=("Some members were entered more than once with different capital letters or extra spaces in their names. Normalise "
       "every text column of the members file (remove surrounding spaces, capitalise each word) and count how many distinct "
       "full names remain. `result` should be that number (an integer)."),
 allowed=['text column'], order=False, keys=[],
 intended=("Strip and title-case full_name (and the other text columns), then count the distinct normalised full names: "
           "the answer is one integer."),
 notes='',
 checks=[('result_kind', {'kind': 'scalar'}), ('numeric_in_range', {'columns': ['__values__'], 'min': 1, 'max': 240})],
 direction='HARM', reason='on 3.x the object-type test skips the text columns, so case and space variants are counted as different names',
 naive='''import pandas as pd

df = pd.read_csv("members.csv")
text_cols = [c for c in df.columns if pd.api.types.is_object_dtype(df[c])]
for c in text_cols:
    df[c] = df[c].str.strip().str.title()
result = int(df["full_name"].nunique())
''',
 ref='''import pandas as pd

df = pd.read_csv("members.csv")
names = df["full_name"].str.strip().str.title()
result = int(len(set(names.dropna().tolist())))
'''),
dict(
 id='M_QF1_16', row='S01', invited=['S01'], files=['QF1_STRING/price_list.csv'],
 text=("Prepare the price list for a label printer: every text column must be in upper case with no spaces around the values; "
       "numbers stay unchanged. `result` should be the cleaned table with the same columns, sorted by sku."),
 allowed=['text column'], order=True, keys=['sku'],
 intended=("Strip and upper-case sku, item and section, keep price as it is, and return all 64 rows with the four columns "
           "sorted by sku ascending."),
 notes='the row index may be 0..63 or carried over from the file.',
 checks=[('n_groups_equals', {'n': 64}), ('columns_present', {'columns': ['sku', 'item', 'section', 'price']}),
         ('sorted_by', {'keys': ['sku'], 'ascending': [True]})],
 direction='HARM', reason='on 3.x the selection of object-typed columns is empty, so the text is printed unchanged',
 naive='''import pandas as pd

df = pd.read_csv("price_list.csv")
text_cols = df.dtypes[df.dtypes == object].index
for c in text_cols:
    df[c] = df[c].str.strip().str.upper()
result = df.sort_values("sku").reset_index(drop=True)
''',
 ref='''import pandas as pd

df = pd.read_csv("price_list.csv")
out = pd.DataFrame({
    "sku": [s.strip().upper() for s in df["sku"].tolist()],
    "item": [s.strip().upper() for s in df["item"].tolist()],
    "section": [s.strip().upper() for s in df["section"].tolist()],
    "price": df["price"].tolist(),
})
result = out.sort_values("sku", kind="mergesort").reset_index(drop=True)
'''),
# ------------------------------------------------------------------ S02 (slots 02, 07, 12)
dict(
 id='M_QF1_02', row='S02', invited=['S02'], files=['QF1_STRING/members.csv'],
 text=("Convert the members file into JSON text: a list with one JSON record per member, holding the keys member_id, full_name, "
       "home_city and fee, in file order. A city that is empty or '-' must appear as JSON null; all other values stay as they "
       "are. `result` should be that JSON text (a string)."),
 allowed=['JSON null'], order=False, keys=[],
 intended=("Build one record per member (240 records, file order) with member_id, full_name and fee unchanged and home_city "
           "unchanged except that empty cells and '-' become null, and serialise the list as JSON text."),
 notes='whitespace and key order inside the JSON text, and escaping of non-ASCII letters, may differ; fee may be written as 150 or 150.0.',
 checks=[('result_kind', {'kind': 'scalar'})],
 direction='HARM', reason='on 3.x the None written into the text column is stored as NaN, so the JSON text contains NaN instead of null (invalid JSON)',
 naive='''import json
import pandas as pd

df = pd.read_csv("members.csv")
df.loc[df["home_city"].str.strip() == "-", "home_city"] = None
df = df.where(pd.notnull(df), None)
result = json.dumps(df.to_dict(orient="records"), ensure_ascii=False)
''',
 ref='''import json
import pandas as pd

df = pd.read_csv("members.csv")
records = []
for mid, name, city, fee in zip(df["member_id"].tolist(), df["full_name"].tolist(), df["home_city"].tolist(), df["fee"].tolist()):
    if not isinstance(city, str) or city.strip() == "-":
        city = None
    records.append({"member_id": int(mid), "full_name": name, "home_city": city, "fee": float(fee)})
result = json.dumps(records, ensure_ascii=False)
'''),
dict(
 id='M_QF1_07', row='S02', invited=['S02'], files=['QF1_STRING/members.csv'],
 text=("Count the members per home city. Write the city names without surrounding spaces and with each word capitalised. "
       "Members whose city is empty or '-' are counted under the name 'Unknown'. `result` should be a Series indexed by city "
       "name with the member counts, sorted by city name."),
 allowed=[], order=True, keys=['__index__'],
 intended=("Tidy home_city (strip, title case), map empty cells and '-' to 'Unknown', count members per city and sort by city "
           "name: 9 labels (8 cities plus Unknown) whose counts add up to 240."),
 notes='city may be a column with a count column instead of a Series.',
 checks=[('n_groups_equals', {'n': 9}), ('counts_sum_to_rows', {'column': '__values__', 'expected': 240}),
         ('sorted_by', {'keys': ['__index__'], 'ascending': [True]})],
 direction='HARM', reason="on 3.x the None sentinel becomes NaN, the 'is None' test fails and the unknown members drop out of the counts",
 naive='''import pandas as pd

df = pd.read_csv("members.csv")
city = df["home_city"].str.strip()
city = city.where(city != "-", None)
city = city.where(city.notna(), None)
city = city.map(lambda v: "Unknown" if v is None else v).str.title()
result = city.value_counts().sort_index()
''',
 ref='''import pandas as pd

df = pd.read_csv("members.csv")
labels = []
for v in df["home_city"].tolist():
    if not isinstance(v, str) or v.strip() == "-":
        labels.append("Unknown")
    else:
        labels.append(v.strip().title())
counts = {}
for lab in labels:
    counts[lab] = counts.get(lab, 0) + 1
keys = sorted(counts)
result = pd.Series([counts[k] for k in keys], index=pd.Index(keys), dtype="int64")
'''),
dict(
 id='M_QF1_12', row='S02', invited=['S02'], files=['QF1_STRING/members.csv'],
 text=("List the member_id of every member whose home city is not known (the cell is empty or holds '-'). `result` should "
       "be a Python list of these ids in increasing order."),
 allowed=[], order=True, keys=['__values__'],
 intended="Select the members with an empty home_city or '-' (14 members) and return their member_id values as a sorted list.",
 notes='',
 checks=[('n_groups_equals', {'n': 14}), ('numeric_in_range', {'columns': ['__values__'], 'min': 5001, 'max': 5240}),
         ('sorted_by', {'keys': ['__values__'], 'ascending': [True]})],
 direction='HARM', reason='on 3.x the None placeholders become NaN, so the identity test for None finds no member',
 naive='''import pandas as pd

df = pd.read_csv("members.csv")
df["home_city"] = df["home_city"].str.strip().replace("-", None)
df = df.where(df.notna(), None)
result = sorted(int(m) for m, c in zip(df["member_id"], df["home_city"]) if c is None)
''',
 ref='''import pandas as pd

df = pd.read_csv("members.csv")
ids = []
for mid, city in zip(df["member_id"].tolist(), df["home_city"].tolist()):
    if not isinstance(city, str) or city.strip() == "-":
        ids.append(int(mid))
result = sorted(ids)
'''),
# ------------------------------------------------------------------ S03 (slots 03, 08, 13)
dict(
 id='M_QF1_03', row='S03', invited=['S03'], files=['QF1_STRING/members.csv'],
 text=("How many members live in each city? Tidy the city names first (remove surrounding spaces, capitalise each word). "
       "Members with an empty city or '-' are not counted. `result` should be a Series indexed by city with the counts."),
 allowed=[], order=False, keys=[],
 intended="Tidy home_city, drop empty and '-' cities and count members per city: 8 cities, 226 members in total.",
 notes='city may be a column with a count column instead of a Series.',
 checks=[('n_groups_equals', {'n': 8}), ('counts_sum_to_rows', {'column': '__values__', 'expected': 226})],
 direction='FIX', reason="on 2.x converting to text turns the empty cells into the city 'Nan'; 3.x keeps them missing so they drop out as asked",
 naive='''import pandas as pd

df = pd.read_csv("members.csv")
city = df["home_city"].astype(str).str.strip().str.title()
city = city[city != "-"]
result = city.value_counts().sort_index()
''',
 ref='''import pandas as pd

df = pd.read_csv("members.csv")
counts = {}
for v in df["home_city"].tolist():
    if isinstance(v, str) and v.strip() != "-":
        k = v.strip().title()
        counts[k] = counts.get(k, 0) + 1
keys = sorted(counts)
result = pd.Series([counts[k] for k in keys], index=pd.Index(keys), dtype="int64")
'''),
dict(
 id='M_QF1_08', row='S03', invited=['S03'], files=['QF1_STRING/members.csv'],
 text=("Give every distinct home city a number: tidy the names first (remove surrounding spaces, capitalise each word), then "
       "number the cities 0, 1, 2, ... in alphabetical order. Members whose city is empty or '-' get the number -1. `result` "
       "should be a table with the columns member_id and city_code, one row per member in file order."),
 allowed=[], order=False, keys=[],
 intended=("Tidy home_city; the 8 known cities in alphabetical order get codes 0-7; empty and '-' cities get -1; return "
           "member_id and city_code for all 240 members in file order."),
 notes='',
 checks=[('n_groups_equals', {'n': 240}), ('numeric_in_range', {'columns': ['city_code'], 'min': -1, 'max': 7}),
         ('columns_present', {'columns': ['member_id', 'city_code']})],
 direction='FIX', reason="on 2.x converting to text makes the empty cells a city called 'Nan' that takes a code and shifts the later codes",
 naive='''import pandas as pd

df = pd.read_csv("members.csv")
city = df["home_city"].astype(str).str.strip().str.title()
city = city.where(city != "-")
codes = city.astype("category").cat.codes
result = pd.DataFrame({"member_id": df["member_id"], "city_code": codes})
''',
 ref='''import pandas as pd

df = pd.read_csv("members.csv")
tidy = []
for v in df["home_city"].tolist():
    tidy.append(v.strip().title() if isinstance(v, str) and v.strip() != "-" else None)
order = sorted({t for t in tidy if t is not None})
code_of = {c: i for i, c in enumerate(order)}
codes = [code_of[t] if t is not None else -1 for t in tidy]
result = pd.DataFrame({"member_id": df["member_id"].astype("int64").tolist(), "city_code": codes})
result["city_code"] = result["city_code"].astype("int64")
'''),
dict(
 id='M_QF1_13', row='S03', invited=['S03'], files=['QF1_STRING/branch_sales.csv'],
 text=("For each branch, count the weeks whose sales figure is missing. Keep the branch codes exactly as written (five "
       "digits with leading zeros) and list only branches with at least one missing week. `result` should be a Series indexed "
       "by branch code with these counts."),
 allowed=['leading zeros'], order=False, keys=[],
 intended=("Read branch_code as text, select the rows whose sales cell is empty (6 rows) and count them per branch code: "
           "5 branches, counts adding up to 6."),
 notes='branch_code may be a column with a count column instead of a Series.',
 checks=[('n_groups_equals', {'n': 5}), ('counts_sum_to_rows', {'column': '__values__', 'expected': 6})],
 direction='HARM', reason="on 3.x converting the numbers to text keeps missing values as NaN, so the comparison with the text 'nan' finds nothing",
 naive='''import pandas as pd

df = pd.read_csv("branch_sales.csv", dtype={"branch_code": str})
missing = df["sales"].astype(str).str.strip().isin(["", "nan", "NaN", "None"])
result = df[missing].groupby("branch_code").size()
''',
 ref='''import pandas as pd

df = pd.read_csv("branch_sales.csv", dtype={"branch_code": str})
counts = {}
for code, sales in zip(df["branch_code"].tolist(), df["sales"].tolist()):
    if pd.isna(sales):
        counts[code] = counts.get(code, 0) + 1
keys = sorted(counts)
result = pd.Series([counts[k] for k in keys], index=pd.Index(keys), dtype="int64")
'''),
# ------------------------------------------------------------------ S06 (slots 04, 09, 14)
dict(
 id='M_QF1_04', row='S06', invited=['S06'], files=['QF1_STRING/branch_sales.csv'],
 text=("Total the sales of each branch over all weeks. The branch codes must keep their leading zeros exactly as written in "
       "the file (for example '01005'). There are only a few distinct branches, so read the branch code as a categorical "
       "column. `result` should be a Series indexed by branch code with the total sales."),
 allowed=['leading zeros', 'categorical'], order=False, keys=[],
 intended=("Read branch_code as text labels (12 branches, codes with leading zeros), sum sales per branch (missing sales "
           "ignored) and return the totals indexed by the code text."),
 notes='branch_code may be a column; totals may be integers or floats.',
 checks=[('n_groups_equals', {'n': 12}), ('numeric_in_range', {'columns': ['__values__'], 'min': 0, 'max': None})],
 direction='HARM', reason='on 3.1 reading the codes as categories infers integer categories, so the leading zeros are lost',
 naive='''import pandas as pd

df = pd.read_csv("branch_sales.csv", dtype={"branch_code": "category"})
result = df.groupby("branch_code", observed=True)["sales"].sum()
''',
 ref='''import pandas as pd

df = pd.read_csv("branch_sales.csv", dtype={"branch_code": str})
tot = {}
for code, s in zip(df["branch_code"].tolist(), df["sales"].tolist()):
    tot[code] = tot.get(code, 0.0) + (0.0 if pd.isna(s) else float(s))
keys = sorted(tot)
result = pd.Series([tot[k] for k in keys], index=pd.Index(keys), dtype="float64")
'''),
dict(
 id='M_QF1_09', row='S06', invited=['S06'], files=['QF1_STRING/members.csv'],
 text=("How many members pay each yearly fee? There are only a few fee levels, so treat the fee as a categorical label and "
       "show each fee exactly as it is written in the file, with both decimals (for example '104.50'). `result` should be a "
       "Series indexed by the fee text with the number of members."),
 allowed=['categorical'], order=False, keys=[],
 intended=("Read fee as text, count the members per fee text (12 fee levels, 240 members) and index the counts by the fee "
           "exactly as written, e.g. '104.50'."),
 notes='the fee may be a column with a count column instead of a Series.',
 checks=[('n_groups_equals', {'n': 12}), ('counts_sum_to_rows', {'column': '__values__', 'expected': 240})],
 direction='HARM', reason="on 3.1 categories read from the file become numbers, so '104.50' turns into 104.5",
 naive='''import pandas as pd

df = pd.read_csv("members.csv", dtype={"fee": "category"})
result = df["fee"].value_counts().sort_index()
''',
 ref='''import pandas as pd

df = pd.read_csv("members.csv", dtype={"fee": str})
counts = {}
for f in df["fee"].tolist():
    counts[f] = counts.get(f, 0) + 1
keys = sorted(counts, key=float)
result = pd.Series([counts[k] for k in keys], index=pd.Index(keys), dtype="int64")
'''),
dict(
 id='M_QF1_14', row='S06', invited=['S06'], files=['QF1_STRING/branch_sales.csv'],
 text=("Make a wide table of weekly sales: one row per week (1-15) and one column per branch, with the branch codes as column "
       "names exactly as written in the file (five digits with leading zeros). The branch codes are a fixed set of labels, so "
       "read them as categories. A missing sales figure counts as 0, and several rows for the same branch and week are added "
       "up. `result` should be that table, rows in week order."),
 allowed=['leading zeros'], order=True, keys=['__index__'],
 intended=("Read branch_code as text, treat missing sales as 0, sum sales per (week, branch) and pivot to 15 rows (weeks "
           "1-15, ascending) by 12 columns named by the branch code text, with 0 where a branch has no row in a week."),
 notes='week may be a column instead of the index; column order may differ.',
 checks=[('n_groups_equals', {'n': 15}), ('no_nulls', {'columns': []}), ('sorted_by', {'keys': ['__index__'], 'ascending': [True]})],
 direction='HARM', reason='on 3.1 the categorical codes are inferred as integers, so the column names lose their leading zeros',
 naive='''import pandas as pd

df = pd.read_csv("branch_sales.csv", dtype={"branch_code": "category"})
df["sales"] = df["sales"].fillna(0)
result = df.pivot_table(index="week", columns="branch_code", values="sales", aggfunc="sum", fill_value=0, observed=False)
''',
 ref='''import pandas as pd

df = pd.read_csv("branch_sales.csv", dtype={"branch_code": str})
weeks = sorted(set(int(w) for w in df["week"].tolist()))
codes = sorted(set(df["branch_code"].tolist()))
cell = {}
for w, c, s in zip(df["week"].tolist(), df["branch_code"].tolist(), df["sales"].tolist()):
    cell[(int(w), c)] = cell.get((int(w), c), 0.0) + (0.0 if pd.isna(s) else float(s))
data = {c: [cell.get((w, c), 0.0) for w in weeks] for c in codes}
out = pd.DataFrame(data, index=pd.Index(weeks), columns=codes)
out.columns.name = "branch_code"
result = out
'''),
# ------------------------------------------------------------------ O01 (slots 05, 10, 15)
dict(
 id='M_QF1_05', row='O01', invited=['O01'], files=['QF1_STRING/price_list.csv'],
 text=("Export the price list as JSON text: one JSON record per item holding the keys sku, item, section and price, in file "
       "order, leaving the text values as they are. Read the prices as exact decimal numbers (no binary rounding), and write "
       "them into the JSON as numbers, not as text. To check the export, `result` should be a pandas DataFrame built from "
       "the parsed JSON records."),
 allowed=['decimal numbers'], order=False, keys=[],
 intended=("Produce 64 records in file order with sku, item and section unchanged and price as a JSON number (e.g. 9.5 for "
           "'9.50'); result is the DataFrame built from the parsed records (64 rows, columns sku, item, section, price)."),
 notes='a price number may be 9.5 or 9.50; text values may keep their surrounding spaces.',
 checks=[('n_groups_equals', {'n': 64}), ('numeric_in_range', {'columns': ['price'], 'min': 0, 'max': None})],
 direction='HARM', reason="on 3.x JSON export writes decimal values as text such as '9.50', against the request for numbers",
 naive='''import json
from decimal import Decimal
import pandas as pd

df = pd.read_csv("price_list.csv", converters={"price": Decimal})
result = pd.DataFrame(json.loads(df.to_json(orient="records")))
''',
 ref='''import json
import pandas as pd

df = pd.read_csv("price_list.csv", dtype={"price": str})
records = [{"sku": s, "item": i, "section": sec, "price": float(p)}
           for s, i, sec, p in zip(df["sku"].tolist(), df["item"].tolist(), df["section"].tolist(), df["price"].tolist())]
result = pd.DataFrame(json.loads(json.dumps(records)), columns=["sku", "item", "section", "price"])
'''),
dict(
 id='M_QF1_10', row='O01', invited=['O01'], files=['QF1_STRING/price_list.csv'],
 text=("Add up the prices of the items in each section exactly, using decimal arithmetic so that no rounding error appears. "
       "Write the section names in lower case without surrounding spaces. Produce JSON text that maps each section to its "
       "total as a JSON number, and set `result` to the parsed JSON (a Python dict)."),
 allowed=['decimal arithmetic'], order=False, keys=[],
 intended=("Clean section (strip, lower), sum the prices per section exactly (4 sections) and return a dict section -> total "
           "as a number, e.g. {'bakery': ..., 'dairy': ...}."),
 notes='totals may be written with or without trailing zeros.',
 checks=[('n_groups_equals', {'n': 4}), ('numeric_in_range', {'columns': ['__values__'], 'min': 0, 'max': None})],
 direction='HARM', reason='on 3.x the decimal totals are written into the JSON as text, not as numbers',
 naive='''import json
from decimal import Decimal
import pandas as pd

df = pd.read_csv("price_list.csv", converters={"price": Decimal})
df["section"] = df["section"].str.strip().str.lower()
totals = df.groupby("section")["price"].sum()
result = json.loads(totals.to_json())
''',
 ref='''import json
from decimal import Decimal
import pandas as pd

df = pd.read_csv("price_list.csv", dtype={"price": str})
tot = {}
for sec, p in zip(df["section"].tolist(), df["price"].tolist()):
    k = sec.strip().lower()
    tot[k] = tot.get(k, Decimal("0")) + Decimal(p)
result = json.loads(json.dumps({k: float(tot[k]) for k in sorted(tot)}))
'''),
dict(
 id='M_QF1_15', row='O01', invited=['O01'], files=['QF1_STRING/price_list.csv'],
 text=("Produce JSON text that maps each sku to its price, keeping the price exactly as written in the file, two decimals "
       "included ('9.50' must stay '9.50'), so read the prices as exact decimals rather than floating-point numbers. `result` "
       "should be the parsed JSON (a Python dict from sku to price)."),
 allowed=['decimals'], order=False, keys=[],
 intended="Return a dict with the 64 skus as keys and the price text exactly as written (two decimals, e.g. '9.50') as values.",
 notes="the price may be given as text '9.50'; a number would lose the trailing zero.",
 checks=[('n_groups_equals', {'n': 64})],
 direction='FIX', reason="on 2.x the decimals are exported as floating-point numbers and lose the written form ('9.50' becomes 9.5); 3.x keeps the text",
 naive='''import json
from decimal import Decimal
import pandas as pd

df = pd.read_csv("price_list.csv", converters={"price": Decimal})
result = json.loads(df.set_index("sku")["price"].to_json())
''',
 ref='''import json
import pandas as pd

df = pd.read_csv("price_list.csv", dtype={"price": str})
result = json.loads(json.dumps({s: p for s, p in zip(df["sku"].tolist(), df["price"].tolist())}))
'''),
]
