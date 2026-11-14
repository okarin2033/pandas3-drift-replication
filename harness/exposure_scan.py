# HRUN: exposure-regex scan (FULL_PREREG 4.4(c), review M3). Written 2026-11-11 by pkg:HRUN. Standard library only.
# tasks/exposure_regex.tsv (schema conventions/schema/exposure_regex.tsv.schema.json): columns id, family, regex, matches_naive,
# matches_reference, note; one frozen regex per SILENT catalogue row; Python `re` with re.MULTILINE on the program text.
# usage: python3 -I exposure_scan.py [--table tasks/exposure_regex.tsv] PROGRAM.py ...        (prints one line per program: path <TAB> ids)
import os, re, sys

HARNESS = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HARNESS)
DEFAULT_TABLE = os.path.join(STUDY, 'tasks', 'exposure_regex.tsv')


def load(path=DEFAULT_TABLE):
    """-> [(catalogue_id, compiled re.MULTILINE pattern)] in file order. Raises ValueError for a missing column or an invalid regex.
    Rows are split on TAB only (regexes may contain quotes); the header row is required."""
    with open(path, encoding='utf-8') as f:
        lines = f.read().split('\n')
    lines = [ln.rstrip('\r') for ln in lines if ln.strip()]
    if not lines:
        raise ValueError('%s is empty' % path)
    header = lines[0].split('\t')
    for col in ('id', 'regex'):
        if col not in header:
            raise ValueError('%s: column %r missing in header %r' % (path, col, header))
    i_id, i_rx = header.index('id'), header.index('regex')
    rows = []
    for n, ln in enumerate(lines[1:], 2):
        cells = ln.split('\t')
        if len(cells) <= max(i_id, i_rx):
            raise ValueError('%s line %d: too few columns' % (path, n))
        cid, rx = cells[i_id].strip(), cells[i_rx]
        try:
            rows.append((cid, re.compile(rx, re.MULTILINE)))
        except re.error as e:
            raise ValueError('%s line %d (%s): invalid regex: %s' % (path, n, cid, e))
    return rows


def scan(program_text, rows):
    """Sorted catalogue ids (unique) whose regex matches the program text."""
    return sorted({cid for cid, rx in rows if rx.search(program_text)})


def scan_file(program_path, rows):
    with open(program_path, encoding='utf-8', errors='replace') as f:
        return scan(f.read(), rows)


if __name__ == '__main__':
    args = sys.argv[1:]
    table = DEFAULT_TABLE
    if args[:1] == ['--table']:
        table, args = args[1], args[2:]
    rows = load(table)
    for p in args:
        print('%s\t%s' % (p, ','.join(scan_file(p, rows))))
