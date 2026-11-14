# HRUN: command-line driver of the run side. Written 2026-11-11 by pkg:HRUN. Standard library only (host side; python3 -I).
#   python3 -I harness/run_programs.py --jobs JOBS.jsonl --configs E0a,E0b,E1,E2 --out-root DIR [--variants main,clean,dirty]
#          [--work SCRATCH_DIR] [--workers 2] [--compare] [--trace-drift] [--trace-e2] [--force] [--study DIR]
# JOBS.jsonl, one object per line:
#   {"program_id": "confirm/S01", "program_path": "mechanisms/confirm/S01.py", "task_id": null | "M_QF1_01",
#    "card": null | "tasks/M1/M_QF1_01/task.json" | "mechanisms/confirm/S01.card.json" | {inline card},
#    "files": ["QF1_STRING/people.csv"],            # relative to fixtures/<variant>/ ...
#    "fixtures_root": null | "mechanisms/confirm/data/S01"}   # ... or a flat folder whose *.csv are all copied
# Writes <out-root>/<run_config>/<program_id>.json.gz (+ .result.json.gz, .trace.json.gz); resumable (existing records are skipped).
# --compare writes <out-root>/compare/<pair_id>/<program_id>.json (oracle output + warning flags + warning lines) for every pair of
# CONVENTIONS 4.2 whose two records exist, and <out-root>/compare/_program/<program_id>.json (oracle.classify_program).
# --trace-drift runs T0 and T1 (and T2 with --trace-e2) for programs that drift on E0a~E1 (E0a~E2), before the comparisons are written.
# Relative paths in the jobs file are relative to the study folder. Exit 0 when every job produced a record (statuses are printed).
import argparse, collections, json, os, shutil, sys, tempfile

HARNESS = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HARNESS)
if HARNESS not in sys.path:
    sys.path.insert(0, HARNESS)
import configs as cfgmod
import oracle
import runner_full as rf
import warndef


def load_jobs(path, study=STUDY):
    jobs = []
    with open(path, encoding='utf-8') as f:
        for n, ln in enumerate(f, 1):
            if not ln.strip():
                continue
            j = json.loads(ln)
            for k in ('program_id', 'program_path'):
                if k not in j:
                    raise ValueError('%s line %d: missing %r' % (path, n, k))
            j.setdefault('task_id', None)
            j.setdefault('card', None)
            jobs.append(j)
    ids = [j['program_id'] for j in jobs]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise ValueError('duplicate program_id in jobs: %s' % dup[:5])
    return jobs


def resolve_card(job, study=STUDY):
    """Card of a job: inline dict, path to a task.json / card json (relative to the study), or None (unflagged)."""
    c = job.get('card')
    if c is None or isinstance(c, dict):
        return oracle.card_of(c) if c else None
    p = c if os.path.isabs(c) else os.path.join(study, c)
    with open(p, encoding='utf-8') as f:
        return oracle.card_of(json.load(f))


def load_record(out_root, run_config, program_id):
    """Run record with the canonical result merged in under 'result', 'result_dt', 'result_type' (if status ok), or None."""
    rec = rf.load_finished(out_root, run_config, program_id)
    if rec is None:
        return None
    if rec.get('result_path'):
        res = rf.read_gz_json(os.path.join(out_root, rec['result_path']))
        rec['result'], rec['result_dt'] = res['result'], res.get('result_dt')
        rec['result_type'] = res.get('result_type', rec.get('result_type'))
    return rec


def load_trace(out_root, rec):
    if rec and rec.get('trace_path'):
        return rf.read_gz_json(os.path.join(out_root, rec['trace_path']))
    return None


def load_program_records(out_root, program_id, run_configs=None):
    names = run_configs or [n for n in _all_run_configs()]
    out = {}
    for rc in names:
        r = load_record(out_root, rc, program_id)
        if r is not None:
            out[rc] = r
    return out


def _all_run_configs():
    names = list(cfgmod.CONFIGS)
    for v in ('clean', 'dirty'):
        names += [cfgmod.run_config_name(c, v) for c in cfgmod.VARIANT_CONFIGS]
    return names


def _drift(records, base_rc, tgt_rc, card):
    b, t = records.get(base_rc), records.get(tgt_rc)
    if b is None or t is None or b.get('status') != 'ok':
        return False
    return bool(oracle.compare(b, t, card)['drift'])


def run_jobs(jobs, configs, out_root, variants=('main',), workers=2, work_dir=None, study=STUDY, limits=None, force=False,
             compare=False, trace_drift=False, trace_e2=False, fixtures_base=None, keep_work=False, log=print, gate=None):
    """Run every job in every config x variant; returns the list of run-record paths (existing and new). Resumable."""
    own_work = work_dir is None
    work_dir = work_dir or tempfile.mkdtemp(prefix='hrun_work_')
    os.makedirs(work_dir, exist_ok=True)
    out_root = os.path.abspath(out_root)
    run_cfgs = cfgmod.run_configs_for(configs, variants)
    not_run = []
    tasks = [(j, rc) for rc in run_cfgs for j in jobs]
    own_gate = gate is None
    gate = gate or rf.MemoryGate(log=log)
    if own_gate:
        gate.start()
    try:
        status = rf.run_all(tasks, out_root, work_dir, study=study, workers=workers, limits=limits, gate=gate, keep_work=keep_work,
                            force=force, fixtures_base=fixtures_base, log=log)
        if trace_drift:
            extra = []
            for j in jobs:
                card = resolve_card(j, study)
                recs = load_program_records(out_root, j['program_id'], ['E0a', 'E1', 'E2', 'T0', 'T1', 'T2'])
                if _drift(recs, 'E0a', 'E1', card):
                    extra += [(j, 'T0'), (j, 'T1')]
                if trace_e2 and _drift(recs, 'E0a', 'E2', card):
                    extra += [(j, 'T0'), (j, 'T2')]
            seen, uniq = set(), []
            for j, rc in extra:
                if (j['program_id'], rc) not in seen:
                    seen.add((j['program_id'], rc))
                    uniq.append((j, rc))
            if uniq:
                log('trace runs for %d (program, config) pairs' % len(uniq))
                status.update(rf.run_all(uniq, out_root, work_dir, study=study, workers=workers, limits=limits, gate=gate,
                                         keep_work=keep_work, force=force, fixtures_base=fixtures_base, log=log))
    finally:
        if own_gate:
            gate.stop()
        if own_work and not keep_work:
            shutil.rmtree(work_dir, ignore_errors=True)
    for (rc, pid), st in status.items():
        if st == 'not run':
            not_run.append(rc)
    if not_run:
        log('NOT RUN (config absent): %s' % ', '.join(sorted(set(not_run))))
    if compare:
        write_comparisons(jobs, out_root, study, log=log)
    paths = []
    for j in jobs:
        for rc in run_cfgs + [c for c in ('T0', 'T1', 'T2') if trace_drift]:
            p = rf.record_paths(out_root, rc, j['program_id'])[0]
            if os.path.exists(p):
                paths.append(p)
    c = collections.Counter(status.values())
    log('statuses: ' + ', '.join('%s=%d' % kv for kv in sorted(c.items())))
    if c.get('harness_error'):
        log('HARNESS: %d run(s) ended in harness_error (record written; see exc_msg)' % c['harness_error'])
        ext = [p for p in paths if (rf.read_gz_json(p) or {}).get('harness_error_kind') == 'external_sigkill'
               and rf.read_gz_json(p).get('status') == 'harness_error']
        if ext:                                                  # REPAIR5 (LR6): kills the harness did not send
            fin = sum(1 for p in ext if rf.is_finished(rf.read_gz_json(p)))
            log('HARNESS: %d of them ended by an external SIGKILL (LR6); %d after %d runs (final, counted as exclusions)'
                % (len(ext), fin, rf.EXTERNAL_KILL_MAX_RUNS))
    return paths


def write_comparisons(jobs, out_root, study=STUDY, log=print):
    n = 0
    for j in jobs:
        pid = j['program_id']
        card = resolve_card(j, study)
        recs = load_program_records(out_root, pid)
        if not recs:
            continue
        cls = oracle.classify_program(recs, card, pairs=[p for p in cfgmod.TARGET_PAIRS if p[0] in recs and p[1] in recs] or None)
        _write_json(os.path.join(out_root, 'compare', '_program', pid + '.json'),
                    dict(cls, program_id=pid, task_id=j.get('task_id')))
        for base_rc, tgt_rc in cfgmod.COMPARISON_PAIRS:
            b, t = recs.get(base_rc), recs.get(tgt_rc)
            if b is None or t is None:
                continue
            pair = cfgmod.pair_id(base_rc, tgt_rc)
            blk = oracle.pair_block(b, t, card)
            blk.update({'pair': pair, 'program_id': pid, 'task_id': j.get('task_id'), 'baseline_status': b.get('status'),
                        'target_status': t.get('status'), 'clean_on_233': cls['clean_on_233'], 'exclusion': cls['exclusion'],
                        'warned_E0a': cls['warned_E0a']})
            if b.get('status') == 'ok' and t.get('status') == 'ok':
                blk['class_raw'] = oracle.compare(b, t, card)['class']
            _write_json(os.path.join(out_root, 'compare', pair, pid + '.json'), blk)
            n += 1
    log('wrote %d pair comparisons under %s' % (n, os.path.join(out_root, 'compare')))


def _write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp%d' % os.getpid()
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=1, sort_keys=True, default=str)
    os.replace(tmp, path)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__ and __doc__.splitlines()[0])
    ap.add_argument('--jobs', required=True)
    ap.add_argument('--configs', required=True, help='comma-separated base configs, e.g. E0a,E0b,E1,E2')
    ap.add_argument('--variants', default='main', help='comma-separated fixture variants (main,clean,dirty); variant runs exist for E0a,E0b,E1 only')
    ap.add_argument('--out-root', required=True)
    ap.add_argument('--work', default=None)
    ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--compare', action='store_true')
    ap.add_argument('--trace-drift', action='store_true')
    ap.add_argument('--trace-e2', action='store_true')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--study', default=STUDY)
    ap.add_argument('--fixtures-base', default=None)
    ap.add_argument('--mem-limit-gb', type=float, default=rf.MEM_LIMIT_BYTES / 1024 ** 3)
    ap.add_argument('--wall', type=float, default=rf.WALL_TIMEOUT)
    ap.add_argument('--cpu', type=int, default=rf.CPU_LIMIT)
    ap.add_argument('--keep-work', action='store_true')
    a = ap.parse_args(argv)
    configs = [c for c in a.configs.split(',') if c]
    for c in configs:
        if c not in cfgmod.CONFIGS:
            ap.error('unknown config %r (known: %s)' % (c, ','.join(cfgmod.CONFIGS)))
    variants = tuple(v for v in a.variants.split(',') if v)
    jobs = load_jobs(a.jobs, a.study)
    limits = rf.Limits(wall=a.wall, cpu=a.cpu, mem_bytes=int(a.mem_limit_gb * 1024 ** 3))
    paths = run_jobs(jobs, configs, a.out_root, variants, a.workers, a.work, a.study, limits, a.force, a.compare, a.trace_drift,
                     a.trace_e2, a.fixtures_base, a.keep_work)
    print('%d run records under %s' % (len(paths), os.path.abspath(a.out_root)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
