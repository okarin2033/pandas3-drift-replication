# HRUN: host-side runner of the full study. Written 2026-11-11 by pkg:HRUN. Standard library only (keeps the host process light).
# Copy-and-extend of pilots/r3/harness/runner.py (read-only there). Runs one program in one run config inside the sandbox
# (sandbox_full.sb + child_full.py) and writes the run record of conventions/schema/run_record.schema.json:
#   <out_root>/<run_config>/<program_id>.json.gz          the record (written last: its existence means the run is finished)
#   <out_root>/<run_config>/<program_id>.result.json.gz   canonical result {"result","result_dt","result_type"} (status ok only)
#   <out_root>/<run_config>/<program_id>.trace.json.gz    line trace (T0/T1/T2 only; CONVENTIONS section 4.3)
# Limits (FULL_PREREG section 6): 90 s wall (process group killed), 60 s CPU (ulimit -t), 3 GB RSS (in-process watchdog plus a host-side
# check). Machine rule: at most 2 workers (HRUN_ALLOW_MORE_WORKERS=1 lifts the cap for the author's own machine). Memory gate as the
# pilot: pause below 20% free memory, resume at 25%. Resumable: a finished record is skipped (a harness_error record is re-run).
# REPAIR5 2026-11-11 (lead ruling LR6, review RV-10; copy before: logs/repair5_2026-11-11/backup/runner_full_before.py): a run that ends
# by SIGKILL which the harness did not send itself (no out.json; not the harness's own wall-clock kill, which is a timeout, nor its
# memory kill or its CPU limit) is `harness_error` (harness_error_kind 'external_sigkill'), not `crash`. It is run again on resume, at
# most two more times (3 runs in all, counted in `external_sigkill_runs`); after that it stays harness_error and is counted with the
# other harness_error records (run_programs log; the analyzer's run problems / exclusions). The rule is the same for every model and
# environment.
import concurrent.futures as cf, datetime, gzip, hashlib, json, os, re, shutil, signal, subprocess, sys, threading, time

HARNESS = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HARNESS)
if HARNESS not in sys.path:
    sys.path.insert(0, HARNESS)
import configs as cfgmod

WALL_TIMEOUT = 90
CPU_LIMIT = 60
MEM_LIMIT_BYTES = 3 * 1024 ** 3
TRACE_SECONDS = 60
MAX_WORKERS = 2
SCHEMA_VERSION = 'run_record/1'
EXTERNAL_KILL_MAX_RUNS = 3          # LR6: the first run and at most two more


class Limits:
    def __init__(self, wall=WALL_TIMEOUT, cpu=CPU_LIMIT, mem_bytes=MEM_LIMIT_BYTES, trace_seconds=TRACE_SECONDS):
        self.wall, self.cpu, self.mem_bytes, self.trace_seconds = wall, cpu, mem_bytes, trace_seconds


class FixtureError(Exception):
    pass


# ---------------------------------------------------------------- memory gate (pilot runner.py)
def free_pct():
    try:
        out = subprocess.run(['/usr/bin/memory_pressure', '-Q'], capture_output=True, text=True, timeout=20).stdout
        m = re.search(r'free percentage:\s*(\d+)%', out)
        return int(m.group(1)) if m else 100
    except Exception:
        return 100


class MemoryGate:
    """Pause new runs while free memory is below `pause_below` percent; resume at `resume_at` (pilot: 20 / 25, polled every 15 s)."""

    def __init__(self, free_fn=free_pct, pause_below=20, resume_at=25, interval=15.0, log=print):
        self.free_fn, self.pause_below, self.resume_at, self.interval, self.log = free_fn, pause_below, resume_at, interval, log
        self.paused = threading.Event()
        self._stop = threading.Event()
        self._thread = None
        self.pauses = 0

    def check(self):
        fp = self.free_fn()
        if fp < self.pause_below:
            if not self.paused.is_set():
                self.pauses += 1
                self.log('[memory] free %d%% < %d%%: pausing' % (fp, self.pause_below))
            self.paused.set()
        elif fp >= self.resume_at and self.paused.is_set():
            self.log('[memory] free %d%%: resuming' % fp)
            self.paused.clear()
        return fp

    def start(self):
        self.check()

        def loop():
            while not self._stop.is_set():
                self.check()
                self._stop.wait(self.interval)
        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()
        return self

    def stop(self):
        self._stop.set()

    def wait_if_paused(self, poll=1.0):
        while self.paused.is_set() and not self._stop.is_set():
            time.sleep(poll)


# ---------------------------------------------------------------- helpers
def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def harness_sha256(harness=HARNESS):
    h = hashlib.sha256()
    for fn in ('child_full.py', 'sandbox_full.sb'):
        h.update(fn.encode() + b'\0')
        with open(os.path.join(harness, fn), 'rb') as f:
            h.update(f.read())
    return h.hexdigest()


def write_gz_json(path, obj, **kw):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp%d' % os.getpid()
    with open(tmp, 'wb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as gz:
            gz.write(json.dumps(obj, **kw).encode('utf-8'))
    os.replace(tmp, path)


def read_gz_json(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        return json.load(f)


def canonical_result_sha(obj):
    return sha256_bytes(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode('utf-8'))


_vcache = {}


def venv_versions(venv, study=STUDY):
    """Pinned versions of a venv from envs/<venv>.freeze.txt and pyvenv.cfg (fallback when a run produced no record of its own)."""
    key = (study, venv)
    if key in _vcache:
        return _vcache[key]
    v = {'python': 'unknown', 'pandas': 'unknown', 'numpy': 'unknown', 'pyarrow': None, 'dateutil': None, 'tzdata': None}
    try:
        with open(os.path.join(study, 'envs', venv + '.freeze.txt'), encoding='utf-8') as f:
            lines = f.read().splitlines()
        for ln in lines:
            m = re.match(r'^([A-Za-z0-9_.-]+)==(\S+)', ln.strip())
            if m:
                k = {'pandas': 'pandas', 'numpy': 'numpy', 'pyarrow': 'pyarrow', 'python-dateutil': 'dateutil',
                     'tzdata': 'tzdata'}.get(m.group(1).lower())
                if k:
                    v[k] = m.group(2)
        m = re.search(r'cpython-(\d+\.\d+\.\d+)', os.path.realpath(os.path.join(study, 'envs', venv, 'bin', 'python')))
        if m:
            v['python'] = m.group(1)
    except Exception:
        pass
    _vcache[key] = v
    return v


def resolve_fixtures(job, variant, study=STUDY, fixtures_base=None):
    """-> [(source path, basename)] for the job's fixture variant. `files`: paths relative to fixtures/<variant>/;
    `fixtures_root`: a flat folder of *.csv (or one with main/clean/dirty subfolders)."""
    out = []
    base = fixtures_base or os.path.join(study, 'fixtures')
    for rel in job.get('files') or []:
        p = os.path.join(base, variant, rel)
        if not os.path.isfile(p):
            raise FixtureError('fixture not found: %s' % p)
        out.append((p, os.path.basename(rel)))
    fr = job.get('fixtures_root')
    if fr:
        fr = fr if os.path.isabs(fr) else os.path.join(study, fr)
        sub = os.path.join(fr, variant)
        if os.path.isdir(sub):
            d = sub
        elif variant == 'main' and os.path.isdir(fr):
            d = fr
        else:
            raise FixtureError('fixtures_root %s has no %s variant' % (fr, variant))
        for fn in sorted(os.listdir(d)):
            if fn.lower().endswith('.csv') and os.path.isfile(os.path.join(d, fn)):
                out.append((os.path.join(d, fn), fn))
    names = [b for _, b in out]
    if len(set(names)) != len(names):
        raise FixtureError('duplicate fixture basenames: %s' % sorted({n for n in names if names.count(n) > 1}))
    return out


def record_paths(out_root, run_config, program_id):
    base = os.path.join(out_root, run_config, program_id)
    return base + '.json.gz', base + '.result.json.gz', base + '.trace.json.gz'


def external_kill_runs(prev):
    """Number of runs of this program/config that ended by an external SIGKILL so far (LR6)."""
    try:
        return int((prev or {}).get('external_sigkill_runs') or 0)
    except (TypeError, ValueError):
        return 0


def is_finished(prev):
    """A record is final unless it is a harness_error; an external-SIGKILL harness_error is final after EXTERNAL_KILL_MAX_RUNS runs."""
    if prev is None:
        return False
    if prev.get('status') != 'harness_error':
        return True
    return prev.get('harness_error_kind') == 'external_sigkill' and external_kill_runs(prev) >= EXTERNAL_KILL_MAX_RUNS


def status_without_out(timed_out, rss_killed, exitcode, cpu_ru, limits):
    """Status of a run that wrote no out.json (LR6 for an external SIGKILL). -> (status, harness_error_kind or None)."""
    if timed_out:
        return 'timeout', None
    if rss_killed:
        return 'memory_limit', None
    if exitcode in (-signal.SIGXCPU, 128 + signal.SIGXCPU) or \
            (exitcode in (-signal.SIGKILL, 128 + signal.SIGKILL) and cpu_ru is not None and cpu_ru >= limits.cpu - 1):
        return 'cpu_limit', None
    if exitcode in (-signal.SIGKILL, 128 + signal.SIGKILL):
        return 'harness_error', 'external_sigkill'
    return 'crash', None


def load_finished(out_root, run_config, program_id):
    p = record_paths(out_root, run_config, program_id)[0]
    if not os.path.exists(p):
        return None
    try:
        return read_gz_json(p)
    except Exception:
        return None


# ---------------------------------------------------------------- one run
def _proc_rss_kb(pid):
    try:
        out = subprocess.run(['/bin/ps', '-o', 'rss=', '-p', str(pid)], capture_output=True, text=True, timeout=5).stdout.strip()
        return int(out) if out else None
    except Exception:
        return None


def _sandbox_cmd(cfg, wd, study, harness, limits, envs_dir=None):
    venv_dir = os.path.join(envs_dir or os.path.join(study, 'envs'), cfg.venv)
    py = os.path.join(venv_dir, 'bin', 'python')
    pyreal = os.path.realpath(py)
    pyhome = os.path.dirname(os.path.dirname(pyreal))
    home = os.path.realpath(os.path.expanduser('~'))
    return py, ['/bin/sh', '-c', 'ulimit -t %d; exec "$@"' % limits.cpu, 'sh', '/usr/bin/sandbox-exec',
                '-f', os.path.join(harness, 'sandbox_full.sb'), '-D', 'WORKDIR=' + wd, '-D', 'HOMEDIR=' + home,
                '-D', 'VENVDIR=' + os.path.realpath(venv_dir), '-D', 'PYHOME=' + pyhome, '-D', 'HARNESS=' + os.path.realpath(harness),
                '-D', 'PYEXE=' + py, '-D', 'PYREAL=' + pyreal]


def base_record(job, run_config, cfg, variant, study):
    return {'schema_version': SCHEMA_VERSION, 'program_id': job['program_id'], 'task_id': job.get('task_id'),
            'run_config': run_config, 'config': cfg.name, 'fixture_variant': variant, 'venv': cfg.venv, 'mode': cfg.mode,
            'hash_seed': cfg.hash_seed, 'versions': dict(venv_versions(cfg.venv, study)),
            'options': {'mode.copy_on_write': 'n/a', 'future.infer_string': 'n/a'}, 'status': 'harness_error',
            'result_path': None, 'result_sha256': None, 'result_type': None, 'warnings': [], 'n_warnings': 0,
            'warning_filter_calls_neutralised': 0, 'stdout_sha256': sha256_bytes(b''), 'files_written': {}, 'wall_s': 0.0,
            'cpu_s': None, 'max_rss_bytes': None, 'exc_type': None, 'exc_msg': None, 'exc_user_line': None,
            'trace_path': None, 'trace_truncated': None,
            'started_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
            'harness_sha256': harness_sha256(os.path.join(study, 'harness'))}


def run_one(job, run_config, out_root, work_root, study=STUDY, limits=None, keep_work=False, force=False, fixtures_base=None,
            env_extra=None, envs_dir=None):
    """Run `job` in `run_config`; returns the run record (dict; canonical result NOT loaded), or None if the config is 'not run'
    (C1 without its venv). Existing finished records are returned unchanged (resumable) unless force=True."""
    limits = limits or Limits()
    harness = os.path.join(study, 'harness')
    cfg_name, variant = cfgmod.parse_run_config(run_config)
    cfg = cfgmod.CONFIGS[cfg_name]
    prev = load_finished(out_root, run_config, job['program_id'])
    if not force and is_finished(prev):
        prev['_skipped'] = True
        return prev
    kills_before = external_kill_runs(prev)
    py = os.path.join(envs_dir or os.path.join(study, 'envs'), cfg.venv, 'bin', 'python')
    if not os.path.exists(py):
        if cfg_name == 'C1':
            return None
    rec = base_record(job, run_config, cfg, variant, study)
    if kills_before:
        rec['external_sigkill_runs'] = kills_before                  # LR6: carried over until the program finishes
    rec_path, res_path, trace_path = record_paths(out_root, run_config, job['program_id'])
    work_root = os.path.realpath(work_root)       # sandbox subpath rules match real paths (/var -> /private/var on macOS)
    wd = os.path.join(work_root, run_config, re.sub(r'[^A-Za-z0-9_.\-]', '__', job['program_id']))
    t0 = time.time()
    try:
        if not os.path.exists(py):
            raise FileNotFoundError('venv interpreter missing: ' + py)
        fixtures = resolve_fixtures(job, variant, study, fixtures_base)
        shutil.rmtree(wd, ignore_errors=True)
        os.makedirs(os.path.join(wd, 'tmp'))
        fixhash = {}
        for src, bn in fixtures:
            shutil.copy2(src, os.path.join(wd, bn))
            fixhash[bn] = sha256_file(src)
        pp = job['program_path']
        pp = pp if os.path.isabs(pp) else os.path.join(study, pp)
        shutil.copy2(pp, os.path.join(wd, 'prog.py'))
        rec['program_sha256'] = sha256_file(pp)
        oj = os.path.join(wd, 'out.json')
        py, pre = _sandbox_cmd(cfg, wd, study, harness, limits, envs_dir)
        cmd = pre + [py, '-s', '-P', os.path.join(harness, 'child_full.py'), wd, cfg.mode, oj, json.dumps(fixhash),
                     str(limits.mem_bytes), str(limits.trace_seconds)]
        envv = {'PATH': '/usr/bin:/bin', 'HOME': wd, 'TMPDIR': os.path.join(wd, 'tmp'), 'PYTHONHASHSEED': str(cfg.hash_seed),
                'TZ': 'UTC', 'MPLBACKEND': 'Agg', 'LANG': 'en_US.UTF-8', 'LC_ALL': 'en_US.UTF-8', 'OMP_NUM_THREADS': '1',
                'OPENBLAS_NUM_THREADS': '1', 'VECLIB_MAXIMUM_THREADS': '1', 'PYTHONDONTWRITEBYTECODE': '1',
                'PYTHONIOENCODING': 'utf-8'}
        envv.update(env_extra or {})
        so_p, se_p = wd + '.stdout', wd + '.stderr'
        rec['started_at'] = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
        t0 = time.time()
        with open(so_p, 'wb') as so_f, open(se_p, 'wb') as se_f:
            p = subprocess.Popen(cmd, env=envv, cwd=wd, stdin=subprocess.DEVNULL, stdout=so_f, stderr=se_f,
                                 start_new_session=True)
            timed_out = rss_killed = False
            ru = None
            exitcode = None
            last_ps = 0.0
            while True:
                pid, st, ru_ = os.wait4(p.pid, os.WNOHANG)
                if pid:
                    p.returncode = exitcode = os.waitstatus_to_exitcode(st)
                    ru = ru_
                    break
                now = time.time()
                if now - t0 > limits.wall:
                    timed_out = True
                elif now - last_ps >= 1.0:
                    last_ps = now
                    kb = _proc_rss_kb(p.pid)
                    if kb is not None and kb * 1024 > limits.mem_bytes * 1.15:
                        rss_killed = True
                if timed_out or rss_killed:
                    try:
                        os.killpg(p.pid, signal.SIGKILL)
                    except Exception:
                        pass
                    _, st, ru = os.wait4(p.pid, 0)
                    p.returncode = exitcode = os.waitstatus_to_exitcode(st)
                    break
                time.sleep(0.03)
        rec['wall_s'] = round(time.time() - t0, 3)
        rec['rc'] = exitcode
        child = None
        if os.path.exists(oj):
            try:
                with open(oj) as _jf:
                    child = json.load(_jf)
            except Exception as e:
                child = {'status': 'crash', 'note': 'unreadable out.json: ' + type(e).__name__}
        with open(se_p, 'rb') as _ef:
            rec['proc_stderr_tail'] = _ef.read()[-2000:].decode('utf-8', 'replace')
        cpu_ru = round(ru.ru_utime + ru.ru_stime, 3) if ru is not None else None
        if child is None:
            st_, kind_ = status_without_out(timed_out, rss_killed, exitcode, cpu_ru, limits)
            child = {'status': st_}
            if kind_ == 'external_sigkill':                          # LR6
                rec['harness_error_kind'] = kind_
                rec['external_sigkill_runs'] = kills_before + 1
                child['exc_type'] = 'ExternalSIGKILL'
                child['exc_msg'] = ('ended by SIGKILL not sent by the harness (run %d of at most %d; lead ruling LR6)'
                                    % (kills_before + 1, EXTERNAL_KILL_MAX_RUNS))
        elif timed_out:
            child['status'] = 'timeout'
        elif rss_killed:
            child['status'] = 'memory_limit'
        rec['status'] = child['status']
        for k_dst, k_src in (('versions', 'versions'), ('options', 'options')):
            if child.get(k_src):
                rec[k_dst] = child[k_src]
        rec['warnings'] = child.get('warnings', [])
        rec['n_warnings'] = child.get('n_warnings', 0)
        rec['warning_filter_calls_neutralised'] = child.get('user_filter_calls', 0)
        rec['stdout_sha256'] = child.get('stdout_sha256', rec['stdout_sha256'])
        rec['stdout_tail'] = child.get('stdout_tail', '')
        rec['files_written'] = child.get('files', {})
        for k in ('exc_type', 'exc_msg', 'exc_user_line'):
            rec[k] = child.get(k)
        rec['cpu_s'] = child.get('cpu_s', cpu_ru)
        rec['max_rss_bytes'] = child.get('max_rss_bytes') or (int(ru.ru_maxrss) if ru is not None else None)
        for k in ('t_user', 'exc_last_frame', 'option_error', 'stderr_tail', 'sys_version', 'py_hash_seed_env',
                  'hash_randomization_flag', 'filters_at_start', 'stdout_chars', 'note'):
            if k in child:
                rec[k] = child[k]
        if child['status'] == 'ok':
            obj = {'result': child['result'], 'result_dt': child.get('result_dt'), 'result_type': child.get('result_type')}
            write_gz_json(res_path, obj)
            rec['result_path'] = os.path.relpath(res_path, out_root)
            rec['result_sha256'] = canonical_result_sha(obj)
            rec['result_values_sha256'] = canonical_result_sha(child['result'])
            rec['result_type'] = child.get('result_type')
        if cfg.mode == 'trace' and isinstance(child.get('trace'), dict):
            tr = child['trace']
            write_gz_json(trace_path, tr)
            rec['trace_path'] = os.path.relpath(trace_path, out_root)
            rec['trace_truncated'] = bool(tr.get('truncated'))
            rec['n_trace_events'] = len(tr.get('events', []))
        elif cfg.mode == 'trace':
            rec['trace_truncated'] = None
    except Exception as e:                                        # host-side problem: a record is still written
        rec['status'] = 'harness_error'
        rec['exc_type'] = type(e).__name__
        rec['exc_msg'] = str(e)[:500]
        rec['wall_s'] = round(time.time() - t0, 3)
    finally:
        if not keep_work:
            shutil.rmtree(wd, ignore_errors=True)
            for ext in ('.stdout', '.stderr'):
                try:
                    os.remove(wd + ext)
                except OSError:
                    pass
    write_gz_json(rec_path, rec)
    return rec


# ---------------------------------------------------------------- many runs
def cap_workers(workers):
    if workers > MAX_WORKERS and os.environ.get('HRUN_ALLOW_MORE_WORKERS') != '1':
        print('[runner] workers %d > %d (machine rule): using %d (HRUN_ALLOW_MORE_WORKERS=1 lifts the cap)'
              % (workers, MAX_WORKERS, MAX_WORKERS), flush=True)
        return MAX_WORKERS
    return max(1, workers)


def run_all(tasks, out_root, work_root, study=STUDY, workers=2, limits=None, gate=None, keep_work=False, force=False,
            fixtures_base=None, progress_every=25, log=print):
    """tasks: list of (job, run_config). Returns {(run_config, program_id): status or 'not run'}."""
    workers = cap_workers(workers)
    own_gate = gate is None
    gate = gate or MemoryGate(log=log)
    if own_gate:
        gate.start()
    results = {}
    todo = []
    for job, rc in tasks:
        prev = load_finished(out_root, rc, job['program_id'])
        if not force and is_finished(prev):
            results[(rc, job['program_id'])] = prev['status']
        else:
            todo.append((job, rc))
    log('%d runs to do, %d finished (skipped)' % (len(todo), len(results)))

    def one(t):
        job, rc = t
        gate.wait_if_paused()
        try:
            rec = run_one(job, rc, out_root, work_root, study, limits, keep_work, force, fixtures_base)
            return rc, job['program_id'], ('not run' if rec is None else rec['status'])
        except Exception as e:                                    # run_one catches its own errors; this is a last resort
            log('HARNESS ERROR %s %s: %s: %s' % (rc, job['program_id'], type(e).__name__, e))
            return rc, job['program_id'], 'harness_error'
    t0 = time.time()
    try:
        with cf.ThreadPoolExecutor(max_workers=workers) as ex:
            for n, (rc, pid, st) in enumerate(ex.map(one, todo), 1):
                results[(rc, pid)] = st
                if n % progress_every == 0 or n == len(todo):
                    log('%d/%d done (%.0fs); last %s %s %s' % (n, len(todo), time.time() - t0, rc, pid, st))
    finally:
        if own_gate:
            gate.stop()
    return results
