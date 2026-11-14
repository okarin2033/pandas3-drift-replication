# Process report of the generation (LR82.2 item 11): X-4 extraction failures per model with call dates and the run window (FULL_PREREG 12
# l.478-479, 13 l.538, STAGE2 T9.4) and B.40 programs obtained in a second or later pass (LR80 item 8).
# Written 2026-11-13 in the T11 preparation step. Status: draft; decides nothing.
#
# Reads, per model, ONLY what LR80 item 8 allows: the names of the program files in <gen-dir>/<model>/ (to count them), status.json, and
# the fields `at`, `ok`, `http` of attempts.jsonl (no other field is kept, no program file, no raw/ folder, no console). Extraction failures
# are the programs with `empty_source` in per_program.jsonl (the generator writes an empty program when no code could be extracted).
# B.40 reads the pass log written by logs/t9_2026-11-13/pass_loop.sh (columns model, pass, start_utc, end_utc, exit, state, files_before,
# files_after, failed_calls_by_http); its path is a command-line argument.
#   python3 -I -B sec_process_report.py <common> --gen-dir generations --run-start 2026-11-12T20:51:18Z [--window-days 7] [--planned 1000]
#          [--pass-log logs/t9_2026-11-13/PASS_LOG.tsv] --B 10000 --seed 20261111
import argparse
import collections
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sec_common as C  # noqa: E402

PLANNED_DEFAULT = 1000                 # 200 tasks x k = 5 (LR80 item 3)
WINDOW_DAYS_DEFAULT = 7                # section 12: all calls within 7 days (a target whose overrun is reported, not a stop rule)
PASS_COLUMNS = ('model', 'pass', 'start_utc', 'end_utc', 'exit', 'state', 'files_before', 'files_after', 'failed_calls_by_http')


def parse_time(s):
    """ISO 8601 -> aware UTC datetime. A time without an offset is read as local time (as logs/t9_2026-11-13/pass_loop.sh does)."""
    d = datetime.datetime.fromisoformat(str(s).replace('Z', '+00:00'))
    if d.tzinfo is None:
        d = d.astimezone()
    return d.astimezone(datetime.timezone.utc)


def read_attempts(path):
    """-> list of (at, ok, http); only these three fields are kept (LR80 item 8)."""
    out = []
    with open(path, encoding='utf-8') as f:
        for ln in f:
            if not ln.strip():
                continue
            r = json.loads(ln)
            try:
                at = parse_time(r.get('at'))
            except Exception:
                at = None
            out.append((at, bool(r.get('ok')), r.get('http')))
    return out


def model_dirs(gen_dir, models):
    return {m: os.path.join(gen_dir, m) for m in models if os.path.isdir(os.path.join(gen_dir, m))}


def x4_rows(inp, gen_dir, run_start, window_days, planned):
    start = parse_time(run_start)
    end = start + datetime.timedelta(days=window_days)
    rows, by_day = [], []
    fails = collections.Counter(p['model'] for p in inp.per_program if p.get('empty_source'))
    gen = collections.Counter(p['model'] for p in inp.per_program)
    for m in inp.models:
        d = os.path.join(gen_dir, m)
        if not os.path.isdir(d):
            rows.append({'model': m, 'model_folder_found': False, 'programs_in_per_program': gen[m], 'extraction_failures': fails[m]})
            continue
        n_files = sum(1 for nm in os.listdir(d) if re.search(r'__s\d+\.py$', nm))
        state = None
        sp = os.path.join(d, 'status.json')
        if os.path.isfile(sp):
            with open(sp, encoding='utf-8') as f:
                state = json.load(f).get('state')
        att = read_attempts(os.path.join(d, 'attempts.jsonl')) if os.path.isfile(os.path.join(d, 'attempts.jsonl')) else []
        times = [a for a, _, _ in att if a is not None]
        first, last = (min(times), max(times)) if times else (None, None)
        http = collections.Counter(str(h) for _, ok, h in att if not ok)
        days = collections.Counter(a.strftime('%Y-%m-%d') for a in times)
        for day, n in sorted(days.items()):
            by_day.append({'model': m, 'date_utc': day, 'calls': n})
        rows.append({'model': m, 'model_folder_found': True, 'program_files': n_files, 'planned': planned,
                     'share_of_planned': n_files / planned if planned else None, 'state': state,
                     'programs_in_per_program': gen[m], 'extraction_failures': fails[m],
                     'extraction_failure_share': (fails[m] / gen[m]) if gen[m] else None,
                     'calls_logged': len(att), 'calls_ok': sum(1 for _, ok, _ in att if ok),
                     'failed_calls_by_http': ','.join('%s:%d' % kv for kv in sorted(http.items())) or 'none',
                     'first_call_utc': first.strftime('%Y-%m-%dT%H:%M:%SZ') if first else None,
                     'last_call_utc': last.strftime('%Y-%m-%dT%H:%M:%SZ') if last else None,
                     'span_days': ((last - first).total_seconds() / 86400.0) if first else None,
                     'calls_after_window_end': sum(1 for a in times if a > end), 'window_overrun': bool(last and last > end)})
    return rows, by_day, {'run_start_utc': start.strftime('%Y-%m-%dT%H:%M:%SZ'), 'window_end_utc': end.strftime('%Y-%m-%dT%H:%M:%SZ'),
                          'window_days': window_days}


def b40_rows(inp, pass_log):
    """Programs added in passes after the first: for each model the sum of files_after - files_before over the rows of the pass log."""
    with open(pass_log, encoding='utf-8') as f:
        lines = [ln.rstrip('\n') for ln in f if ln.strip()]
    head = lines[0].split('\t')
    missing = [c for c in PASS_COLUMNS if c not in head]
    if missing:
        raise C.Refuse('pass log: columns missing: %s' % ', '.join(missing))
    acc = collections.OrderedDict()
    for ln in lines[1:]:
        r = dict(zip(head, ln.split('\t')))
        a = acc.setdefault(r['model'], {'passes_logged': 0, 'programs_added': 0, 'first_pass': None, 'last_state': None})
        a['passes_logged'] += 1
        a['programs_added'] += max(0, int(r['files_after']) - int(r['files_before']))
        a['first_pass'] = a['first_pass'] if a['first_pass'] is not None else r['pass']
        a['last_state'] = r['state']
    return [{'model': m, **v} for m, v in acc.items()]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    C.add_common_args(ap)
    ap.add_argument('--gen-dir', required=True, help='generations/ (T11: after the analysis; reads only names, status.json, at/ok/http)')
    ap.add_argument('--run-start', required=True, help='start of the main run (UTC, ISO 8601), the first call of the T9 log')
    ap.add_argument('--window-days', type=int, default=WINDOW_DAYS_DEFAULT)
    ap.add_argument('--planned', type=int, default=PLANNED_DEFAULT)
    ap.add_argument('--pass-log', default=None, help='B.40: logs/t9_2026-11-13/PASS_LOG.tsv')
    ap.add_argument('--ruled-path', default=None)
    a = ap.parse_args(argv)
    if not os.path.isdir(a.gen_dir):
        raise C.Refuse('--gen-dir is not a folder')
    extra = {'PASS_LOG.tsv': a.pass_log} if a.pass_log else None
    inp = C.load_inputs(a, extra)
    C.self_check(inp)
    tool = os.path.abspath(__file__)
    rows, by_day, win = x4_rows(inp, a.gen_dir, a.run_start, a.window_days, a.planned)
    cols = ['model', 'program_files', 'planned', 'state', 'extraction_failures', 'extraction_failure_share', 'calls_logged', 'calls_ok',
            'failed_calls_by_http', 'first_call_utc', 'last_call_utc', 'span_days', 'calls_after_window_end', 'window_overrun']
    meta = C.meta_block(inp, tool, ['X-4'], dict(win, planned=a.planned))
    md = C.header_md(inp, 'X-4', 'Generation process per model: extraction failures, call dates, run window', meta,
                     'Extraction failures = programs with an empty source in per_program.jsonl. Call dates and counts from the fields at/ok/http '
                     'of attempts.jsonl only. The 7-day run window is a target whose overrun is reported, not a stop rule (section 13). '
                     'Window: %s to %s.' % (win['run_start_utc'], win['window_end_utc']))
    md += ['', C.md_table(cols, rows)]
    C.emit(a.out, 'X-4', inp, meta, md, [('models', cols, rows), ('calls_by_day', ['model', 'date_utc', 'calls'], by_day)],
           {'item': 'X-4', 'models': rows, 'calls_by_day': by_day, 'window': win})
    print('wrote X-4.{json,md,tsv}')
    if a.pass_log:
        b = b40_rows(inp, a.pass_log)
        bcols = ['model', 'passes_logged', 'first_pass', 'programs_added', 'last_state']
        bmeta = C.meta_block(inp, tool, ['B.40'], {'pass_log_sha256': C.sha256_file(a.pass_log)})
        bmd = C.header_md(inp, 'B.40', 'Programs obtained in a second or later pass', bmeta,
                          'Sum of files_after - files_before over the passes logged by pass_loop.sh (the pass log starts with pass 2; the first '
                          'pass of a model is the original run and is not in the log).')
        bmd += ['', C.md_table(bcols, b)]
        C.emit(a.out, 'B.40', inp, bmeta, bmd, [('passes', bcols, b)], {'item': 'B.40', 'models': b})
        print('wrote B40.{json,md,tsv}')
    return 0


if __name__ == '__main__':
    sys.exit(C.run_main(main))
