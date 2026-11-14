# Main-run generator for the Born Legacy study: ONE script for all models (from the pilot's gen_openrouter.py).
# Written 2026-11-11 by pkg:HSTAT_GEN. Status: prepared. NOT RUN against the real
# service in the build stage (no paid call, no key file read): its tests use a mock HTTP server on 127.0.0.1 only.
# Standard library only. Implements FULL_PREREG section 3 (extraction rule), 4.2 (decoding and serving policy), 13 (caps,
# stop rules) and STAGE2 T5.10.
#
# usage: OPENROUTER_KEY_FILE=<path> python3 -I harness/gen_full.py --config harness/gen_configs/<model_key>.json
#            --prompts tasks/prompts --out generations/ [--tasks tasks/tasks.json] [--dry-run] [--limit N]
# The key is read ONLY inside this process, from the file whose path is in the environment variable (default
# OPENROUTER_KEY_FILE, option --key-env); it is never printed, logged or written (every logged text is passed through
# redact()). --dry-run needs no key and makes no network call: it renders every request and the worst-case reservation.
#
# Request policy (section 4.2): one user message (the prompt file, byte for byte), no system prompt, max_tokens 8000,
# temperature and top_p are NEVER sent (lead decision 2), provider pinned with allow_fallbacks=false, `reasoning` as set in
# the model config at T7, `seed` = 1000 + k only if the config says the endpoint lists `seed`, usage accounting on.
# Behaviour: resumable (a finished program is the file <out>/<model_key>/<task>__s<k>.py), sample-major order, at most 4
# calls in flight, up to 3 retries on transient errors, a response from a provider other than the pinned one is discarded
# (stored under raw_discarded/, billed in the ledger) and retried, raw JSON per call, per-model spend file, a total ledger
# shared by all models, worst-case reservation before every call (prompt + max_tokens at twice list price), per-model cap and
# total cap (section 13 rule a), unavailability for 7 days (rule b) recorded in <model_dir>/status.json.
# REPAIR5 2026-11-11 (lead ruling LR5, review RV-9; copy before: logs/repair5_2026-11-11/backup/gen_full_before.py): a real run refuses
# to start a model whose config lacks the pinned provider's prices (price_in_per_m, price_out_per_m) and `prices_checked_at` (an ISO
# date or date-time written at T7); three CONSECUTIVE responses whose provider string differs from the pin halt that model
# (status state 'halted:provider_mismatch', report file provider_mismatch_report.json, exit code 4). The count
# survives a restart (status.json); a response from the pinned provider resets it. A halted model starts again only with
# --resume-after-provider-halt (after the lead's decision, which is recorded in status.json).
import argparse
import datetime
import fcntl
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

PLACEHOLDER = '__FILL_AT_T7__'
MAX_IN_FLIGHT = 4
RETRIES = 3
SEVEN_DAYS = 7 * 24 * 3600
TRANSIENT_HTTP = {408, 409, 425, 429, 500, 502, 503, 504, 520, 522, 524}
PROVIDER_MISMATCH_HALT = 3                      # LR5: consecutive responses from a provider other than the pin halt the model
PROVIDER_HALT_STATE = 'halted:provider_mismatch'
AVAILABILITY_HTTP = {404, 503}
ALLOWED_BODY_KEYS = {'model', 'messages', 'max_tokens', 'provider', 'usage', 'reasoning', 'seed'}
FORBIDDEN_BODY_KEYS = {'temperature', 'top_p', 'top_k', 'system', 'stop', 'frequency_penalty', 'presence_penalty'}
DEFAULT_BACKOFF = (5, 15, 45)
OPENROUTER_HOST = 'openrouter.ai'
LOOPBACK_HOSTS = {'127.0.0.1', 'localhost', '::1'}


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec='seconds')


# ------------------------------------------------------------------------------------------------ extraction (section 3)
_FENCE_LABELS = {'', 'python', 'python3', 'py'}


def extract_code(txt):
    """Pre-registered rule (section 3, unchanged from the pilot): the longest fenced block labelled python, python3, py or
    unlabelled; else the whole reply if it compiles; else empty. Fences are paired line by line, so a block with another
    label (```bash ... ```) is skipped as a whole and cannot swallow the next python block (the pilot's regex could)."""
    txt = txt or ''
    blocks, cur, label, inside = [], [], '', False
    for line in txt.split('\n'):
        s = line.strip()
        if not inside:
            if s.startswith('```') and re.fullmatch(r'[A-Za-z0-9_+\-]*', s[3:].strip()):
                inside, cur, label = True, [], s[3:].strip().lower()
        elif s.endswith('```'):                      # closing fence, alone on its line or at the end of the last code line
            tail = line.rstrip()
            alone = s == '```'
            if not alone:
                cur.append(tail[:tail.rindex('```')])
            if label in _FENCE_LABELS:
                blocks.append('\n'.join(cur) + ('\n' if alone else ''))
            inside = False
        else:
            cur.append(line)
    if blocks:
        return max(blocks, key=len)
    try:
        compile(txt, '<reply>', 'exec')
        return txt
    except (SyntaxError, ValueError):
        return ''


# ------------------------------------------------------------------------------------------------ config, key, request
def load_config(path):
    with open(path, encoding='utf-8') as f:
        c = json.load(f)
    for key in ('model', 'model_key', 'endpoint', 'price_in_per_m', 'price_out_per_m', 'k', 'max_tokens'):
        if key not in c:
            raise SystemExit('config %s lacks %r' % (path, key))
    c.setdefault('seed_supported', False)
    c.setdefault('total_cap_usd', 40.0)
    c.setdefault('workers', MAX_IN_FLIGHT)
    return c


def unresolved(cfg):
    """Config items still to be filled at T7 (calibration): a real run refuses to start while any is left."""
    out = []
    if cfg.get('provider') in (None, '', PLACEHOLDER):
        out.append('provider')
    if cfg.get('reasoning') == PLACEHOLDER:
        out.append('reasoning')
    if not isinstance(cfg.get('cap_usd'), (int, float)) or isinstance(cfg.get('cap_usd'), bool):
        out.append('cap_usd')
    for k in ('price_in_per_m', 'price_out_per_m'):                # LR5: the pinned provider's prices, written at T7
        v = cfg.get(k)
        # REPAIR6 2026-11-12 (lead ruling LR20 (1), review SF9): a price of 0 is refused too (the cap reservation would be 0)
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not v > 0:
            out.append(k)
    if not _iso_date(cfg.get('prices_checked_at')):
        out.append('prices_checked_at')
    return out


def _iso_date(v):
    """True for an ISO-8601 date or date-time string (LR5: when the pinned provider's prices were checked)."""
    if not isinstance(v, str) or not v.strip() or v == PLACEHOLDER:
        return False
    try:
        datetime.datetime.fromisoformat(v.strip().replace('Z', '+00:00'))
        return True
    except ValueError:
        return False


def check_endpoint(url):
    u = urllib.parse.urlparse(url)
    host = u.hostname
    if host in LOOPBACK_HOSTS:
        return 'loopback'
    if host == OPENROUTER_HOST and u.scheme == 'https':
        return 'openrouter'
    raise SystemExit('refusing endpoint %r: only https://openrouter.ai/... or a loopback address is allowed' % url)


def read_key(env_name):
    """Read the API key from the file named by the environment variable `env_name`. Accepts a bare key or a line
    `OPENROUTER_API_KEY=...` (optionally `export `). Returns the key; never prints it."""
    path = os.environ.get(env_name)
    if not path:
        raise SystemExit('environment variable %s (path of the key file) is not set' % env_name)
    with open(os.path.expanduser(path), encoding='utf-8') as f:
        lines = [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith('#')]
    for line in lines:
        if line.startswith('export '):
            line = line[7:]
        if line.startswith('OPENROUTER_API_KEY='):
            return line.split('=', 1)[1].strip().strip('"').strip("'")
    if len(lines) == 1 and '=' not in lines[0]:
        return lines[0]
    raise SystemExit('no key found in the file named by %s' % env_name)


class Redactor:
    def __init__(self):
        self.secrets = []

    def add(self, s):
        if s and len(s) >= 6:
            self.secrets.append(s)

    def __call__(self, text):
        text = str(text)
        for s in self.secrets:
            text = text.replace(s, '[redacted]')
        return text


redact = Redactor()


def build_body(cfg, prompt, k):
    """The request body of section 4.2. No temperature, no top_p, no system message."""
    body = {'model': cfg['model'], 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': cfg['max_tokens'],
            'usage': {'include': True}}
    if cfg.get('provider') not in (None, '', PLACEHOLDER):
        body['provider'] = {'order': [cfg['provider']], 'allow_fallbacks': False}
    r = cfg.get('reasoning')
    if r not in (None, PLACEHOLDER):
        body['reasoning'] = r
    if cfg.get('seed_supported'):
        body['seed'] = 1000 + k
    assert set(body) <= ALLOWED_BODY_KEYS and not (set(body) & FORBIDDEN_BODY_KEYS)
    return body


def worst_case(prompt, price_in_per_m, price_out_per_m, max_tokens):
    """Worst-case reservation per call (section 13): prompt + max_tokens at twice list price. The prompt length in tokens is
    over-estimated as characters / 2.5 (as in the pilot)."""
    return 2.0 * (len(prompt) / 2.5 * price_in_per_m / 1e6 + max_tokens * price_out_per_m / 1e6)


def norm_name(s):
    return re.sub(r'[^a-z0-9]', '', str(s or '').lower())


def provider_ok(cfg, resp):
    pr = cfg.get('provider_response') or []
    if isinstance(pr, str):
        pr = [pr]
    want = {norm_name(x) for x in [cfg.get('provider')] + list(pr) if x != PLACEHOLDER}
    return norm_name(resp.get('provider')) in want


def message_text(resp):
    msg = ((resp.get('choices') or [{}])[0].get('message')) or {}
    c = msg.get('content')
    if isinstance(c, list):
        return ''.join(p.get('text', '') for p in c if isinstance(p, dict))
    return c or ''


# ------------------------------------------------------------------------------------------------ ledger
class Ledger:
    """Per-model spend file plus a total state file shared by all model processes (flock). Reservations are held in the
    total file, so concurrent models see each other's in-flight worst cases; reservations of dead processes are dropped."""

    def __init__(self, out_root, model_key, cap, total_cap):
        self.model_dir = os.path.join(out_root, model_key)
        os.makedirs(self.model_dir, exist_ok=True)
        self.model_key, self.cap, self.total_cap = model_key, float(cap), float(total_cap)
        self.spend_f = os.path.join(self.model_dir, 'spend.json')
        self.total_f = os.path.join(out_root, '_total.json')
        self.lock_f = os.path.join(out_root, '_total.lock')
        self.lock = threading.Lock()
        self.local = {}
        if os.path.exists(self.spend_f):
            with open(self.spend_f) as f:
                self.spend = json.load(f)
        else:
            self.spend = {'cap': self.cap, 'spent': 0.0, 'calls': 0, 'discarded_calls': 0, 'discarded_spent': 0.0}
        self.spend['cap'] = self.cap
        self._save_spend()
        with self._flock():
            t = self._read_total()
            dead = [r for r, v in t['reserved'].items() if v['model'] == self.model_key or not _alive(v['pid'])]
            for r in dead:
                del t['reserved'][r]
            self._write_total(t)

    def _flock(self):                                    # context manager over the shared lock file
        outer = self

        class _L:
            def __enter__(s):
                s.fd = os.open(outer.lock_f, os.O_CREAT | os.O_RDWR, 0o644)
                fcntl.flock(s.fd, fcntl.LOCK_EX)
                return s

            def __exit__(s, *a):
                fcntl.flock(s.fd, fcntl.LOCK_UN)
                os.close(s.fd)
                return False
        return _L()

    def _read_total(self):
        if os.path.exists(self.total_f):
            with open(self.total_f) as f:
                return json.load(f)
        return {'settled': 0.0, 'by_model': {}, 'reserved': {}}

    def _write_total(self, t):
        tmp = self.total_f + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(t, f, indent=1)
        os.replace(tmp, self.total_f)

    def _save_spend(self):
        tmp = self.spend_f + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(self.spend, f, indent=1)
        os.replace(tmp, self.spend_f)

    def reserve(self, worst):
        """-> (rid, None) or (None, why). why = 'model_cap' / 'total_cap' when the cap is exhausted, or '..._busy' when the cap
        would be exceeded only because other calls are still in flight (their worst cases are reserved): the caller waits."""
        with self.lock, self._flock():
            if self.spend['spent'] + sum(self.local.values()) + worst > self.cap:
                return None, 'model_cap_busy' if self.local else 'model_cap'
            t = self._read_total()
            committed = t['settled'] + sum(v['amount'] for v in t['reserved'].values())
            if committed + worst > self.total_cap:
                return None, 'total_cap_busy' if t['reserved'] else 'total_cap'
            rid = uuid.uuid4().hex
            t['reserved'][rid] = {'amount': worst, 'pid': os.getpid(), 'model': self.model_key}
            self._write_total(t)
            self.local[rid] = worst
            return rid, None

    def settle(self, rid, cost, discarded=False):
        """Release the reservation and book the actual cost (0 for a failed call, which OpenRouter does not bill)."""
        with self.lock, self._flock():
            t = self._read_total()
            t['reserved'].pop(rid, None)
            self.local.pop(rid, None)
            t['settled'] += cost
            t['by_model'][self.model_key] = t['by_model'].get(self.model_key, 0.0) + cost
            self._write_total(t)
            self.spend['spent'] += cost
            if discarded:
                self.spend['discarded_calls'] += 1
                self.spend['discarded_spent'] += cost
            elif cost >= 0:
                self.spend['calls'] += 1
            self._save_spend()

    def release(self, rid):
        with self.lock, self._flock():
            t = self._read_total()
            t['reserved'].pop(rid, None)
            self.local.pop(rid, None)
            self._write_total(t)

    def totals(self):
        with self._flock():
            t = self._read_total()
        return {'settled': t['settled'], 'reserved': sum(v['amount'] for v in t['reserved'].values()), 'by_model': t['by_model']}


def _alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


# ------------------------------------------------------------------------------------------------ status
class Status:
    def __init__(self, model_dir):
        self.path = os.path.join(model_dir, 'status.json')
        self.lock = threading.Lock()
        self.d = {}
        if os.path.exists(self.path):
            with open(self.path) as f:
                self.d = json.load(f)

    def update(self, **kw):
        with self.lock:
            self.d.update(kw)
            self.d['updated'] = now()
            tmp = self.path + '.tmp'
            with open(tmp, 'w') as f:
                json.dump(self.d, f, indent=1)
            os.replace(tmp, self.path)

    def get(self, k, default=None):
        return self.d.get(k, default)


# ------------------------------------------------------------------------------------------------ the run
class Runner:
    def __init__(self, cfg, prompts_dir, out_root, tasks, key, backoff=DEFAULT_BACKOFF, timeout=300, limit=0, workers=None,
                 dry_run=False, log=print):
        self.cfg, self.prompts_dir, self.out_root, self.tasks = cfg, prompts_dir, out_root, tasks
        self.key, self.backoff, self.timeout, self.limit, self.dry_run, self.log = key, backoff, timeout, limit, dry_run, log
        self.workers = max(1, min(int(workers or cfg.get('workers', MAX_IN_FLIGHT)), MAX_IN_FLIGHT))
        self.model_dir = os.path.join(out_root, cfg['model_key'])
        self.raw_dir = os.path.join(self.model_dir, 'raw')
        self.disc_dir = os.path.join(self.model_dir, 'raw_discarded')
        self.stop = threading.Event()
        self.stop_reason = None
        self.lock = threading.Lock()
        self.counts = {'ok': 0, 'failed': 0, 'discarded': 0, 'retries': 0, 'empty_programs': 0, 'cap_stop': 0}
        self.consecutive_mismatch = 0                      # LR5; restored from status.json below
        self.mismatch_events = []
        self.halt_events, self.halt_count = None, 0
        self.in_flight = 0
        self.max_in_flight_seen = 0
        self.cap = cfg.get('cap_usd') if isinstance(cfg.get('cap_usd'), (int, float)) else 0.0
        if not dry_run:
            os.makedirs(self.raw_dir, exist_ok=True)
            self.ledger = Ledger(out_root, cfg['model_key'], self.cap, cfg['total_cap_usd'])
            self.status = Status(self.model_dir)
            self.attempt_log = os.path.join(self.model_dir, 'attempts.jsonl')
            self.consecutive_mismatch = int(self.status.get('consecutive_provider_mismatches') or 0)
            self.mismatch_events = list(self.status.get('provider_mismatch_events') or [])

    # -- jobs
    def missing(self):
        out = []
        for k in range(self.cfg['k']):                     # sample-major: partial runs still cover every task
            for tid in self.tasks:
                if not os.path.exists(os.path.join(self.model_dir, '%s__s%d.py' % (tid, k))):
                    out.append((tid, k))
        return out

    def jobs(self):
        out = self.missing()
        return out[:self.limit] if self.limit else out

    def prompt_of(self, tid):
        with open(os.path.join(self.prompts_dir, tid + '.txt'), 'rb') as f:
            return f.read().decode('utf-8')

    def log_attempt(self, d):
        d['at'] = now()
        line = redact(json.dumps(d))
        with self.lock:
            with open(self.attempt_log, 'a', encoding='utf-8') as f:
                f.write(line + '\n')

    # -- one HTTP call; returns (resp|None, error|None, http_status|None)
    def post(self, body):
        data = json.dumps(body).encode('utf-8')
        req = urllib.request.Request(self.cfg['endpoint'], data=data, headers={
            'Authorization': 'Bearer ' + self.key, 'Content-Type': 'application/json'})
        with self.lock:
            self.in_flight += 1
            self.max_in_flight_seen = max(self.max_in_flight_seen, self.in_flight)
        try:
            raw = urllib.request.urlopen(req, timeout=self.timeout).read()
            resp = json.loads(raw)
            if isinstance(resp, dict) and 'error' in resp and 'choices' not in resp:
                code = (resp['error'] or {}).get('code') if isinstance(resp['error'], dict) else None
                return None, redact('error body: ' + json.dumps(resp['error'])[:300]), code if isinstance(code, int) else 502
            if 'choices' not in resp:
                return None, redact('no_choices: ' + json.dumps(resp)[:300]), 502
            return resp, None, 200
        except urllib.error.HTTPError as e:
            return None, redact('HTTP %s: %s' % (e.code, e.read().decode('utf-8', 'replace')[:300])), e.code
        except Exception as e:                             # timeouts, resets, DNS, JSON errors
            return None, redact(type(e).__name__ + ': ' + str(e)[:300]), None
        finally:
            with self.lock:
                self.in_flight -= 1

    def run_job(self, job):
        tid, k = job
        pid = '%s__s%d' % (tid, k)
        prompt = self.prompt_of(tid)
        cfg = self.cfg
        worst = worst_case(prompt, cfg['price_in_per_m'], cfg['price_out_per_m'], cfg['max_tokens'])
        body = build_body(cfg, prompt, k)
        last_err, http_status = None, None
        for attempt in range(1 + RETRIES):
            if self.stop.is_set():
                return pid, 'skipped'
            rid, why = self.ledger.reserve(worst)
            while rid is None and why.endswith('_busy') and not self.stop.is_set():
                time.sleep(0.02)                            # other calls in flight hold the reservation: wait, do not stop
                rid, why = self.ledger.reserve(worst)
            if rid is None and self.stop.is_set():
                return pid, 'skipped'
            if rid is None:
                self.halt('cap_' + why)
                with self.lock:
                    self.counts['cap_stop'] += 1
                return pid, 'cap_reached:' + why
            t0 = time.time()
            resp, err, http_status = self.post(body)
            secs = round(time.time() - t0, 1)
            if resp is None:
                self.ledger.release(rid)                     # a failed HTTP call is not billed by the service
                self.log_attempt({'pid': pid, 'attempt': attempt, 'ok': False, 'err': err, 'http': http_status, 'secs': secs})
                last_err = err
                transient = http_status is None or http_status in TRANSIENT_HTTP
                if not transient:
                    break
                if attempt < RETRIES:
                    with self.lock:
                        self.counts['retries'] += 1
                    time.sleep(self.backoff[min(attempt, len(self.backoff) - 1)] if self.backoff else 0)
                continue
            usage = resp.get('usage') or {}
            cost = usage.get('cost')
            est = usage.get('prompt_tokens', 0) * cfg['price_in_per_m'] / 1e6 + usage.get('completion_tokens', 0) * cfg['price_out_per_m'] / 1e6
            booked = float(cost) if cost is not None else worst
            if not provider_ok(cfg, resp):                  # unpinned provider: discard, bill, retry
                self.ledger.settle(rid, booked, discarded=True)
                os.makedirs(self.disc_dir, exist_ok=True)
                self.write_json(os.path.join(self.disc_dir, '%s__a%d.json' % (pid, attempt)),
                                {'pid': pid, 'attempt': attempt, 'reason': 'provider_mismatch', 'provider_returned': resp.get('provider'),
                                 'provider_pinned': cfg.get('provider'), 'at': now(), 'response': resp, 'cost_reported': cost})
                self.log_attempt({'pid': pid, 'attempt': attempt, 'ok': False, 'err': 'provider_mismatch: got %r' % resp.get('provider'),
                                  'secs': secs})
                with self.lock:
                    self.counts['discarded'] += 1
                    if attempt < RETRIES:
                        self.counts['retries'] += 1
                    self.consecutive_mismatch += 1                # LR5: consecutive responses from an unpinned provider
                    self.mismatch_events = (self.mismatch_events + [{'pid': pid, 'attempt': attempt, 'at': now(),
                                                                     'provider_returned': resp.get('provider'),
                                                                     'provider_pinned': cfg.get('provider')}])[-PROVIDER_MISMATCH_HALT:]
                    n_mis, events = self.consecutive_mismatch, list(self.mismatch_events)
                self.status.update(consecutive_provider_mismatches=n_mis, provider_mismatch_events=events)
                if n_mis >= PROVIDER_MISMATCH_HALT:
                    with self.lock:
                        if self.halt_events is None:              # the events that triggered the halt, kept for the report
                            self.halt_events, self.halt_count = events, n_mis
                    self.halt('provider_mismatch')
                    return pid, 'provider_mismatch_halt'
                last_err, http_status = 'provider_mismatch', None
                if attempt < RETRIES:
                    time.sleep(self.backoff[min(attempt, len(self.backoff) - 1)] if self.backoff else 0)
                continue
            self.ledger.settle(rid, booked)
            with self.lock:
                self.consecutive_mismatch = 0                     # LR5: a response from the pinned provider resets the count
                self.mismatch_events = []
            self.status.update(last_success_at=now(), unavailable_since=None, consecutive_provider_mismatches=0,
                               provider_mismatch_events=[])
            rec = {'pid': pid, 'task': tid, 'sample': k, 'model_requested': cfg['model'], 'request': body, 'at': now(),
                   'attempt': attempt, 'response': resp, 'cost_reported': cost, 'cost_list_estimate': est}
            self.write_json(os.path.join(self.raw_dir, pid + '.json'), rec)
            code = extract_code(message_text(resp))
            tmp = os.path.join(self.model_dir, pid + '.py.tmp')
            with open(tmp, 'w', encoding='utf-8') as f:
                f.write(code)
            os.replace(tmp, os.path.join(self.model_dir, pid + '.py'))
            self.log_attempt({'pid': pid, 'attempt': attempt, 'ok': True, 'secs': secs, 'cost': cost})
            with self.lock:
                self.counts['ok'] += 1
                if not code.strip():
                    self.counts['empty_programs'] += 1
            if cost is not None and est > 0 and float(cost) > 1.25 * est + 1e-6:
                self.halt('cost_anomaly')
                return pid, 'COST_ANOMALY reported %s vs list %.5f' % (cost, est)
            return pid, 'ok'
        with self.lock:
            self.counts['failed'] += 1
        if http_status in AVAILABILITY_HTTP or http_status is None:
            self.note_unavailable()
        return pid, 'failed: ' + str(last_err)

    def note_unavailable(self):
        since = self.status.get('unavailable_since')
        if not since:
            self.status.update(unavailable_since=now())
            return
        age = (datetime.datetime.now().astimezone() - datetime.datetime.fromisoformat(since)).total_seconds()
        if age >= SEVEN_DAYS:
            self.halt('unavailable_7d')

    @staticmethod
    def write_json(path, obj):
        tmp = path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(obj, f, indent=1)
        os.replace(tmp, path)

    def halt(self, reason):
        with self.lock:
            if self.stop_reason is None:
                self.stop_reason = reason
        self.stop.set()

    def run(self):
        jobs = self.jobs()
        total_all = self.cfg['k'] * len(self.tasks)
        t = self.ledger.totals()
        self.log('%d calls to make (%d of %d programs exist); model spend $%.4f of cap $%.2f; all models $%.4f of $%.2f'
                 % (len(jobs), total_all - len(self.missing()), total_all, self.ledger.spend['spent'], self.cap, t['settled'],
                    self.cfg['total_cap_usd']))
        since = self.status.get('unavailable_since')
        if not since:
            self.status.update(unavailable_since=now())
            return
        age = (datetime.datetime.now().astimezone() - datetime.datetime.fromisoformat(since)).total_seconds()
        if age >= SEVEN_DAYS:
            self.halt('unavailable_7d')

    @staticmethod
    def write_json(path, obj):
        tmp = path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(obj, f, indent=1)
        os.replace(tmp, path)

    def halt(self, reason):
        with self.lock:
            if self.stop_reason is None:
                self.stop_reason = reason
        self.stop.set()

    def run(self):
        jobs = self.jobs()
        total_all = self.cfg['k'] * len(self.tasks)
        t = self.ledger.totals()
        self.log('%d calls to make (%d of %d programs exist); model spend $%.4f of cap $%.2f; all models $%.4f of $%.2f'
                 % (len(jobs), total_all - len(self.jobs()) if not self.limit else total_all - len(jobs), total_all,
                    self.ledger.spend['spent'], self.cap, t['settled'], self.cfg['total_cap_usd']))
        since = self.status.get('unavailable_since')
        if since:
            age = (datetime.datetime.now().astimezone() - datetime.datetime.fromisoformat(since)).total_seconds()
            self.log('endpoint was unavailable since %s (%.1f days)' % (since, age / 86400))
        self.status.update(state='running', started=now(), pid=os.getpid())
        queue = list(jobs)
        qlock = threading.Lock()
        results = []

        def worker():
            while not self.stop.is_set():
                with qlock:
                    if not queue:
                        return
                    job = queue.pop(0)
                res = self.run_job(job)
                with self.lock:
                    results.append(res)
                    n = len(results)
                if res[1] != 'ok' or n % 20 == 0:
                    self.log('%d/%d %s %s | model spend $%.4f' % (n, len(jobs), res[0], res[1], self.ledger.spend['spent']))
        threads = [threading.Thread(target=worker, daemon=True) for _ in range(self.workers)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
        all_left = self.missing()
        if not all_left:
            self.status.update(state='complete', stop_rule=None)
        elif self.stop_reason in ('cap_model_cap', 'cap_total_cap'):
            self.status.update(state='stopped', stop_rule='a', stop_detail=self.stop_reason)
        elif self.stop_reason == 'unavailable_7d':
            self.status.update(state='stopped', stop_rule='b', stop_detail='endpoint unavailable for 7 consecutive days')
        elif self.stop_reason == 'cost_anomaly':
            self.status.update(state='paused:cost_anomaly', stop_rule=None)
        elif self.stop_reason == 'provider_mismatch':
            detail = ('%d consecutive responses from a provider other than the pinned %r; model halted (LR5)'
                      % (self.halt_count, self.cfg.get('provider')))
            self.write_json(os.path.join(self.model_dir, 'provider_mismatch_report.json'),
                            {'model': self.cfg['model'], 'provider_pinned': self.cfg.get('provider'),
                             'provider_response_accepted': self.cfg.get('provider_response'), 'at': now(), 'detail': detail,
                             'events': self.halt_events, 'rule': 'lead ruling LR5 (FULL_PREREG_AMENDMENT_10.md lists it; '
                             'LEAD_RULINGS_LR1-LR12_2026-11-11.md)'})
            self.status.update(state=PROVIDER_HALT_STATE, stop_rule=None, stop_detail=detail)
        else:
            self.status.update(state='running', stop_rule=None)
        self.log('done: %s | spent $%.4f | %d programs still to generate | stop: %s'
                 % (self.counts, self.ledger.spend['spent'], len(all_left), self.stop_reason))
        return {'counts': self.counts, 'remaining': len(all_left), 'stop_reason': self.stop_reason,
                'max_in_flight': self.max_in_flight_seen, 'results': results}


# ------------------------------------------------------------------------------------------------ dry run
def dry_run(cfg, prompts_dir, tasks, out_path=None, log=print):
    """Render every request and its worst-case reservation without network, key or output folders."""
    miss = unresolved(cfg)
    n, total_worst, lines = 0, 0.0, []
    for k in range(cfg['k']):
        for tid in tasks:
            with open(os.path.join(prompts_dir, tid + '.txt'), 'rb') as f:
                prompt = f.read().decode('utf-8')
            body = build_body(cfg, prompt, k)
            worst = worst_case(prompt, cfg['price_in_per_m'], cfg['price_out_per_m'], cfg['max_tokens'])
            total_worst += worst
            n += 1
            lines.append({'task': tid, 'sample': k, 'endpoint': cfg['endpoint'], 'body': body, 'worst_case_reservation_usd': worst})
    log('DRY RUN %s: %d requests (%d tasks x k=%d), endpoint %s' % (cfg['model'], n, len(tasks), cfg['k'], cfg['endpoint']))
    log('  body keys: %s ; temperature/top_p sent: no ; system prompt: no ; max_tokens %s ; seed %s ; reasoning %s ; provider %s'
        % (sorted(lines[0]['body']) if lines else '-', cfg['max_tokens'], 'only where the endpoint lists seed (1000+k)'
           if cfg.get('seed_supported') else 'never (endpoint does not list it)', cfg.get('reasoning'), cfg.get('provider')))
    if lines:
        log('  worst-case reservation per call: first $%.5f, max $%.5f; sum over all requests $%.4f; cap_usd %s; total cap $%s'
            % (lines[0]['worst_case_reservation_usd'], max(l['worst_case_reservation_usd'] for l in lines), total_worst,
               cfg.get('cap_usd'), cfg['total_cap_usd']))
    if miss:
        log('  UNRESOLVED (filled at T7; a real run refuses to start): %s' % ', '.join(miss))
    if out_path:
        with open(out_path, 'w', encoding='utf-8') as f:
            for l in lines:
                f.write(json.dumps(l) + '\n')
    return {'n': n, 'total_worst': total_worst, 'unresolved': miss, 'lines': lines}


# ------------------------------------------------------------------------------------------------ main
def task_ids(prompts_dir, tasks_json=None):
    if tasks_json:
        with open(tasks_json, encoding='utf-8') as f:
            d = json.load(f)
        ids = [t['id'] for t in (d['tasks'] if isinstance(d, dict) else d)]
    else:
        ids = sorted(f[:-4] for f in os.listdir(prompts_dir) if f.endswith('.txt'))
    missing = [t for t in ids if not os.path.exists(os.path.join(prompts_dir, t + '.txt'))]
    if missing:
        raise SystemExit('no prompt file for tasks: %s' % ', '.join(missing[:5]))
    return ids


def main(argv=None):
    ap = argparse.ArgumentParser(description='Generator for the main run (one script for all models).')
    ap.add_argument('--config', required=True)
    ap.add_argument('--prompts', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--tasks', default=None, help='tasks.json (order of tasks); default: sorted prompt file names')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--dry-run-out', default=None, help='write the rendered requests (JSONL) here')
    ap.add_argument('--limit', type=int, default=0, help='stop after this many new calls (0 = no limit)')
    ap.add_argument('--workers', type=int, default=None, help='at most 4 are used')
    ap.add_argument('--backoff', default=None, help='comma-separated seconds between retries (default 5,15,45)')
    ap.add_argument('--timeout', type=int, default=300)
    ap.add_argument('--key-env', default='OPENROUTER_KEY_FILE')
    ap.add_argument('--resume-after-provider-halt', default=None, metavar='NOTE',
                    help='LR5: start a model halted after consecutive provider mismatches, after the lead decided (the note is recorded)')
    ap.add_argument('--mark-stopped', choices=['a', 'b', 'c'], default=None,
                    help='record that the model is stopped by a section 13 rule (c = harness or generator bug) and exit')
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    check_endpoint(cfg['endpoint'])
    tasks = task_ids(a.prompts, a.tasks)
    if a.dry_run:
        dry_run(cfg, a.prompts, tasks, a.dry_run_out)
        return 0
    if a.mark_stopped:
        mdir = os.path.join(a.out, cfg['model_key'])
        os.makedirs(mdir, exist_ok=True)
        Status(mdir).update(state='stopped', stop_rule=a.mark_stopped, stop_detail='marked by hand')
        print('marked %s as stopped by rule %s' % (cfg['model_key'], a.mark_stopped))
        return 0
    miss = unresolved(cfg)
    if miss:
        print('refusing to start: config items not filled in yet (T7): %s' % ', '.join(miss), file=sys.stderr)
        return 2
    st_path = os.path.join(a.out, cfg['model_key'], 'status.json')
    if os.path.exists(st_path):
        st = Status(os.path.dirname(st_path))
        if st.get('state') == PROVIDER_HALT_STATE:
            if not a.resume_after_provider_halt:
                print('refusing to start: %s is halted after consecutive provider mismatches (LR5), see '
                      'provider_mismatch_report.json; start again only with --resume-after-provider-halt "<lead decision>"'
                      % cfg['model_key'], file=sys.stderr)
                return 2
            st.update(state='running', stop_detail=None, consecutive_provider_mismatches=0, provider_mismatch_events=[],
                      provider_halt_cleared={'at': now(), 'note': a.resume_after_provider_halt})
    key = read_key(a.key_env)
    redact.add(key)
    backoff = tuple(float(x) for x in a.backoff.split(',')) if a.backoff is not None else DEFAULT_BACKOFF
    os.makedirs(os.path.join(a.out, cfg['model_key']), exist_ok=True)
    lockf = open(os.path.join(a.out, cfg['model_key'], '.run.lock'), 'w')
    try:
        fcntl.flock(lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print('another process is already generating %s' % cfg['model_key'], file=sys.stderr)
        return 2
    r = Runner(cfg, a.prompts, a.out, tasks, key, backoff, a.timeout, a.limit, a.workers, log=lambda s: print(redact(s), flush=True))
    res = r.run()
    if res['stop_reason'] == 'provider_mismatch':
        print('HALTED: %d consecutive responses from a provider other than the pin (LR5)'
              % PROVIDER_MISMATCH_HALT, file=sys.stderr)
        return 4
    return 3 if res['stop_reason'] == 'cost_anomaly' else 0


if __name__ == '__main__':
    sys.exit(main())
