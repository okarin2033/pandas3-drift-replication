"""Stratum R fetch (STAGE2 T4.2; FULL_PREREG section 4.3 R selection rule; Amendment 8 items 1-2; lead rulings LR9, LR10).

Written 2026-11-11 by pkg:R_BUILD. Public Stack Exchange API, plain unauthenticated
GET, no key, no account, neutral User-Agent. At most MAX_REQUESTS requests in total (counted in the request log); every `backoff`
field is honoured; the run stops at the first throttle error (error_id 502 or HTTP 429/503) and records how far it got (C8).
Raw responses (they hold third-party question text) are written ONLY under --out, which must be the local-only folder; the request log
written there holds URLs, times, sizes, sha256 and the quota fields only, and is copied into the study folder by the caller.
Request 1: filter=total (the API's own count of the frame). Requests 2..: filter=withbody, pagesize=100, sort=creation, order=asc
(stable paging: questions created during the fetch can only be appended at the end), all pages until has_more is false.
Usage: python3 -I -B fetch_so.py --out <LOCAL>/tasks_R/downloads
"""
import gzip, hashlib, json, os, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone

MAX_REQUESTS = 200
BASE = 'https://api.stackexchange.com/2.3/questions'
COMMON = [('site', 'stackoverflow'), ('tagged', 'pandas'), ('fromdate', '1768953600')]   # 2026-01-21 00:00 UTC
UA = 'research-fetch/1.0'
PAUSE_S = 2.0


def now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


class Fetcher:
    def __init__(self, out):
        self.out, self.n, self.log, self.wait_until = out, 0, [], 0.0

    def get(self, params, name):
        if self.n >= MAX_REQUESTS:
            raise SystemExit('request budget of %d reached' % MAX_REQUESTS)
        delay = max(self.wait_until - time.time(), 0.0)
        if delay:
            time.sleep(delay)
        url = BASE + '?' + urllib.parse.urlencode(params)
        self.n += 1
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Encoding': 'gzip'})
        t = now()
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                status, raw = r.status, r.read()
        except urllib.error.HTTPError as e:
            status, raw = e.code, e.read()
        try:
            body = gzip.decompress(raw)
        except OSError:
            body = raw
        path = os.path.join(self.out, name)
        with open(path, 'wb') as f:
            f.write(body)
        try:
            js = json.loads(body.decode('utf-8'))
        except ValueError:
            js = {}
        rec = {'n': self.n, 'utc': t, 'url': url, 'http': status, 'file': name, 'bytes': len(body),
               'sha256': hashlib.sha256(body).hexdigest(), 'items': len(js.get('items', [])) if isinstance(js, dict) else None,
               'has_more': js.get('has_more'), 'quota_max': js.get('quota_max'), 'quota_remaining': js.get('quota_remaining'),
               'backoff': js.get('backoff'), 'error_id': js.get('error_id'), 'error_name': js.get('error_name'),
               'total': js.get('total')}
        self.log.append(rec)
        print(json.dumps(rec), flush=True)
        wait = PAUSE_S + (float(js['backoff']) if js.get('backoff') else 0.0)
        self.wait_until = time.time() + wait
        throttled = status in (429, 503) or js.get('error_id') == 502 or js.get('error_name') == 'throttle_violation'
        return status, js, throttled


def main():
    out = sys.argv[sys.argv.index('--out') + 1]
    os.makedirs(out, exist_ok=True)
    if os.listdir(out):
        raise SystemExit('output folder not empty: refusing to fetch twice')
    f = Fetcher(out)
    state = {'started_utc': now(), 'stopped_by': None, 'pages_complete': False}
    try:
        st, js, thr = f.get(COMMON + [('filter', 'total')], 'total.json')
        if thr or st != 200:
            state['stopped_by'] = 'throttle or error on the total request (http %s, %s)' % (st, js.get('error_name'))
            return
        page = 1
        while True:
            st, js, thr = f.get(COMMON + [('filter', 'withbody'), ('pagesize', '100'), ('page', str(page)),
                                          ('sort', 'creation'), ('order', 'asc')], 'questions_p%d.json' % page)
            if thr:
                state['stopped_by'] = 'throttle error on page %d (http %s, %s)' % (page, st, js.get('error_name'))
                return
            if st != 200 or 'items' not in js:
                state['stopped_by'] = 'error on page %d (http %s, %s)' % (page, st, js.get('error_name'))
                return
            if page == 1 and js['items'] and not any('content_license' in q for q in js['items']):
                state['stopped_by'] = 'content_license missing from the withbody filter; stop before more requests'
                return
            if not js.get('has_more'):
                state['pages_complete'] = True
                return
            page += 1
    finally:
        state['ended_utc'] = now()
        state['requests'] = f.n
        state['max_requests'] = MAX_REQUESTS
        state['user_agent'] = UA
        state['log'] = f.log
        with open(os.path.join(out, 'fetch_log.json'), 'w', encoding='utf-8') as fh:
            json.dump(state, fh, indent=1)
        print(json.dumps({k: v for k, v in state.items() if k != 'log'}))


if __name__ == '__main__':
    main()
