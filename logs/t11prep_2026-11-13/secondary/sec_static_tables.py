# Static tables of the secondary analyses (LR82.2 item 11): X-1 the frozen silent-capacity table beside the design-implied H4 and the third
# reading of H3 (Amendment 2 (a), (c)); X-5 the results of the registered controls (P+, P-, harm wiring; pilot, not study data); X-7 the
# provider table (Amendments 13 and 14). No study outcome is an input: each table is read from a registered text or from a control
# evaluation by a script, with the sha256 of every source in the header.
# Written 2026-11-13 in the T11 preparation step. Status: draft; decides nothing.
#   python3 -I -B sec_static_tables.py x1 --amendment2 FULL_PREREG_AMENDMENT_2.md --freeze-parameters logs/t8_2026-11-13/FREEZE_PARAMETERS.md \
#       [--summary results/summary.json] --out DIR
#   python3 -I -B sec_static_tables.py x5 --pplus F.json --pminus F.json [--lr16 F.json] [--harm-wiring F.txt]
#       [--first-pplus F.json --first-pminus F.json [--first-harm-wiring F.txt]] --out DIR
#   python3 -I -B sec_static_tables.py x7 --amendment13 FULL_PREREG_AMENDMENT_13.md --amendment14 FULL_PREREG_AMENDMENT_14.md --out DIR
# LR83.5: X-5 is built from the controls of record, the controls as run again before the freeze under LR74 (the records of the T8 apply
# step: pplus_eval.json, pminus_eval.json, lr16_eval.json); the first runs of 2026-11-11 are named in a note with the differences (computed
# from the two sets of evaluations; the reasons are not stated here). X-7 shows the provider of the main run for every model.
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sec_common as C  # noqa: E402

CONTROLS_LABEL = 'oracle and harm controls, not study data'


class Light:
    """The few attributes of sec_common.Inputs that the header and the writers use (these tables have no per_program input)."""

    def __init__(self, files, label=None, study=None):
        self.study = study or C.find_study()
        self.stats = C.harness(self.study)
        self.B, self.seed = C.B_DEFAULT, C.SEED       # unused by these tables; written into the header only
        self.files = files
        self.label = label
        self.test_mode = bool(label)


def read_text(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


# ------------------------------------------------------------------------------------------------ X-1
def parse_amendment2(text):
    """Per-family silent capacity and the G1, G2 totals of Amendment 2 (a); the sums are checked."""
    plain = text.replace('**', '')
    m = re.search(r'QF1 (\d+)/(\d+), QF2 (\d+)/(\d+), QF3 (\d+)/(\d+), QF4 (\d+)/(\d+), QF5 (\d+)/(\d+), QF6 (\d+)/(\d+), QF7 (\d+)/(\d+), '
                  r'QF8 (\d+)/(\d+);\s*G1 (\d+)/(\d+) \(([0-9.]+)\),\s*G2 (\d+)/(\d+) \(([0-9.]+)\)', plain)
    if not m:
        raise C.Refuse('Amendment 2 (a): the silent-capacity sentence was not found in the expected form')
    v = [int(x) for x in m.groups()[:16]] + [int(m.group(17)), int(m.group(18)), int(m.group(20)), int(m.group(21))]
    fam = {'QF%d' % (i + 1): (v[2 * i], v[2 * i + 1]) for i in range(8)}
    g1, g2 = (v[16], v[17]), (v[18], v[19])
    if (fam['QF1'][0] + fam['QF2'][0], fam['QF1'][1] + fam['QF2'][1]) != g1:
        raise C.Refuse('Amendment 2 (a): QF1 + QF2 do not add up to G1')
    if (sum(fam['QF%d' % i][0] for i in range(3, 9)), sum(fam['QF%d' % i][1] for i in range(3, 9))) != g2:
        raise C.Refuse('Amendment 2 (a): QF3..QF8 do not add up to G2')
    m3 = re.search(r'a positive result may also arise because G2\s+includes tasks whose invited idiom warns on 3\.x \((\d+) of (\d+) G2 tasks vs (\d+) of (\d+) G1 tasks', plain)
    if not m3:
        raise C.Refuse('Amendment 2 (c): the third-reading sentence was not found in the expected form')
    reading = re.search(r'"(a positive result may also arise[^"]*)"', plain, re.S)
    third = {'g2_warn': int(m3.group(1)), 'g2_n': int(m3.group(2)), 'g1_warn': int(m3.group(3)), 'g1_n': int(m3.group(4)),
             'text': ' '.join(reading.group(1).split()) if reading else None}
    if (third['g2_n'] - third['g2_warn'], third['g1_n'] - third['g1_warn']) != (g2[0], g1[0]):
        raise C.Refuse('Amendment 2 (c): the counts of the third reading do not equal 96 - 88 and 32 - 31')
    return fam, g1, g2, third


def parse_h4_design(text):
    m = re.search(r'design-implied H4\(M\) = \*\*([0-9.]+)\*\* \((\d+) unwarned of (\d+) drift units\)', text)
    if not m:
        raise C.Refuse('FREEZE_PARAMETERS: the design-implied H4 line was not found in the expected form')
    return float(m.group(1)), int(m.group(2)), int(m.group(3))


def x1(a):
    t2, tf = read_text(a.amendment2), read_text(a.freeze_parameters)
    fam, g1, g2, third = parse_amendment2(t2)
    h4, unw, units = parse_h4_design(tf)
    files = {'FULL_PREREG_AMENDMENT_2.md': C.sha256_file(a.amendment2), 'FREEZE_PARAMETERS.md': C.sha256_file(a.freeze_parameters)}
    check = None
    if a.summary:
        files['summary.json'] = C.sha256_file(a.summary)
        with open(a.summary, encoding='utf-8') as f:
            sv = json.load(f).get('h4_design_implied')
        check = {'summary_h4_design_implied': sv if not isinstance(sv, dict) else sv.get('value', sv),
                 'equals_frozen_value': (sv == h4) if not isinstance(sv, dict) else (sv.get('value') == h4)}
    inp = Light(files)
    rows = [{'scope': k, 'tasks_with_silent_naive_drift': v[0], 'tasks': v[1], 'share': v[0] / v[1]} for k, v in fam.items()]
    rows += [{'scope': 'G1 (QF1 + QF2)', 'tasks_with_silent_naive_drift': g1[0], 'tasks': g1[1], 'share': g1[0] / g1[1]},
             {'scope': 'G2 (QF3 to QF8)', 'tasks_with_silent_naive_drift': g2[0], 'tasks': g2[1], 'share': g2[0] / g2[1]}]
    meta = C.meta_block(inp, os.path.abspath(__file__), ['X-1'], {'source': 'Amendment 2 (a), (c); FREEZE_PARAMETERS section 5'})
    cols = ['scope', 'tasks_with_silent_naive_drift', 'tasks', 'share']
    md = C.header_md(inp, 'X-1', 'Frozen silent-capacity table beside the design-implied H4', meta,
                     'Static table read from the registered text; no outcome is an input. Share of M tasks whose naive drift is silent on E1 '
                     '(Amendment 2 (a)); reported next to the design-implied H4 and not a hypothesis.')
    md += ['', C.md_table(cols, rows), '',
           'Design-implied H4 (M), warning definition warn_233_measured: %s (%d unwarned of %d drift units).' % (h4, unw, units), '',
           'Third reading of a positive H3 (Amendment 2 (c)): "%s" Counts: %d of %d G2 tasks vs %d of %d G1 tasks.' % (
               third['text'], third['g2_warn'], third['g2_n'], third['g1_warn'], third['g1_n'])]
    if check:
        md += ['', 'Check against summary.json: %s' % json.dumps(check)]
    obj = {'item': 'X-1', 'silent_capacity': rows, 'design_implied_H4': {'value': h4, 'unwarned': unw, 'drift_units': units},
           'H3_third_reading': third, 'summary_check': check}
    C.emit(a.out, 'X-1', inp, meta, md, [('capacity', cols, rows)], obj)
    return 0


# ------------------------------------------------------------------------------------------------ X-7
def parse_provider_table(text):
    lines = text.split('\n')
    start = next((i for i, ln in enumerate(lines) if ln.startswith('| Model | Pinned provider')), None)
    if start is None:
        raise C.Refuse('Amendment 13: the calibration table was not found')
    head = [c.strip() for c in lines[start].strip().strip('|').split('|')]
    rows = []
    for ln in lines[start + 2:]:
        if not ln.startswith('|'):
            break
        cells = [c.strip() for c in ln.strip().strip('|').split('|')]
        if len(cells) != len(head):
            raise C.Refuse('Amendment 13: a row of the calibration table has %d cells, expected %d' % (len(cells), len(head)))
        rows.append(dict(zip(head, cells)))
    return head, rows


def amendment14_provider(t14):
    """The provider of the main run for qwen/qwen3.5-9b from Amendment 14: (provider, precision, place, calls answered, earlier-pins note, sentence)."""
    note = re.search(r'The provider table states for this model: (.+?)\n', t14)
    if not note:
        raise C.Refuse('Amendment 14: the provider-table sentence was not found')
    sentence = ' '.join(note.group(1).split())
    m = re.match(r'(first pin .+?), provider of the main run (\S+) \((\w+)\)\.', sentence)
    m2 = re.search(r'Next endpoint by `[^`]+`: (\w+) \(stated precision (\w+)\), place (\d+)\. Its 20 calibration calls: (\d+ of \d+) answered', t14)
    if not m or not m2 or (m.group(2), m.group(3)) != (m2.group(1), m2.group(2)) or 'qwen__qwen3.5-9b' not in t14:
        raise C.Refuse('Amendment 14: the provider of the main run was not found in the expected form')
    return m2.group(1), m2.group(2), m2.group(3), m2.group(4), m.group(1), sentence


PROVIDER_COLS = ['Model', 'Provider of the main run (place in the order of rule P)', 'Stated precision', 'Reasoning setting of record',
                 'Calls answered', 'Earlier pins (note)']


def x7(a):
    t13, t14 = read_text(a.amendment13), read_text(a.amendment14)
    head, rows13 = parse_provider_table(t13)
    prov, prec, place, calls, earlier_note, sentence = amendment14_provider(t14)
    files = {'FULL_PREREG_AMENDMENT_13.md': C.sha256_file(a.amendment13), 'FULL_PREREG_AMENDMENT_14.md': C.sha256_file(a.amendment14)}
    inp = Light(files)
    c_model, c_pin, c_prec, c_reason, c_calls = head[0], head[1], head[2], head[3], head[4]
    rows, found = [], False
    for r in rows13:
        pin, _, earlier = r[c_pin].partition(';')
        out = {PROVIDER_COLS[0]: r[c_model], PROVIDER_COLS[1]: pin.strip(), PROVIDER_COLS[2]: r[c_prec],
               PROVIDER_COLS[3]: r[c_reason], PROVIDER_COLS[4]: r[c_calls],
               PROVIDER_COLS[5]: earlier.strip() or 'none'}
        if r[c_model] == 'qwen/qwen3.5-9b':                    # Amendment 14: the provider of the main run
            found = True
            out[PROVIDER_COLS[1]] = '%s (%s)' % (prov, place)
            out[PROVIDER_COLS[2]] = prec
            out[PROVIDER_COLS[4]] = calls
            out[PROVIDER_COLS[5]] = 'Amendment 13 pinned %s (%s); Amendment 14: %s' % (pin.strip(), earlier.strip() or 'no earlier pin', earlier_note)
        rows.append(out)
    if not found:
        raise C.Refuse('Amendment 13: the row of qwen/qwen3.5-9b was not found')
    meta = C.meta_block(inp, os.path.abspath(__file__), ['X-7'], {'rows': len(rows)})
    md = C.header_md(inp, 'X-7', 'Provider table (provider of the main run, precision, reasoning setting)', meta,
                     'Read from the calibration table of Amendment 13 by a script. The provider column is the provider of the main run for '
                     'every model; for qwen/qwen3.5-9b it is the one Amendment 14 states (SiliconFlow; its precision and its 20 calibration '
                     'calls are those of Amendment 14); the earlier pins are in the last column. Amendment 14: %s' % sentence)
    md += ['', C.md_table(PROVIDER_COLS, rows, 60)]
    obj = {'item': 'X-7', 'table': rows, 'columns': PROVIDER_COLS, 'amendment14_sentence': sentence}
    C.emit(a.out, 'X-7', inp, meta, md, [('providers', PROVIDER_COLS, rows)], obj)
    return 0


# ------------------------------------------------------------------------------------------------ X-5
def eval_row(label, path, role, files, source):
    d = json.loads(read_text(path))
    files[role] = C.sha256_file(path)
    return d, {'control': label, 'source': source, 'scored': d['scored'], 'passed': d['passed'],
               'failed_checks': ', '.join(d.get('fails') or []) or 'none'}


def first_runs_note(rec, first):
    """The difference between the controls of record and the first runs of 2026-11-11, from the two sets of evaluations (numbers only)."""
    parts = []
    for key, label in (('pplus', 'P+'), ('pminus', 'P-'), ('harm', 'harm wiring')):
        r, f = rec.get(key), first.get(key)
        if f is None:
            continue
        if key == 'harm':
            parts.append('harm wiring: first run %s; not repeated under LR74 (the row is the first run)' % f['text'])
            continue
        txt = '%s: first run %d of %d passed%s; controls of record %d of %d passed%s' % (
            label, f['passed'], f['scored'], '' if not f['fails'] else ' (failed: %s)' % ', '.join(f['fails']),
            r['passed'], r['scored'], '' if not r['fails'] else ' (failed: %s)' % ', '.join(r['fails']))
        if key == 'pminus':
            txt += '; specificity %d of %d -> %d of %d, sensitivity %d of %d -> %d of %d' % (
                f['spec'][0], f['spec'][1], r['spec'][0], r['spec'][1], f['sens'][0], f['sens'][1], r['sens'][0], r['sens'][1])
        parts.append(txt)
    return '; '.join(parts)


def x5(a):
    files, rows, extra, rec, first = {}, [], {}, {}, {}
    src = 'controls of record: LR74 run before the freeze (T8 apply step)'
    if a.pplus:
        d, row = eval_row('P+ (positive oracle controls, deciding checks)', a.pplus, 'pplus_eval.json', files, src)
        rows.append(row)
        rec['pplus'] = d
    if a.pminus:
        d, row = eval_row('P- (negative oracle controls and matching positives)', a.pminus, 'pminus_eval.json', files, src)
        rows.append(row)
        rec['pminus'] = dict(d, spec=d.get('specificity'), sens=d.get('sensitivity'))
        extra['P-_specificity'] = d.get('specificity')
        extra['P-_sensitivity_matching_positives'] = d.get('sensitivity')
    if a.lr16:
        d, row = eval_row('LR16 control (4 checks)', a.lr16, 'lr16_eval.json', files, src)
        rows.append(row)
    if a.harm_wiring:
        txt = read_text(a.harm_wiring)
        files['harm_wiring_eval.txt'] = C.sha256_file(a.harm_wiring)
        m = re.search(r'mismatches: (\d+)', txt)
        n_ok = len(re.findall(r'\bOK\s*$', txt, re.M))
        if not m:
            raise C.Refuse('harm wiring evaluation: no "mismatches:" line')
        rows.append({'control': 'harm pre-label wiring check', 'source': 'first run of 2026-11-11 (not repeated under LR74)',
                     'scored': n_ok + int(m.group(1)), 'passed': n_ok,
                     'failed_checks': 'none' if int(m.group(1)) == 0 else '%s mismatches' % m.group(1)})
        first['harm'] = {'text': '%d of %d passed, mismatches %s' % (n_ok, n_ok + int(m.group(1)), m.group(1))}
    if not rows:
        raise C.Refuse('x5 needs at least one of --pplus, --pminus, --lr16, --harm-wiring')
    if a.first_pplus:
        d = json.loads(read_text(a.first_pplus))
        files['first_pplus_eval_2026-11-11.json'] = C.sha256_file(a.first_pplus)
        first['pplus'] = d
    if a.first_pminus:
        d = json.loads(read_text(a.first_pminus))
        files['first_pminus_eval_2026-11-11.json'] = C.sha256_file(a.first_pminus)
        first['pminus'] = dict(d, spec=d.get('specificity'), sens=d.get('sensitivity'))
    inp = Light(files, label=CONTROLS_LABEL)
    cols = ['control', 'source', 'scored', 'passed', 'failed_checks']
    meta = C.meta_block(inp, os.path.abspath(__file__), ['X-5'], extra)
    note = first_runs_note(rec, first) if first else 'no first-run evaluation was given'
    md = C.header_md(inp, 'X-5', 'Results of the registered controls (controls of record, LR83.5)', meta,
                     'Section 9: P+ required 100% sensitivity, P- required 100% specificity. The table is built from the controls as run again '
                     'before the freeze under LR74 (the records of the T8 apply step), which are the controls of record (LR83.5). The determinism '
                     'control (E0a vs E0b) and the adjacent-minor control C1 are study-data results (exclusion counts, B.14); the opt-out control '
                     'A4 and the independent re-run (T13) are study-data steps and are not in this table.')
    md += ['', C.md_table(cols, rows), '', 'Note on the first runs of 2026-11-11 (not used for the table): ' + note + '.']
    if extra:
        md += ['', 'Extra: ' + json.dumps(extra)]
    C.emit(a.out, 'X-5', inp, meta, md, [('controls', cols, rows)], {'item': 'X-5', 'controls': rows, 'extra': extra, 'first_runs_note': note})
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('x1')
    p.add_argument('--amendment2', required=True)
    p.add_argument('--freeze-parameters', required=True)
    p.add_argument('--summary', default=None, help='optional: results/summary.json, to check h4_design_implied against the frozen value')
    p.add_argument('--out', required=True)
    p = sp.add_parser('x5')
    p.add_argument('--pplus', help='controls of record: pplus_eval.json of the T8 apply step (LR74)')
    p.add_argument('--pminus', help='controls of record: pminus_eval.json of the T8 apply step')
    p.add_argument('--lr16', help='controls of record: lr16_eval.json of the T8 apply step')
    p.add_argument('--harm-wiring', help='harm wiring evaluation (only the first run of 2026-11-11 exists)')
    p.add_argument('--first-pplus', help='the first run of 2026-11-11 (named in the note only)')
    p.add_argument('--first-pminus', help='the first run of 2026-11-11 (named in the note only)')
    p.add_argument('--out', required=True)
    p = sp.add_parser('x7')
    p.add_argument('--amendment13', required=True)
    p.add_argument('--amendment14', required=True)
    p.add_argument('--out', required=True)
    a = ap.parse_args(argv)
    return {'x1': x1, 'x5': x5, 'x7': x7}[a.cmd](a)


if __name__ == '__main__':
    sys.exit(C.run_main(main))
