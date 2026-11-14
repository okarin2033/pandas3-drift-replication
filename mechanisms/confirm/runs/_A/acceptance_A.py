"""MECH_A acceptance checks (pkg:MECH_A, 2026-11-11). Prints PASS/FAIL per check."""
import csv, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
CONF = os.path.abspath(os.path.join(HERE, '..', '..'))
S = os.path.abspath(os.path.join(CONF, '..', '..'))
SIL = 'S01 S02 S03 S04 S05 S06 O01 D01 D02 D03 D04 D05 D06 D07 D08 D09 D10 C01 C02 C03 C04 C05 C06'.split()
LIDS = 'L01 L02 L03 L04 L05 L06'.split()
res = []
def chk(name, ok, detail=''):
    res.append(ok); print(('PASS' if ok else 'FAIL'), name, detail)
def schema_ok(sch, path):
    sch = json.load(open(os.path.join(S, 'conventions', 'schema', sch)))
    rows = list(csv.reader(open(path, encoding='utf-8'), delimiter='\t'))
    names = [c['name'] for c in sch['columns']]
    bad = [(r[0], c['name']) for r in rows[1:] for v, c in zip(r, sch['columns']) if not re.fullmatch(c['pattern'], v)]
    return rows[0] == names and all(len(r) == len(names) for r in rows[1:]) and not bad, bad
ok, bad = schema_ok('confirm_status.tsv.schema.json', os.path.join(CONF, 'status_A.tsv'))
chk('status_A.tsv matches confirm_status schema', ok, str(bad))
ok, bad = schema_ok('data_needs.tsv.schema.json', os.path.join(CONF, 'data_needs_A.tsv'))
chk('data_needs_A.tsv matches data_needs schema', ok, str(bad))
st = {r['id']: r for r in csv.DictReader(open(os.path.join(CONF, 'status_A.tsv'), encoding='utf-8'), delimiter='\t')}
chk('every assigned SILENT row has a status', all(i in st and st[i]['status'] in ('CONFIRMED', 'NOT_REPRODUCED', 'NOT_FEASIBLE') for i in SIL),
    '%d/%d' % (sum(i in st for i in SIL), len(SIL)))
chk('L01-L06 LOUD on E1', all(st[i]['loud'] == 'yes' and st[i]['status'] == 'LOUD_CONFIRMED' for i in LIDS))
chk('NOT_REPRODUCED rows have two attempts and a note', all(r['attempts'] == '2' and r['note'] for r in st.values() if r['status'] == 'NOT_REPRODUCED'))
chk('CONFIRMED rows drift on E1 or E2', all('yes' in (r['drift_E1'], r['drift_E2']) for r in st.values() if r['status'] == 'CONFIRMED'))
for r in st.values():
    for p in r['programs'].split(';'):
        if not os.path.exists(os.path.join(CONF, p)):
            chk('program file exists ' + p, False)
summ = list(csv.DictReader(open(os.path.join(HERE, 'summary_all_2026-11-11.tsv'), encoding='utf-8'), delimiter='\t'))
chk('every attempt deterministic E0a vs E0b', all(r['det_E0a_E0b'] == 'yes' for r in summ), '%d attempts' % len(summ))
progs = {p for r in st.values() for p in r['programs'].split(';')}
chk('every listed program was run on 7 configs', all(r['program'] + '.py' in progs and all(r['st_' + c] != 'NA' for c in ('E0a', 'E0b', 'E1', 'E2', 'E0pa', 'E3', 'E4')) for r in summ)
    and len(summ) == len(progs))
dn = {r['id'] for r in csv.DictReader(open(os.path.join(CONF, 'data_needs_A.tsv'), encoding='utf-8'), delimiter='\t')}
chk('data needs for every confirmed row', dn == {i for i, r in st.items() if r['status'] == 'CONFIRMED'})
txt = open(os.path.join(CONF, 'NOTES_A.md'), encoding='utf-8').read()
fam = {}
for i in SIL:
    fam.setdefault(st[i]['family'], 0); fam[st[i]['family']] += st[i]['status'] == 'CONFIRMED'
chk('NOTES_A.md reports per-family counts', all(('**%d**' % v) in txt and k in txt for k, v in fam.items()), str(fam))
print('ALL PASS' if all(res) else 'SOME FAIL')
