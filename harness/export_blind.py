# Blind export for the second reviewer (STAGE2 T4.4; FULL_PREREG 4.3, 4.4(b), 10.1). Standard library only.
# Written 2026-11-11 by pkg:SHARED. Conventions: conventions/CONVENTIONS.md section 8.
#
# usage: python3 -I harness/export_blind.py --pkg M1     (M1, M2, R or A)
# Reads  tasks/<PKG>/*/task.json (and checks tasks/<PKG>/prompts/<id>.txt if present), tasks/_private/salt.txt.
# Writes tasks/blind/<PKG>/<blind_id>.json + INDEX.tsv     (the ONLY files BLIND reads in phases 1-2)
#        tasks/blind_reveal/<PKG>/m_invited.json          (M packages only; BLIND opens it in phase 3)
#        tasks/_private/blind_map_<PKG>.json              (task id -> blind id; BLIND never reads tasks/_private/)
# Blind id = 'B' + first 12 hex digits of sha256(salt + task_id). Exported fields are a fixed whitelist
# (BLIND_FIELDS); family, catalogue ids, naive, reference, card fields and predictions are never exported.
import argparse, datetime, glob, hashlib, json, os, sys


def _slurp(path, encoding='utf-8'):
    with open(path, encoding=encoding) as f:
        return f.read()


def _jload(path, encoding='utf-8'):
    with open(path, encoding=encoding) as f:
        return json.load(f)

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from render_prompts import render  # noqa: E402

PKGS = ('M1', 'M2', 'R', 'A')
BLIND_FIELDS = ('schema_version', 'blind_id', 'stratum', 'task_text', 'fixture_descriptions', 'prompt')
BLIND_FIELDS_R = BLIND_FIELDS + ('intent_summary',)


class ExportError(RuntimeError):
    pass


def read_salt(study):
    p = os.path.join(study, 'tasks', '_private', 'salt.txt')
    if not os.path.exists(p):
        raise ExportError('salt not found: %s (created once by SHARED; never regenerate it)' % p)
    s = _slurp(p, encoding='utf-8').strip()
    if len(s) < 32:
        raise ExportError('salt too short: ' + p)
    return s


def blind_id(salt, task_id):
    return 'B' + hashlib.sha256((salt + task_id).encode('utf-8')).hexdigest()[:12]


def blind_record(task):
    """The whitelist view of one task (nothing else may be added here)."""
    rec = {
        'schema_version': 'blind_task/1',
        'blind_id': None,
        'stratum': task['stratum'],
        'task_text': task['task_text'],
        'fixture_descriptions': ['%s: %s' % (os.path.basename(f['path']), f['description']) for f in task['files']],
        'prompt': render(task),
    }
    if task['stratum'] == 'R':
        rec['intent_summary'] = task.get('intent_summary')
    return rec


def _write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=1, ensure_ascii=False, sort_keys=True)
    os.replace(tmp, path)


def export(study, pkg, now=None):
    if pkg not in PKGS:
        raise ExportError('unknown package %r (use %s)' % (pkg, ', '.join(PKGS)))
    salt = read_salt(study)
    paths = sorted(glob.glob(os.path.join(study, 'tasks', pkg, '*', 'task.json')))
    if not paths:
        raise ExportError('no tasks in tasks/%s/' % pkg)
    now = now or datetime.datetime.now().astimezone().isoformat(timespec='seconds')
    out_dir = os.path.join(study, 'tasks', 'blind', pkg)
    os.makedirs(out_dir, exist_ok=True)
    mapping, invited, seen = {}, {}, {}
    for p in paths:
        t = _jload(p, encoding='utf-8')
        tid = t['id']
        want_stratum = {'R': 'R', 'A': 'A'}.get(pkg, 'M')
        if t.get('stratum') != want_stratum:
            raise ExportError('%s: stratum %s does not belong in package %s' % (tid, t.get('stratum'), pkg))
        rec = blind_record(t)
        pf = os.path.join(study, 'tasks', pkg, 'prompts', tid + '.txt')
        if os.path.exists(pf) and _slurp(pf, encoding='utf-8') != rec['prompt']:
            raise ExportError('%s: prompt file differs from the rendered prompt; re-render first' % tid)
        bid = blind_id(salt, tid)
        if bid in seen:
            raise ExportError('blind id collision %s: %s and %s' % (bid, seen[bid], tid))
        seen[bid] = tid
        rec['blind_id'] = bid
        allowed = BLIND_FIELDS_R if t['stratum'] == 'R' else BLIND_FIELDS
        assert set(rec) == set(allowed), sorted(set(rec) ^ set(allowed))
        _write_json(os.path.join(out_dir, bid + '.json'), rec)
        mapping[tid] = bid
        if t['stratum'] == 'M':
            invited[bid] = sorted(set(t.get('invited_ids_author') or []))
    # remove stale blind files of this package (ids no longer present)
    for old in glob.glob(os.path.join(out_dir, 'B*.json')):
        if os.path.basename(old)[:-5] not in seen:
            os.remove(old)
    with open(os.path.join(out_dir, 'INDEX.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('blind_id\tstratum\n')
        for bid in sorted(seen):
            f.write('%s\t%s\n' % (bid, 'R' if pkg == 'R' else ('A' if pkg == 'A' else 'M')))
    salt_sha = hashlib.sha256(salt.encode('utf-8')).hexdigest()
    _write_json(os.path.join(study, 'tasks', '_private', 'blind_map_%s.json' % pkg),
                {'package': pkg, 'created': now, 'salt_sha256': salt_sha, 'map': mapping})
    if pkg in ('M1', 'M2'):
        _write_json(os.path.join(study, 'tasks', 'blind_reveal', pkg, 'm_invited.json'),
                    {'package': pkg, 'created': now,
                     'note': 'BLIND opens this file only in phase 3 (blind id -> invited catalogue id(s))',
                     'invited': invited})
    return {'package': pkg, 'n': len(mapping), 'out_dir': out_dir}


def main(argv=None):
    ap = argparse.ArgumentParser(description='Export the blind view of one task package.')
    ap.add_argument('--pkg', required=True, choices=PKGS)
    ap.add_argument('--study', default=STUDY)
    a = ap.parse_args(argv)
    try:
        r = export(a.study, a.pkg)
    except ExportError as e:
        print('EXPORT ERROR:', e, file=sys.stderr)
        return 1
    print('exported %d blind task(s) of %s to %s' % (r['n'], r['package'], r['out_dir']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
