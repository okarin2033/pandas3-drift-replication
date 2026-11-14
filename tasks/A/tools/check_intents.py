"""Pre-freeze checks of the stratum-A intents (pkg:TASKS_RA, 2026-11-11).

Checks: ids follow the round-robin order of CONVENTIONS section 3.1 (first 32); every file exists in GEN; banned-word lint of
the task text; no 8-word sequence shared with any pilot task text, pilot file description or pilot prompt (lower-cased
[a-z0-9]+ tokens; same rule as harness/validate_tasks.py); no 8-word sequence shared between A intents.
Usage: python3 -I -B tasks/A/tools/check_intents.py   (from anywhere; paths derived from this file)
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
P = os.path.abspath(os.path.join(S, '..', '..', 'pilots', 'r3'))
sys.path.insert(0, HERE)
from intents_src import GENERIC, INTENTS  # noqa: E402

TOK = re.compile(r'[a-z0-9]+')


def grams(text, n=8):
    t = TOK.findall(text.lower())
    return {' '.join(t[i:i + n]) for i in range(len(t) - n + 1)}


def expected_ids(n):
    ids, k = [], 0
    while len(ids) < n:
        k += 1
        for f in GENERIC:
            if len(ids) < n:
                ids.append('A_%s_%02d' % (f, k))
    return ids


def main():
    errs = []
    ids = list(INTENTS)
    if ids != expected_ids(len(ids)):
        errs.append('ids not in round-robin order')
    for tid, (files, text) in INTENTS.items():
        for f in files:
            if not os.path.exists(os.path.join(S, 'fixtures', 'main', 'GEN', f)):
                errs.append('%s: missing file %s' % (tid, f))
        if '`result`' not in text:
            errs.append('%s: text does not say what `result` is' % tid)
    # lint (task text only; full prompts are linted after rendering)
    cmd = [sys.executable, '-I', '-B', os.path.join(S, 'harness', 'lint_prompts.py'), '--json']
    for tid, (files, text) in INTENTS.items():
        cmd += ['--text', text]
    out = subprocess.run(cmd, capture_output=True, text=True)
    print('lint rc', out.returncode)
    print(out.stdout[-1500:])
    if out.returncode != 0:
        errs.append('lint not clean')
    # pilot overlap
    pt = json.load(open(os.path.join(P, 'data', 'tasks', 'tasks.json'), encoding='utf-8'))['tasks']
    pilot_text = []
    for t in pt:
        pilot_text.append(t.get('task', ''))
        for f in t.get('files', []):
            if isinstance(f, dict):
                pilot_text.append(' '.join(str(v) for v in f.values()))
    pdir = os.path.join(P, 'data', 'prompts')
    if os.path.isdir(pdir):
        for fn in sorted(os.listdir(pdir)):
            if fn.endswith('.txt'):
                pilot_text.append(open(os.path.join(pdir, fn), encoding='utf-8').read())
    pg = set()
    for x in pilot_text:
        pg |= grams(x)
    n_hits = 0
    for tid, (files, text) in INTENTS.items():
        hit = grams(text) & pg
        if hit:
            n_hits += 1
            errs.append('%s: 8-gram overlap with pilot: %s' % (tid, sorted(hit)[:3]))
    # overlap among A intents
    items = list(INTENTS.items())
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            h = grams(items[i][1][1]) & grams(items[j][1][1])
            if h:
                print('NOTE internal 8-gram overlap %s / %s: %s' % (items[i][0], items[j][0], sorted(h)[:2]))
    print('intents: %d; pilot texts compared: %d; pilot 8-grams: %d; tasks with pilot overlap: %d'
          % (len(INTENTS), len(pilot_text), len(pg), n_hits))
    print('ERRORS: %d' % len(errs))
    for e in errs:
        print('  ' + e)
    return 1 if errs else 0


if __name__ == '__main__':
    sys.exit(main())
