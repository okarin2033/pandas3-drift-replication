# Deterministic seeded samplers (FULL_PREREG 10.1 independent cards, 5 version-hint ablation). Standard library only.
# Written 2026-11-11 by pkg:SHARED. Conventions: conventions/CONVENTIONS.md section 9.
#
# 1) Independent-card sample (section 10.1: "a random 25% of tasks in every stratum (seed 20261111)"):
#      python3 -I harness/sample_seeded.py cards [--blind-dir tasks/blind] [--out FILE]
#    Population: the blind ids in tasks/blind/*/B*.json (fields blind_id and stratum only), so BLIND can draw it
#    without seeing task ids. One random.Random(20261111); strata in the order M, R, A; within a stratum the ids
#    are sorted (string order) and k = ceil(0.25 * n) are drawn with rng.sample; the rng is NOT re-seeded between
#    strata. Rounding rule: ceil (so every non-empty stratum gets at least one card).
#    Output TSV: stratum <TAB> id (sorted within stratum).
#
# 2) Version-hint ablation sample (section 5: "40 M tasks drawn at random (seed 20261111, 5 per surviving family)"):
#      python3 -I harness/sample_seeded.py ablation (--tasks-json tasks/tasks.json | --pkg-dirs) [--out FILE]
#    Population: stratum-M task ids, grouped by family code (QF1..QF8 from the id). One random.Random(20261111);
#    families in order QF1..QF8 (only families that have tasks, i.e. surviving families); within a family the ids
#    are sorted and 5 are drawn with rng.sample; no re-seeding between families. If fewer than 8 families survive
#    the sample is 5 per surviving family (5 x f < 40 tasks); it is NOT topped up, the script prints a
#    DEVIATION line and INTEGRATE records it (definitional: section 5 says 40). A family with fewer than 5 tasks is
#    an error. Output TSV: family <TAB> task_id.
import argparse, glob, json, math, os, random, re, sys


def _slurp(path, encoding='utf-8'):
    with open(path, encoding=encoding) as f:
        return f.read()


def _jload(path, encoding='utf-8'):
    with open(path, encoding=encoding) as f:
        return json.load(f)

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
SEED = 20261111
CARD_SHARE = 0.25
STRATA = ('M', 'R', 'A')
ABLATION_PER_FAMILY = 5
FAMILY_CODES = ['QF%d' % i for i in range(1, 9)]
RE_M = re.compile(r'^M_(QF[1-8])_(0[1-9]|1[0-6])$')


def card_k(n):
    return math.ceil(CARD_SHARE * n) if n > 0 else 0


def card_sample(ids_by_stratum, seed=SEED):
    """ids_by_stratum: {'M': [...], 'R': [...], 'A': [...]} -> {stratum: sorted sample}."""
    rng = random.Random(seed)
    out = {}
    for st in STRATA:
        ids = sorted(set(ids_by_stratum.get(st, [])))
        out[st] = sorted(rng.sample(ids, card_k(len(ids)))) if ids else []
    return out


def ablation_sample(m_ids, seed=SEED, per_family=ABLATION_PER_FAMILY):
    """m_ids: stratum-M task ids -> (rows [(family_code, task_id)], notices [str])."""
    fams = {}
    for t in m_ids:
        m = RE_M.match(t)
        if not m:
            raise ValueError('not a stratum-M task id: %r' % t)
        fams.setdefault(m.group(1), set()).add(t)
    rng = random.Random(seed)
    rows, notices = [], []
    for code in FAMILY_CODES:
        ids = sorted(fams.get(code, ()))
        if not ids:
            continue
        if len(ids) < per_family:
            raise ValueError('family %s has only %d tasks (< %d)' % (code, len(ids), per_family))
        for t in sorted(rng.sample(ids, per_family)):
            rows.append((code, t))
    n_fam = len({r[0] for r in rows})
    if n_fam < len(FAMILY_CODES):
        notices.append('DEVIATION: only %d of 8 families survive; ablation sample = %d x %d = %d tasks (< 40), '
                       'not topped up; record in DEVIATIONS.md (definitional, section 5)'
                       % (n_fam, per_family, n_fam, per_family * n_fam))
    return rows, notices


def read_blind_dir(blind_dir):
    ids = {st: [] for st in STRATA}
    for p in sorted(glob.glob(os.path.join(blind_dir, '*', 'B*.json'))):
        d = _jload(p, encoding='utf-8')
        ids.setdefault(d['stratum'], []).append(d['blind_id'])
    return ids


def m_ids_from(study, tasks_json=None):
    if tasks_json:
        d = _jload(tasks_json, encoding='utf-8')
        return [t['id'] for t in d['tasks'] if t.get('stratum') == 'M']
    out = []
    for pkg in ('M1', 'M2'):
        for p in sorted(glob.glob(os.path.join(study, 'tasks', pkg, '*', 'task.json'))):
            out.append(_jload(p, encoding='utf-8')['id'])
    return out


def _emit(lines, out):
    text = '\n'.join(lines) + '\n'
    if out:
        with open(out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    else:
        sys.stdout.write(text)


def main(argv=None):
    ap = argparse.ArgumentParser(description='Seeded samplers (seed 20261111).')
    sub = ap.add_subparsers(dest='cmd', required=True)
    c = sub.add_parser('cards', help='25%% per stratum for independent cards (ceil), over blind ids')
    c.add_argument('--blind-dir', default=os.path.join(STUDY, 'tasks', 'blind'))
    c.add_argument('--ids-tsv', help='alternative input: stratum<TAB>id lines (tests)')
    c.add_argument('--out')
    b = sub.add_parser('ablation', help='5 M tasks per surviving family')
    b.add_argument('--study', default=STUDY)
    b.add_argument('--tasks-json')
    b.add_argument('--pkg-dirs', action='store_true', help='read tasks/M1 and tasks/M2 folders')
    b.add_argument('--out')
    a = ap.parse_args(argv)
    if a.cmd == 'cards':
        if a.ids_tsv:
            ids = {st: [] for st in STRATA}
            for line in _slurp(a.ids_tsv, encoding='utf-8').splitlines(True):
                p = line.rstrip('\n').split('\t')
                if len(p) == 2 and p[0] in STRATA:
                    ids[p[0]].append(p[1])
        else:
            ids = read_blind_dir(a.blind_dir)
        s = card_sample(ids)
        lines = ['stratum\tid']
        for st in STRATA:
            lines += ['%s\t%s' % (st, i) for i in s[st]]
        _emit(lines, a.out)
        print('# cards: ' + ', '.join('%s %d of %d' % (st, len(s[st]), len(set(ids.get(st, [])))) for st in STRATA),
              file=sys.stderr)
        return 0
    if not (a.tasks_json or a.pkg_dirs):
        ap.error('ablation needs --tasks-json or --pkg-dirs')
    rows, notices = ablation_sample(m_ids_from(a.study, a.tasks_json))
    _emit(['family\ttask_id'] + ['%s\t%s' % r for r in rows], a.out)
    for n in notices:
        print(n, file=sys.stderr)
    print('# ablation: %d tasks' % len(rows), file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
