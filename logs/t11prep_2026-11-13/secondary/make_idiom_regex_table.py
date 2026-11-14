# Writes idiom_regex_sec17.tsv: the new regexes for the four example idioms of FULL_PREREG section 17 (LR82.2 item 5). The table has the
# columns of tasks/exposure_regex.tsv (id, family, regex, matches_naive, matches_reference, note) and is read with the frozen
# harness/exposure_scan.load (Python `re`, re.MULTILINE). Written once on 2026-11-13 of the T11 preparation step, BEFORE any
# generated program was read; the regexes are hashed with the code (SECONDARY.sha256) and never revised after programs are read.
# Run: python3 -I -B make_idiom_regex_table.py OUT.tsv
import sys

ROWS = [
    ('N01', 'section17_dtype_object',
     r'''\bdtypes?(?:\[[^\]\n]*\])?\s*[!=]=\s*(?:object\b|np\.object_|numpy\.object_|["\'](?:O|object)["\'])'''
     r'''|\bdtypes?\s+is(?:\s+not)?\s+(?:object\b|np\.object_)'''
     r'''|\.dtype\.kind\s*[!=]=\s*["\']O["\']|\bis_object_dtype\('''
     r'''|\.dtype\s+in\s*[\(\[][^\n\)\]]*(?:\bobject\b|["\']O["\'])''',
     'dtype == object test: column dtype compared with object / "O" / np.object_, dtype.kind == "O", is_object_dtype, dtype in (object, ...)'),
    ('N02', 'section17_astype_str',
     r'''\.astype\(\s*(?:str|["\'](?:str|U\d*|unicode)["\']|np\.str_|numpy\.str_)\s*(?:,[^\n\)]*)?\)''',
     'astype(str): str, "str", "U", "U<n>", np.str_ (not "string"). The clause "on columns with missing values" is NOT expressible on program text; '
     'every astype(str) is matched whether or not the column holds missing values'),
    ('N03', 'section17_int64_epoch',
     r'''(?:to_datetime|[dD]ate[tT]ime|datetime64|\.dt\b|[tT]imestamp|[eE]poch|\bdates?\b|\btimes?\b|_at\b|_ts\b)[^\n#]*\.(?:astype|view)\(\s*(?:np\.|numpy\.)?["\']?(?:int64|i8)["\']?\s*\)'''
     r'''|\.asi8\b'''
     r'''|(?:[tT]imestamp|datetime|to_datetime|\.dt\b)[^\n#]*\.value\b'''
     r'''|(?://|/)\s*(?:10\s*\*\*\s*9|1e9|1_000_000_000|1000000000)\b''',
     'int64 epoch: a datetime cast to int64 (astype / view, on a line with a date or time word), .asi8, Timestamp .value, division by 10**9 / 1e9 / '
     '1_000_000_000 (nanosecond-epoch arithmetic). Over-inclusive by design: a text scan cannot see the unit of the datetime, so it also matches, '
     'for example, an int64 cast of a timedelta component on a line with a date word'),
    ('N04', 'section17_observed_explicit',
     r'''[(,]\s*observed\s*=(?!=)|^\s*observed\s*=\s*\w+\s*[,)]''',
     'observed= passed explicitly as a keyword (groupby, pivot_table, crosstab, ...), any value; a plain assignment to a variable called observed is not matched'),
]
HEADER = ['id', 'family', 'regex', 'matches_naive', 'matches_reference', 'note']


def main():
    out = sys.argv[1]
    with open(out, 'w', encoding='utf-8', newline='') as f:
        f.write('\t'.join(HEADER) + '\n')
        for cid, fam, rx, note in ROWS:
            assert '\t' not in rx and '\n' not in rx and '\t' not in note
            f.write('\t'.join([cid, fam, rx, 'n/a', 'n/a', note]) + '\n')


if __name__ == '__main__':
    main()
