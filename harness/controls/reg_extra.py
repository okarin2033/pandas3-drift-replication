# VERIFY (T6): supporting facts for logs/regression_pilot.md (every number comes from the regression records). Standard library only.
# Run: python3 -I -B harness/controls/reg_extra.py > logs/regression/extra_facts.txt
import collections, csv, gzip, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(os.path.dirname(HERE))
P = os.path.join(os.path.dirname(os.path.dirname(S)), 'pilots', 'r3')
sys.path.insert(0, os.path.join(S, 'harness'))
import attribution as A, run_programs as rp, warndef  # noqa: E402
R = os.path.join(S, 'logs', 'regression', 'runs')
progs = [(m, 't%02d__s%d' % (t, k)) for m in ('qwen35_9b', 'sonnet55') for t in range(1, 49) for k in range(5)]

print('== 1. versions (set over all 1920 base records; pilot records in brackets)')
vs = collections.Counter(); vp = collections.Counter()
for m, p in progs:
    for cfg in ('E0a', 'E0b', 'E1', 'E2'):
        r = rp.load_record(R, cfg, 'gen/pilot_%s/%s' % (m, p))
        pr = json.load(gzip.open(os.path.join(P, 'data', 'runs', cfg, m, p + '.json.gz'), 'rt'))
        v = r['versions']; w = pr['versions']
        vs[(cfg, v['python'], v['pandas'], v['numpy'], v.get('pyarrow'))] += 1
        vp[(cfg, w['python'], w['pandas'], w['numpy'], w.get('pyarrow'))] += 1
for k in sorted(vs): print('new  ', k, vs[k])
for k in sorted(vp): print('pilot', k, vp[k])

print('\n== 2. E0b hash seed: records by (config, PYTHONHASHSEED in the child environment)')
c = collections.Counter()
for m, p in progs:
    for cfg in ('E0a', 'E0b'):
        r = rp.load_record(R, cfg, 'gen/pilot_%s/%s' % (m, p)); c[(cfg, r['py_hash_seed_env'], r['hash_randomization_flag'])] += 1
print(dict(c))
nd = 0; same_status = 0
for m, p in progs:
    a = rp.load_record(R, 'E0a', 'gen/pilot_%s/%s' % (m, p)); b = rp.load_record(R, 'E0b', 'gen/pilot_%s/%s' % (m, p))
    if a['status'] == 'ok' and b['status'] == 'ok':
        same_status += 1
        if a['result'] != b['result'] or a['result_dt'] != b['result_dt']:
            nd += 1
print('programs ok on both E0a and E0b: %d; of these with a different canonical result or dtype record: %d' % (same_status, nd))

print('\n== 3. warning definitions on the new records (user-phase warnings; distinct warnings per record)')
n_rec = 0; n_diff = 0; msgs = collections.Counter(); n_np = 0
for m, p in progs:
    for cfg in ('E0a', 'E1', 'E2'):
        r = rp.load_record(R, cfg, 'gen/pilot_%s/%s' % (m, p)); n_rec += 1
        a = warndef.pandas_warnings(r, 'pilot'); b = warndef.pandas_warnings(r, 'prereg')
        if len(a) != len(b):
            n_diff += 1
            for w in a:
                if not warndef.is_pandas_warning(w, 'prereg'):
                    msgs[(w['category_qualname'], w['category_module'], w['message'][:70])] += 1
        for w in r.get('warnings', []):
            if w.get('phase') == 'user' and warndef.is_numpy_originated(w):
                n_np += 1
wd = []
for ln in open(os.path.join(S, 'logs', 'regression', 'results', 'per_program.jsonl')):
    d = json.loads(ln)
    if d['warned_E0a']['prereg'] != d['warned_E0a']['pilot']:
        wd.append((d['program_id'], 'warned_E0a prereg=%s pilot=%s' % (d['warned_E0a']['prereg'], d['warned_E0a']['pilot']),
                   'E1 %s' % d['targets']['E0a~E1']['class'], 'E2 %s' % d['targets']['E0a~E2']['class']))
print('programs whose warned_E0a differs between the section 3 definition and the pilot definition: %d' % len(wd))
for x in wd: print('  ', x)
print('records %d; records where the pilot definition counts a pandas warning that the section 3 definition does not: %d; user-phase warnings classed NumPy-originated: %d' % (n_rec, n_diff, n_np))
for k, v in msgs.most_common(5): print('  ', k, v)
print('warning categories among user-phase pandas warnings (prereg) over E0a/E1/E2:')
cat = collections.Counter()
for m, p in progs:
    for cfg in ('E0a', 'E1', 'E2'):
        r = rp.load_record(R, cfg, 'gen/pilot_%s/%s' % (m, p))
        for w in warndef.pandas_warnings(r, 'prereg'): cat[(cfg, w['category_qualname'])] += 1
print(dict(sorted(cat.items())))

print('\n== 4. E2 attribution with and without the T2 trace (the pilot had no 3.0.x traces)')
pm = {}
for ln in open(os.path.join(S, 'harness', 'pilot_label_map.tsv'), encoding='utf-8'):
    if ln.startswith('#') or ln.startswith('pilot_label') or not ln.strip(): continue
    f = ln.rstrip('\n').split('\t'); pm[f[0]] = (set(f[1].split(';')), f[2])
pil = {(d['model'], d['prog']): d for d in (json.loads(l) for l in open(os.path.join(P, 'results', 'per_program.jsonl')))}
tab = collections.Counter(); show = []
for ln in open(os.path.join(S, 'logs', 'regression', 'results', 'per_program.jsonl')):
    d = json.loads(ln)
    t = d['targets'].get('E0a~E2')
    if not t or not t['drift']: continue
    m = d['model'].replace('pilot_', ''); p = d['task_id'] + '__s%d' % d['sample']
    pid = d['program_id']
    src = open(os.path.join(S, 'logs', 'regression', 'inputs', 'generations', d['model'], p + '.py')).read()
    recs = rp.load_program_records(R, pid, ['E0a', 'E2', 'A1', 'A2', 'A3', 'A4'])
    a_no = A.attribute({'program_id': pid, 'source': src}, recs, None, None, 'E2')
    lab = pil[(m, p)].get('mech_E2') or ''
    comps = [x for x in lab.replace('|', '+').split('+') if x]
    ok_ids = set().union(*[pm[x][0] for x in comps if x in pm]) if comps else set(); fams = {pm[x][1] for x in comps if x in pm}
    def agree(prim): return prim in ok_ids or A.family_of(prim) in fams
    tab[('with T2', agree(t['primary_label']))] += 1; tab[('without T2', agree(a_no['primary']))] += 1
    if not agree(t['primary_label']):
        show.append((pid, lab, t['primary_label'], t['attribution_step'], a_no['primary'], a_no['step'], agree(a_no['primary'])))
print(dict(tab))
for x in show: print('  differs with T2:', x)
