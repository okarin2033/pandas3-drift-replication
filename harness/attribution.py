# ATTRIB_HARM: mechanism attribution (FULL_PREREG section 11; STAGE2 T5.1 fix 2, T5.4; pilot REVIEW m8, CHANGES 23:50).
# Written 2026-11-11 by pkg:ATTRIB_HARM (drafted_by: pkg:ATTRIB_HARM; status: prepared).
# Standard library only (host side). Rules and the frozen priority order live in harness/attribution_rules.tsv (row order = priority).
#
# attribute(program, records, traces, card, target) labels ONE drift (or LOUD) program on ONE target (E1 or E2; E3/E4 accepted):
#   Step 1 'flags'     option flags: A2 (2.3.3 + future.infer_string) or A4 (3.1.x with the string dtype off, E1/E3 only) reproduce the
#                      target behaviour -> string-dtype rows S01-S04; A1 (2.3.3 + copy_on_write) -> CoW rows C01, C02, C03, C05; A3 (both)
#                      only -> both sets. The family is then refined to catalogue ids by the divergent line (any rule of those rows incl.
#                      'refine' rules), else by the static program text, else the family code (QF1 / QF3) is the label.
#   Step 2 'line'      the first divergent line of the T0 and T1 (E1) or T2 (E2) traces; for a LOUD target the line that raised
#                      (exc_user_line) and the exception message. ALL matching rules are recorded (multi-label); the primary label is the
#                      first match in the frozen order. The datetime-unit trace signal ([ns] on 2.3.3, [us|ms|s] on the target at the
#                      divergence event) is used ONLY after the line's own rule matches (pilot fix 2): its labels are appended after the
#                      line labels and become primary only when no line rule matched.
#   Step 3 'warn_line' 2.3.3 (E0a) pandas warnings emitted at the divergent line, matched by warn_regex; then 'warn_any': anywhere.
#   Step 4 'static'    rules (use = all) on the comment-stripped program text.
#   Otherwise          'UNATTRIBUTED' (step 'none').
# 'truncated' = either trace was truncated (a length difference at a truncated end is not taken as a divergence).
import io, json, os, re, sys, tokenize

HARNESS = os.path.dirname(os.path.abspath(__file__))
if HARNESS not in sys.path:
    sys.path.insert(0, HARNESS)

RULES_PATH = os.path.join(HARNESS, 'attribution_rules.tsv')
LOUD_STATUSES = ('error', 'timeout', 'cpu_limit', 'memory_limit', 'crash')
FAMILY_CODES = ['QF%d' % i for i in range(1, 9)]
STR_IDS = ('S01', 'S02', 'S03', 'S04')          # emulated by future.infer_string on 2.3.3 (A2) and undone by A4
COW_IDS = ('C01', 'C02', 'C03', 'C05')          # emulated by mode.copy_on_write on 2.3.3 (A1)
UNIT_IDS = ('D01', 'D02', 'D04')                # sources of a datetime64 unit change
UNIT_BASE_RE = re.compile(r'datetime64\[ns')
UNIT_TGT_RE = re.compile(r'datetime64\[(us|ms|s)\b')
STEPS = ('flags', 'line', 'warn_line', 'warn_any', 'static', 'none')


# ------------------------------------------------------------------------------------------------ rules
class Rule:
    __slots__ = ('rule', 'label', 'family', 'tier', 'use', 'line', 'ctx', 'neg', 'warn', 'exc', 'order')

    def __init__(self, row, order):
        self.rule, self.label, self.family, self.tier, self.use = row['rule'], row['label'], row['family'], row['tier'], row['use']
        self.order = order
        self.line = re.compile(row['line_regex']) if row['line_regex'] else None
        self.ctx = re.compile(row['context_regex'], re.MULTILINE) if row['context_regex'] else None
        self.neg = re.compile(row['neg_regex']) if row['neg_regex'] else None
        self.warn = re.compile(row['warn_regex']) if row['warn_regex'] else None
        self.exc = re.compile(row['exc_regex']) if row['exc_regex'] else None

    def context_ok(self, program_text):
        return self.ctx is None or bool(self.ctx.search(program_text))

    def line_match(self, line_text, program_text):
        if self.line is None or not line_text:
            return False
        if not self.line.search(line_text):
            return False
        if self.neg is not None and self.neg.search(line_text):
            return False
        return self.context_ok(program_text)


def load_rules(path=RULES_PATH):
    with open(path, encoding='utf-8') as f:
        lines = [ln.rstrip('\n') for ln in f if ln.strip() and not ln.startswith('#')]
    hdr = lines[0].split('\t')
    rules = []
    for i, ln in enumerate(lines[1:]):
        parts = ln.split('\t')
        parts += [''] * (len(hdr) - len(parts))
        rules.append(Rule(dict(zip(hdr, parts)), i))
    return rules


RULES = load_rules()


def _priority(rules, loud=False):
    seq = [r for r in rules if r.tier != 'L'] + [r for r in rules if r.tier == 'L']
    if loud:
        seq = [r for r in rules if r.tier == 'L'] + [r for r in rules if r.tier != 'L']
    out = []
    for r in seq:
        if r.label not in out:
            out.append(r.label)
    return out + FAMILY_CODES + ['UNATTRIBUTED']


PRIORITY = _priority(RULES)                      # frozen order for drift targets (also the order of attribution_rules.tsv)
PRIORITY_LOUD = _priority(RULES, loud=True)      # LOUD targets: LOUD_CONTEXT rows first
FAMILY_OF = {r.label: r.family for r in RULES}


def _rank(label, loud=False):
    order = PRIORITY_LOUD if loud else PRIORITY
    return order.index(label) if label in order else len(order)


def sort_labels(labels, loud=False):
    seen = []
    for lab in labels:
        if lab not in seen:
            seen.append(lab)
    return sorted(seen, key=lambda x: _rank(x, loud))


# ------------------------------------------------------------------------------------------------ source text
def strip_comments(src):
    """Program text with comments blanked (strings kept); falls back to a naive '#' cut per line if tokenizing fails."""
    src = src or ''
    try:
        lines = src.splitlines(True)
        toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
        out = [list(ln) for ln in lines]
        for t in toks:
            if t.type == tokenize.COMMENT:
                (r, c), (_, c2) = t.start, t.end
                if 0 < r <= len(out):
                    for k in range(c, min(c2, len(out[r - 1]))):
                        if out[r - 1][k] != '\n':
                            out[r - 1][k] = ' '
        return ''.join(''.join(x) for x in out)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return '\n'.join(re.sub(r'#.*$', '', ln) for ln in src.splitlines())


def source_line(src_clean, lineno):
    lines = src_clean.splitlines()
    if lineno is None or not (0 < lineno <= len(lines)):
        return ''
    return lines[lineno - 1]


# ------------------------------------------------------------------------------------------------ traces
def _events(trace):
    """Accepts the CONVENTIONS section 4.3 object {'events': [...], 'truncated': ...}, a pilot record with 'trace', or a bare list."""
    if trace is None:
        return None, False
    if isinstance(trace, list):
        return trace, False
    if 'events' in trace:
        return trace.get('events') or [], bool(trace.get('truncated'))
    if 'trace' in trace:
        t = trace['trace']
        if isinstance(t, dict):
            return t.get('events') or [], bool(t.get('truncated'))
        return t or [], bool(trace.get('trace_truncated') or trace.get('truncated'))
    return None, False


def divergence(trace_base, trace_target):
    """First divergence of two line traces (pilot analyze.first_divergence, extended with truncation):
    {'kind': 'control'|'value'|'length', 'line', 'event', 'vars', 'unit_vars', 'truncated'} or None (also None if a trace is missing).
    'line' is the program line whose execution produced the difference (the line event before the first differing snapshot).
    A length difference is not a divergence when the shorter trace was truncated (the comparison simply ran out)."""
    a, ta = _events(trace_base)
    b, tb = _events(trace_target)
    if a is None or b is None:
        return None
    trunc = ta or tb
    for i in range(min(len(a), len(b))):
        la, ea, fa, sa = a[i][:4]
        lb, eb, fb, sb = b[i][:4]
        prev = a[i - 1][0] if i > 0 else la
        if (la, ea, fa) != (lb, eb, fb):
            return {'kind': 'control', 'line': prev, 'event': i, 'vars': [], 'unit_vars': [], 'truncated': trunc}
        sa, sb = sa or {}, sb or {}
        diff = sorted(k for k in set(sa) | set(sb) if (sa.get(k) or [None])[0] != (sb.get(k) or [None])[0])
        if diff:
            units = sorted(k for k in set(sa) & set(sb)
                           if UNIT_BASE_RE.search(str((sa[k] or [None, ''])[1])) and UNIT_TGT_RE.search(str((sb[k] or [None, ''])[1])))
            return {'kind': 'value', 'line': prev, 'event': i, 'vars': diff[:8], 'unit_vars': units[:8], 'truncated': trunc}
    if len(a) != len(b):
        i = min(len(a), len(b))
        shorter_truncated = (ta if len(a) < len(b) else tb)
        if shorter_truncated:
            return None
        return {'kind': 'length', 'line': a[i - 1][0] if i > 0 else None, 'event': i, 'vars': [], 'unit_vars': [], 'truncated': trunc}
    return None


def first_divergent_line(trace_base, trace_target):
    d = divergence(trace_base, trace_target)
    return d.get('line') if d else None


def traces_truncated(traces):
    return any(_events(t)[1] for t in (traces or {}).values() if t is not None)


# ------------------------------------------------------------------------------------------------ rule matching
def line_labels(line_text, program_clean, rules=None, uses=('all', 'line'), labels=None):
    rules = RULES if rules is None else rules
    out = []
    for r in rules:
        if r.use not in uses or (labels is not None and r.label not in labels):
            continue
        if r.line_match(line_text, program_clean):
            out.append(r.label)
    return out


def exc_labels(exc_text, program_clean, rules=None):
    rules = RULES if rules is None else rules
    return [r.label for r in rules if r.exc is not None and exc_text and r.exc.search(exc_text) and r.context_ok(program_clean)]


def static_labels(program_clean, rules=None, uses=('all',), labels=None):
    out = []
    for ln in program_clean.splitlines():
        if ln.strip():
            out.extend(line_labels(ln, program_clean, rules, uses, labels))
    return out


def warn_labels(warnings, program_clean, line=None, rules=None):
    """Labels whose warn_regex matches a 2.3.3 pandas warning (prereg definition), optionally only warnings emitted at `line`."""
    rules = RULES if rules is None else rules
    out = []
    for w in warnings:
        if line is not None and w.get('user_line') != line:
            continue
        msg = str(w.get('message') or w.get('msg') or '')
        for r in rules:
            if r.warn is not None and r.warn.search(msg) and r.context_ok(program_clean):
                out.append(r.label)
    return out


def unit_labels(program_clean):
    """Datetime-unit trace signal -> catalogue rows: D02 / D04 when the program converts numbers or builds ranges, else D01."""
    hits = [lab for lab in static_labels(program_clean, uses=('all',), labels=('D02', 'D04'))]
    hits = sort_labels(hits)
    return hits or ['D01']


# ------------------------------------------------------------------------------------------------ dtype-propagation signal (ON: Amendment 4)
# REPAIR 2026-11-11 (STAGE2_BUILD_REVIEW MF6, STAGE2_BUILD_CHECK F4; HARNESS_FIXES finding 1, VERIFY V10). Added to the section 11
# procedure by FULL_PREREG_AMENDMENT_4 (2026-11-11, REPAIR2): attribute() uses it unless called with dtype_signal=False
# (module switch DTYPE_SIGNAL_DEFAULT below; analyze_full.py --dtype-signal off reproduces the procedure without it).
# The signal: the earliest trace event, at or before the first divergent event, at which some variable's dtype string differs between the
# two traces after the string-dtype change (object -> str/string) and the datetime-unit change (own signal) are normalised away. Rules
# (use all/line) that match THAT line are appended after the divergent line's own labels, like the datetime-unit signal (pilot fix 2).
_DT_NORM = [(re.compile(r'\bstr(ing)?(\[[a-z_]+\])?(?!\w)'), 'object'), (re.compile(r'datetime64\[(ns|us|ms|s)'), 'datetime64[*')]


def _norm_typestr(t):
    t = str(t or '')
    for rx, rep in _DT_NORM:
        t = rx.sub(rep, t)
    return t


def dtype_propagation_line(trace_base, trace_target, upto_event=None):
    """Program line of the earliest event (<= upto_event) where a variable's normalised dtype string differs, or None."""
    a, _ = _events(trace_base)
    b, _ = _events(trace_target)
    if a is None or b is None:
        return None
    n = min(len(a), len(b)) if upto_event is None else min(len(a), len(b), upto_event + 1)
    for i in range(n):
        sa, sb = (a[i][3] if len(a[i]) > 3 else None) or {}, (b[i][3] if len(b[i]) > 3 else None) or {}
        for k in set(sa) & set(sb):
            ta, tb = (sa[k] or [None, ''])[1], (sb[k] or [None, ''])[1]
            if _norm_typestr(ta) != _norm_typestr(tb):
                return a[i - 1][0] if i > 0 else a[i][0]
    return None


# ------------------------------------------------------------------------------------------------ option flags (step 1)
def _status(rec):
    return (rec or {}).get('status')


def reproduces(a_rec, tgt_rec, card=None):
    """True when the attribution run gives the target's behaviour: both complete with results that agree up to dtype/order
    (oracle.compare under the program's card), or both complete without `result`. With a flagged card the flagged order / dtype
    change counts as a difference (VERIFY fix F4: an order-significant program whose A-runs keep the 2.3.3 order must not be
    'reproduced' by every flag run just because the rows are the same multiset)."""
    if a_rec is None or tgt_rec is None:
        return False
    if _status(a_rec) == 'no_result' and _status(tgt_rec) == 'no_result':
        return True
    if _status(a_rec) != 'ok' or _status(tgt_rec) != 'ok':
        return False
    import oracle
    c = oracle.compare(a_rec, tgt_rec, card)
    return c.get('class') in ('IDENTICAL', 'DTYPE_ONLY', 'ORDER_ONLY')


def flag_families(records, target, card=None):
    """-> (set of row tuples to refine within, evidence dict)."""
    tgt, e0 = records.get(target), records.get('E0a')
    ev = {'flag_cow': reproduces(records.get('A1'), tgt, card), 'flag_str': reproduces(records.get('A2'), tgt, card),
          'flag_both': reproduces(records.get('A3'), tgt, card),
          'optout_restores': reproduces(records.get('A4'), e0, card) if target in ('E1', 'E3') else False}
    fams = []
    if ev['flag_str'] or ev['optout_restores']:
        fams.append(('QF1', STR_IDS))
    if ev['flag_cow']:
        fams.append(('QF3', COW_IDS))
    if not fams and ev['flag_both']:
        fams = [('QF1', STR_IDS), ('QF3', COW_IDS)]
    return fams, ev


# ------------------------------------------------------------------------------------------------ main entry
# REPAIR2 2026-11-11 (review MF6, lead decision C3): module switch for the dtype-propagation signal. attribute(..., dtype_signal=None)
# uses this value; analyze_full.py --dtype-signal on|off sets it for one analysis. Its value is decided by FULL_PREREG_AMENDMENT_4.
DTYPE_SIGNAL_DEFAULT = True    # switched on by FULL_PREREG_AMENDMENT_4 (2026-11-11; P+ 88/88, P- 46/46 with it on)


def attribute(program, records, traces, card=None, target='E1', dtype_signal=None):
    """program = {'program_id', 'source'}; records keyed by run config (E0a, the target, A1-A4 when run);
    traces = {'T0': ..., 'T1': ... | 'T2': ...} or None. Returns {'labels', 'primary', 'step', 'truncated', 'first_divergent_line',
    'evidence'} (INTERFACES.md section 4). `card` is accepted for the interface; attribution does not use it."""
    if dtype_signal is None:                       # REPAIR2 2026-11-11: module default (FULL_PREREG_AMENDMENT_4)
        dtype_signal = DTYPE_SIGNAL_DEFAULT
    src = (program or {}).get('source') or ''
    clean = strip_comments(src)
    tgt = records.get(target) or {}
    loud = _status(tgt) in LOUD_STATUSES
    traces = traces or {}
    tname = {'E1': 'T1', 'E2': 'T2', 'E3': 'T1', 'E4': 'T2'}.get(target, 'T1')
    truncated = traces_truncated({k: traces.get(k) for k in ('T0', tname)})
    div = divergence(traces.get('T0'), traces.get(tname)) if traces.get('T0') is not None and traces.get(tname) is not None else None
    line = div.get('line') if div else None
    exc_text = ''
    if loud:
        exc_text = '%s: %s' % (tgt.get('exc_type') or '', tgt.get('exc_msg') or '')
        if tgt.get('exc_user_line'):
            line = tgt.get('exc_user_line')
    line_text = source_line(clean, line)
    ev = {'divergence': div, 'line_text': line_text.strip()[:200], 'exc': exc_text[:200] if loud else None}

    def result(labels, step, extra=()):
        labs = sort_labels(labels, loud) + [x for x in extra if x not in labels]
        prim = labs[0] if labs else 'UNATTRIBUTED'
        return {'labels': labs or ['UNATTRIBUTED'], 'primary': prim, 'step': step, 'truncated': bool(truncated),
                'first_divergent_line': line, 'evidence': ev}

    # step 1: option flags (string dtype / copy-on-write)
    fams, fev = flag_families(records, target, card)
    ev['flags'] = fev
    if fams and not loud:
        refined, extra = [], []
        for fam, ids in fams:
            line_got = line_labels(line_text, clean, uses=('all', 'line', 'refine'), labels=ids)
            text_got = static_labels(clean, uses=('all', 'line', 'refine'), labels=ids)
            if line_got:
                # VERIFY fix F6: the divergent line is where the effect shows (for copy=False it is the later write, which matches the
                # broad write rule); the rows of the flagged family that the program text names are added AFTER the line labels, so
                # the primary label still comes from the line (as for the datetime-unit signal, pilot fix 2).
                refined.extend(sort_labels(line_got))
                extra.extend(x for x in sort_labels(text_got) if x not in line_got)
            else:
                refined.extend(sort_labels(text_got) if text_got else [fam])
        return result(refined, 'flags', extra=extra)

    # LOUD_CONTEXT rows describe breaks, so they are matched only for LOUD targets
    active = RULES if loud else [r for r in RULES if r.tier != 'L']

    # step 2: the first divergent line (all matching rules; unit signal only after line evidence)
    if line is not None:
        labs = line_labels(line_text, clean, rules=active)
        if loud:
            labs += exc_labels(exc_text, clean)
        unit = unit_labels(clean) if (div and div.get('unit_vars')) else []
        ev['unit_signal'] = unit
        dprop = []
        if dtype_signal and div and div.get('kind') == 'value':      # REPAIR MF6; on by default since FULL_PREREG_AMENDMENT_4
            dline = dtype_propagation_line(traces.get('T0'), traces.get(tname), div.get('event'))
            if dline is not None and dline != line:
                dprop = sort_labels(line_labels(source_line(clean, dline), clean, rules=active))
                ev['dtype_propagation'] = {'line': dline, 'labels': dprop}
        if labs:
            more = [u for u in unit if u not in labs]
            return result(labs, 'line', extra=sort_labels(more) + [d for d in dprop if d not in labs and d not in more])
        if unit:
            return result(unit, 'line', extra=[d for d in dprop if d not in unit])
    elif loud and exc_text.strip(': '):
        labs = exc_labels(exc_text, clean)
        if labs:
            return result(labs, 'line')

    # step 3: 2.3.3 warnings at that line, then anywhere
    import warndef
    ws = warndef.pandas_warnings(records.get('E0a'), 'prereg')
    if line is not None:
        labs = warn_labels(ws, clean, line=line, rules=active)
        if labs:
            return result(labs, 'warn_line')
    labs = warn_labels(ws, clean, rules=active)
    if labs:
        return result(labs, 'warn_any')

    # step 4: static program text
    labs = static_labels(clean, rules=active)
    if labs:
        return result(labs, 'static')
    return result([], 'none')


def components(labels):
    """Component labels for 'component-label shares' (section 11): every label except UNATTRIBUTED."""
    return [x for x in labels or [] if x != 'UNATTRIBUTED']


def family_of(label):
    """QF code of a catalogue id or family code ('-' for LOUD rows, None for UNATTRIBUTED)."""
    if label in FAMILY_CODES:
        return label
    return FAMILY_OF.get(label)


if __name__ == '__main__':
    # quick listing of the frozen order: python3 -I harness/attribution.py
    print('drift order:', ' '.join(PRIORITY))
    print('LOUD order :', ' '.join(PRIORITY_LOUD))
