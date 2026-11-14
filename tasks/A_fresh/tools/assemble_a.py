"""Select the fresh-intent A tasks to use (FULL_PREREG_AMENDMENT_8 item 4) and report the task-set counts. REPAIR3, 2026-11-11.

Rule (registered): |A| = 200 - 128 - |R|; the first 40 - |R| candidates in the id order of INTENTS_FRESH.tsv are used, the other |R|
are listed as unused. A candidate that failed its reference check is dropped with its reason (Amendment 8 item 4: it would be rewritten
by an unexposed writer, which this tool cannot do) and the next candidate is NOT moved up silently: the tool stops and reports.
|R| is read from tasks/R/*/task.json and is accepted only when tasks/R/SELECTION.md no longer says BLOCKED (the R build has run).
Without --apply nothing is written except the report. With --apply the selected folders are copied from tasks/A_fresh/<id>/ to
tasks/A/<id>/ (refusing to overwrite) together with their rendered prompts; INTEGRATE (logs/integrate/tools/merge_tasks.py) must then
be re-run to rebuild tasks/tasks.json, followed by the blind steps (invited_ids_reviewer, 25% card sample) for the new tasks.
Usage: python3 -I -B tasks/A_fresh/tools/assemble_a.py [--report FILE] [--apply]
"""
import csv, glob, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
S = os.path.abspath(os.path.join(PKG, '..', '..'))
N_TOTAL, N_M = 200, 128


def main():
    apply = '--apply' in sys.argv
    rep = sys.argv[sys.argv.index('--report') + 1] if '--report' in sys.argv else None
    order = [r['id'] for r in csv.DictReader(open(os.path.join(S, 'tasks', 'A_intents_fresh', 'out', 'INTENTS_FRESH.tsv'),
                                                  encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE)]
    tj = json.load(open(os.path.join(S, 'tasks', 'tasks.json'), encoding='utf-8'))['tasks']
    cnt = {s: sum(1 for t in tj if t['stratum'] == s) for s in ('M', 'R', 'A')}
    r_folders = sorted(glob.glob(os.path.join(S, 'tasks', 'R', '*', 'task.json')))
    sel_md = open(os.path.join(S, 'tasks', 'R', 'SELECTION.md'), encoding='utf-8').read()
    r_built = 'BLOCKED' not in sel_md[:600]
    ref = {}
    for ln in open(os.path.join(PKG, 'logs', 'refcheck.tsv'), encoding='utf-8').read().splitlines()[1:]:
        f = ln.split('\t')
        ok = f[2] == 'ok' and (f[1] == 'E0a' or f[3] in ('IDENTICAL', 'DTYPE_ONLY')) and not f[4]
        ref[f[0]] = ref.get(f[0], True) and ok
    cand_ok = [i for i in order if ref.get(i)]
    out = ['# A-task assembly report (tasks/A_fresh/tools/assemble_a.py)', '',
           'tasks.json now: M %d, R %d, A %d, total %d of %d registered.' % (cnt['M'], cnt['R'], cnt['A'], sum(cnt.values()), N_TOTAL),
           'Fresh candidates: %d built, %d pass the reference check on E0a, E0b, E0pa, E1, E2, E3, E4.' % (len(order), len(cand_ok)),
           'R folders: %d; R build has run: %s.' % (len(r_folders), 'yes' if r_built else 'no (tasks/R/SELECTION.md says BLOCKED)')]
    code = 0
    if not r_built:
        out.append('|R| is not known, so the number of fresh A tasks to use (40 - |R|) is not known: nothing selected.')
        out.append('Possible outcomes: |R| = k gives |A| = %d - k and uses %s.' % (N_TOTAL - N_M, '; '.join(
            'k=%d: %s' % (k, ('%s..%s' % (order[0], order[39 - k]) if k < 40 else 'none')) for k in (0, 10, 20, 30, 40))))
        code = 2
    else:
        n_r = len(r_folders)
        need = 40 - n_r
        use, unused = order[:need], order[need:]
        bad = [i for i in use if not ref.get(i)]
        out.append('|R| = %d, so %d fresh A tasks are used: %s; unused: %s.' % (n_r, need, ', '.join(use) or 'none', ', '.join(unused) or 'none'))
        if bad:
            out.append('STOP: selected candidates without a passing reference: %s (Amendment 8 item 4: rewrite by an unexposed writer).' % bad)
            code = 1
        elif apply:
            for i in use:
                dst = os.path.join(S, 'tasks', 'A', i)
                if os.path.exists(dst):
                    sys.exit('refusing to overwrite %s' % dst)
            for i in use:
                shutil.copytree(os.path.join(PKG, i), os.path.join(S, 'tasks', 'A', i))
                shutil.copyfile(os.path.join(PKG, 'prompts', i + '.txt'), os.path.join(S, 'tasks', 'A', 'prompts', i + '.txt'))
            json.dump({'r_count': n_r, 'used': use, 'unused': unused}, open(os.path.join(PKG, 'logs', 'assembly.json'), 'w'), indent=1)
            out.append('copied %d task folders and prompts into tasks/A/; re-run INTEGRATE next.' % len(use))
    text = '\n'.join(out) + '\n'
    if rep:
        open(rep, 'w', encoding='utf-8').write(text)
    print(text)
    return code


if __name__ == '__main__':
    sys.exit(main())
