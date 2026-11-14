# Stratum-M quota allocation (FULL_PREREG section 4.3). Standard library only. Written 2026-11-11 by pkg:SHARED.
#
# Rule: 16 tasks per quota family, spread round-robin over the family's CONFIRMED SILENT rows in catalogue order
# (the row order of mechanisms/catalogue.tsv; conventions section 3.3): slot j = 1..16 goes to row ((j-1) mod r),
# so each confirmed row gets floor(16/r) or ceil(16/r) tasks and the first (16 mod r) rows get the ceiling.
# A family with 0 confirmed rows is dropped (row_id NONE, n_tasks 0); its quota is not moved elsewhere.
#
# usage: python3 -I harness/allocate_quota.py [--status mechanisms/confirm/status.tsv]
#                                              [--catalogue mechanisms/catalogue.tsv]
#                                              [--out mechanisms/confirm/quota_allocation.tsv]
# Output columns: family, row_id, n_tasks, task_slots, note (schema: conventions/schema/quota_allocation.tsv.schema.json)
import argparse, csv, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
FAMILIES = ['QF1_STRING', 'QF2_DATETIME', 'QF3_COW', 'QF4_GROUPBY', 'QF5_ORDER', 'QF6_NA_DTYPE', 'QF7_INDEX_REDUCE',
            'QF8_NUMERIC']
QUOTA = 16
COLUMNS = ['family', 'row_id', 'n_tasks', 'task_slots', 'note']


def read_tsv(path):
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE))


def allocate(status_rows, catalogue_order=None, quota=QUOTA):
    """status_rows: dicts with id, family, scope, status. catalogue_order: list of ids in catalogue order (if None,
    the order of status_rows is used). Returns (rows, dropped_families)."""
    order = {cid: i for i, cid in enumerate(catalogue_order or [r['id'] for r in status_rows])}
    for r in status_rows:
        if r['id'] not in order:
            raise ValueError('status row %s not in the catalogue order' % r['id'])
    out, dropped = [], []
    for fam in FAMILIES:
        conf = sorted((r['id'] for r in status_rows
                       if r.get('family') == fam and r.get('scope', 'SILENT') == 'SILENT'
                       and r.get('status') == 'CONFIRMED'), key=lambda c: order[c])
        code = fam.split('_', 1)[0]
        if not conf:
            dropped.append(fam)
            out.append({'family': fam, 'row_id': 'NONE', 'n_tasks': 0, 'task_slots': [],
                        'note': 'DROPPED: 0 confirmed rows'})
            continue
        slots = {c: [] for c in conf}
        for j in range(quota):
            slots[conf[j % len(conf)]].append('M_%s_%02d' % (code, j + 1))
        for c in conf:
            note = '' if slots[c] else 'more confirmed rows than quota slots'
            out.append({'family': fam, 'row_id': c, 'n_tasks': len(slots[c]), 'task_slots': slots[c],
                        'note': note})
    return out, dropped


def write(rows, path):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE)
        w.writerow(COLUMNS)
        for r in rows:
            w.writerow([r['family'], r['row_id'], r['n_tasks'], ','.join(r['task_slots']), r['note']])
    os.replace(tmp, path)


def main(argv=None):
    ap = argparse.ArgumentParser(description='Allocate the 16 M tasks per family over confirmed rows.')
    ap.add_argument('--status', default=os.path.join(STUDY, 'mechanisms', 'confirm', 'status.tsv'))
    ap.add_argument('--catalogue', default=os.path.join(STUDY, 'mechanisms', 'catalogue.tsv'))
    ap.add_argument('--out', default=os.path.join(STUDY, 'mechanisms', 'confirm', 'quota_allocation.tsv'))
    a = ap.parse_args(argv)
    status = read_tsv(a.status)
    cat = [r['id'] for r in read_tsv(a.catalogue)]
    rows, dropped = allocate(status, cat)
    write(rows, a.out)
    total = sum(r['n_tasks'] for r in rows)
    for fam in FAMILIES:
        fr = [r for r in rows if r['family'] == fam]
        print('%-17s %s' % (fam, ' '.join('%s:%d' % (r['row_id'], r['n_tasks']) for r in fr)))
    print('M tasks allocated: %d; dropped families: %s' % (total, ', '.join(dropped) if dropped else 'none'))
    print('wrote', a.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
