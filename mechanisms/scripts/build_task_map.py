# Read-only over the frozen pilot; writes pilot_task_map.tsv. Standard library only.
import json, csv, collections, sys
R3 = sys.argv[1]; OUT = sys.argv[2]
tasks = json.load(open(R3 + '/data/tasks/tasks.json'))['tasks']
rows = [json.loads(l) for l in open(R3 + '/results/per_program.jsonl')]
inv = {  # judgment from task text: catalogue ids whose pattern the task text invites (not evidence of drift)
 'TXT': 'S01 S02 S03', 'IMP': 'S01 S02 C01 C02 C04 N01', 'CONV': 'S01 S03 N01 N03', 'BIN': 'G01 R06 S01',
 'DATE': 'D01 D02 D06', 'TS': 'D01 D03 D04 L01 X01', 'TOP': 'G03 R03 S01', 'MRG': 'G04 R01 R05 S01',
 'PIV': 'G01 R04 R06 S01', 'ENC': 'S03 D01 N01', 'UPD': 'C01 C02 C03 N01', 'RPT': 'G03 G05 I01 R02 S01'}
over = {'t05': 'S01 S02 C02 D01', 't07': 'S01 C02 L02 L04', 't18': 'D01 D02', 't21': 'D01 D03 L01', 't23': 'D03 L01',
        't35': 'R04 R06', 't36': 'R04', 't37': 'S03 D01', 't39': 'N01', 't45': 'G03 G05 I01', 't47': 'I01 G05'}
agg = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rows:
    agg[r['task']][r['model']].append(r)
with open(OUT, 'w', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    w.writerow(['task', 'family', 'source', 'invited_catalogue_ids_judgment', 'sonnet55_clean_drift_loud', 'qwen35_9b_clean_drift_loud', 'drift_mechanisms_pilot_label'])
    for t in tasks:
        cells = []; mechs = collections.Counter()
        for m in ('sonnet55', 'qwen35_9b'):
            ps = agg[t['id']][m]
            clean = sum(1 for p in ps if p['e0_status'] == 'ok')
            d = [p for p in ps if p.get('cls_E1') in ('SILENT_DRIFT', 'WARNED_DRIFT')]
            lo = sum(1 for p in ps if p.get('cls_E1') == 'LOUD')
            cells.append(f'{clean}/{len(d)}/{lo}')
            for p in d: mechs[p.get('mech_E1')] += 1
        src = t['source']['kind'] + (':so' + str(t['source']['question_id']) if t['source']['kind'] == 'forum' else '')
        w.writerow([t['id'], t['family'], src, over.get(t['id'], inv[t['family']]), cells[0], cells[1], dict(mechs) or ''])
