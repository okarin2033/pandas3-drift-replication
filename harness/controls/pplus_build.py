# VERIFY (T5.11, P+): build the positive-control inputs from the CONFIRMED rows of status_A.tsv / status_B.tsv (read-only).
# Written 2026-11-11 by pkg:VERIFY. Standard library only. Run: python3 -I -B harness/controls/pplus_build.py
# For every CONFIRMED or LOUD_CONFIRMED row and every program file of that row (attempt a and, if present, b) it
#   * copies the program to logs/controls/pplus/generations/ctlplus/<tid>__s0.py   (tid = id, or id_b for attempt b)
#   * writes a synthetic task entry (stratum M, family from the status file, catalogue_row = id, card flags from <id>.card.json)
#   * writes a job line (program id gen/ctlplus/<tid>__s0, flat fixtures folder mechanisms/confirm/data/<id>)
# and writes pplus_expect.json: the expectation per program from the status file (drift_E1 / drift_E2 / loud) and
# which attempt decided the row (the first attempt with drift on E1 or E2 in MECH's own comparison files, or LOUD for L rows).
import csv, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.dirname(os.path.dirname(HERE))
CONF = os.path.join(S, 'mechanisms', 'confirm')
OUT = os.path.join(S, 'logs', 'controls', 'pplus')


def read_tsv(p):
    with open(p, encoding='utf-8') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def mech_drift(rid, pid, pair):
    p = os.path.join(CONF, 'runs', rid, 'compare', pair, 'confirm', pid + '.json')
    try:
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def main():
    rows = read_tsv(os.path.join(CONF, 'status_A.tsv')) + read_tsv(os.path.join(CONF, 'status_B.tsv'))
    os.makedirs(os.path.join(OUT, 'generations', 'ctlplus'), exist_ok=True)
    tasks, jobs, expect = [], [], {}
    for r in rows:
        if r['status'] not in ('CONFIRMED', 'LOUD_CONFIRMED'):
            continue
        rid = r['id']
        progs = [x for x in r['programs'].split(';') if x]
        decided = None
        for i, prog in enumerate(progs):
            base = prog[:-3]
            tid = base                                # S01 or S01_b
            card_path = os.path.join(CONF, base + '.card.json')
            card = json.load(open(card_path)) if os.path.exists(card_path) else {}
            shutil.copyfile(os.path.join(CONF, prog), os.path.join(OUT, 'generations', 'ctlplus', tid + '__s0.py'))
            tasks.append({'id': tid, 'stratum': 'M', 'family': r['family'], 'catalogue_row': rid, 'invited_ids_author': [rid],
                          'order_significant': bool(card.get('order_significant')), 'sort_keys': card.get('sort_keys') or [],
                          'dtype_significant': bool(card.get('dtype_significant')),
                          'note': 'P+ control: MECH confirm program of row %s, attempt %s (not study data)' % (rid, 'ab'[i])})
            jobs.append({'program_id': 'gen/ctlplus/%s__s0' % tid, 'program_path': 'logs/controls/pplus/generations/ctlplus/%s__s0.py' % tid,
                         'task_id': tid, 'card': ({'order_significant': bool(card.get('order_significant')), 'sort_keys': card.get('sort_keys') or [],
                                                   'dtype_significant': bool(card.get('dtype_significant'))} if card else None),
                         'fixtures_root': 'mechanisms/confirm/data/%s' % rid})
            mine = {}
            for pair in ('E0a~E1', 'E0a~E2'):
                c = mech_drift(rid, base, pair)
                mine[pair] = None if c is None else {'class': c.get('class'), 'drift': c.get('drift'), 'target_status': c.get('target_status')}
            expect[tid] = {'row': rid, 'family': r['family'], 'status': r['status'], 'attempt': 'ab'[i], 'mech_drift': mine,
                           'status_drift_E1': r['drift_E1'], 'status_drift_E2': r['drift_E2'], 'status_loud': r['loud']}
            if decided is None and r['status'] == 'CONFIRMED' and any(v and v['drift'] for v in mine.values()):
                decided = tid
            if decided is None and r['status'] == 'LOUD_CONFIRMED':
                decided = tid
        for tid, e in expect.items():
            if e['row'] == rid:
                e['deciding'] = (tid == decided)
    # supplementary controls written by VERIFY (not MECH programs); reported apart, never counted in the P+ percentage
    for name, rid in (('N01_c', 'N01'),):
        src = os.path.join(HERE, 'pplus_extra', name + '.py')
        fam = [r['family'] for r in rows if r['id'] == rid][0]
        shutil.copyfile(src, os.path.join(OUT, 'generations', 'ctlplus', name + '__s0.py'))
        tasks.append({'id': name, 'stratum': 'M', 'family': fam, 'catalogue_row': rid, 'invited_ids_author': [rid],
                      'order_significant': False, 'sort_keys': [], 'dtype_significant': False,
                      'note': 'supplementary P+ control by VERIFY (not study data)'})
        jobs.append({'program_id': 'gen/ctlplus/%s__s0' % name, 'program_path': 'logs/controls/pplus/generations/ctlplus/%s__s0.py' % name,
                     'task_id': name, 'card': None, 'fixtures_root': 'mechanisms/confirm/data/%s' % rid})
        base = [e for e in expect.values() if e['row'] == rid and e['deciding']][0]
        expect[name] = dict(base, attempt='c', deciding=False, supplementary=True)
    with open(os.path.join(OUT, 'tasks.json'), 'w', encoding='utf-8') as f:
        json.dump({'schema_version': 'tasks/1', 'label': 'P+ controls, not study data', 'tasks': tasks}, f, indent=1)
    with open(os.path.join(OUT, 'jobs.jsonl'), 'w', encoding='utf-8') as f:
        for j in jobs:
            f.write(json.dumps(j) + '\n')
    with open(os.path.join(OUT, 'pplus_expect.json'), 'w', encoding='utf-8') as f:
        json.dump(expect, f, indent=1, sort_keys=True)
    nd = sum(1 for e in expect.values() if e['deciding'])
    print('programs %d, rows %d, deciding programs %d' % (len(jobs), len({e['row'] for e in expect.values()}), nd))


if __name__ == '__main__':
    sys.exit(main())
