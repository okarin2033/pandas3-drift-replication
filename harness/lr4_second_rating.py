# Second blind invitation rating of lead ruling LR4 (REPAIR5_REVIEW.md MF4 (a)). Written 2026-11-12 (REPAIR5 fixes,
# step 7). Status: draft; NOT RUN against
# the real service (no paid call, no key file read in this step): its tests use the mock HTTP server on 127.0.0.1 and the dummy key.
# Standard library only.
#
# LR4: "A model family outside the study set rates the same sealed package under the same instructions, in two sealed parts as in
# Amendment 7 ... It runs as the first item of T7 and its cost counts inside the calibration cap." Rater: the coder-B model of
# Amendment 9, mistralai/mistral-small-2603 (Mistral has no studied model), config harness/rater_configs/mistralai__mistral-small-2603.json.
#
# What it does (one run; resumable after a stop):
#  1. Checks the package: BRIEF.md, TASK_BLIND_RERATE.md, idioms.tsv and part1_items.jsonl against tasks/blind_rerate/INPUTS.sha256, and
#     the two EMPTY templates (rebuilt from part1_items.jsonl and from the blind_id/code columns of the reveal file) against their
#     template hashes in the same file. Any mismatch: refused, nothing sent.
#  2. Part 1: one chat request whose single user message holds the fixed adapter text PART1_INTRO, BRIEF.md verbatim, idioms.tsv
#     verbatim, part1_items.jsonl verbatim and the empty part-1 template. The reply must contain the filled table (one row per blind_id,
#     same order, codes from idioms.tsv). The table is written to <out>/part1_answers.tsv and SEALED (<out>/part1_answers.sha256)
#     before part 2 is built: the reveal file is not read into any request before that seal exists.
#  3. Part 2: the same conversation continued (the part-1 request and the model's own part-1 reply, then a user message with the fixed
#     adapter text PART2_INTRO and the empty part-2 template). The reply must rate every (blind_id, code) row 1-3 with a reason. Written
#     to <out>/part2_items.tsv and sealed. Then RATER_PROVENANCE.md and status.json (state 'sealed_both').
#  A reply that cannot be parsed is billed, kept under raw/, and the request is repeated up to --max-attempts times in all; then the
#  step stops (state 'part1_unparseable' / 'part2_unparseable').
#
# Money and provider (LR4, LR5, LR12): spend is booked in the calibration ledger (<gen-root>/calibration/spend.json, cap $1.00, the same
# Ledger as calibrate.py) and the shared total (<gen-root>/_total.json, $40). The pinned provider's prices and prices_checked_at come from
# calibrate.pinned_prices (config pinning that provider, or <gen-root>/calibration/<model_key>/endpoints.json from
# `calibrate.py endpoints --config harness/rater_configs/...`); without them nothing is sent. Three consecutive responses from a
# provider other than the pin halt the rating (exit 4, report file). A response from another provider is billed and discarded.
# No temperature, top_p or system message is sent. The key is read only from the file named by OPENROUTER_KEY_FILE.
#
# Usage (T7, first item; key file named in the brief):
#   python3 -I -B harness/calibrate.py endpoints --config harness/rater_configs/mistralai__mistral-small-2603.json --gen-root generations
#   OPENROUTER_KEY_FILE=<path> python3 -I -B harness/lr4_second_rating.py --config harness/rater_configs/mistralai__mistral-small-2603.json \
#       --gen-root generations --provider <Name>
# The weighted kappa between the two ratings and the LR3 table for the second rating are computed later (blind_id -> task_id mapping and
# the INTEGRATE I2 rule), not here.
# T7 2026-11-13, lead rulings LR67 and LR68 (LEAD_RULINGS_LR67-LR68_2026-11-13.md; copy before:
# logs/t7_2026-11-13/backup/harness/lr4_second_rating.py; deviation T7-1 of deviations/T7.md):
#  - LR67: a reply table with exactly as many rows as the template is read by position. An identifier cell that differs from the
#    template's identifier at that position by ONE single-character edit and equals no identifier of the template is accepted as that
#    template row; the sealed table carries the template's identifier and the row is recorded (part<N>_identifier_slips.json, status,
#    provenance). Every other difference is unparseable as before. In part 2 the code cell must equal the template exactly.
#  - LR68: with --reread-stored, the stored replies of a part (raw/part<N>__r<n>.json, in the order received) are read again under the
#    rule before any new request; the first that reads is the reply of record. Nothing is sent for a reply that is read again.
import argparse
import hashlib
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import gen_full as g  # noqa: E402
import calibrate as cal  # noqa: E402

STUDY = os.path.dirname(HERE)
PKG = os.path.join(STUDY, 'tasks', 'blind_rerate')
REVEAL = os.path.join(STUDY, 'tasks', 'blind_rerate_reveal', 'part2_items.tsv')
P1_HEADER = ['blind_id', 'first_choice_codes', 'possible_codes', 'comment']
P2_HEADER = ['blind_id', 'code', 'strength', 'reason']
FIXED_FILES = ('BRIEF.md', 'TASK_BLIND_RERATE.md', 'idioms.tsv', 'part1_items.jsonl')

PART1_INTRO = """You are the rater of a blind rating task. Work alone, from the material in this message only. Below are the rating brief
(BRIEF.md), the idiom descriptions (idioms.tsv) and the tasks (part1_items.jsonl), each between lines BEGIN <name> and END <name>.
Do part 1 exactly as the brief says. Part 2 does not exist yet; it will be given to you only after your part-1 answer is sealed.
Answer with the filled table part1_answers.tsv and nothing else that could be mistaken for it: one code block opened by ```tsv and
closed by ```, tab-separated, the header line exactly as in the template, then one row per blind_id in the template's order. Codes
are comma-separated without spaces (for example K07,K22); leave a cell empty when no code applies; the comment is optional, one
sentence, without tabs or line breaks."""

PART2_INTRO = """Your part-1 answer above has been sealed (sha256 {sha}). Now do part 2 exactly as the brief says. The template
part2_items.tsv follows between BEGIN and END: 130 rows, each a task (blind_id, see part1_items.jsonl above) and ONE idiom code. Rate
how strongly the task's wording invites that specific idiom, exactly as described in idioms.tsv: 3, 2 or 1 as defined in the brief,
with a one-sentence reason. Answer with the filled table and nothing else that could be mistaken for it: one code block opened by
```tsv and closed by ```, tab-separated, the header line exactly as in the template, every row of the template in the same order with
blind_id and code unchanged, strength 1, 2 or 3, and a reason without tabs or line breaks."""


class Stop(Exception):
    def __init__(self, state, msg):
        super().__init__(msg)
        self.state = state


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def read_bytes(p):
    with open(p, 'rb') as f:
        return f.read()


def templates(pkg, reveal):
    """The two empty templates, rebuilt exactly as handed over (their hashes are in INPUTS.sha256)."""
    ids = [json.loads(ln)['blind_id'] for ln in read_bytes(os.path.join(pkg, 'part1_items.jsonl')).decode('utf-8').splitlines() if ln.strip()]
    t1 = '\t'.join(P1_HEADER) + '\n' + ''.join(i + '\t\t\t\n' for i in ids)
    rows = read_bytes(reveal).decode('utf-8').splitlines()
    if rows[0].split('\t') != P2_HEADER:
        raise cal.Refused('reveal file header is not %s' % P2_HEADER)
    pairs = [tuple(r.split('\t')[:2]) for r in rows[1:] if r.strip()]
    t2 = '\t'.join(P2_HEADER) + '\n' + ''.join('%s\t%s\t\t\n' % p for p in pairs)
    return ids, pairs, t1, t2


def check_package(pkg, reveal):
    """-> (ids, pairs, t1, t2, hashes) or raises Refused. Every line of INPUTS.sha256 must match (templates rebuilt)."""
    want = {}
    for ln in read_bytes(os.path.join(pkg, 'INPUTS.sha256')).decode('utf-8').splitlines():
        if ln.strip() and not ln.startswith('#'):
            h, name = ln.split(None, 1)
            want[name.strip()] = h
    ids, pairs, t1, t2 = templates(pkg, reveal)
    got = {n: sha_bytes(read_bytes(os.path.join(pkg, n))) for n in FIXED_FILES}
    got['part1_answers.tsv'] = sha_bytes(t1.encode('utf-8'))
    got['../blind_rerate_reveal/part2_items.tsv'] = sha_bytes(t2.encode('utf-8'))
    bad = sorted(n for n in want if got.get(n) != want[n])
    if bad or set(want) != set(got):
        raise cal.Refused('package does not match INPUTS.sha256: %s' % (bad or sorted(set(want) ^ set(got))))
    return ids, pairs, t1, t2, got


def block(name, text):
    return 'BEGIN %s\n%s%sEND %s\n' % (name, text, '' if text.endswith('\n') else '\n', name)


def part1_message(pkg, t1):
    parts = [PART1_INTRO, '', block('BRIEF.md', read_bytes(os.path.join(pkg, 'BRIEF.md')).decode('utf-8')),
             block('idioms.tsv', read_bytes(os.path.join(pkg, 'idioms.tsv')).decode('utf-8')),
             block('part1_items.jsonl', read_bytes(os.path.join(pkg, 'part1_items.jsonl')).decode('utf-8')),
             block('part1_answers.tsv (template)', t1)]
    return '\n'.join(parts)


def part2_message(sha1, t2):
    return PART2_INTRO.format(sha=sha1) + '\n\n' + block('part2_items.tsv (template)', t2)


def extract_table(text, header):
    """Rows (lists) of the first ```tsv block (or, failing that, of the lines from the header on). None if no header is found."""
    m = re.search(r'```(?:tsv)?[ \t]*\n(.*?)```', text, re.S)
    body = m.group(1) if m else text
    lines = body.replace('\r\n', '\n').split('\n')
    for i, ln in enumerate(lines):
        if ln.strip('\n').split('\t') == header:
            return [x.split('\t') for x in lines[i + 1:] if x.strip()]
    return None


def one_edit(a, b):
    """True if a differs from b by exactly one single-character edit (one character dropped, added or replaced)."""
    if a == b:
        return False
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la == lb:
        return sum(1 for x, y in zip(a, b) if x != y) == 1
    short, long_ = (a, b) if la < lb else (b, a)
    return any(long_[:i] + long_[i + 1:] == short for i in range(len(long_)))


def align_ids(got, ids):
    """LR67. got: identifier cells of the reply in order; ids: the template's identifiers in order. -> (slips, None) or (None, why);
    slips: [{'position' (1-based), 'cell_as_written', 'template_identifier'}]."""
    if len(got) != len(ids):
        return None, 'blind_ids differ from the template (%d rows, %d expected)' % (len(got), len(ids))
    known, slips = set(ids), []
    for i, (a, b) in enumerate(zip(got, ids)):
        if a == b:
            continue
        if a in known or not one_edit(a, b):
            return None, 'blind_ids differ from the template (%d rows, %d expected)' % (len(got), len(ids))
        slips.append({'position': i + 1, 'cell_as_written': a, 'template_identifier': b})
    return slips, None


def reread_stored(raw_dir, part, parse):
    """LR68. Reads the stored replies raw/part<part>__r<n>.json in the order received (n ascending) with `parse`.
    -> (text, table, response, file name, log) of the first reply that reads, or (None, None, None, None, log)."""
    log, names = [], []
    for nm in os.listdir(raw_dir) if os.path.isdir(raw_dir) else []:
        m = re.match(r'part%d__r(\d+)\.json$' % part, nm)
        if m:
            names.append((int(m.group(1)), nm))
    for _, nm in sorted(names):
        with open(os.path.join(raw_dir, nm), encoding='utf-8') as f:
            resp = json.load(f)
        text = g.message_text(resp)
        table, why = parse(text)
        if table is not None:
            log.append({'file': nm, 'outcome': 'reread_stored_ok'})
            return text, table, resp, nm, log
        log.append({'file': nm, 'outcome': 'reread_stored_unparseable', 'why': why})
    return None, None, None, None, log


def parse_part1(text, ids, codes, slips=None):
    rows = extract_table(text, P1_HEADER)
    if rows is None:
        return None, 'no table with the part-1 header'
    rows = [(r + [''] * 4)[:4] if len(r) <= 4 else None for r in rows]
    if any(r is None for r in rows):
        return None, 'a row has more than 4 cells'
    found, why = align_ids([r[0] for r in rows], ids)
    if found is None:
        return None, why
    for r, tid in zip(rows, ids):
        r[0] = tid
    if slips is not None:
        slips[:] = found
    for r in rows:
        for cell in (r[1], r[2]):
            for c in [x for x in cell.split(',') if x.strip()]:
                if c.strip() not in codes:
                    return None, '%s: unknown code %r' % (r[0], c)
        r[1], r[2] = ','.join(x.strip() for x in r[1].split(',') if x.strip()), ','.join(x.strip() for x in r[2].split(',') if x.strip())
    return '\t'.join(P1_HEADER) + '\n' + ''.join('\t'.join(r) + '\n' for r in rows), None


def parse_part2(text, pairs, slips=None):
    rows = extract_table(text, P2_HEADER)
    if rows is None:
        return None, 'no table with the part-2 header'
    if any(len(r) != 4 for r in rows):
        return None, 'a row does not have 4 cells'
    if len(rows) != len(pairs) or [r[1] for r in rows] != [c for _, c in pairs]:
        return None, 'rows differ from the template (%d rows, %d expected)' % (len(rows), len(pairs))
    known, found = {b for b, _ in pairs}, []
    for i, (r, (bid, _)) in enumerate(zip(rows, pairs)):
        if r[0] != bid:
            if r[0] in known or not one_edit(r[0], bid):
                return None, 'rows differ from the template (%d rows, %d expected)' % (len(rows), len(pairs))
            found.append({'position': i + 1, 'cell_as_written': r[0], 'template_identifier': bid})
            r[0] = bid
    if slips is not None:
        slips[:] = found
    for r in rows:
        if r[2].strip() not in ('1', '2', '3'):
            return None, '%s %s: strength %r' % (r[0], r[1], r[2])
        if not r[3].strip():
            return None, '%s %s: empty reason' % (r[0], r[1])
        r[2] = r[2].strip()
    return '\t'.join(P2_HEADER) + '\n' + ''.join('\t'.join(r) + '\n' for r in rows), None


class Rater:
    def __init__(self, cfg, provider, gen_root, key, out, prices, max_attempts=2, backoff=g.DEFAULT_BACKOFF, timeout=600,
                 cal_cap=cal.CAL_CAP_USD, pkg=PKG, reveal=REVEAL, reread=False):
        self.reread = reread
        self.cfg = dict(cfg, provider=provider, price_in_per_m=prices['price_in_per_m'], price_out_per_m=prices['price_out_per_m'],
                        prices_checked_at=prices['prices_checked_at'])
        self.cfg['provider_response'] = cfg.get('provider_response') if cfg.get('provider_response') not in (None, g.PLACEHOLDER) else []
        self.prices, self.key, self.out = prices, key, out
        self.max_attempts, self.backoff, self.timeout = max_attempts, backoff, timeout
        self.pkg, self.reveal = pkg, reveal
        self.ledger = g.Ledger(gen_root, 'calibration', cal_cap, cfg.get('total_cap_usd', 40.0))
        self.raw_dir = os.path.join(out, 'raw')
        self.disc_dir = os.path.join(out, 'raw_discarded')
        os.makedirs(self.raw_dir, exist_ok=True)
        self.calls_f = os.path.join(out, 'calls.jsonl')
        self.status_f = os.path.join(out, 'status.json')
        self.poster = g.Runner.__new__(g.Runner)
        self.poster.cfg, self.poster.key, self.poster.timeout = self.cfg, key, timeout
        self.poster.lock = g.threading.Lock()
        self.poster.in_flight = self.poster.max_in_flight_seen = 0

    # -- records
    def _record(self, d):
        d['at'] = g.now()
        with open(self.calls_f, 'a', encoding='utf-8') as f:
            f.write(g.redact(json.dumps(d)) + '\n')

    def status(self):
        if os.path.exists(self.status_f):
            with open(self.status_f, encoding='utf-8') as f:
                return json.load(f)
        return {'state': 'not_started'}

    def set_status(self, **kw):
        s = self.status()
        s.update(kw, updated_at=g.now())
        with open(self.status_f, 'w', encoding='utf-8') as f:
            json.dump(s, f, indent=1)

    def _seal(self, name, text):
        p = os.path.join(self.out, name)
        if os.path.exists(p):
            raise Stop('error', '%s exists already; a sealed answer is never overwritten' % name)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(text)
        h = sha_bytes(text.encode('utf-8'))
        with open(os.path.join(self.out, name[:-4] + '.sha256'), 'w', encoding='utf-8') as f:
            f.write('%s  %s\n# %s\n' % (h, name, g.now()))
        return h

    # -- one request with the LR5 rules; returns the reply text
    def call(self, part, messages):
        body = g.build_body(self.cfg, messages[0]['content'], 0)
        body['messages'] = messages
        assert set(body) <= g.ALLOWED_BODY_KEYS and not (set(body) & g.FORBIDDEN_BODY_KEYS)
        prompt_chars = sum(len(m['content']) for m in messages)
        worst = g.worst_case('x' * prompt_chars, self.cfg['price_in_per_m'], self.cfg['price_out_per_m'], self.cfg['max_tokens'])
        transient = 0
        while True:
            rid, why = self.ledger.reserve(worst)
            if rid is None:
                raise Stop('cap_stop', 'calibration cap: %s (the cap is not raised; LR12)' % why)
            resp, err, http = self.poster.post(body)
            if resp is None:
                self.ledger.settle(rid, 0.0)
                self._record({'part': part, 'http': http, 'error': err, 'outcome': 'failed'})
                if (http in g.TRANSIENT_HTTP or http is None) and transient < g.RETRIES:
                    time.sleep(self.backoff[min(transient, len(self.backoff) - 1)])
                    transient += 1
                    continue
                raise Stop('failed', 'part %d request failed: %s' % (part, err))
            usage = resp.get('usage') or {}
            cost, cost_basis = cal.booked_cost(usage, worst, self.cfg['price_in_per_m'], self.cfg['price_out_per_m'])  # REPAIR6 fixes
            ok_prov = g.provider_ok(self.cfg, resp)
            self.ledger.settle(rid, cost, discarded=not ok_prov)
            n = len([x for x in os.listdir(self.raw_dir)]) + (len(os.listdir(self.disc_dir)) if os.path.isdir(self.disc_dir) else 0)
            d = self.raw_dir if ok_prov else self.disc_dir
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, 'part%d__r%d.json' % (part, n)), 'w', encoding='utf-8') as f:
                json.dump(resp, f, indent=1)
            ch = (resp.get('choices') or [{}])[0]
            rec = {'part': part, 'http': 200, 'provider_returned': resp.get('provider'), 'provider_ok': ok_prov,
                   'model_returned': resp.get('model'), 'finish_reason': ch.get('finish_reason'),
                   'prompt_tokens': usage.get('prompt_tokens'), 'completion_tokens': usage.get('completion_tokens'), 'cost': cost,
                   'cost_reported': usage.get('cost'), 'cost_basis': cost_basis,
                   'request_sha256': sha_bytes(json.dumps(body, sort_keys=True).encode('utf-8'))}
            if not ok_prov:
                n_mis = cal.consecutive_mismatches(self.calls_f) + 1
                self._record(dict(rec, outcome='provider_mismatch_discarded', consecutive_mismatches=n_mis))
                if n_mis >= g.PROVIDER_MISMATCH_HALT:
                    with open(os.path.join(self.out, 'provider_mismatch_report.json'), 'w', encoding='utf-8') as f:
                        json.dump({'written': g.now(), 'model': self.cfg['model'], 'provider_pinned': self.cfg['provider'],
                                   'consecutive_mismatches': n_mis,
                                   'rule': 'lead ruling LR5 (three consecutive mismatches halt)'}, f, indent=1)
                    raise Stop(g.PROVIDER_HALT_STATE, '%d consecutive responses from a provider other than the pin' % n_mis)
                continue
            self._record(dict(rec, outcome='ok'))
            return g.message_text(resp), rec

    def _attempts(self, part, messages, parse):
        last = None
        if self.reread:                                      # LR68: stored replies first, in the order received; nothing is sent
            text, table, resp, nm, log = reread_stored(self.raw_dir, part, parse)
            for e in log:
                self._record(dict(e, part=part, rule='LR67, LR68'))
            if table is not None:
                return text, table, {'provider_returned': resp.get('provider'), 'reread_file': nm}
        for i in range(self.max_attempts):
            text, rec = self.call(part, messages)
            table, why = parse(text)
            if table is not None:
                return text, table, rec
            last = why
            self._record({'part': part, 'outcome': 'unparseable', 'why': why, 'attempt': i + 1})
        raise Stop('part%d_unparseable' % part, 'part %d reply could not be parsed after %d attempt(s): %s' % (part, self.max_attempts, last))

    def run(self):
        st = self.status()
        if st.get('state') == 'sealed_both':
            return st
        if st.get('state') == g.PROVIDER_HALT_STATE:
            raise Stop(g.PROVIDER_HALT_STATE, 'halted earlier')
        ids, pairs, t1, t2, hashes = check_package(self.pkg, self.reveal)
        codes = {ln.split('\t')[0] for ln in read_bytes(os.path.join(self.pkg, 'idioms.tsv')).decode('utf-8').splitlines()[1:] if ln.strip()}
        self.set_status(state='started', model=self.cfg['model'], provider_pinned=self.cfg['provider'], prices=self.prices,
                        package_hashes=hashes, started_at=st.get('started_at') or g.now())
        m1 = {'role': 'user', 'content': part1_message(self.pkg, t1)}
        p1 = os.path.join(self.out, 'part1_answers.tsv')
        if not os.path.exists(os.path.join(self.out, 'part1_answers.sha256')):
            slips1 = []
            text1, table1, rec1 = self._attempts(1, [m1], lambda t: parse_part1(t, ids, codes, slips1))
            with open(os.path.join(self.out, 'part1_reply.txt'), 'w', encoding='utf-8') as f:
                f.write(text1)
            self._slips(1, slips1, rec1)
            sha1 = self._seal('part1_answers.tsv', table1)
            self.set_status(state='part1_sealed', part1_sha256=sha1, part1_sealed_at=g.now(), part1_provider=rec1['provider_returned'],
                            part1_identifier_slips=len(slips1), part1_reply_file=rec1.get('reread_file'))
        sha1 = sha_bytes(read_bytes(p1))
        with open(os.path.join(self.out, 'part1_reply.txt'), encoding='utf-8') as f:
            text1 = f.read()
        # the reveal file enters a request only now, after the part-1 seal exists
        msgs = [m1, {'role': 'assistant', 'content': text1}, {'role': 'user', 'content': part2_message(sha1, t2)}]
        slips2 = []
        text2, table2, rec2 = self._attempts(2, msgs, lambda t: parse_part2(t, pairs, slips2))
        self._slips(2, slips2, rec2)
        sha2 = self._seal('part2_items.tsv', table2)
        self.set_status(state='sealed_both', part2_sha256=sha2, part2_sealed_at=g.now(), part2_provider=rec2['provider_returned'],
                        part2_identifier_slips=len(slips2), part2_reply_file=rec2.get('reread_file'))
        self.provenance()
        return self.status()

    def _slips(self, part, slips, rec):
        """LR67: the rows read by position, with the cell as written, kept beside the sealed table."""
        with open(os.path.join(self.out, 'part%d_identifier_slips.json' % part), 'w', encoding='utf-8') as f:
            json.dump({'written': g.now(), 'rule': 'lead ruling LR67', 'reply_read_again_from': rec.get('reread_file'),
                       'rows': slips}, f, indent=1)

    def provenance(self):
        s = self.status()
        txt = ['# Rater provenance (second blind invitation rating, lead ruling LR4)', '',
               'LLM-assisted.', '',
               '- Rater: model %s through OpenRouter, provider pinned %r (returned: part 1 %r, part 2 %r); written by '
               'harness/lr4_second_rating.py.' % (s['model'], s['provider_pinned'], s.get('part1_provider'), s.get('part2_provider')),
               '- Start: %s. Part 1 sealed: %s (sha256 %s). Part 2 sealed: %s (sha256 %s).' % (
                   s.get('started_at'), s.get('part1_sealed_at'), s.get('part1_sha256'), s.get('part2_sealed_at'), s.get('part2_sha256')),
               '- Material seen: the fixed adapter text of the script, BRIEF.md, idioms.tsv, part1_items.jsonl and the empty part-1 '
               'template; after the part-1 seal, its own part-1 reply and the empty part-2 template. Nothing else of the project.',
               '- Package hashes checked against tasks/blind_rerate/INPUTS.sha256 (templates rebuilt): all match.',
               '- Identifier cells read by position under lead ruling LR67 (one single-character slip, the template identifier is '
               'sealed): part 1 %s row(s), part 2 %s row(s) (part1_identifier_slips.json, part2_identifier_slips.json). Replies read '
               'again from the stored files under lead ruling LR68: part 1 %s, part 2 %s.' % (
                   s.get('part1_identifier_slips'), s.get('part2_identifier_slips'), s.get('part1_reply_file') or 'none',
                   s.get('part2_reply_file') or 'none'),
               '- Prices used for the cap reservation: %s.' % json.dumps(s.get('prices')),
               '- Spend: booked in the calibration ledger (cap $1.00) and the shared total; see calls.jsonl and <gen-root>/calibration/spend.json.']
        with open(os.path.join(self.out, 'RATER_PROVENANCE.md'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(txt) + '\n')


def main(argv=None):
    ap = argparse.ArgumentParser(description='LR4 second blind invitation rating (two sealed parts) through OpenRouter.')
    ap.add_argument('--config', required=True, help='harness/rater_configs/<model_key>.json (read only)')
    ap.add_argument('--gen-root', required=True, help='main-run output root (generations/); writes under <gen-root>/calibration/')
    ap.add_argument('--provider', required=True, help='provider to pin')
    ap.add_argument('--out', default=None, help='default <gen-root>/calibration/lr4_second_rating')
    ap.add_argument('--package', default=PKG)
    ap.add_argument('--reveal', default=REVEAL)
    ap.add_argument('--max-attempts', type=int, default=2, help='requests per part when a reply cannot be parsed (each is billed)')
    ap.add_argument('--backoff', default=None)
    ap.add_argument('--timeout', type=int, default=600)
    ap.add_argument('--key-env', default='OPENROUTER_KEY_FILE')
    ap.add_argument('--resume-after-provider-halt', default=None, metavar='NOTE', help="LR5: the lead's decision to resume, recorded")
    ap.add_argument('--reread-stored', action='store_true',
                    help='LR68: read the stored replies of a part again (in the order received) before any new request')
    a = ap.parse_args(argv)
    cfg = g.load_config(a.config)
    g.check_endpoint(cfg['endpoint'])
    out = a.out or os.path.join(a.gen_root, 'calibration', cal.LR4_DIR)
    os.makedirs(out, exist_ok=True)
    os.makedirs(os.path.join(a.gen_root, 'calibration'), exist_ok=True)
    lockf = open(os.path.join(a.gen_root, 'calibration', '.run.lock'), 'w')      # one calibration process at a time
    try:
        g.fcntl.flock(lockf, g.fcntl.LOCK_EX | g.fcntl.LOCK_NB)
    except OSError:
        print('another calibration process is running', file=sys.stderr)
        return cal.EXIT_REFUSED
    try:                                                    # every precondition before the key is read
        prices = cal.pinned_prices(cfg, a.provider, os.path.join(a.gen_root, 'calibration', cfg['model_key']))
        check_package(a.package, a.reveal)
    except cal.Refused as e:
        print('refused: %s' % e, file=sys.stderr)
        return cal.EXIT_REFUSED
    key = g.read_key(a.key_env)
    g.redact.add(key)
    backoff = tuple(float(x) for x in a.backoff.split(',')) if a.backoff is not None else g.DEFAULT_BACKOFF
    r = Rater(cfg, a.provider, a.gen_root, key, out, prices, a.max_attempts, backoff, a.timeout, pkg=a.package, reveal=a.reveal,
              reread=a.reread_stored)
    if r.status().get('state') == g.PROVIDER_HALT_STATE:
        if not a.resume_after_provider_halt:
            print('halted after consecutive provider mismatches (LR5); restart only with '
                  '--resume-after-provider-halt NOTE', file=sys.stderr)
            return cal.EXIT_HALT
        r._record({'part': None, 'outcome': 'resume_after_provider_halt', 'note': a.resume_after_provider_halt})
        r.set_status(state='resumed', resumes=r.status().get('resumes', []) + [{'at': g.now(), 'note': a.resume_after_provider_halt}])
    try:
        s = r.run()
    except Stop as e:
        r.set_status(state=e.state, stop_reason=g.redact(str(e)))
        print('stopped (%s): %s' % (e.state, g.redact(str(e))), file=sys.stderr)
        return cal.EXIT_HALT if e.state == g.PROVIDER_HALT_STATE else cal.EXIT_STOP
    print(json.dumps({k: s.get(k) for k in ('state', 'part1_sha256', 'part2_sha256')}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
