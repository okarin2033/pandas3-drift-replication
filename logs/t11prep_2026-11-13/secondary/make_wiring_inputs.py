# Builds SYNTHETIC wiring inputs for the pilot runs of the agreement, attribution and arm tools (python3 -I -B make_wiring_inputs.py S OUT).
# S = study folder, OUT = output folder (created). Reads only logs/regression/results/per_program.jsonl, logs/regression/inputs/tasks.json
# and logs/t11prep_2026-11-13/smoke_regression/test_codes.tsv (pilot data, "not study data"). The files it writes are not coder judgements:
# coder A = the pilot pre-labels written as codes; coder B = coder A with every 4th code replaced; hand attribution = the automatic
# primary label with every 3rd replaced; the "hint arm" = the pilot programs s0-s2 of the first 40 tasks used a second time. They test
# the wiring (formats, joins, refusals) only; no number computed from them means anything.
import hashlib
import json
import os
import shutil
import sys

S, OUT = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
os.makedirs(OUT, exist_ok=True)
pp = [json.loads(l) for l in open(os.path.join(S, 'logs', 'regression', 'results', 'per_program.jsonl'), encoding='utf-8') if l.strip()]
tasks = json.load(open(os.path.join(S, 'logs', 'regression', 'inputs', 'tasks.json'), encoding='utf-8'))['tasks']
codes = [ln.rstrip('\n').split('\t') for ln in open(os.path.join(S, 'logs', 't11prep_2026-11-13', 'smoke_regression', 'test_codes.tsv'), encoding='utf-8')][1:]
HDR = 'program_id\tcode\tweight\tcoder\tcoder_code\titem_id\n'


def write(name, text):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f:
        f.write(text)


write('coder_a_synthetic.tsv', HDR + ''.join('%s\t%s\t1.0\tcoderA_synthetic\tA_ONLY_CORRECT\ti%d\n' % (c[0], c[1], i) for i, c in enumerate(codes)))
alt = {'HARM_3X': 'FIX_3X', 'FIX_3X': 'HARM_3X', 'BOTH_ACCEPTABLE': 'NEITHER', 'NEITHER': 'BOTH_ACCEPTABLE', 'UNDETERMINABLE': 'NEITHER'}
sel = [c for i, c in enumerate(codes) if i % 2 == 0]          # coder B sees every second item (the "double-coded sample")
write('coder_b_synthetic.tsv', HDR + ''.join('%s\t%s\t1.0\tcoderB_synthetic\tA_ONLY_CORRECT\tj%d\n' % (c[0], alt[c[1]] if k % 4 == 3 else c[1], k)
                                            for k, c in enumerate(sel)))
write('resolved_codes_synthetic.tsv', 'program_id\tcode\tweight\n' + ''.join('%s\t%s\t1.0\n' % (c[0], c[1]) for c in codes))
drift = [p for p in pp if (p['targets'].get('E0a~E1') or {}).get('drift')]
rows = []
for i, p in enumerate(drift[:30]):
    t = p['targets']['E0a~E1']
    pl = t.get('primary_label') or 'UNATTRIBUTED'
    if i % 3 == 2:
        pl = 'UNATTRIBUTED' if pl != 'UNATTRIBUTED' else 'S01'
    rows.append('%s\t%s\t%s' % (p['program_id'], pl, ';'.join(t.get('labels') or [pl])))
write('hand_attribution_synthetic.tsv', 'program_id\tprimary_label\tlabels\n' + '\n'.join(rows) + '\n')
write('second_rating_synthetic.tsv', 'task_id\tinvitation_strength\n')
write('second_rating_pairs_synthetic.tsv', 'task_id\tidiom_id\tquota_row\tstrength_first\tstrength_second\tp1_first_choice_first\tp1_listed_first\tp1_first_choice_second\tp1_listed_second\n')   # header only: the pilot tasks have no M stratum and no first rating
ids = [t['id'] for t in tasks][:40]
write('sample_tasks_synthetic.tsv', 'task_id\n' + '\n'.join(ids) + '\n')
hint = [p for p in pp if p['model'] == 'pilot_qwen35_9b' and p['task_id'] in set(ids) and p['sample'] <= 2]
write('hint_arm_wiring_per_program.jsonl', ''.join(json.dumps(p) + '\n' for p in hint))
write('arm_default_effort_wiring_per_program.jsonl', ''.join(json.dumps(p) + '\n' for p in pp if p['model'] == 'pilot_sonnet55' and p['sample'] <= 2))
hw = [json.loads(l) for l in open(os.path.join(S, 'logs', 'controls', 'harm_wiring', 'results', 'per_program.jsonl'), encoding='utf-8') if l.strip()]
hrows = []
for i, p in enumerate(hw):
    pre = (p['targets'].get('E0a~E1') or {}).get('harm_prelabel')
    if pre:
        hrows.append('%s\t%s\t1.0\tcoderA_synthetic\tA_ONLY_CORRECT\tk%d\n' % (p['program_id'], pre if i < len(hw) - 1 else alt[pre], i))
write('harm_wiring_coder_a_synthetic.tsv', HDR + ''.join(hrows))
# ---- LR82 additions
dec = {'HARM_3X': 'A_ONLY_CORRECT', 'FIX_3X': 'B_ONLY_CORRECT'}          # side A = E0a, side B = E1 for every synthetic item
key = {'items': {}}
a_rows, b_rows, b_ans, res_rows, dis_items = [], [], [], [], []
for i, c in enumerate(codes):
    iid = 'C%04d' % (i + 1)
    key['items'][iid] = {'program_id': c[0], 'A': 'E0a', 'B': 'E1', 'weight': 1.0, 'double_coded': i % 2 == 0}
    cc = dec.get(c[1], c[1])
    a_rows.append('%s\t%s\t1.0\tcoderA_synthetic\t%s\t%s\n' % (c[0], c[1], cc, iid))
    if i % 2 == 0:                                                      # the double-coded sample: every second item, every 4th differs
        k = i // 2
        bcode = alt[c[1]] if k % 4 == 3 else c[1]
        bcc = dec.get(bcode, bcode)
        b_rows.append('%s\t%s\t1.0\tcoderB_synthetic\t%s\t%s\n' % (c[0], bcode, bcc, iid))
        b_ans.append(json.dumps({'item_id': iid, 'code': bcc, 'reason': 'synthetic reason for wiring %s' % iid}))
        if bcode != c[1]:
            res_rows.append('%s,%s,synthetic resolution' % (iid, 'A_ONLY_CORRECT'))
            dis_items.append((iid, c[0], c[1], bcode))
# LR84.2: the third coder (two of three), SYNTHETIC: on the 1st, 4th, ... disagreement the code of coder A, on the 2nd, 5th, ... the code of
# coder B, on the 3rd, 6th, ... a code that neither gave (all three differ -> UNDETERMINABLE)
HARM_ORDER = ['HARM_3X', 'FIX_3X', 'BOTH_ACCEPTABLE', 'NEITHER', 'UNDETERMINABLE']
inv = {'HARM_3X': 'A_ONLY_CORRECT', 'FIX_3X': 'B_ONLY_CORRECT'}
c_rows = []
for k, (iid, pid, acode, bcode) in enumerate(dis_items):
    ccode = acode if k % 3 == 0 else (bcode if k % 3 == 1 else [x for x in HARM_ORDER if x not in (acode, bcode)][0])
    c_rows.append('%s\t%s\t1.0\tcoderC_synthetic\t%s\t%s\n' % (pid, ccode, inv.get(ccode, ccode), iid))
write('coder_c_res_synthetic.tsv', HDR + ''.join(c_rows))
write('coder_a_res_synthetic.tsv', HDR + ''.join(a_rows))
write('coder_b_res_synthetic.tsv', HDR + ''.join(b_rows))
write('coder_b_answers_synthetic.jsonl', '\n'.join(b_ans) + '\n')
write('resolution_answers_synthetic.csv', 'item_id,code,note\n' + '\n'.join(res_rows) + '\n')
write('sheet_key_synthetic.json', json.dumps(key))
shutil.copyfile(os.path.join(S, 'harness', 'oracle.py'), os.path.join(OUT, 'oracle_copy_synthetic.py'))
h = hashlib.sha256(open(os.path.join(OUT, 'oracle_copy_synthetic.py'), 'rb').read()).hexdigest()
write('oracle_copy_synthetic.sha256', '%s  oracle_copy_synthetic.py\n' % h)
ft = ['t01', 't02', 't03']
write('flags_synthetic.tsv', 'task_id\tstratum\torder_significant\tsort_keys\trow_order\texisted_before_rulings\n' +
      ''.join('%s\tA\ttrue\t["__index__"]\tfile\tyes\n' % t for t in ft))
write('flags23_synthetic.tsv', 'task_id\tstratum\torder_significant\tsort_keys\trow_order\texisted_before_rulings\n' +
      ''.join('%s\tA\ttrue\t["__index__"]\tfile\tyes\n' % t for t in ft[:2]))
print('resolution wiring: %d coded, %d double-coded, %d to resolve' % (len(a_rows), len(b_rows), len(res_rows)))
print('coder A %d rows, coder B %d rows, hand %d rows, hint arm %d programs' % (len(codes), len(sel), len(rows), len(hint)))
