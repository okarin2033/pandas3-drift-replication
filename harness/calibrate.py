# Calibration tool for STAGE2 T7 (review RV-8 of REPAIR_REVIEW.md). Written 2026-11-11 (REPAIR4). Status: draft; NOT RUN against the real service (no paid call, no key file read in the build stage):
# its tests use a mock HTTP server on 127.0.0.1 and the dummy key file only.
# Standard library only. Reuses gen_full.py for the key handling, the endpoint guard, the request policy of FULL_PREREG section
# 4.2 and the shared ledger, so calibration spend is booked into the SAME total ledger as the main run (`<gen-root>/_total.json`,
# so the $40 total of section 13 includes calibration) and against a calibration cap of $1.00 (STAGE2 T7).
#
# Two sub-commands:
#   endpoints  GET the public OpenRouter endpoints metadata of one model (no key) and store it unchanged:
#              python3 -I harness/calibrate.py endpoints --config harness/gen_configs/<key>.json --gen-root generations
#   first-model (REPAIR6, lead ruling LR20 (3)) applies the rule for the first calibration model once, from the ten configs and the
#              pinned provider's checked prices (no request, no key):
#              python3 -I harness/calibrate.py first-model --configs harness/gen_configs --pins <pins.json> --gen-root generations
#   calls      the T7.2 calls of one model: every prompt file of --prompts (or --prompt-ids) x --samples (default 5),
#              provider pinned (--provider), reasoning tried in the order of --reasoning (default: disabled, then the lowest
#              effort values), the first setting that the endpoint accepts is kept for all remaining calls of that model:
#              OPENROUTER_KEY_FILE=<path> python3 -I harness/calibrate.py calls --config harness/gen_configs/<key>.json \
#                  --provider <Name> --prompts ../../pilots/r3/data/prompts --prompt-ids t01,t02,t03,t04 --gen-root generations
#
# Writes only under <gen-root>/calibration/ (per model: endpoints.json, raw/<call>.json, calls.jsonl, summary.json; and the
# calibration spend file spend.json), plus the shared total ledger <gen-root>/_total.json and its lock, which gen_full.py uses.
# The prompt files are only read. What counts as "rejected": HTTP 400 (or an in-body error with code 400) for a reasoning setting;
# the call is then repeated with the next setting. Transient errors (gen_full.TRANSIENT_HTTP) are retried as in gen_full; a response
# from another provider than the pinned one is stored under raw_discarded/, billed, and retried (section 4.2). Nothing here sets a
# reasoning setting, cap or k for the study: CALIBRATION.md and the configs are written in the T7 step from summary.json.
# REPAIR5 fixes 2026-11-12 (REPAIR5_REVIEW.md MF4 (b) and (c); copy before: logs/repair5_fixes_2026-11-12/backup/calibrate_before_mf4.py):
#  - LR5 for calibration: `calls` refuses to start without the PINNED provider's prices and the time they were checked. They come from
#    the config only when the config already pins that same provider and holds numeric prices > 0 and an ISO `prices_checked_at`;
#    otherwise from the stored public metadata <gen-root>/calibration/<model_key>/endpoints.json (sub-command `endpoints`): the
#    endpoint(s) whose provider_name equals --provider (same name normalisation as gen_full.provider_ok), per-token prices x 1e6, the
#    highest if several endpoints of that provider differ, prices_checked_at = the metadata's fetched_at. A price of 0 or a missing
#    price is refused (the cap reservation would be 0). The frame-snapshot prices are never used for calibration.
#  - LR5 halt: three CONSECUTIVE responses whose provider differs from the pin halt that model (exit 4, provider_mismatch_report.json,
#    halt.json). The count is read back from calls.jsonl, so it survives a restart; a response from the pinned provider resets it. A
#    halted model starts again only with --resume-after-provider-halt NOTE (the lead's decision, recorded).
#  - LR12 gate: the first model that runs `calls` must be declared with --first-model (the cheap model named by the T7 brief); it is
#    recorded in <gen-root>/calibration/first_model.json. `calls` for any other model refuses until the reading record
#    <gen-root>/calibration/first_model_read.json exists (written by whoever read the first model's output; fields first_model,
#    read_at (ISO), read_by, files_read (non-empty list), note) and the first model has a summary.json.
#  - LR4 order gate: LR4 makes the second blind invitation rating the FIRST item of T7, so `calls` refuses until
#    <gen-root>/calibration/lr4_second_rating/status.json says state 'sealed_both' (harness/lr4_second_rating.py), unless
#    --lr4-not-first NOTE records the lead's decision to go on without it.
import argparse
import datetime
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import gen_full as g  # noqa: E402

CAL_CAP_USD = 1.00                      # STAGE2 T7 cap, all calibration calls of all models together
EXIT_REFUSED, EXIT_STOP, EXIT_HALT = 2, 3, 4
LR4_DIR = 'lr4_second_rating'


class Refused(Exception):
    """A precondition of LR4, LR5 or LR12 is not met: nothing is sent."""


def booked_cost(usage, worst, price_in_per_m, price_out_per_m):
    """REPAIR6 fixes (REPAIR6_REVIEW.md section 6, "Ledger and $1.00 cap"): the cost booked for a billed (http 200) response.
    -> (booked, basis). The reported usage.cost when it is a finite number >= 0 ('reported'); otherwise (missing, null, not a
    number, negative) the larger of the worst-case reservation and the token estimate at the pinned prices ('worst_case_no_cost'),
    so that the calibration cap stays hard. gen_full books the worst case in the same situation. Used by Calibrator.one and by
    lr4_second_rating.Rater.call."""
    usage = usage or {}
    c = usage.get('cost')
    if c is not None and not isinstance(c, bool):
        try:
            v = float(c)
        except (TypeError, ValueError):
            v = None
        if v is not None and v == v and v not in (float('inf'), float('-inf')) and v >= 0:
            return v, 'reported'

    def num(x):
        return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) and x >= 0 else 0.0
    est = num(usage.get('prompt_tokens')) * price_in_per_m / 1e6 + num(usage.get('completion_tokens')) * price_out_per_m / 1e6
    return max(float(worst), est), 'worst_case_no_cost'


def _iso(v):
    return g._iso_date(v)


def _pos_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0


def pinned_prices(cfg, provider, mdir):
    """-> dict(price_in_per_m, price_out_per_m, prices_checked_at, source[, endpoints]) for the pinned provider, or raises Refused."""
    if cfg.get('provider') not in (None, '', g.PLACEHOLDER) and g.norm_name(cfg.get('provider')) == g.norm_name(provider) and \
            _pos_num(cfg.get('price_in_per_m')) and _pos_num(cfg.get('price_out_per_m')) and _iso(cfg.get('prices_checked_at')):
        return {'price_in_per_m': float(cfg['price_in_per_m']), 'price_out_per_m': float(cfg['price_out_per_m']),
                'prices_checked_at': cfg['prices_checked_at'], 'source': 'config (pins the same provider)'}
    ep = os.path.join(mdir, 'endpoints.json')
    if not os.path.exists(ep):
        raise Refused('no prices of the pinned provider %r: the config does not hold them (with prices_checked_at) and %s does not '
                      'exist; run the endpoints sub-command first (LR5)' % (provider, os.path.basename(ep)))
    with open(ep, encoding='utf-8') as f:
        meta = json.load(f)
    checked = meta.get('fetched_at')
    if not _iso(checked):
        raise Refused('endpoints.json has no ISO fetched_at, so prices_checked_at is unknown (LR5)')
    eps = (((meta.get('response') or {}).get('data') or {}).get('endpoints')) or []
    mine = [e for e in eps if g.norm_name(e.get('provider_name')) == g.norm_name(provider)]
    if not mine:
        raise Refused('the pinned provider %r is not among the endpoints in endpoints.json (LR5)' % provider)
    pin, pout = [], []
    for e in mine:
        pr = e.get('pricing') or {}
        try:
            pin.append(float(pr.get('prompt')) * 1e6)
            pout.append(float(pr.get('completion')) * 1e6)
        except (TypeError, ValueError):
            raise Refused('endpoint of %r has no numeric prompt/completion price in endpoints.json (LR5)' % provider)
    if not (min(pin) > 0 and min(pout) > 0):
        raise Refused('price 0 for the pinned provider %r: the cap reservation would be 0; refused (LR5, review SF9)' % provider)
    return {'price_in_per_m': max(pin), 'price_out_per_m': max(pout), 'prices_checked_at': checked,
            'source': 'endpoints.json (public metadata of the pinned provider)', 'endpoints': len(mine)}


def consecutive_mismatches(calls_f):
    """Number of trailing billed responses (http 200) from a provider other than the pin, read from calls.jsonl; a response from the
    pinned provider or a recorded resume decision resets it (LR5)."""
    n = 0
    if not os.path.exists(calls_f):
        return 0
    with open(calls_f, encoding='utf-8') as f:
        for ln in f:
            d = json.loads(ln)
            if d.get('outcome') == 'resume_after_provider_halt':
                n = 0
            elif d.get('http') == 200:
                n = n + 1 if d.get('provider_ok') is False else 0
    return n


def _sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def lr4_gate(gen_root, override_note=None):
    """LR4: the second blind invitation rating is the first item of T7. -> None or raises Refused."""
    st = os.path.join(gen_root, 'calibration', LR4_DIR, 'status.json')
    if os.path.exists(st):
        with open(st, encoding='utf-8') as f:
            if json.load(f).get('state') == 'sealed_both':
                return None
    if override_note:
        return None
    raise Refused('LR4: the second blind invitation rating (harness/lr4_second_rating.py) is the first item of T7 and is not sealed '
                  '(%s); pass --lr4-not-first NOTE only on the lead\'s decision' % os.path.relpath(st, gen_root))


# REPAIR6 2026-11-12 (lead ruling LR20 (3) as adopted, FULL_PREREG_AMENDMENT_11.md; copy before:
# logs/repair6_2026-11-12/backup/calibrate_before_repair6.py): the first calibration model is the cheapest of the ten by the pinned
# provider's output price at T7 (ties: input price, then identifier). Sub-command `first-model` applies the rule once: it reads the
# ten configs, the provider pinned for each (--pins JSON {model_key: provider}) and the pinned provider's prices (pinned_prices: the
# config pinning that provider with checked prices, or the stored public metadata endpoints.json of `endpoints`), refuses if any of the
# ten has no checked price or a price of 0 (LR5/LR20 (1)), and writes <gen-root>/calibration/first_model_rule.json. `calls
# --first-model` then refuses any model other than the one that file names. Nothing is sent and no key is read by `first-model`.
FIRST_MODEL_RULE = 'first_model_rule.json'
RULE_TEXT = ('lead ruling LR20 (3): the first calibration model is the cheapest of the ten by the pinned provider\'s output price at T7 '
             '(ties: input price, then identifier)')


def first_model_by_rule(configs, pins, gen_root):
    """configs: list of config dicts (the ten models); pins: {model_key: provider}. -> (choice model_key, table) or raises Refused."""
    table, bad = [], []
    for cfg in configs:
        key = cfg['model_key']
        prov = pins.get(key)
        if not prov:
            bad.append('%s: no pinned provider given' % key)
            continue
        try:
            p = pinned_prices(cfg, prov, os.path.join(gen_root, 'calibration', key))
        except Refused as e:
            bad.append('%s: %s' % (key, e))
            continue
        table.append({'model_key': key, 'model': cfg['model'], 'provider': prov, 'price_out_per_m': p['price_out_per_m'],
                      'price_in_per_m': p['price_in_per_m'], 'prices_checked_at': p['prices_checked_at'], 'source': p['source']})
    if bad:
        raise Refused('LR20 (3): the rule needs the checked prices of the pinned provider of every model (LR5): ' + '; '.join(bad))
    if not table:
        raise Refused('LR20 (3): no model configuration given')
    table.sort(key=lambda r: (r['price_out_per_m'], r['price_in_per_m'], r['model']))
    return table[0]['model_key'], table


def cmd_first_model(config_paths, pins, gen_root, expected_n=10):
    cfgs = [g.load_config(p) for p in config_paths]
    if expected_n is not None and len(cfgs) != expected_n:
        raise Refused('LR20 (3): %d configurations given, the rule ranks the ten studied models' % len(cfgs))
    keys = [c['model_key'] for c in cfgs]
    if len(set(keys)) != len(keys):
        raise Refused('LR20 (3): repeated model_key among the configurations')
    cal = os.path.join(gen_root, 'calibration')
    out = os.path.join(cal, FIRST_MODEL_RULE)
    if os.path.exists(out) or os.path.exists(os.path.join(cal, 'first_model.json')):
        raise Refused('LR20 (3): the rule has already been applied (%s or first_model.json exists)' % FIRST_MODEL_RULE)
    choice, table = first_model_by_rule(cfgs, pins, gen_root)
    os.makedirs(cal, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump({'written': g.now(), 'rule': RULE_TEXT, 'first_model': choice, 'n_models': len(table), 'table': table}, f, indent=1)
    return choice, table


def rule_choice(gen_root):
    """The model named by first_model_rule.json, checked against its own table; raises Refused if the file is missing or inconsistent."""
    p = os.path.join(gen_root, 'calibration', FIRST_MODEL_RULE)
    if not os.path.exists(p):
        raise Refused('LR20 (3): the first calibration model is chosen by the rule; run the first-model sub-command first (%s missing)'
                      % FIRST_MODEL_RULE)
    with open(p, encoding='utf-8') as f:
        d = json.load(f)
    tab = d.get('table') or []
    if not tab:
        raise Refused('LR20 (3): %s has no table' % FIRST_MODEL_RULE)
    best = min(tab, key=lambda r: (r['price_out_per_m'], r['price_in_per_m'], r['model']))
    if best['model_key'] != d.get('first_model'):
        raise Refused('LR20 (3): %s names %r but its table gives %r' % (FIRST_MODEL_RULE, d.get('first_model'), best['model_key']))
    return d['first_model']


def check_rule_provider(gen_root, model_key, provider):
    """REPAIR6 fixes (REPAIR6_REVIEW.md section 6, "First-model rule"): `calls` for the first calibration model must use the provider
    that the LR20 (3) ranking used for that model (the provider column of first_model_rule.json, written from --pins). A different
    --provider, or a rule row without a provider, is refused; nothing is sent."""
    p = os.path.join(gen_root, 'calibration', FIRST_MODEL_RULE)
    if not os.path.exists(p):
        raise Refused('LR20 (3): %s missing; the provider of the first model cannot be checked' % FIRST_MODEL_RULE)
    with open(p, encoding='utf-8') as f:
        d = json.load(f)
    rows = [r for r in (d.get('table') or []) if r.get('model_key') == model_key]
    if len(rows) != 1 or not str(rows[0].get('provider') or '').strip():
        raise Refused('LR20 (3): %s has no single row with a provider for %s; the provider used by the rule cannot be checked'
                      % (FIRST_MODEL_RULE, model_key))
    if g.norm_name(rows[0]['provider']) != g.norm_name(provider):
        raise Refused('LR20 (3): --provider %r differs from the provider %r that the rule table used for %s; refused'
                      % (provider, rows[0]['provider'], model_key))


def lr12_gate(gen_root, model_key, declare_first, provider=None):
    """LR12: one cheap model runs first and its output is read before the others. -> 'first' / 'later', or raises Refused.
    REPAIR6 fixes: when `provider` is given (the `calls` path always gives it), every call of the first model is refused unless
    `provider` is the provider of that model in the LR20 (3) rule table (check_rule_provider)."""
    cal = os.path.join(gen_root, 'calibration')
    fm = os.path.join(cal, 'first_model.json')
    if not os.path.exists(fm):
        if not declare_first:
            raise Refused('LR12: no first calibration model is recorded; the cheap first model named by the T7 brief must be run first '
                          'with --first-model')
        chosen = rule_choice(gen_root)                      # REPAIR6: LR20 (3)
        if chosen != model_key:
            raise Refused('LR20 (3): the first calibration model by the rule is %s, not %s' % (chosen, model_key))
        if provider is not None:
            check_rule_provider(gen_root, model_key, provider)
        os.makedirs(cal, exist_ok=True)
        with open(fm, 'w', encoding='utf-8') as f:
            json.dump({'first_model': model_key, 'recorded_at': g.now(), 'rule': 'lead ruling LR12: one cheap model runs first and '
                       'its output is read before the others; chosen by ' + RULE_TEXT}, f, indent=1)
        return 'first'
    with open(fm, encoding='utf-8') as f:
        first = json.load(f)['first_model']
    if first == model_key:
        if provider is not None:
            check_rule_provider(gen_root, model_key, provider)
        return 'first'
    if declare_first:
        raise Refused('LR12: %s is already recorded as the first calibration model' % first)
    if not os.path.exists(os.path.join(cal, first, 'summary.json')):
        raise Refused('LR12: the first model %s has no summary.json yet' % first)
    rd = os.path.join(cal, 'first_model_read.json')
    if not os.path.exists(rd):
        raise Refused('LR12: the output of the first model %s has not been recorded as read (%s missing)' % (first, os.path.basename(rd)))
    with open(rd, encoding='utf-8') as f:
        r = json.load(f)
    if r.get('first_model') != first or not _iso(r.get('read_at')) or not str(r.get('read_by') or '').strip() or \
            not isinstance(r.get('files_read'), list) or not r['files_read']:
        raise Refused('LR12: %s must name first_model %r and hold read_at (ISO), read_by and a non-empty files_read list'
                      % (os.path.basename(rd), first))
    return 'later'
DEFAULT_REASONING = [{'enabled': False}, {'effort': 'minimal'}, {'effort': 'low'}]
USER_AGENT = 'study-calibration/1.0'    # neutral; no name, e-mail or account


def endpoints_url(cfg):
    u = urllib.parse.urlparse(cfg['endpoint'])
    base = '%s://%s' % (u.scheme, u.netloc)
    return base + '/api/v1/models/%s/endpoints' % cfg['model']


def cmd_endpoints(cfg, gen_root, url=None, timeout=60):
    url = url or endpoints_url(cfg)
    g.check_endpoint(url)
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})          # public metadata: no key is sent
    raw = urllib.request.urlopen(req, timeout=timeout).read()
    data = json.loads(raw)
    mdir = os.path.join(gen_root, 'calibration', cfg['model_key'])
    os.makedirs(mdir, exist_ok=True)
    with open(os.path.join(mdir, 'endpoints.json'), 'w', encoding='utf-8') as f:
        json.dump({'fetched_at': g.now(), 'url': url, 'response': data}, f, indent=1)
    eps = ((data.get('data') or {}).get('endpoints')) or []
    rows = [{'provider': e.get('provider_name'), 'tag': e.get('tag'), 'quantization': e.get('quantization'),
             'supported_parameters': e.get('supported_parameters'), 'pricing': e.get('pricing'), 'status': e.get('status')}
            for e in eps]
    with open(os.path.join(mdir, 'endpoints_table.json'), 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=1)
    return rows


class Calibrator:
    def __init__(self, cfg, provider, prompts, gen_root, key, reasoning=None, samples=5, backoff=g.DEFAULT_BACKOFF, timeout=300,
                 cal_cap=CAL_CAP_USD, log=print, prices=None):
        self.cfg = dict(cfg, provider=provider)
        self.prices = prices                                 # MF4 (b): pinned provider's prices (pinned_prices); required
        if prices is not None:
            self.cfg.update(price_in_per_m=prices['price_in_per_m'], price_out_per_m=prices['price_out_per_m'],
                            prices_checked_at=prices['prices_checked_at'])
        self.cfg['provider_response'] = cfg.get('provider_response') if cfg.get('provider_response') not in (None, g.PLACEHOLDER) else []
        self.prompts, self.key, self.samples = prompts, key, samples
        self.reasoning = list(reasoning or DEFAULT_REASONING)
        self.backoff, self.timeout, self.log = backoff, timeout, log
        self.ledger = g.Ledger(gen_root, 'calibration', cal_cap, cfg.get('total_cap_usd', 40.0))
        self.mdir = os.path.join(gen_root, 'calibration', cfg['model_key'])
        self.raw_dir = os.path.join(self.mdir, 'raw')
        self.disc_dir = os.path.join(self.mdir, 'raw_discarded')
        os.makedirs(self.raw_dir, exist_ok=True)
        self.calls_f = os.path.join(self.mdir, 'calls.jsonl')
        self.setting_idx = 0
        self.rejected = []
        self.halt_f = os.path.join(self.mdir, 'halt.json')
        self.halted = False
        self.poster = g.Runner.__new__(g.Runner)        # reuse gen_full.Runner.post (one HTTP call, redacted errors)
        self.poster.cfg, self.poster.key, self.poster.timeout = self.cfg, key, timeout
        self.poster.lock = g.threading.Lock()
        self.poster.in_flight = self.poster.max_in_flight_seen = 0

    def _record(self, d):
        d['at'] = g.now()
        with open(self.calls_f, 'a', encoding='utf-8') as f:
            f.write(g.redact(json.dumps(d)) + '\n')

    def _done(self):
        if not os.path.exists(self.calls_f):
            return set()
        out = set()
        with open(self.calls_f, encoding='utf-8') as f:
            for ln in f:
                d = json.loads(ln)
                if d.get('final'):
                    out.add(d['call_id'])
                if d.get('kept_setting') is not None:
                    self.setting_idx = max(self.setting_idx, d['kept_setting'])
        return out

    def one(self, pid, prompt, k):
        call_id = '%s__s%d' % (pid, k)
        worst = g.worst_case(prompt, self.cfg['price_in_per_m'], self.cfg['price_out_per_m'], self.cfg['max_tokens'])
        attempts = 0
        while True:
            if self.setting_idx >= len(self.reasoning):
                self._record({'call_id': call_id, 'final': True, 'outcome': 'all_reasoning_settings_rejected'})
                return 'all_rejected'
            setting = self.reasoning[self.setting_idx]
            body = g.build_body(dict(self.cfg, reasoning=setting), prompt, k)
            rid, why = self.ledger.reserve(worst)
            if rid is None:
                self._record({'call_id': call_id, 'final': False, 'outcome': 'cap_stop', 'why': why})
                return 'cap_stop'
            resp, err, http = self.poster.post(body)
            if resp is None:
                self.ledger.settle(rid, 0.0)
                if http == 400:                                     # setting rejected: next setting, same call
                    self.rejected.append({'setting': setting, 'error': err})
                    self._record({'call_id': call_id, 'final': False, 'outcome': 'rejected', 'reasoning': setting,
                                  'http': http, 'error': err})
                    self.setting_idx += 1
                    continue
                if (http in g.TRANSIENT_HTTP or http is None) and attempts < g.RETRIES:
                    time.sleep(self.backoff[min(attempts, len(self.backoff) - 1)])
                    attempts += 1
                    continue
                self._record({'call_id': call_id, 'final': True, 'outcome': 'failed', 'reasoning': setting, 'http': http,
                              'error': err})
                return 'failed'
            usage = resp.get('usage') or {}
            cost, cost_basis = booked_cost(usage, worst, self.cfg['price_in_per_m'], self.cfg['price_out_per_m'])   # REPAIR6 fixes
            ok_prov = g.provider_ok(self.cfg, resp)
            self.ledger.settle(rid, cost, discarded=not ok_prov)
            d = self.disc_dir if not ok_prov else self.raw_dir
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, '%s__a%d.json' % (call_id, attempts)), 'w', encoding='utf-8') as f:
                json.dump(resp, f, indent=1)
            ch = (resp.get('choices') or [{}])[0]
            rec = {'call_id': call_id, 'reasoning': setting, 'kept_setting': self.setting_idx, 'http': 200,
                   'provider_returned': resp.get('provider'), 'provider_ok': ok_prov, 'model_returned': resp.get('model'),
                   'finish_reason': ch.get('finish_reason'), 'native_finish_reason': ch.get('native_finish_reason'),
                   'prompt_tokens': usage.get('prompt_tokens'), 'completion_tokens': usage.get('completion_tokens'),
                   'reasoning_tokens': (usage.get('completion_tokens_details') or {}).get('reasoning_tokens'),
                   'cost': cost, 'cost_reported': usage.get('cost'), 'cost_basis': cost_basis,
                   'empty_content': not g.message_text(resp).strip()}
            if not ok_prov:
                n_mis = consecutive_mismatches(self.calls_f) + 1        # this response included
                if n_mis >= g.PROVIDER_MISMATCH_HALT:                   # LR5: halt the model
                    self._record(dict(rec, final=False, outcome='provider_mismatch_discarded', consecutive_mismatches=n_mis))
                    self._halt(n_mis)
                    return 'provider_mismatch_halt'
            if not ok_prov and attempts < g.RETRIES:
                self._record(dict(rec, final=False, outcome='provider_mismatch_discarded'))
                attempts += 1
                continue
            self._record(dict(rec, final=True, outcome='ok' if ok_prov else 'provider_mismatch_after_retries'))
            return 'ok' if ok_prov else 'provider_mismatch'

    def _halt(self, n_mis):
        recs = []
        with open(self.calls_f, encoding='utf-8') as f:
            recs = [json.loads(ln) for ln in f]
        events = [r for r in recs if r.get('http') == 200][-n_mis:]
        rep = {'written': g.now(), 'model_key': self.cfg['model_key'], 'provider_pinned': self.cfg['provider'],
               'consecutive_mismatches': n_mis, 'events': [{k: e.get(k) for k in ('call_id', 'at', 'provider_returned', 'cost')}
                                                          for e in events],
               'rule': 'lead ruling LR5: three consecutive responses whose provider differs from the pin halt that model and are '
                       'reported to the lead (applied to calibration by REPAIR5 fixes MF4)',
               'next': 'the lead decides; a restart needs --resume-after-provider-halt NOTE'}
        with open(os.path.join(self.mdir, 'provider_mismatch_report.json'), 'w', encoding='utf-8') as f:
            f.write(g.redact(json.dumps(rep, indent=1)))
        with open(self.halt_f, 'w', encoding='utf-8') as f:
            json.dump({'state': g.PROVIDER_HALT_STATE, 'at': g.now(), 'consecutive_mismatches': n_mis, 'resumes': []}, f, indent=1)
        self.halted = True

    def resume_after_halt(self, note):
        """Record the lead's decision to resume a halted model (resets the consecutive count)."""
        with open(self.halt_f, encoding='utf-8') as f:
            h = json.load(f)
        h['resumes'] = h.get('resumes', []) + [{'at': g.now(), 'note': note}]
        h['state'] = 'resumed'
        with open(self.halt_f, 'w', encoding='utf-8') as f:
            json.dump(h, f, indent=1)
        self._record({'call_id': None, 'final': False, 'outcome': 'resume_after_provider_halt', 'note': note})

    def is_halted(self):
        if not os.path.exists(self.halt_f):
            return False
        with open(self.halt_f, encoding='utf-8') as f:
            return json.load(f).get('state') == g.PROVIDER_HALT_STATE

    def run(self, prompt_ids):
        done = self._done()
        counts = {}
        for k in range(self.samples):                       # sample-major, as in the main run
            for pid in prompt_ids:
                if '%s__s%d' % (pid, k) in done:
                    continue
                with open(os.path.join(self.prompts, pid + '.txt'), 'rb') as f:
                    prompt = f.read().decode('utf-8')
                r = self.one(pid, prompt, k)
                counts[r] = counts.get(r, 0) + 1
                if r in ('cap_stop', 'all_rejected', 'provider_mismatch_halt'):
                    return self.summary(counts, stop=r)
        return self.summary(counts)

    def summary(self, counts, stop=None):
        recs = []
        if os.path.exists(self.calls_f):
            with open(self.calls_f, encoding='utf-8') as f:
                recs = [json.loads(ln) for ln in f]
        fin = [r for r in recs if r.get('final') and r.get('outcome') == 'ok']

        def mean(field):
            xs = [r[field] for r in fin if isinstance(r.get(field), (int, float))]
            return (sum(xs) / len(xs)) if xs else None
        fr = {}
        for r in fin:
            fr[str(r.get('finish_reason'))] = fr.get(str(r.get('finish_reason')), 0) + 1
        kept = self.reasoning[self.setting_idx] if self.setting_idx < len(self.reasoning) else None
        s = {'written': g.now(), 'model': self.cfg['model'], 'model_key': self.cfg['model_key'], 'provider_pinned': self.cfg['provider'],
             'reasoning_tried_in_order': self.reasoning, 'reasoning_rejected': [r for r in recs if r.get('outcome') == 'rejected'],
             'reasoning_kept': kept, 'calls_ok': len(fin), 'outcomes_this_invocation': counts, 'stop': stop,
             'providers_returned': sorted({str(r.get('provider_returned')) for r in recs if r.get('http') == 200}),
             'provider_mismatches': sum(1 for r in recs if r.get('provider_ok') is False),
             'mean_prompt_tokens': mean('prompt_tokens'), 'mean_completion_tokens': mean('completion_tokens'),
             'mean_reasoning_tokens': mean('reasoning_tokens'), 'finish_reasons': fr,
             'cost_ok_calls': sum(r.get('cost') or 0.0 for r in fin),
             'cost_all_billed_calls': sum(r.get('cost') or 0.0 for r in recs if r.get('http') == 200),
             'ledger': self.ledger.totals(), 'note': 'calibration output; never analysed as study data (STAGE2 T7.4)',
             'prices_used': self.prices, 'halted': self.is_halted()}
        with open(os.path.join(self.mdir, 'summary.json'), 'w', encoding='utf-8') as f:
            f.write(g.redact(json.dumps(s, indent=1)))
        return s


def main(argv=None):
    ap = argparse.ArgumentParser(description='STAGE2 T7 calibration tool (endpoints metadata and calibration calls).')
    ap.add_argument('command', choices=['endpoints', 'calls', 'first-model'])
    ap.add_argument('--config', default=None, help='gen_configs/<model_key>.json (read only; endpoints and calls)')
    ap.add_argument('--configs', default=None, help='first-model: folder of the ten model configurations (*.json), read only')
    ap.add_argument('--pins', default=None, help='first-model: JSON file {model_key: provider pinned at T7}')
    ap.add_argument('--gen-root', required=True, help='the main-run output root (generations/); writes go to <gen-root>/calibration/')
    ap.add_argument('--endpoints-url', default=None, help='override (tests: a loopback URL)')
    ap.add_argument('--provider', default=None, help='provider to pin (calls)')
    ap.add_argument('--prompts', default=None, help='folder of prompt files <id>.txt (read only)')
    ap.add_argument('--prompt-ids', default=None, help='comma-separated prompt ids (default: every .txt file, sorted)')
    ap.add_argument('--samples', type=int, default=5)
    ap.add_argument('--reasoning', default=None, help='JSON list of reasoning objects in the order to try (default: disabled, minimal, low)')
    ap.add_argument('--backoff', default=None)
    ap.add_argument('--timeout', type=int, default=300)
    ap.add_argument('--key-env', default='OPENROUTER_KEY_FILE')
    ap.add_argument('--first-model', action='store_true', help='LR12: declare this model the cheap first calibration model')
    ap.add_argument('--lr4-not-first', default=None, metavar='NOTE', help="LR4 gate override: the lead's decision, recorded")
    ap.add_argument('--resume-after-provider-halt', default=None, metavar='NOTE', help="LR5: the lead's decision to resume, recorded")
    a = ap.parse_args(argv)
    if a.command == 'first-model':                          # REPAIR6: LR20 (3); nothing is sent, no key is read
        if not a.configs or not a.pins:
            print('first-model needs --configs and --pins', file=sys.stderr)
            return EXIT_REFUSED
        paths = sorted(os.path.join(a.configs, f) for f in os.listdir(a.configs) if f.endswith('.json'))
        with open(a.pins, encoding='utf-8') as f:
            pins = json.load(f)
        try:
            choice, table = cmd_first_model(paths, pins, a.gen_root)
        except Refused as e:
            print('refused: %s' % e, file=sys.stderr)
            return EXIT_REFUSED
        for r in table:
            print('%-40s %-14s out %10.4f  in %10.4f' % (r['model_key'], r['provider'], r['price_out_per_m'], r['price_in_per_m']))
        print('first calibration model by LR20 (3): %s' % choice)
        return 0
    if not a.config:
        print('%s needs --config' % a.command, file=sys.stderr)
        return EXIT_REFUSED
    cfg = g.load_config(a.config)
    g.check_endpoint(cfg['endpoint'])
    if a.command == 'endpoints':
        rows = cmd_endpoints(cfg, a.gen_root, a.endpoints_url, a.timeout)
        print('%d endpoints stored for %s' % (len(rows), cfg['model_key']))
        return 0
    if not a.provider or not a.prompts:
        print('calls needs --provider and --prompts', file=sys.stderr)
        return 2
    ids = a.prompt_ids.split(',') if a.prompt_ids else sorted(f[:-4] for f in os.listdir(a.prompts) if f.endswith('.txt'))
    mdir = os.path.join(a.gen_root, 'calibration', cfg['model_key'])
    os.makedirs(os.path.join(a.gen_root, 'calibration'), exist_ok=True)
    lockf = open(os.path.join(a.gen_root, 'calibration', '.run.lock'), 'w')      # one calibration process at a time
    try:
        g.fcntl.flock(lockf, g.fcntl.LOCK_EX | g.fcntl.LOCK_NB)
    except OSError:
        print('another calibration process is running', file=sys.stderr)
        return 2
    try:                                                    # MF4: every precondition is checked before the key is read
        lr4_gate(a.gen_root, a.lr4_not_first)
        prices = pinned_prices(cfg, a.provider, mdir)
        halted = False
        if os.path.exists(os.path.join(mdir, 'halt.json')):
            with open(os.path.join(mdir, 'halt.json'), encoding='utf-8') as f:
                halted = json.load(f).get('state') == g.PROVIDER_HALT_STATE
        if halted and not a.resume_after_provider_halt:
            print('model %s is halted after consecutive provider mismatches (LR5); restart only with '
                  '--resume-after-provider-halt NOTE' % cfg['model_key'], file=sys.stderr)
            return EXIT_HALT
        lr12_gate(a.gen_root, cfg['model_key'], a.first_model, provider=a.provider)    # REPAIR6 fixes: provider vs rule table
    except Refused as e:
        print('refused: %s' % e, file=sys.stderr)
        return EXIT_REFUSED
    if a.lr4_not_first:                                     # the lead's decision to calibrate without the LR4 rating, recorded
        with open(os.path.join(a.gen_root, 'calibration', 'lr4_not_first.jsonl'), 'a', encoding='utf-8') as f:
            f.write(json.dumps({'at': g.now(), 'model_key': cfg['model_key'], 'note': a.lr4_not_first}) + '\n')
    key = g.read_key(a.key_env)
    g.redact.add(key)
    backoff = tuple(float(x) for x in a.backoff.split(',')) if a.backoff is not None else g.DEFAULT_BACKOFF
    reasoning = json.loads(a.reasoning) if a.reasoning else None
    c = Calibrator(cfg, a.provider, a.prompts, a.gen_root, key, reasoning, a.samples, backoff, a.timeout,
                   log=lambda s: print(g.redact(s), flush=True), prices=prices)
    if a.resume_after_provider_halt and c.is_halted():
        c.resume_after_halt(a.resume_after_provider_halt)
    s = c.run(ids)
    print(g.redact(json.dumps({k: s[k] for k in ('model_key', 'reasoning_kept', 'calls_ok', 'stop', 'providers_returned',
                                                 'mean_completion_tokens', 'mean_reasoning_tokens', 'cost_all_billed_calls')})))
    if s['stop'] == 'provider_mismatch_halt':
        print('halted: %d consecutive responses from a provider other than the pin (LR5)'
              % g.PROVIDER_MISMATCH_HALT, file=sys.stderr)
        return EXIT_HALT
    return 0 if s['stop'] is None else EXIT_STOP


if __name__ == '__main__':
    sys.exit(main())
