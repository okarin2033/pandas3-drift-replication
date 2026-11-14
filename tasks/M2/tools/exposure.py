# Exposure regexes (FULL_PREREG 4.4(c)) for the SILENT catalogue rows of QF5-QF8 (package TASKS_M2).
# Written 2026-11-11 by pkg:TASKS_M2; prepared. Standard library only:
#   python3 -I -B tasks/M2/tools/exposure.py
# Writes tasks/M2/exposure_regex_part.tsv (schema conventions/schema/exposure_regex.tsv.schema.json), re-loads it with
# harness/exposure_scan.load (Python re, re.MULTILINE) and fills matches_naive / matches_reference from the naive.py and
# reference.py files of the tasks whose invited_ids_author contain the row. Full cross-match matrix: tasks/M2/logs/exposure_matrix.tsv.
# The regexes were written from the catalogue's idiom descriptions and checked against the naive solutions only; they were not
# tuned on any study output (none exists).
import csv, glob, json, os, sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(TOOLS)
STUDY = os.path.dirname(os.path.dirname(PKG))
sys.path.insert(0, os.path.join(STUDY, 'harness'))
import exposure_scan

# one level of nested parentheses inside a call
A1 = r'(?:[^()]|\([^()]*\))*'
# two levels
A2 = r'(?:[^()]|\((?:[^()]|\([^()]*\))*\))*'
NULLABLE = r'''(?:convert_dtypes\(|dtype_backend\s*=|["'](?:Int|UInt|Float)(?:8|16|32|64)["']|["']boolean["'])'''

REGEX = {
    'R01': (r'\bconcat\(' + A2 + r'\bsort\s*=\s*False', 'concat(..., sort=False) (any argument layout, two nesting levels)'),
    'R02': (r'\bvalue_counts\(' + A1 + r'\bsort\s*=\s*False', 'value_counts(..., sort=False) on a Series, DataFrame or groupby'),
    'R03': (r'\.n(?:largest|smallest)\(', 'nlargest / nsmallest (top-N with ties)'),
    'R04': (r'(?<!np)(?<!numpy)\.stack\(', '.stack( but not np.stack('),
    'R05': (r'\bconcat\(', 'any concat call (whether an input is empty or all-NA cannot be seen statically)'),
    'R06': (r'\bqcut\(|\bpivot_table\(' + A1 + r'\bmargins\s*=\s*True|\.unstack\(' + A1 + r'\bsort\s*=\s*False|\.join\(\s*\[',
            'qcut, pivot_table(margins=True), unstack(sort=False), join with a list'),
    'R07': (r'''\.join\(''' + A1 + r'''\bhow\s*=\s*["'](?:left|right)["']''', 'join(how="left"/"right")'),
    'N01': (r'(?<!str)\.(?:replace|fillna|ffill|bfill|where|mask|clip)\(',
            'replace / fillna / ffill / bfill / where / mask / clip, except .str.replace (also matches Python str.replace)'),
    'N02': (r'(?s)(?=.*' + NULLABLE + r')(?=.*(?<![/])/(?![/=]))',
            'nullable columns (convert_dtypes, dtype_backend, Int64/Float64/boolean) and a division anywhere in the program'),
    'N03': (r'\.insert\(|\bpd\.(?:Series|Index)\(\s*[A-Za-z_][\w.]*(?:\[[^\]]*\])?\s*\)',
            'Index.insert or a Series/Index built from an existing pandas object'),
    'N04': (r'\.value_counts\(', 'any value_counts call'),
    'N05': (r'(?s)(?=.*' + NULLABLE + r')(?=.*(?:>=|<=|(?<![=!<>-])[<>](?![=<>])|\.(?:gt|ge|lt|le|eq|ne)\())',
            'nullable values and a comparison anywhere in the program'),
    'N06': (r'(?s)(?=.*\.rank\()(?=.*' + NULLABLE + r')', 'rank() together with nullable columns'),
    'N07': (r'''(?s)(?=.*(?:Categorical|["']category["']|\.cat\.))(?=.*\.(?:map|replace)\()''',
            'categorical data together with map or replace'),
    'I01': (r'\b(?:np|numpy)\.(?:sum|prod|std|var|mean|min|max|nansum|nanprod|nanstd|nanvar|nanmean)\(\s*[A-Za-z_]\w*\s*(?:\[\s*\[|[,)])'
            r'|\.(?:sum|prod|std|var|mean|min|max)\(\s*axis\s*=\s*None',
            'NumPy reduction applied to a frame-like variable or a double-bracket selection, or axis=None'),
    'I02': (r'(?<!iloc)(?<!loc)\[\s*-?\d+\s*:\s*-?\d*\s*\]|(?<!iloc)(?<!loc)\[\s*:\s*-?\d+\s*\]',
            'integer slice with [] (not .iloc/.loc); also matches list slices'),
    'I03': (r'(?<!iloc)(?<!loc)(?<!at)\[\s*-?\d+\s*\](?!\s*=)', 'integer key with [] (not .iloc/.loc/.at); also matches lists'),
    'I04': (r'(?:&|\||\^)\s*[\[(]\s*(?:True|False)\b', 'logical operator with a literal list or tuple of booleans'),
    'I05': (r'\.index\s*(?:==|!=|<=|>=|<(?!<)|>(?!>))|(?:==|!=|<=|>=)\s*[\w.]*\.index\b(?!\s*\()'
            r'|\bpd\.Index\(' + A1 + r'\)\s*(?:==|!=|<=|>=|<|>)|\bnp\.(?:isinf|isnan|isfinite)\(\s*[\w.]*\.index\b',
            'comparison of an Index with another object, or a NumPy predicate on an Index'),
    'I06': (r'''\.(?:sum|prod|mean|min|max)\(''' + A1 + r'''\baxis\s*=\s*(?:1|["']columns["'])''',
            'row-wise sum/prod/mean/min/max (axis=1)'),
    'X01': (r'''(?s)(?=.*\.(?:rolling|expanding)\()(?=.*(?:\.(?:sem|std|var|skew|kurt)\(|["'](?:sem|std|var|skew|kurt)["']))''',
            'rolling or expanding window together with sem/std/var/skew/kurt'),
    'X02': (r'''interpolation\s*=\s*["']nearest["']|\.combine_first\(''', 'quantile with interpolation="nearest", combine_first'),
}


def main():
    with open(os.path.join(STUDY, 'mechanisms', 'catalogue.tsv'), encoding='utf-8', newline='') as f:
        cat = [r for r in csv.DictReader(f, delimiter='\t')
               if r['scope'] == 'SILENT' and r['quota_family'] in ('QF5_ORDER', 'QF6_NA_DTYPE', 'QF7_INDEX_REDUCE', 'QF8_NUMERIC')]
    missing = [r['id'] for r in cat if r['id'] not in REGEX]
    if missing:
        raise SystemExit('no regex for %s' % missing)
    tasks = []
    for p in sorted(glob.glob(os.path.join(PKG, 'M_QF*', 'task.json'))):
        with open(p, encoding='utf-8') as f:
            t = json.load(f)
        d = os.path.dirname(p)
        with open(os.path.join(d, 'naive.py'), encoding='utf-8') as f:
            nv = f.read()
        with open(os.path.join(d, 'reference.py'), encoding='utf-8') as f:
            rf = f.read()
        tasks.append((t, nv, rf))
    out = os.path.join(PKG, 'exposure_regex_part.tsv')
    # first pass: write regexes with placeholder counts, re-load through the harness loader, then count
    def write(counts):
        with open(out, 'w', encoding='utf-8', newline='') as f:
            f.write('id\tfamily\tregex\tmatches_naive\tmatches_reference\tnote\n')
            for r in cat:
                rx, note = REGEX[r['id']]
                mn, mr = counts.get(r['id'], ('0/0', '0/0'))
                f.write('\t'.join([r['id'], r['quota_family'], rx, mn, mr,
                                   note + '; drafted_by pkg:TASKS_M2 2026-11-11, prepared']) + '\n')
    write({})
    rows = exposure_scan.load(out)
    counts, matrix = {}, []
    for cid, _ in rows:
        inv = [(t, nv, rf) for t, nv, rf in tasks if cid in t['invited_ids_author']]
        mn = sum(1 for t, nv, rf in inv if cid in exposure_scan.scan(nv, rows))
        mr = sum(1 for t, nv, rf in inv if cid in exposure_scan.scan(rf, rows))
        counts[cid] = ('%d/%d' % (mn, len(inv)), '%d/%d' % (mr, len(inv)))
    write(counts)
    rows = exposure_scan.load(out)
    with open(os.path.join(PKG, 'logs', 'exposure_matrix.tsv'), 'w', encoding='utf-8') as f:
        f.write('task\tcatalogue_row\tnaive_matches\treference_matches\n')
        for t, nv, rf in tasks:
            f.write('%s\t%s\t%s\t%s\n' % (t['id'], t['catalogue_row'], ','.join(exposure_scan.scan(nv, rows)),
                                          ','.join(exposure_scan.scan(rf, rows))))
    for cid, _ in rows:
        print(cid, 'naive', counts[cid][0], 'reference', counts[cid][1])
    print('rows', len(rows), 'written', out)


if __name__ == '__main__':
    main()
