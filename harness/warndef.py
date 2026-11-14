# HRUN: warning definitions (FULL_PREREG section 3, "pandas warning", "warned on 2.3.3"; pilot review m1, m2).
# Written 2026-11-11 by pkg:HRUN. Pure functions on run-record warning dicts (conventions/schema/run_record.schema.json $defs.warning).
# Standard library only. Two definitions: 'prereg' (default, with the NumPy-message exclusion) and 'pilot' (kept as a sensitivity flag).
import os, re

HARNESS = os.path.dirname(os.path.abspath(__file__))
NUMPY_MESSAGES_PATH = os.path.join(HARNESS, 'numpy_messages.txt')
PYTHON_MESSAGES_PATH = os.path.join(HARNESS, 'python_messages.txt')   # REPAIR2 2026-11-11, FULL_PREREG_AMENDMENT_5 (lead decision C4)
FUTURE_DEP = ('builtins.FutureWarning', 'builtins.DeprecationWarning', 'builtins.PendingDeprecationWarning')
DEFINITIONS = ('prereg', 'pilot')
_cache = {}


def load_numpy_messages(path=NUMPY_MESSAGES_PATH):
    """Message prefixes of the frozen NumPy-message list (blank lines and lines starting with '#' are skipped)."""
    path = os.path.abspath(path)
    key = (path, os.path.getmtime(path))
    if key not in _cache:
        with open(path, encoding='utf-8') as f:
            _cache[key] = [ln.rstrip('\n').strip() for ln in f if ln.strip() and not ln.lstrip().startswith('#')]
    return _cache[key]


def load_python_messages(path=PYTHON_MESSAGES_PATH):
    """Message prefixes of the frozen CPython-message list (FULL_PREREG_AMENDMENT_5); same file format as numpy_messages.txt."""
    return load_numpy_messages(path)


def _module(rec):
    return str(rec.get('category_module') or '')


def is_numpy_originated(rec, messages=None):
    """Category class defined in numpy, or message on the frozen NumPy-message list (starts with an entry)."""
    mod = _module(rec)
    if mod == 'numpy' or mod.startswith('numpy.'):
        return True
    msg = str(rec.get('message') or '').strip()
    return any(msg.startswith(m) for m in (messages if messages is not None else load_numpy_messages()))


def is_python_originated(rec, python_messages=None):
    """FULL_PREREG_AMENDMENT_5 (lead decision C4): category class defined in builtins and message on the frozen CPython-message list
    (warnings that the interpreter itself raises, e.g. '~' on a bool, even when a pandas frame is on the stack)."""
    if _module(rec) != 'builtins':
        return False
    msg = str(rec.get('message') or '').strip()
    return any(msg.startswith(m) for m in (python_messages if python_messages is not None else load_python_messages()))


def is_pandas_warning(rec, definition='prereg', messages=None):
    """rec = one run-record warning. Only warnings of phase 'user' (the program's own run) count.
    'prereg' (section 3): category class defined in a pandas module, or a Future/Deprecation/PendingDeprecation warning (any subclass,
        by MRO) emitted with a pandas frame on the stack, in both cases unless the message is NumPy-originated or (Amendment 5)
        Python-originated (builtins category, message on harness/python_messages.txt).
    'pilot' (analyze.py is_pd_warning): category module starts with 'pandas', or a pandas frame on the stack and category name
        != 'RuntimeWarning' (no NumPy exclusion)."""
    if definition not in DEFINITIONS:
        raise ValueError('definition must be one of %s' % (DEFINITIONS,))
    if rec.get('phase') != 'user':
        return False
    if definition == 'pilot':
        if _module(rec).startswith('pandas'):
            return True
        return bool(rec.get('pandas_on_stack')) and rec.get('category_qualname') != 'RuntimeWarning'
    if is_numpy_originated(rec, messages):
        return False
    if is_python_originated(rec):                       # REPAIR2 2026-11-11, FULL_PREREG_AMENDMENT_5
        return False
    mod = _module(rec)
    if mod == 'pandas' or mod.startswith('pandas.'):
        return True
    return bool(rec.get('pandas_on_stack')) and any(m in FUTURE_DEP for m in rec.get('mro', []))


def is_future_dep(rec, definition='prereg', messages=None):
    """A pandas warning (by `definition`) that is a FutureWarning, DeprecationWarning or PendingDeprecationWarning (subclasses included)."""
    return is_pandas_warning(rec, definition, messages) and any(m in FUTURE_DEP for m in rec.get('mro', []))


def pandas_warnings(run_record, definition='prereg', messages=None):
    return [w for w in ((run_record or {}).get('warnings') or []) if is_pandas_warning(w, definition, messages)]


def warned_233(run_record_E0a, definition='prereg', messages=None):
    """'Warned on 2.3.3' (section 3, also used in H4): E0a emitted at least one pandas Future/Deprecation/PendingDeprecation warning."""
    return any(is_future_dep(w, definition, messages) for w in ((run_record_E0a or {}).get('warnings') or []))


def warning_lines(run_record, definition='prereg', messages=None):
    """Data for the locally-silent outcome: the program lines (innermost prog.py frame; None if not attributable) of every pandas warning."""
    return sorted((w.get('user_line') for w in pandas_warnings(run_record, definition, messages)),
                  key=lambda x: (x is None, x if x is not None else 0))


def warning_signature(w):
    """Category plus message template (digits and addresses masked), as the pilot's wsig; used for 'warning only'."""
    m = re.sub(r'0x[0-9a-fA-F]+', '0x', w.get('message', ''))
    m = re.sub(r'\d+', '#', m)
    return str(w.get('category_qualname', '')) + ':' + m[:120]


def locally_silent(run_record, first_divergent_line, definition='prereg', messages=None):
    """True when no pandas warning was emitted at or before the first divergent line (review m2).
    A pandas warning whose program line is unknown (None) is counted as 'at or before' (conservative: it can only lower the count).
    Returns None when the first divergent line is unknown."""
    if first_divergent_line is None:
        return None
    for w in pandas_warnings(run_record, definition, messages):
        ul = w.get('user_line')
        if ul is None or ul <= first_divergent_line:
            return False
    return True
