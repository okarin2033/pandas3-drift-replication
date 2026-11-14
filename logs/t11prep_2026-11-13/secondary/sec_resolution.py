# Resolution of coding disagreements (FULL_PREREG 10.4 "Disagreements are resolved ... the resolved code is used for H5"; REVIEW X-6, T-5).
# Written 2026-11-13 in the T11 preparation step. Status: draft; decides nothing.
#
# THE MODE OF AMENDMENT 15 ITEM 4 (LR84.2), used at T12: two of three.
#   third-list:    python3 -I -B sec_resolution.py third-list --coder-a A.tsv --coder-b B.tsv --out DIR
#                  -> DIR/third_coder_items.jsonl ({"item_id"} per double-coded item on which the two codes differ): the items that the third
#                  coder codes, blind to both earlier codes, with the same prompt; prints counts only.
#   two-of-three:  python3 -I -B sec_resolution.py two-of-three --coder-a A.tsv --coder-b B.tsv --coder-c C.tsv --out DIR
#                  -> DIR/codes_resolved.tsv (program_id, code, weight: the file `harness/analyze_full.py --codes` reads), resolution_log.tsv,
#                  RESOLUTION_REPORT.md, resolution_report.json.
#   Rule: for every double-coded program on which coder A and coder B differ, the resolved code is the code that two of the three coders gave
#   (the third coder's code equals A's or B's); if all three differ it is UNDETERMINABLE. The resolved file holds coder A's code for the
#   programs coded once and for the double-coded programs on which the two coders agree, and the resolved code for the others. The third
#   coder must have coded exactly the disagreements (a missing or an extra item refuses). Reported: how many codes differed, how many were
#   resolved (to A's code, to B's code), how many are UNDETERMINABLE, how many codes changed from coder A's.
#   All three files are decoded coding files (columns program_id, code, weight, coder, coder_code, item_id) written by
#   `harness/coding_sheet.py decode` with the sheet key; the three coders see the same item numbers.
#
# THE MODES FOR A PERSON AS CODER A (LR82.2 item 12; kept in the tool, not used at T12 under Amendment 15): sheet and resolve.
# The rule of LR82.2 item 12 (coder B a model): the resolution is made by coder A. For every double-coded program on which the two codes
# differ he sees both codes and coder B's written reason, without version labels, and records the resolved code. The resolved file holds
# coder A's codes for the programs coded once and the resolved codes for the others; the number of codes changed at the resolution is
# reported. The resolved file is the TSV that harness/analyze_full.py reads with --codes (program_id, code, weight).
#
# Two steps, both on the decoded coding files that `harness/coding_sheet.py decode` writes (columns program_id, code, weight, coder,
# coder_code, item_id; one file per coder) and coder B's own answer file (item_id, code, reason / note):
#   sheet:    python3 -I -B sec_resolution.py sheet --coder-a A.tsv --coder-b B.tsv --coder-b-answers B_answers.(csv|jsonl) --out DIR
#             -> DIR/resolution_sheet.tsv, resolution_sheet.md  (for coder A: item_id, his code, coder B's code, coder B's reason; no
#                program id, model, task, stratum, family, pre-label, environment or version label; codes in the words of the coding sheet)
#                DIR/resolution_private.tsv (NOT for coder A: item_id <-> program_id, the unmasked reasons)
#   resolve:  python3 -I -B sec_resolution.py resolve --coder-a A.tsv --coder-b B.tsv --answers RES.(csv|jsonl) --key harm/_private/sheet_key.json --out DIR
#             -> DIR/codes_resolved.tsv, resolution_log.tsv (private), RESOLUTION_REPORT.md, resolution_report.json
# Coder A's resolution answers use the format of the coding answers (csv: item_id, code, note; jsonl: item_id, code, reason) with the
# coder codes A_ONLY_CORRECT / B_ONLY_CORRECT / BOTH_ACCEPTABLE / NEITHER / UNDETERMINABLE; they are mapped to the harm codes by the frozen
# coding_sheet.decode with the sheet key, exactly as the first coding was.
import argparse
import collections
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sec_common as C  # noqa: E402

HARM_CODES = ('HARM_3X', 'FIX_3X', 'BOTH_ACCEPTABLE', 'NEITHER', 'UNDETERMINABLE')
MASK = '[label removed]'
SHEET_COLUMNS = ['item_id', 'your_code', 'coder_B_code', 'coder_B_reason']


def _cs(study):
    C.harness(study)
    import coding_sheet
    return coding_sheet


def read_decoded(path):
    rows = C.read_tsv(path)
    need = {'program_id', 'code', 'weight', 'coder_code', 'item_id'}
    if rows and not need <= set(rows[0]):
        raise C.Refuse('%s: columns missing: %s' % (os.path.basename(path), ', '.join(sorted(need - set(rows[0])))))
    out = {}
    for r in rows:
        if r['program_id'] in out:
            raise C.Refuse('%s: duplicate program_id %s' % (os.path.basename(path), r['program_id']))
        if r['code'] not in HARM_CODES:
            raise C.Refuse('%s: unknown harm code %r' % (os.path.basename(path), r['code']))
        out[r['program_id']] = {'code': r['code'], 'coder_code': r['coder_code'], 'item_id': r['item_id'],
                                'weight': float(r['weight']) if r.get('weight') not in (None, '') else None}
    return out


def disagreements(A, B):
    """-> (double-coded program ids, disagreement ids). Coder B must not have coded a program that coder A has not coded."""
    extra = sorted(set(B) - set(A))
    if extra:
        raise C.Refuse('coder B has %d items that coder A has not coded (first: %s)' % (len(extra), extra[0]))
    dbl = sorted(B)
    for pid in dbl:
        if A[pid]['item_id'] != B[pid]['item_id']:
            raise C.Refuse('the two coders have different item ids for %s: they did not see the same sheet' % pid)
    return dbl, [pid for pid in dbl if A[pid]['code'] != B[pid]['code']]


def mask_labels(forbidden_re, text):
    """Replace every version / environment / design label of the blindness list in coder B's reason; -> (text, number of replacements)."""
    new, n = forbidden_re.subn(MASK, text or '')
    return ' '.join(new.split()), n


def make_sheet(a):
    cs = _cs(C.find_study(a.study))
    A, B = read_decoded(a.coder_a), read_decoded(a.coder_b)
    dbl, dis = disagreements(A, B)
    answers = {x['item_id']: x for x in cs.read_answers(a.coder_b_answers)}
    rows, private, masked = [], [], 0
    for pid in dis:
        iid = B[pid]['item_id']
        ans = answers.get(iid)
        if ans is None:
            raise C.Refuse('no answer of coder B for item %s in %s' % (iid, os.path.basename(a.coder_b_answers)))
        if ans['code'] != B[pid]['coder_code']:
            raise C.Refuse('item %s: the code in coder B\'s answer file differs from the decoded file' % iid)
        reason, k = mask_labels(cs.FORBIDDEN_RE, ans.get('reason') or '')
        masked += 1 if k else 0
        rows.append({'item_id': iid, 'your_code': A[pid]['coder_code'], 'coder_B_code': B[pid]['coder_code'], 'coder_B_reason': reason})
        private.append({'item_id': iid, 'program_id': pid, 'code_A': A[pid]['code'], 'code_B': B[pid]['code'],
                        'coder_B_reason_unmasked': ' '.join((ans.get('reason') or '').split()), 'labels_removed': k})
    rows.sort(key=lambda r: r['item_id'])
    private.sort(key=lambda r: r['item_id'])
    text = '\n'.join('\t'.join(str(r[c]) for c in SHEET_COLUMNS) for r in rows)
    if cs.FORBIDDEN_RE.search(text.replace(MASK, '')):
        raise C.Refuse('blindness guard: a version or design label is left in the resolution sheet')
    os.makedirs(a.out, exist_ok=True)
    C.write_tsv(os.path.join(a.out, 'resolution_sheet.tsv'), SHEET_COLUMNS, rows)
    C.write_tsv(os.path.join(a.out, 'resolution_private.tsv'), ['item_id', 'program_id', 'code_A', 'code_B', 'coder_B_reason_unmasked',
                                                              'labels_removed'], private)
    md = ['# Resolution sheet (for coder A)', '',
          '%d of %d double-coded items carry two different codes. For each item below open the same item page you coded, read coder B\'s code '
          'and written reason, and record the code that you now hold, in the same answer format as before (item_id, code, note) with one '
          'of A_ONLY_CORRECT, B_ONLY_CORRECT, BOTH_ACCEPTABLE, NEITHER, UNDETERMINABLE. A and B are the two results of the item page. The '
          'sheet carries no program, model, task, family, stratum, environment or version label; where coder B\'s reason contained one it is '
          'replaced by "%s" (%d reasons).' % (len(rows), len(dbl), MASK, masked), '',
          C.md_table(SHEET_COLUMNS, rows, limit=10 ** 6)]
    with open(os.path.join(a.out, 'resolution_sheet.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(md) + '\n')
    print('resolution sheet: %d items to resolve of %d double-coded; reasons with a label removed: %d' % (len(rows), len(dbl), masked))
    return 0


def resolve(a):
    study = C.find_study(a.study)
    cs = _cs(study)
    A, B = read_decoded(a.coder_a), read_decoded(a.coder_b)
    dbl, dis = disagreements(A, B)
    with open(a.key, encoding='utf-8') as f:
        key = json.load(f)
    answers = cs.read_answers(a.answers)
    seen = collections.Counter(x['item_id'] for x in answers)
    dup = sorted(i for i, n in seen.items() if n > 1)
    if dup:
        raise C.Refuse('resolution answers: duplicate item ids (first: %s)' % dup[0])
    resolved_rows = cs.decode(answers, key, 'resolution by coder A')
    by_pid = {}
    for r in resolved_rows:
        if r['code'] not in HARM_CODES:
            raise C.Refuse('resolution answer for %s maps to an unknown code %r' % (r['item_id'], r['code']))
        by_pid[r['program_id']] = r
    need, got = set(dis), set(by_pid)
    if need - got:
        raise C.Refuse('%d disagreeing items have no resolution (first: %s)' % (len(need - got), A[sorted(need - got)[0]]['item_id']))
    if got - need:
        extra = sorted(got - need)[0]
        raise C.Refuse('%d resolution answers are for items without a disagreement (first: %s)' % (len(got - need), by_pid[extra]['item_id']))
    out, log, changed, to_b, to_neither = [], [], 0, 0, 0
    for pid in sorted(A):
        code = by_pid[pid]['code'] if pid in need else A[pid]['code']
        out.append({'program_id': pid, 'code': code, 'weight': A[pid]['weight']})
        if pid in need:
            ch = code != A[pid]['code']
            changed += 1 if ch else 0
            to_b += 1 if code == B[pid]['code'] else 0
            to_neither += 1 if code not in (A[pid]['code'], B[pid]['code']) else 0
            log.append({'item_id': A[pid]['item_id'], 'program_id': pid, 'code_A': A[pid]['code'], 'code_B': B[pid]['code'], 'resolved': code,
                        'changed_from_A': 'yes' if ch else 'no'})
    os.makedirs(a.out, exist_ok=True)
    C.write_tsv(os.path.join(a.out, 'codes_resolved.tsv'), ['program_id', 'code', 'weight'], out)
    C.write_tsv(os.path.join(a.out, 'resolution_log.tsv'), ['item_id', 'program_id', 'code_A', 'code_B', 'resolved', 'changed_from_A'], log)
    counts = collections.Counter(r['code'] for r in out)
    rep = {'item': 'X-6', 'label': 'registered procedure (resolution of coding disagreements), LR82.2 item 12',
           'programs_coded_by_A': len(A), 'programs_double_coded': len(dbl), 'codes_that_differed': len(dis),
           'codes_changed_at_the_resolution': changed, 'resolved_to_the_code_of_coder_B': to_b,
           'resolved_to_a_code_of_neither_coder': to_neither, 'kept_the_code_of_coder_A': len(dis) - changed,
           'rows_in_resolved_file': len(out), 'resolved_file_code_counts': dict(sorted(counts.items())),
           'inputs_sha256': {'coder_a': C.sha256_file(a.coder_a), 'coder_b': C.sha256_file(a.coder_b), 'answers': C.sha256_file(a.answers),
                             'key': C.sha256_file(a.key)},
           'tool': os.path.basename(__file__), 'tool_sha256': C.sha256_file(os.path.abspath(__file__)),
           'created': datetime.datetime.now().astimezone().strftime('%Y-%m-%dT%H:%M:%S%z')}
    with open(os.path.join(a.out, 'resolution_report.json'), 'w', encoding='utf-8') as f:
        json.dump(rep, f, indent=1)
        f.write('\n')
    md = ['# Resolution of coding disagreements', '',
          'Rule (LR82.2 item 12): coder A resolved every double-coded program on which the two codes differed, seeing both codes and coder '
          'B\'s written reason without version labels. Resolved file: coder A\'s code for programs coded once, the resolved code for the others.',
          '', '- Programs coded by coder A: %d; double-coded: %d; codes that differed: %d.' % (len(A), len(dbl), len(dis)),
          '- **Codes changed at the resolution (resolved code differs from coder A\'s first code): %d** (of which equal to coder B\'s code: %d; '
          'a code of neither coder: %d); coder A kept his code in %d.' % (changed, to_b, to_neither, len(dis) - changed),
          '- Rows in the resolved file: %d; code counts: %s.' % (len(out), json.dumps(rep['resolved_file_code_counts'])),
          '- Inputs (sha256, first 12): ' + ', '.join('%s %s' % (k, v[:12]) for k, v in rep['inputs_sha256'].items()) + '.']
    with open(os.path.join(a.out, 'RESOLUTION_REPORT.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(md) + '\n')
    print('resolved file: %d rows; differing codes %d; changed at the resolution %d' % (len(out), len(dis), changed))
    return 0


def third_list(a):
    A, B = read_decoded(a.coder_a), read_decoded(a.coder_b)
    dbl, dis = disagreements(A, B)
    ids = sorted(B[pid]['item_id'] for pid in dis)
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, 'third_coder_items.jsonl')
    if os.path.exists(path):
        raise C.Refuse('third_coder_items.jsonl exists already')
    with open(path, 'w', encoding='utf-8') as f:
        for i in ids:
            f.write(json.dumps({'item_id': i}) + '\n')
    print('third coder items: %d of %d double-coded items carry two different codes' % (len(ids), len(dbl)))
    return 0


def two_of_three(a):
    """Amendment 15 item 4: the code that two of the three coders gave; UNDETERMINABLE when all three differ."""
    A, B, Cc = read_decoded(a.coder_a), read_decoded(a.coder_b), read_decoded(a.coder_c)
    dbl, dis = disagreements(A, B)
    need, got = set(dis), set(Cc)
    if need - got:
        raise C.Refuse('the third coder has not coded %d disagreeing items (first: %s)' % (len(need - got), A[sorted(need - got)[0]]['item_id']))
    if got - need:
        raise C.Refuse('the third coder has coded %d items without a disagreement (first: %s)' % (len(got - need), Cc[sorted(got - need)[0]]['item_id']))
    for pid in dis:
        if Cc[pid]['item_id'] != A[pid]['item_id']:
            raise C.Refuse('the third coder has another item id for %s: not the same sheet' % pid)
    out, log = [], []
    n_a = n_b = n_und = changed = 0
    for pid in sorted(A):
        code = A[pid]['code']
        if pid in need:
            ca, cb, cc = A[pid]['code'], B[pid]['code'], Cc[pid]['code']
            if cc == ca:
                code, rule = ca, 'A+C'
                n_a += 1
            elif cc == cb:
                code, rule = cb, 'B+C'
                n_b += 1
            else:
                code, rule = 'UNDETERMINABLE', 'all_differ'
                n_und += 1
            ch = code != ca
            changed += 1 if ch else 0
            log.append({'item_id': A[pid]['item_id'], 'program_id': pid, 'code_A': ca, 'code_B': cb, 'code_C': cc, 'resolved': code,
                        'rule': rule, 'changed_from_A': 'yes' if ch else 'no'})
        out.append({'program_id': pid, 'code': code, 'weight': A[pid]['weight']})
    os.makedirs(a.out, exist_ok=True)
    C.write_tsv(os.path.join(a.out, 'codes_resolved.tsv'), ['program_id', 'code', 'weight'], out)
    C.write_tsv(os.path.join(a.out, 'resolution_log.tsv'),
                ['item_id', 'program_id', 'code_A', 'code_B', 'code_C', 'resolved', 'rule', 'changed_from_A'], log)
    counts = collections.Counter(r['code'] for r in out)
    n_res = n_a + n_b
    rep = {'item': 'X-6', 'label': 'registered procedure (resolution of coding disagreements by a third coder), Amendment 15 item 4',
           'programs_coded_by_A': len(A), 'programs_double_coded': len(dbl), 'codes_that_differed': len(dis),
           'resolved_by_two_of_three': n_res, 'resolved_to_the_code_of_coder_A': n_a, 'resolved_to_the_code_of_coder_B': n_b,
           'undetermined_all_three_differ': n_und, 'codes_changed_from_coder_A': changed,
           'rows_in_resolved_file': len(out), 'resolved_file_code_counts': dict(sorted(counts.items())),
           'inputs_sha256': {'coder_a': C.sha256_file(a.coder_a), 'coder_b': C.sha256_file(a.coder_b), 'coder_c': C.sha256_file(a.coder_c)},
           'tool': os.path.basename(__file__), 'tool_sha256': C.sha256_file(os.path.abspath(__file__)),
           'created': datetime.datetime.now().astimezone().strftime('%Y-%m-%dT%H:%M:%S%z')}
    with open(os.path.join(a.out, 'resolution_report.json'), 'w', encoding='utf-8') as f:
        json.dump(rep, f, indent=1)
        f.write('\n')
    md = ['# Resolution of coding disagreements by a third coder', '',
          'Rule (Amendment 15 item 4): for every double-coded program on which coder A and coder B differ, the resolved code is the code that two of '
          'the three coders gave; if all three differ it is UNDETERMINABLE. Resolved file: coder A\'s code for programs coded once and for the '
          'double-coded programs on which the two coders agree, the resolved code for the others.',
          '', '- Programs coded by coder A: %d; double-coded: %d; codes that differed: %d.' % (len(A), len(dbl), len(dis)),
          '- **Resolved by two of three: %d** (to coder A\'s code: %d; to coder B\'s code: %d). **UNDETERMINABLE because all three differ: %d.**' % (
              n_res, n_a, n_b, n_und),
          '- Codes changed from coder A\'s first code: %d.' % changed,
          '- Rows in the resolved file: %d; code counts: %s.' % (len(out), json.dumps(rep['resolved_file_code_counts'])),
          '- Inputs (sha256, first 12): ' + ', '.join('%s %s' % (k, v[:12]) for k, v in rep['inputs_sha256'].items()) + '.']
    with open(os.path.join(a.out, 'RESOLUTION_REPORT.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(md) + '\n')
    print('resolved file: %d rows; differing codes %d; resolved by two of three %d; undetermined %d; changed from coder A %d' % (
        len(out), len(dis), n_res, n_und, changed))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('third-list')
    p.add_argument('--coder-a', required=True)
    p.add_argument('--coder-b', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--study', default=None)
    p = sp.add_parser('two-of-three')
    p.add_argument('--coder-a', required=True)
    p.add_argument('--coder-b', required=True)
    p.add_argument('--coder-c', required=True, help="the third coder's decoded codes (Amendment 15 item 4)")
    p.add_argument('--out', required=True)
    p.add_argument('--study', default=None)
    p = sp.add_parser('sheet')
    p.add_argument('--coder-a', required=True)
    p.add_argument('--coder-b', required=True)
    p.add_argument('--coder-b-answers', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--study', default=None)
    p = sp.add_parser('resolve')
    p.add_argument('--coder-a', required=True)
    p.add_argument('--coder-b', required=True)
    p.add_argument('--answers', required=True, help="coder A's resolution answers")
    p.add_argument('--key', required=True, help='harm/_private/sheet_key.json')
    p.add_argument('--out', required=True)
    p.add_argument('--study', default=None)
    a = ap.parse_args(argv)
    return {'third-list': third_list, 'two-of-three': two_of_three, 'sheet': make_sheet, 'resolve': resolve}[a.cmd](a)


if __name__ == '__main__':
    sys.exit(C.run_main(main))
