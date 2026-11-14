# VERIFY: largest RSS over all run records of the package, record counts by status, and disk use. Written 2026-11-11 by pkg:VERIFY.
# Run: python3 -I -B harness/controls/disk_rss.py > logs/controls/disk_rss_2026-11-11.txt
import collections, glob, gzip, json, os, subprocess
S = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
mx, who, st, n = 0, None, collections.Counter(), 0
for f in [g for sub in ('controls', 'regression') for g in glob.glob(os.path.join(S, 'logs', sub, '**', 'runs', '**', '*.json.gz'), recursive=True)]:
    if f.endswith(('.result.json.gz', '.trace.json.gz')):
        continue
    r = json.load(gzip.open(f, 'rt')); n += 1; st[r['status']] += 1
    if (r.get('max_rss_bytes') or 0) > mx:
        mx, who = r['max_rss_bytes'], '%s %s' % (r['run_config'], r['program_id'])
print('run records: %d; statuses %s' % (n, dict(st)))
print('largest max_rss_bytes: %.1f MB (%s); limit used 2 GB' % (mx / 1e6, who))
for d in ('logs/controls', 'logs/regression', 'harness/controls'):
    print(subprocess.run(['du', '-sh', os.path.join(S, d)], capture_output=True, text=True).stdout.strip().replace(S + '/', ''))
