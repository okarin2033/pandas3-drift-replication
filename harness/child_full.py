# HRUN: runs ONE program inside the sandbox, in one pandas environment. Written 2026-11-11 by pkg:HRUN.
# Copy-and-extend of pilots/r3/harness/child.py (read-only there). Standard library + the venv's numpy/pandas only.
# usage: <venv>/bin/python -s -P child_full.py <workdir> <mode> <out_json> <fixture_hash_json> [<mem_limit_bytes> [<trace_seconds>]]
#   mode: base | cow | str | both | stroff | trace   (see harness/configs.py)
# The program is <workdir>/prog.py; fixtures are copies in <workdir>. Output: one JSON record (the host, runner_full.py, turns it
# into the run record of conventions/schema/run_record.schema.json and splits the canonical result and the trace into their own files).
# Changes against the pilot (each has a unit test in harness/tests/run/):
#   * warnings are recorded at the warnings._showwarnmsg level, so a program's own catch_warnings(record=True) cannot hide them;
#     each record carries category qualname/module, MRO, message, filename, lineno, user_line, pandas_on_stack, phase, count (CONVENTIONS 12)
#   * result type is stored as module.qualname; the oracle compares class names without the module path (pilot CHANGES 23:47)
#   * stdout is hashed in full and only its tail is kept; cpu_s and max_rss_bytes are recorded; trace has a truncation flag
#   * memory limit and trace seconds are arguments (study limits: 3 GB RSS, 60 s trace; section 6)
import sys, os


def main():
    workdir, mode, outjson = sys.argv[1], sys.argv[2], sys.argv[3]
    import json, io, time, math, threading, resource, contextlib, random, hashlib, datetime, decimal, traceback
    prog = os.path.join(workdir, 'prog.py')
    os.chdir(workdir)
    MEM_LIMIT = int(sys.argv[5]) if len(sys.argv) > 5 else 3 * 1024 ** 3     # bytes; ru_maxrss is in bytes on macOS
    TRACE_SECONDS = float(sys.argv[6]) if len(sys.argv) > 6 else 60.0
    TRACE_EVENTS = 20000
    fixhash_json = sys.argv[4] if len(sys.argv) > 4 else '{}'
    rec = {'mode': mode, 'status': 'ok', 'warnings': [], 'n_warnings': 0, 'user_filter_calls': 0,
           'sys_version': sys.version, 'py_hash_seed_env': os.environ.get('PYTHONHASHSEED'),
           'hash_randomization_flag': sys.flags.hash_randomization}

    def memwatch():
        while True:
            if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > MEM_LIMIT:
                try:
                    with open(outjson, 'w') as f:
                        json.dump({'mode': mode, 'status': 'memory_limit',
                                   'max_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}, f)
                finally:
                    os._exit(86)
            time.sleep(0.05)
    threading.Thread(target=memwatch, daemon=True).start()

    import warnings
    WARN_FILE = warnings.__file__
    _orig = {n: getattr(warnings, n) for n in ('filterwarnings', 'simplefilter', 'resetwarnings')}

    def _caller_is_user():
        f = sys._getframe(2)
        while f is not None and f.f_code.co_filename == WARN_FILE:
            f = f.f_back
        return f is not None and f.f_code.co_filename == prog

    def _wrap(name):
        def w(*a, **k):
            if _caller_is_user():          # the program tried to silence/alter warnings: neutralised, counted
                rec['user_filter_calls'] += 1
                return None
            return _orig[name](*a, **k)
        return w
    for n in _orig:
        setattr(warnings, n, _wrap(n))
    _orig['resetwarnings']()
    _orig['simplefilter']('always')

    phase = ['import']
    pandas_dir = ['\0']
    seen = {}
    ORIG_SHOWMSG = warnings._showwarnmsg
    ORIG_IMPL = warnings._showwarnmsg_impl

    def _record(msg):
        f = sys._getframe(2)               # 0 = _record, 1 = my_showmsg, 2 = the code that called warnings.warn
        on_pd, uline = False, None
        while f is not None:
            fn = f.f_code.co_filename
            if fn.startswith(pandas_dir[0]):
                on_pd = True
            if uline is None and fn == prog:
                uline = f.f_lineno
            f = f.f_back
        category = msg.category
        mro = [c.__module__ + '.' + c.__qualname__ for c in category.__mro__]
        text = str(msg.message)[:300]
        rec['n_warnings'] += 1
        key = (category.__module__, category.__qualname__, text, uline, phase[0], bool(on_pd))
        if key in seen:
            seen[key]['count'] += 1
            return
        if len(seen) >= 200:
            return
        d = {'category_qualname': category.__qualname__, 'category_module': category.__module__, 'mro': mro,
             'message': text, 'filename': msg.filename, 'lineno': msg.lineno, 'user_line': uline,
             'pandas_on_stack': on_pd, 'phase': phase[0], 'count': 1}
        seen[key] = d
        rec['warnings'].append(d)

    def my_showmsg(msg):
        try:
            _record(msg)
        except Exception:
            pass
        # a program's own catch_warnings(record=True) replaced the implementation: keep its view intact (it still gets its warnings)
        if warnings._showwarnmsg_impl is not ORIG_IMPL:
            ORIG_SHOWMSG(msg)
    warnings._showwarnmsg = my_showmsg

    import numpy as np
    import pandas as pd
    pandas_dir[0] = os.path.dirname(pd.__file__) + os.sep
    from importlib import metadata as _md

    def _ver(name):
        try:
            return _md.version(name)
        except Exception:
            return None
    rec['versions'] = {'python': sys.version.split()[0], 'pandas': pd.__version__, 'numpy': np.__version__,
                       'pyarrow': None, 'dateutil': _ver('python-dateutil'), 'tzdata': _ver('tzdata')}
    try:
        import pyarrow
        rec['versions']['pyarrow'] = pyarrow.__version__
    except Exception:
        pass
    # diagnostics: non-'always' filters that numpy/pandas registered at import time stay active (as in the pilot)
    try:
        rec['filters_at_start'] = [[str(a), (m.pattern if m is not None else None), c.__name__ if c is not None else None,
                                    (mod.pattern if mod is not None else None), ln] for a, m, c, mod, ln in warnings.filters
                                   if a != 'always'][:40]
    except Exception:
        rec['filters_at_start'] = None
    phase[0] = 'setup'                      # option calls (e.g. the Pandas4Warning of pandas 3.1.1 for infer_string) are 'setup', not 'user'
    try:
        if mode in ('cow', 'both'):
            pd.set_option('mode.copy_on_write', True)
        if mode in ('str', 'both'):
            pd.set_option('future.infer_string', True)
        if mode == 'stroff':
            pd.set_option('future.infer_string', False)
    except Exception as e:
        rec['option_error'] = type(e).__name__ + ': ' + str(e)[:200]
    rec['options'] = {}
    for o in ('mode.copy_on_write', 'future.infer_string'):
        try:
            rec['options'][o] = str(pd.get_option(o))
        except Exception:
            rec['options'][o] = 'n/a'
    random.seed(0)
    np.random.seed(0)

    # ---------------- canonicalisation (oracle input; same format as the pilot, CONVENTIONS section 12) ----------------
    def cv(v):
        if v is None or v is pd.NaT or v is pd.NA:
            return None
        if isinstance(v, np.datetime64):
            return None if np.isnat(v) else 'TS:' + pd.Timestamp(v).isoformat()
        if isinstance(v, np.timedelta64):
            return None if np.isnat(v) else 'TD:' + repr(pd.Timedelta(v).total_seconds())
        if isinstance(v, np.generic):
            v = v.item()
        if isinstance(v, bool):
            return v
        if isinstance(v, int):
            return v
        if isinstance(v, float):
            return None if math.isnan(v) else v
        if isinstance(v, str):
            return v
        if isinstance(v, pd.Timestamp):
            return 'TS:' + v.isoformat()
        if isinstance(v, datetime.datetime):
            return 'TS:' + pd.Timestamp(v).isoformat()
        if isinstance(v, datetime.date):
            return 'D:' + v.isoformat()
        if isinstance(v, (pd.Timedelta, datetime.timedelta)):
            return 'TD:' + repr(pd.Timedelta(v).total_seconds())
        if isinstance(v, pd.Interval):
            return 'IV:' + str(v)
        if isinstance(v, pd.Period):
            return 'PE:' + str(v)
        if isinstance(v, decimal.Decimal):
            return float(v)
        if isinstance(v, (list, tuple)):
            return [cv(u) for u in v]
        if isinstance(v, complex):
            return 'C:' + repr(v)
        try:
            if pd.isna(v):
                return None
        except Exception:
            pass
        return 'OBJ:' + type(v).__name__ + ':' + str(v)[:200]

    def canon(x, depth=0):
        """Returns (values, dtypes). values carry labels and data; dtypes are kept apart."""
        if depth > 6:
            return '<deep>', None
        if isinstance(x, pd.DataFrame):
            data = [[cv(v) for v in x.iloc[:, i].tolist()] for i in range(x.shape[1])]
            return ({'k': 'df', 'columns': [cv(c) for c in x.columns], 'index': [cv(v) for v in x.index.tolist()],
                     'index_names': [cv(n) for n in x.index.names], 'columns_names': [cv(n) for n in x.columns.names],
                     'data': data},
                    {'k': 'df', 'dtypes': [str(t) for t in x.dtypes], 'index': str(x.index.dtype),
                     'columns': str(x.columns.dtype)})
        if isinstance(x, pd.Series):
            return ({'k': 's', 'name': cv(x.name), 'index': [cv(v) for v in x.index.tolist()],
                     'index_names': [cv(n) for n in x.index.names], 'data': [cv(v) for v in x.tolist()]},
                    {'k': 's', 'dtype': str(x.dtype), 'index': str(x.index.dtype)})
        if isinstance(x, pd.Index):
            return ({'k': 'idx', 'name': cv(x.name), 'data': [cv(v) for v in x.tolist()]},
                    {'k': 'idx', 'dtype': str(x.dtype)})
        if isinstance(x, np.ndarray):
            def nest(o):
                return [nest(u) for u in o] if isinstance(o, list) else cv(o)
            return ({'k': 'nd', 'shape': list(x.shape), 'data': nest(x.tolist()) if x.dtype.kind not in 'Mm'
                     else [cv(u) for u in x.ravel()]}, {'k': 'nd', 'dtype': str(x.dtype)})
        if isinstance(x, dict):
            items = [(cv(k), canon(v, depth + 1)) for k, v in x.items()]
            return ({'k': 'dict', 'items': [[k, v[0]] for k, v in items]},
                    {'k': 'dict', 'items': [v[1] for k, v in items]})
        if isinstance(x, (list, tuple)):
            items = [canon(v, depth + 1) for v in x]
            return ({'k': 'list', 'items': [v[0] for v in items]}, {'k': 'list', 'type': type(x).__name__,
                                                                     'items': [v[1] for v in items]})
        if isinstance(x, (set, frozenset)):
            items = sorted((canon(v, depth + 1) for v in x), key=lambda p: json.dumps(p[0], default=str))
            return ({'k': 'list', 'items': [v[0] for v in items]}, {'k': 'set', 'items': [v[1] for v in items]})
        if type(x).__module__.startswith('pandas') and not isinstance(x, (pd.Timestamp, pd.Timedelta, pd.Interval,
                                                                           pd.Period)) and x is not pd.NaT and x is not pd.NA:
            return 'OBJ:' + type(x).__name__, {'k': 'obj', 'type': type(x).__module__ + '.' + type(x).__qualname__}
        return cv(x), {'k': 'scalar', 'type': type(x).__module__ + '.' + type(x).__qualname__}

    # ---------------- trace (diagnostics only; format CONVENTIONS section 4.3) ----------------
    trace_events = []
    T_LIMIT = [None]
    trace_state = {'truncated': False}
    # VERIFY fix F3: the trace deadline (TRACE_SECONDS wall from the start of the program) can fall after the CPU limit (ulimit -t counts
    # the imports too), and then the run is killed (cpu_limit) instead of ending with a truncated trace. The tracer therefore also stops
    # 1.5 s of CPU time before the soft CPU limit.
    _cpu_soft = resource.getrlimit(resource.RLIMIT_CPU)[0]
    CPU_GUARD = (_cpu_soft - 1.5) if (_cpu_soft not in (-1, resource.RLIM_INFINITY) and _cpu_soft > 1.5) else float('inf')

    def colhash(s):
        try:
            k = s.dtype.kind
            if k in 'biuf':
                a = s.to_numpy(dtype='float64', na_value=np.nan)
                a = np.where(np.isnan(a), -1.2345e300, np.round(a, 8))
                return hashlib.md5(a.tobytes()).hexdigest()[:10]
            if k == 'M':
                v = s.dt.tz_localize(None) if getattr(s.dt, 'tz', None) is not None else s
                return hashlib.md5(v.to_numpy(dtype='datetime64[ns]').view('i8').tobytes()).hexdigest()[:10]
            if k == 'm':
                return hashlib.md5(s.to_numpy(dtype='timedelta64[ns]').view('i8').tobytes()).hexdigest()[:10]
            vals = [cv(u) for u in s.astype(object).tolist()]
            if vals and all(u is None or (isinstance(u, (int, float)) and not isinstance(u, bool)) for u in vals):
                a = np.array([np.nan if u is None else u for u in vals], dtype='float64')
                a = np.where(np.isnan(a), -1.2345e300, np.round(a, 8))
                return hashlib.md5(a.tobytes()).hexdigest()[:10]
            return hashlib.md5('\x1f'.join(json.dumps(u, default=str) for u in vals).encode()).hexdigest()[:10]
        except Exception as e:
            return 'err:' + type(e).__name__

    def idxhash(ix):
        # VERIFY fix F7: pd.Series(MultiIndex) raises NotImplementedError, so the snapshot of every result with a MultiIndex was the
        # constant 'err:NotImplementedError' in both versions and a divergence there stayed invisible.
        if isinstance(ix, pd.MultiIndex):
            return hashlib.md5('|'.join(colhash(pd.Series(ix.get_level_values(i))) for i in range(ix.nlevels)).encode()).hexdigest()[:10]
        return colhash(pd.Series(ix))

    def vhash(v):
        if isinstance(v, pd.DataFrame):
            parts = [json.dumps([cv(c) for c in v.columns], default=str), idxhash(v.index)]
            parts += [colhash(v.iloc[:, i]) for i in range(v.shape[1])]
            return hashlib.md5('|'.join(parts).encode()).hexdigest()[:10], 'df:' + ','.join(str(t) for t in v.dtypes)
        if isinstance(v, pd.Series):
            return (hashlib.md5((idxhash(v.index) + '|' + colhash(v)).encode()).hexdigest()[:10],
                    's:' + str(v.dtype))
        if isinstance(v, pd.Index):
            return idxhash(v), 'idx:' + str(v.dtype)
        if isinstance(v, np.ndarray):
            if v.size > 100000:
                return 'big', 'nd:' + str(v.dtype)
            return colhash(pd.Series(v.ravel())), 'nd:' + str(v.dtype)
        if isinstance(v, (list, tuple, dict, set)) and len(v) > 5000:
            return 'big', type(v).__name__
        c = canon(v)[0]
        return hashlib.md5(json.dumps(c, default=str).encode()).hexdigest()[:10], type(v).__name__

    # VERIFY fix F7: stdlib datetime / date / Decimal scalars (for example the result of dt.to_pydatetime()[0]) were not snapshotted either
    DATA_T = (pd.DataFrame, pd.Series, pd.Index, np.ndarray, np.generic, int, float, str, bool, list, tuple, dict,
              set, pd.Timestamp, pd.Timedelta, type(None), datetime.datetime, datetime.date, datetime.timedelta, decimal.Decimal)

    def snapshot(frame):
        out = {}
        for name, v in list(frame.f_locals.items()):
            if name.startswith('__') or not isinstance(v, DATA_T):
                continue
            try:
                out[name] = vhash(v)
            except Exception as e:
                out[name] = ('err:' + type(e).__name__, '')
        return out

    def local_tracer(frame, event, arg):
        if event in ('line', 'return'):
            if len(trace_events) >= TRACE_EVENTS or time.time() > T_LIMIT[0] or time.process_time() >= CPU_GUARD:
                trace_state['truncated'] = True
                sys.settrace(None)
                frame.f_trace = None
                return None
            trace_events.append([frame.f_lineno, event, frame.f_code.co_name, snapshot(frame)])
        return local_tracer

    def global_tracer(frame, event, arg):
        if frame.f_code.co_filename == prog:
            return local_tracer
        return None

    # ---------------- stdout/stderr: hash everything, keep the tail ----------------
    class TailBuffer(io.TextIOBase):
        def __init__(self, keep):
            self.keep, self.tail, self.h, self.n = keep, '', hashlib.sha256(), 0

        def writable(self):
            return True

        def write(self, s):
            if not isinstance(s, str):
                raise TypeError('write() argument must be str, not %s' % type(s).__name__)
            self.h.update(s.encode('utf-8', 'replace'))
            self.n += len(s)
            self.tail = (self.tail + s)[-self.keep:]
            return len(s)

        @property
        def encoding(self):
            return 'utf-8'

    # ---------------- run the program ----------------
    with open(prog, 'rb') as _pf:
        src = _pf.read()
    g = {'__name__': '__main__', '__file__': prog, '__builtins__': __builtins__}
    out_buf, err_buf = TailBuffer(20000), TailBuffer(4000)
    sys.argv = [prog]
    phase[0] = 'user'
    t0 = time.time()
    T_LIMIT[0] = t0 + TRACE_SECONDS
    try:
        code = compile(src, prog, 'exec')
        with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
            if mode == 'trace':
                sys.settrace(global_tracer)
            try:
                exec(code, g)
            finally:
                sys.settrace(None)
    except SystemExit as e:
        if e.code not in (None, 0):
            rec.update(status='error', exc_type='SystemExit', exc_msg=str(e.code)[:300])
    except BaseException as e:
        tb = traceback.extract_tb(e.__traceback__)
        ulines = [fr.lineno for fr in tb if fr.filename == prog]
        rec.update(status='error', exc_type=type(e).__name__, exc_msg=str(e)[:500],
                   exc_user_line=ulines[-1] if ulines else None,
                   exc_last_frame=(os.path.basename(tb[-1].filename) + ':' + str(tb[-1].lineno)) if tb else None)
    rec['t_user'] = round(time.time() - t0, 3)
    phase[0] = 'post'
    rec['stdout_sha256'] = out_buf.h.hexdigest()
    rec['stdout_tail'] = out_buf.tail
    rec['stdout_chars'] = out_buf.n
    rec['stderr_tail'] = err_buf.tail
    if rec['status'] == 'ok':
        if 'result' not in g:
            rec['status'] = 'no_result'
        else:
            try:
                val, dt = canon(g['result'])
                rec['result'] = val
                rec['result_dt'] = dt
                tr = type(g['result'])
                rec['result_type'] = tr.__module__ + '.' + tr.__qualname__
            except Exception as e:
                rec.update(status='canon_error', exc_type=type(e).__name__, exc_msg=str(e)[:300])
    if mode == 'trace':
        rec['trace'] = {'events': trace_events, 'truncated': trace_state['truncated'], 'limit_events': TRACE_EVENTS,
                        'limit_seconds': int(TRACE_SECONDS) if TRACE_SECONDS == int(TRACE_SECONDS) else TRACE_SECONDS}
    import csv
    try:
        orig = json.loads(fixhash_json)
    except Exception:
        orig = {}
    files = {}
    for fn in sorted(os.listdir(workdir)):
        p = os.path.join(workdir, fn)
        if fn in ('prog.py', os.path.basename(outjson)) or not os.path.isfile(p):
            continue
        with open(p, 'rb') as _ff:
            h = hashlib.sha256(_ff.read()).hexdigest()
        if orig.get(fn) == h:
            continue                      # untouched fixture
        d = {'sha256': h, 'size': os.path.getsize(p), 'fixture_modified': fn in orig}
        if fn.lower().endswith('.csv') and d['size'] < 5_000_000:
            try:
                with open(p, newline='', encoding='utf-8', errors='replace') as f:
                    d['rows'] = [row for _, row in zip(range(5000), csv.reader(f))]
            except Exception as e:
                d['rows_error'] = type(e).__name__
        files[fn] = d
    rec['files'] = files
    ru = resource.getrusage(resource.RUSAGE_SELF)
    rec['cpu_s'] = round(ru.ru_utime + ru.ru_stime, 3)
    rec['max_rss_bytes'] = int(ru.ru_maxrss)
    with open(outjson, 'w') as f:
        json.dump(rec, f, default=str)
        f.flush()
        os.fsync(f.fileno())
    os._exit(0)             # do not wait for stray non-daemon threads of the program


if __name__ == '__main__':
    main()
