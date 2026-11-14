# REPAIR6 2026-11-12 (lead ruling LR16, FULL_PREREG_AMENDMENT_11.md): evaluate the two LR16 controls (controls.json entries with
# 'lr16_switch') under the LR16 sensitivity switch of harness/oracle.py, against 'expect_class_under_lr16_switch', and under the LR1
# primary (switch off) against 'expect_class' (the primary is also scored by pminus_eval.py). Reads the stored run records of a P- run
# tree; runs no program. Standard library only.
# Run: python3 -I -B harness/controls/lr16_eval.py --runs <P- run tree> [--out md] [--json json]
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(S, 'harness'))
import oracle  # noqa: E402
import run_programs  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', required=True)
    ap.add_argument('--model', default='ctlminus')
    ap.add_argument('--out', default=None)
    ap.add_argument('--json', default=None)
    a = ap.parse_args(argv)
    ctl = [c for c in json.load(open(os.path.join(HERE, 'controls.json'), encoding='utf-8'))['controls'] if c.get('lr16_switch')]
    rows, fails = [], []
    for c in ctl:
        pid = 'gen/%s/%s__s0' % (a.model, c['name'])
        recs = run_programs.load_program_records(a.runs, pid, ['E0a', 'E0b', 'E1', 'E2'])
        card = dict(c['card'], dtype_significant=bool(c['card'].get('dtype_significant')))
        for mode, cd, exp in (('primary (LR1)', card, c['expect_class']),
                              ('LR16 switch %s' % c['lr16_switch'], dict(card, **{c['lr16_switch']: True}), c['expect_class_under_lr16_switch'])):
            res = oracle.classify_program(recs, cd, pairs=[('E0a', 'E1'), ('E0a', 'E2')])
            for pair in ('E0a~E1', 'E0a~E2'):
                t = res['targets'].get(pair) or {}
                ok = bool(res['clean_on_233']) and t.get('class') in exp
                rows.append({'name': c['name'], 'mode': mode, 'pair': pair, 'class': t.get('class'), 'expected': '/'.join(exp),
                             'lr16_case': t.get('lr16_case'), 'order_note': t.get('order_note'), 'clean': res['clean_on_233'],
                             'scored': pair == 'E0a~E1', 'ok': ok})
                if pair == 'E0a~E1' and not ok:
                    fails.append('%s %s' % (c['name'], mode))
    L = ['# LR16 controls: primary and sensitivity expectations', '', 'Run tree: %s' % os.path.relpath(os.path.abspath(a.runs), S), '',
         '| control | mode | pair | scored | class | expected | LR16 case | order note | ok |', '|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        L.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (r['name'], r['mode'], r['pair'], 'yes' if r['scored'] else 'info',
                                                                    r['class'], r['expected'], r['lr16_case'], r['order_note'], r['ok']))
    sc = [r for r in rows if r['scored']]
    L += ['', 'Scored (E0a~E1): %d, passed %d. FAILS: %s' % (len(sc), sum(r['ok'] for r in sc), fails or 'none')]
    text = '\n'.join(L) + '\n'
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(text)
    if a.json:
        json.dump({'scored': len(sc), 'passed': sum(r['ok'] for r in sc), 'fails': fails, 'rows': rows}, open(a.json, 'w'), indent=1)
    print(L[-1])
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
