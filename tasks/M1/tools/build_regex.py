# Exposure regexes (FULL_PREREG 4.4(c)) for every SILENT catalogue row of QF1_STRING, QF2_DATETIME, QF3_COW, QF4_GROUPBY.
# Written 2026-11-11 by pkg:TASKS_M1; drafted_by pkg:TASKS_M1, status prepared.
# Writes tasks/M1/exposure_regex_part.tsv (schema conventions/schema/exposure_regex.tsv.schema.json) after testing each regex:
#   matches_naive     = naive.py of the tasks whose invited_ids_author contain the row that match / all such naive.py
#   matches_reference = reference.py of the same tasks that match / all
# and tasks/M1/logs/regex_check.tsv with, per row, the matches on the T2 minimal program and its F-main adaptation
# (mechanisms/confirm/<id>.py, fmain/<id>.py; information) and every other M1 naive/reference the regex matches.
# Patterns are applied as harness/exposure_scan.py does: re.compile(rx, re.MULTILINE).search(program_text).
#   python3 -I -B tasks/M1/tools/build_regex.py   (exit 1 if a regex misses a naive solution of its row)
import csv, json, os, re, sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
M1 = os.path.dirname(TOOLS)
STUDY = os.path.dirname(os.path.dirname(M1))
B = r'\[(?:[^\[\]\n]|\[[^\[\]\n]*\])+\]'          # one bracket subscript, one nesting level allowed
P = r'\((?:[^()\n]|\([^()\n]*\))*\)'               # one call argument list, one nesting level allowed

REGEX = [
 # id, family, regex, note
 ('S01', 'QF1_STRING', r'dtypes?\s*[!=]=\s*(?:object\b|np\.object_|["\'](?:O|object)["\'])|is_object_dtype\(|dtype\.kind\s*[!=]=\s*["\']O["\']',
  'equality test of a column type with object / "O", is_object_dtype, or dtype.kind == "O" (select_dtypes("object") is not matched: it also selects the new text type)'),
 ('S02', 'QF1_STRING', r'\.where\([^\n]*,\s*None\s*\)|\.replace\([^\n]*,\s*None\s*\)|\.replace\(\s*\{[^\n]*:\s*None\b|\.loc' + B + r'\s*=\s*None\b|\.isin\(\[[^\]\n]*(?<!["\'])\bNone\b(?!["\'])|[!=]=\s*None\b|lambda[^\n]*\bis\s+(?:not\s+)?None\b|\bfor\b[^\n]*\bif\s+\w+\s+is\s+(?:not\s+)?None\b',
  'None written into a column (where/replace/loc) or None used as the missing-value test (is None in a lambda or comprehension, == None, isin([None]))'),
 ('S03', 'QF1_STRING', r'\.astype\(\s*(?:str|["\']str["\']|["\']U["\'])\s*\)',
  'astype(str) / astype("str")'),
 ('S04', 'QF1_STRING', r'\.values\s*(?:[!=]=|\.tolist\(\))|np\.(?:where|array_equal|unique)\([^\n]*\.values\b',
  'NumPy semantics on .values (no task: row NOT_REPRODUCED)'),
 ('S05', 'QF1_STRING', r'\.str\.(?:extract|extractall|contains|match|fullmatch|findall|replace|count|split|rsplit)\([^\n]*\\[wdsbWDSB]',
  'str regex methods with \\w \\d \\s \\b classes (no task: row NOT_REPRODUCED)'),
 ('S06', 'QF1_STRING', r'read_csv\([^)]*dtype\s*=\s*(?:["\']category["\']|\{[^}]*["\']category["\'])',
  'read_csv with dtype "category" (whole file or per column)'),
 ('O01', 'QF1_STRING', r'(?s)\A(?=.*\bDecimal\b).*?\.to_json\(|json_normalize\(|read_table\(',
  'to_json in a program that uses Decimal; json_normalize; read_table'),
 ('D01', 'QF2_DATETIME', r'\.view\(\s*["\'](?:int64|i8|<i8)["\']\s*\)|\.asi8\b|\b(?:10\s*\*\*\s*9|1e9|1_?000_?000_?000)\b|\.astype\(\s*["\']?(?:int64|i8|<i8)["\']?\s*\)\s*(?://|/)',
  'integer view/asi8 of datetimes, nanosecond scale constants (10**9, 1e9), or an int64 cast followed by a division'),
 ('D02', 'QF2_DATETIME', r'(?:to_datetime|to_timedelta|Timestamp|Timedelta)\([^)]*\bunit\s*=',
  'numeric input with a unit argument to to_datetime / to_timedelta / Timestamp / Timedelta'),
 ('D03', 'QF2_DATETIME', r'\.end_time\b|to_timestamp\([^)]*how\s*=\s*["\']e(?:nd)?["\']',
  'Period end_time or to_timestamp(how="end")'),
 ('D04', 'QF2_DATETIME', r'\b(?:date_range|timedelta_range|bdate_range)\(',
  'date_range / timedelta_range / bdate_range'),
 ('D05', 'QF2_DATETIME', r'\.to_pydatetime\(\)\s*[+-]\s*(?:dt\.|datetime\.)?timedelta\(|\.tz\.zone\b|\.localize\(|\bpytz\b|\.to_pydatetime\(\)[^\n]*\.(?:astimezone|replace)\(|\bstr\([^\n]*\.tz\s*\)|\.tzinfo\b',
  'stdlib arithmetic or tz handling on a converted tz-aware Timestamp, text of the tz attribute, tzinfo, pytz-specific calls'),
 ('D06', 'QF2_DATETIME', r'\b(?:pd\.)?(?:offsets\.)?Day\(|shift\([^)]*freq\s*=\s*["\']\d*D["\']|to_offset\(\s*["\']\d*D["\']',
  'Day offset arithmetic (pd.offsets.Day, shift(freq="D"), to_offset("D"))'),
 ('D07', 'QF2_DATETIME', r'(?s)\A(?=.*(?:read_csv\([^)]*dtype\s*=\s*(?:str\b|["\']str["\']|object\b|["\']object["\'])|\.astype\(\s*(?:str|["\']str["\'])\s*\)))(?=.*to_datetime\([^)]*\bunit\s*=)',
  'to_datetime(..., unit=...) in a program that reads columns as text (dtype=str/object) or casts them to str'),
 ('D08', 'QF2_DATETIME', r'select_dtypes\([^)]*datetime64\[ns',
  'select_dtypes with the "datetime64[ns]" type name'),
 ('D09', 'QF2_DATETIME', r'\binfer_freq\(|\.inferred_freq\b|\.isocalendar\(',
  'infer_freq / inferred_freq / isocalendar'),
 ('D10', 'QF2_DATETIME', r'\.dt\.to_pydatetime\(',
  'Series.dt.to_pydatetime'),
 ('C01', 'QF3_COW', r'\b\w+(?:\.\w+)?' + B + r'\s*' + B + r'\s*=(?!=)|\b\w+\.(?!loc\b|iloc\b|at\b|iat\b|values\b|columns\b|index\b)\w+' + B + r'\s*=(?!=)',
  'two-step indexing assignment df[col][mask] = v (or df.col[mask] = v)'),
 ('C02', 'QF3_COW', r'(?:\]|\b\w+\.\w+)\.(?:fillna|replace|ffill|bfill|pad|backfill|interpolate|clip|where|mask|update)\([^\n]*\binplace\s*=\s*True',
  'in-place method called on a selected column (df[col].fillna(..., inplace=True))'),
 ('C03', 'QF3_COW', r'(?ms)^\s*(\w+)\s*=\s*\w+(?:\[["\'][^"\'\n]+["\']\]|\.(?!loc\b|iloc\b)\w+)(?:\.values|\.to_numpy\(\))?\s*$.*?^\s*\1(?:\.(?:iloc|loc|at|iat))?' + B + r'\s*=(?!=)',
  'a column taken into its own variable and then written through that variable'),
 ('C04', 'QF3_COW', r'(?:(?<![=!<>])=|\breturn)\s*[\w\.\[\]"\']+\.(?:fillna|replace|ffill|bfill|pad|backfill|interpolate|where|mask|clip)\([^\n]*\binplace\s*=\s*True',
  'the return value of an in-place call is assigned or returned'),
 ('C05', 'QF3_COW', r'\bcopy\s*=\s*False\b',
  'copy=False keyword'),
 ('C06', 'QF3_COW', r'(?ms)\b(?:pd\.)?(?:Index|DatetimeIndex)\(\s*(\w+)\b[^\n]*$.*?^\s*\1\s*(?:[-+*/]=|' + B + r'\s*=(?!=))',
  'an Index built from an array variable that is later modified in place'),
 ('G01', 'QF4_GROUPBY', r'(?s)\A(?!.*\bobserved\s*=)(?=.*(?:\bcut\(|\bqcut\(|["\']category["\']|\bCategorical(?:Dtype)?\())(?=.*\.groupby\()',
  'groupby in a program that builds categorical keys (cut, qcut, category, Categorical) and never passes observed='),
 ('G02', 'QF4_GROUPBY', r'\bobserved\s*=\s*False\)[^\n]*\.(?:apply|agg|aggregate)\(',
  'observed=False followed by apply/agg on the same line'),
 ('G03', 'QF4_GROUPBY', r'\.groupby' + P + r'(?:\[\[[^\n]*?\]\])?\.apply\(',
  'DataFrameGroupBy.apply (whole groups passed to the function)'),
 ('G04', 'QF4_GROUPBY', r'\bas_index\s*=\s*False\b',
  'groupby with as_index=False'),
 ('G05', 'QF4_GROUPBY', r'\.(?:agg|aggregate|apply|transform)\([^\n]*\bnp\.(?:std|var|sum|mean|min|max|median|prod|nanstd|nanvar|nansum|nanmean)\b(?!\()|\.(?:agg|aggregate|transform)\(\s*(?:sum|max|min)\s*\)',
  'NumPy or builtin function objects passed to agg/apply/transform'),
 ('G06', 'QF4_GROUPBY', r'groupby\([^\n]*\blevel\s*=\s*\[[^\],\n]+\]|\bfor\b[^\n]*\bin\b[^\n]*groupby\(\s*\[[^\],\n]+\]|\.get_group\(',
  'groupby over a one-element level list, iteration over groupby of a one-element key list, get_group'),
 ('G07', 'QF4_GROUPBY', r'\.groupby' + P + r'(?:\[[^\n]*?\]|\.\w+)?\.(?:sum|mean|cumsum)\(',
  'groupby float sum/mean (no task: row NOT_REPRODUCED)'),
 ('G08', 'QF4_GROUPBY', r'\.groupby' + P + r'(?:\[[^\n]*?\]|\.\w+)?\.(?:any|all|median|sum)\(',
  'groupby any/all/median/sum (integer overflow, NaT cases; no task: row NOT_REPRODUCED)'),
]


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def main():
    with open(os.path.join(STUDY, 'mechanisms', 'catalogue.tsv'), encoding='utf-8', newline='') as f:
        cat = [r for r in csv.DictReader(f, delimiter='\t')]
    want = [r['id'] for r in cat if r['scope'] == 'SILENT' and r['quota_family'] in
            ('QF1_STRING', 'QF2_DATETIME', 'QF3_COW', 'QF4_GROUPBY')]
    have = [r[0] for r in REGEX]
    assert sorted(want) == sorted(have), (sorted(set(want) ^ set(have)))
    order = {cid: i for i, cid in enumerate(want)}
    tasks = {}
    for tid in sorted(d for d in os.listdir(M1) if d.startswith('M_QF')):
        tasks[tid] = json.loads(read(os.path.join(M1, tid, 'task.json')))
    rows_out, log_out, bad = [], [], 0
    for cid, fam, rx, note in sorted(REGEX, key=lambda r: order[r[0]]):
        assert '\t' not in rx
        pat = re.compile(rx, re.MULTILINE)
        inv = [t for t, d in tasks.items() if cid in d['invited_ids_author']]
        nm = [t for t in inv if pat.search(read(os.path.join(M1, t, 'naive.py')))]
        rm = [t for t in inv if pat.search(read(os.path.join(M1, t, 'reference.py')))]
        miss = sorted(set(inv) - set(nm))
        bad += bool(miss)
        other_n = [t for t in tasks if t not in inv and pat.search(read(os.path.join(M1, t, 'naive.py')))]
        other_r = [t for t in tasks if t not in inv and pat.search(read(os.path.join(M1, t, 'reference.py')))]
        t2 = os.path.join(STUDY, 'mechanisms', 'confirm', cid + '.py')
        fm = os.path.join(STUDY, 'mechanisms', 'confirm', 'fmain', cid + '.py')
        t2m = ('yes' if pat.search(read(t2)) else 'no') if os.path.exists(t2) else 'absent'
        fmm = ('yes' if pat.search(read(fm)) else 'no') if os.path.exists(fm) else 'absent'
        n_note = note + ('' if inv else '; no task invites this row in M1')
        if miss:
            n_note += '; MISSES naive of ' + ','.join(miss)
        rows_out.append({'id': cid, 'family': fam, 'regex': rx, 'matches_naive': '%d/%d' % (len(nm), len(inv)),
                         'matches_reference': '%d/%d' % (len(rm), len(inv)), 'note': n_note})
        log_out.append({'id': cid, 'tasks_inviting': ','.join(inv) or '-', 'naive_missed': ','.join(miss) or '-',
                        'references_matched': ','.join(rm) or '-', 'T2_program_match': t2m, 'fmain_program_match': fmm,
                        'other_naive_matched': ','.join(other_n) or '-', 'other_reference_matched': ','.join(other_r) or '-'})
    for name, data in ((os.path.join(M1, 'exposure_regex_part.tsv'), rows_out),
                       (os.path.join(M1, 'logs', 'regex_check.tsv'), log_out)):
        with open(name, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(data[0]), delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE,
                               escapechar=None, quotechar='\x00')
            w.writeheader()
            w.writerows(data)
    ninv = sum(1 for r in rows_out if not r['matches_naive'].startswith('0/0'))
    print('regex rows: %d (rows with inviting tasks: %d); rows missing a naive match: %d' % (len(rows_out), ninv, bad))
    for r in log_out:
        print('%s naive_missed=%s refs=%s T2=%s fmain=%s other_naive=%s' % (r['id'], r['naive_missed'], r['references_matched'],
              r['T2_program_match'], r['fmain_program_match'], r['other_naive_matched']))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
