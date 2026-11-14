# Task validator for the full study (FULL_PREREG sections 3, 4.3, 4.4, 4.5, 5, 10.1). Standard library only.
# Written 2026-11-11 by pkg:SHARED. Rules: conventions/CONVENTIONS.md section 5.
#
# usage:
#   python3 -I harness/validate_tasks.py --pkg M1                 # one package folder (quota check for its families)
#   python3 -I harness/validate_tasks.py --pkg M1 --pkg M2 --pkg R --pkg A --full    # whole set (INTEGRATE)
#   python3 -I harness/validate_tasks.py --tasks-json tasks/tasks.json --full [--require-blind]
#   python3 -I harness/validate_tasks.py --example conventions/example/tasks/EX \
#           --fixtures conventions/example/fixtures                                    # fictitious example only
# options: --option-names PATH (lint; default envs/pandas_option_names.txt; fails loudly if missing)
#          --order-phrases PATH (LR2 closed phrase list; default tools/order_flag_phrases.txt; checked against Amendment 10)
#          --lr2-decisions PATH (lead's per-card LR2.3 decisions; default tasks/LR2_LEAD_DECISIONS.tsv; REPAIR5 fixes MF2)
#          --ruled-fidelity-fails PATH (lead ruling LR43; default tasks/RULED_FIDELITY_FAILS.tsv, pinned in MANIFEST.sha256)
#          --ruled-generic-exemptions PATH (lead ruling LR57; default tasks/RULED_GENERIC_CHECK_EXEMPTIONS.tsv, pinned in MANIFEST.sha256)
#          --pilot DIR (default research/pilots/r3), --catalogue, --quota, --fixtures, --allow-incomplete,
#          --report FILE (JSON report)
# Exit code 0 = valid, 1 = errors, 2 = setup error.
#
# Library use (other packages): schema_errors(instance, schema), tsv_errors(path, tsv_schema),
# check_property_args(check), load_schema(name), validate(tasks_with_dirs, ctx) -> report.
import argparse, csv, glob, json, os, re, sys


def _slurp(path, encoding='utf-8'):
    with open(path, encoding=encoding) as f:
        return f.read()


def _jload(path, encoding='utf-8'):
    with open(path, encoding=encoding) as f:
        return json.load(f)

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from render_prompts import render, RenderError  # noqa: E402
import lint_prompts  # noqa: E402

SCHEMA_DIR = os.path.join(STUDY, 'conventions', 'schema')
FAMILIES = ['QF1_STRING', 'QF2_DATETIME', 'QF3_COW', 'QF4_GROUPBY', 'QF5_ORDER', 'QF6_NA_DTYPE', 'QF7_INDEX_REDUCE',
            'QF8_NUMERIC']
FAM_BY_CODE = {f.split('_', 1)[0]: f for f in FAMILIES}
GENERIC = ['TXT', 'IMP', 'CONV', 'BIN', 'DATE', 'TS', 'TOP', 'MRG', 'PIV', 'ENC', 'UPD', 'RPT']
PKG_FAMILIES = {'M1': FAMILIES[:4], 'M2': FAMILIES[4:]}
DRAFT_STATUS = 'prepared'
R_MIN_DATE = '2026-01-21'
R_MAX = 40
RA_TOTAL = 72          # 200 - 128 (section 4.3); stays 72 if a family is dropped (its quota is not moved)
NGRAM = 8

RE_M = re.compile(r'^M_(QF[1-8])_(0[1-9]|1[0-6])$')
RE_R = re.compile(r'^R_(0[1-9]|[1-3][0-9]|40)$')
RE_A = re.compile(r'^A_(%s)_([0-9]{2})$' % '|'.join(GENERIC))
RE_EX = re.compile(r'^EX_[A-Z0-9]+_[0-9]{2}$')


def pkg_of(task_id):
    """Package folder that owns a task id (conventions section 3.2)."""
    m = RE_M.match(task_id)
    if m:
        return 'M1' if int(m.group(1)[2]) <= 4 else 'M2'
    if RE_R.match(task_id):
        return 'R'
    if RE_A.match(task_id):
        return 'A'
    return None


# ------------------------------------------------------------------ minimal JSON Schema (subset) validator
_TYPES = {'object': dict, 'array': list, 'string': str, 'boolean': bool, 'null': type(None)}


def _is_type(v, t):
    if t == 'integer':
        return isinstance(v, int) and not isinstance(v, bool)
    if t == 'number':
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    return isinstance(v, _TYPES[t])


def _resolve(ref, root):
    if not ref.startswith('#/'):
        raise ValueError('only local $ref supported: ' + ref)
    node = root
    for part in ref[2:].split('/'):
        node = node[part]
    return node


def schema_errors(inst, schema, root=None, path='$'):
    """Validate inst against the JSON-Schema subset used in conventions/schema/. Returns a list of messages."""
    root = schema if root is None else root
    errs = []
    if '$ref' in schema:
        return schema_errors(inst, _resolve(schema['$ref'], root), root, path)
    if 'anyOf' in schema:
        if not any(not schema_errors(inst, s, root, path) for s in schema['anyOf']):
            sub = [e for s in schema['anyOf'] for e in schema_errors(inst, s, root, path)]
            errs.append('%s: matches none of anyOf (%s)' % (path, '; '.join(sub[:3])))
        return errs
    if 'type' in schema:
        ts = schema['type'] if isinstance(schema['type'], list) else [schema['type']]
        if not any(_is_type(inst, t) for t in ts):
            return ['%s: expected %s, got %s' % (path, '|'.join(ts), type(inst).__name__)]
    if 'const' in schema and inst != schema['const']:
        errs.append('%s: must equal %r' % (path, schema['const']))
    if 'enum' in schema and inst not in schema['enum']:
        errs.append('%s: %r not in %r' % (path, inst, schema['enum']))
    if isinstance(inst, str):
        if 'minLength' in schema and len(inst) < schema['minLength']:
            errs.append('%s: shorter than %d' % (path, schema['minLength']))
        if 'pattern' in schema and not re.search(schema['pattern'], inst):
            errs.append('%s: %r does not match %s' % (path, inst, schema['pattern']))
    if _is_type(inst, 'number'):
        if 'minimum' in schema and inst < schema['minimum']:
            errs.append('%s: below %r' % (path, schema['minimum']))
        if 'maximum' in schema and inst > schema['maximum']:
            errs.append('%s: above %r' % (path, schema['maximum']))
    if isinstance(inst, list):
        if 'minItems' in schema and len(inst) < schema['minItems']:
            errs.append('%s: fewer than %d items' % (path, schema['minItems']))
        if 'maxItems' in schema and len(inst) > schema['maxItems']:
            errs.append('%s: more than %d items' % (path, schema['maxItems']))
        if 'items' in schema:
            for i, v in enumerate(inst):
                errs += schema_errors(v, schema['items'], root, '%s[%d]' % (path, i))
    if isinstance(inst, dict):
        for k in schema.get('required', []):
            if k not in inst:
                errs.append('%s: missing required field %r' % (path, k))
        props = schema.get('properties', {})
        for k, v in inst.items():
            if k in props:
                errs += schema_errors(v, props[k], root, path + '.' + k)
            else:
                ap = schema.get('additionalProperties', True)
                if ap is False:
                    errs.append('%s: unexpected field %r' % (path, k))
                elif isinstance(ap, dict):
                    errs += schema_errors(v, ap, root, path + '.' + k)
    return errs


def load_schema(name, schema_dir=SCHEMA_DIR):
    with open(os.path.join(schema_dir, name), encoding='utf-8') as f:
        return json.load(f)


def tsv_errors(path, tsv_schema):
    """Validate a TSV file against a conventions/schema/*.tsv.schema.json description."""
    errs = []
    cols = [c['name'] for c in tsv_schema['columns']]
    with open(path, encoding='utf-8', newline='') as f:
        rows = list(csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE))
    if not rows:
        return ['%s: empty file' % path]
    if rows[0] != cols:
        return ['%s: header %r != %r' % (path, rows[0], cols)]
    for n, r in enumerate(rows[1:], 2):
        if len(r) != len(cols):
            errs.append('%s:%d: %d fields, expected %d' % (path, n, len(r), len(cols)))
            continue
        for c, v in zip(tsv_schema['columns'], r):
            if not re.search(c['pattern'], v):
                errs.append('%s:%d: %s=%r does not match %s' % (path, n, c['name'], v, c['pattern']))
    return errs


def read_tsv(path):
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE))


# ------------------------------------------------------------------ property-check vocabulary
# arg spec: name -> (type, required). 'cols' = list of target names; a target is a column label, '__index__'
# (index labels) or '__values__' (Series values / scalar). Semantics: conventions/CONVENTIONS.md section 5.4.
PROPERTY_CHECKS = {
    'no_null_text': {},
    'no_all_missing_column': {},
    'date_year_in_range': {'columns': ('cols', True), 'min_year': ('int', True), 'max_year': ('int', True)},
    'counts_sum_to_rows': {'column': ('str', True), 'expected': ('int', True)},
    'rate_in_unit_interval': {'columns': ('cols', True)},
    'n_groups_equals': {'n': ('int', True)},
    'no_nulls': {'columns': ('cols', True)},
    'numeric_in_range': {'columns': ('cols', True), 'min': ('num_or_null', True), 'max': ('num_or_null', True)},
    'values_in_set': {'column': ('str', True), 'values': ('list', True)},
    'columns_present': {'columns': ('cols', True)},
    'result_kind': {'kind': ('kind', True)},
    'sorted_by': {'keys': ('cols', True), 'ascending': ('bools', True)},
}
GENERIC_CHECKS = ('no_null_text', 'no_all_missing_column')
RESULT_KINDS = ('dataframe', 'series', 'scalar', 'index', 'other')


def check_property_args(pc):
    errs = []
    name = pc.get('check')
    spec = PROPERTY_CHECKS.get(name)
    if spec is None:
        return ['unknown property check %r' % name]
    args = pc.get('args')
    if not isinstance(args, dict):
        return ['%s: args must be an object' % name]
    for k in args:
        if k not in spec:
            errs.append('%s: unknown argument %r' % (name, k))
    for k, (t, req) in spec.items():
        if k not in args:
            if req:
                errs.append('%s: missing argument %r' % (name, k))
            continue
        v = args[k]
        ok = {
            'cols': isinstance(v, list) and all(isinstance(x, str) and x for x in v),
            'int': isinstance(v, int) and not isinstance(v, bool),
            'str': isinstance(v, str) and bool(v),
            'num_or_null': v is None or (isinstance(v, (int, float)) and not isinstance(v, bool)),
            'list': isinstance(v, list) and len(v) > 0,
            'kind': v in RESULT_KINDS,
            'bools': isinstance(v, list) and all(isinstance(x, bool) for x in v),
        }[t]
        if not ok:
            errs.append('%s: bad argument %s=%r (%s)' % (name, k, v, t))
    if name == 'date_year_in_range' and not errs and args['min_year'] > args['max_year']:
        errs.append('date_year_in_range: min_year > max_year')
    if name == 'sorted_by' and not errs and len(args['keys']) != len(args['ascending']):
        errs.append('sorted_by: keys and ascending differ in length')
    if name in ('rate_in_unit_interval', 'date_year_in_range', 'columns_present', 'sorted_by') and not errs:
        key = 'keys' if name == 'sorted_by' else 'columns'
        if not args[key]:
            errs.append('%s: %s must not be empty' % (name, key))
    return errs


# ------------------------------------------------------------------ context
class Context:
    def __init__(self, study=STUDY, fixtures=None, catalogue=None, quota=None, pilot=None, option_names=None,
                 example=False, lint=True, order_phrases=None, lr2_decisions=None, ruled_fidelity_fails=None,
                 ruled_generic_exemptions=None):
        self.study = study
        self.fixtures = fixtures if fixtures is not None else os.path.join(study, 'fixtures')
        self.catalogue_path = catalogue if catalogue is not None else os.path.join(study, 'mechanisms', 'catalogue.tsv')
        self.quota_path = quota if quota is not None else os.path.join(study, 'mechanisms', 'confirm',
                                                                       'quota_allocation.tsv')
        self.pilot = pilot if pilot is not None else os.path.normpath(os.path.join(study, '..', '..', 'pilots', 'r3'))
        self.example = example
        self.schema = load_schema('task.schema.json')
        self.catalogue = None
        if self.catalogue_path and os.path.exists(self.catalogue_path):
            self.catalogue = {r['id']: r for r in read_tsv(self.catalogue_path)}
        self.descriptions = None
        dpath = os.path.join(self.fixtures, 'descriptions.tsv')
        if os.path.exists(dpath):
            self.descriptions = {r['path']: r['description'] for r in read_tsv(dpath)}
        self.linter = None
        if lint:
            self.linter = lint_prompts.Linter(option_names_path=option_names or os.path.join(study, 'envs',
                                                                                            'pandas_option_names.txt'))
        self.pilot_ngrams = load_pilot_ngrams(self.pilot)
        # LR2 2026-11-11: closed phrase list of Amendment 10 (None when the study has no phrase file, e.g. synthetic tests)
        self.order_phrases = load_order_phrases(study, order_phrases)
        # REPAIR5 fixes 2026-11-12 (MF2): the lead's per-card LR2.3 decisions ({} when the file does not exist)
        self.lr2_decisions = load_lr2_decisions(study, lr2_decisions)
        # REPAIR9 2026-11-13 (lead ruling LR43): R tasks whose fidelity FAIL a ruling has settled ({} when the file does not exist)
        self.ruled_fidelity_fails, self.ruled_fidelity_fails_errors = load_ruled_fidelity_fails(study, ruled_fidelity_fails)
        # REPAIR10 2026-11-13 (lead ruling LR57): cards from which a ruling leaves a generic check off ({} when the file does not exist)
        self.ruled_generic_exemptions, self.ruled_generic_exemptions_errors = load_ruled_generic_exemptions(
            study, ruled_generic_exemptions)


# ------------------------------------------------------------------ lead ruling LR2 (FULL_PREREG_AMENDMENT_10.md)
# Added 2026-11-11 (LR2 step). Kind (a): order_significant true and sort_keys not exactly ["__index__"] (sorted order by stated
# keys; never changed by the LR2 script). Kind (b): order_significant true and sort_keys exactly ["__index__"] (requested file or
# listed order). The closed phrase list is tools/order_flag_phrases.txt, which must be a verbatim ```text block of
# FULL_PREREG_AMENDMENT_10.md; it is applied with re.search to the lower-cased task text, as tools/apply_order_flag_rule.py does.
LR2_IDENTITY = ['__index__']
LR2_AMENDMENT = 'FULL_PREREG_AMENDMENT_10.md'


class OrderPhraseError(Exception):
    pass


def load_order_phrases(study, path=None):
    """-> [(name, compiled regex)] or None if the phrase file does not exist (and no path was given explicitly)."""
    p = path or os.path.join(study, 'tools', 'order_flag_phrases.txt')
    if not os.path.exists(p):
        if path:
            raise OrderPhraseError('LR2 phrase file not found: %s' % p)
        return None
    with open(p, 'rb') as f:
        data = f.read()
    am = os.path.join(study, LR2_AMENDMENT)
    if os.path.exists(am):
        with open(am, 'rb') as f:
            if b'```text\n' + data + b'```' not in f.read():
                raise OrderPhraseError('%s is not a verbatim ```text block of %s' % (p, LR2_AMENDMENT))
    out = []
    for ln in data.decode('utf-8').splitlines():
        if not ln.strip() or ln.startswith('#'):
            continue
        if '\t' not in ln:
            raise OrderPhraseError('phrase line without a TAB: %r' % ln)
        name, rx = ln.split('\t', 1)
        out.append((name, re.compile(rx)))
    if not out:
        raise OrderPhraseError('empty LR2 phrase list')
    return out


# REPAIR5 fixes 2026-11-12 (REPAIR5_REVIEW.md MF2): LR2.3 says the lead decides each reader difference "on the wording of item 1"
# and that "a difference is never decided by a program's output"; LR2.1 says nothing but a stated order of `result` sets the flag. The
# phrase-list check above must therefore give way to a recorded decision of the lead for that card. The record is
# tasks/LR2_LEAD_DECISIONS.tsv (one row per decided card): task_id, lead_decision (none | a | b),
# sort_keys (JSON list; required for a, ["__index__"] for b, [] for none), decided_at (ISO date-time), decided_by, reason (the wording
# of LR2.1 the decision rests on). For a card with a row, the card must agree with the decision (else ERROR: the card has not been
# brought into line); a phrase match on such a card is a NOTE, not an ERROR. Cards without a row are checked as before.
LR2_DECISION_COLUMNS = ['task_id', 'lead_decision', 'sort_keys', 'decided_at', 'decided_by', 'reason']
LR2_DECISIONS_FILE = os.path.join('tasks', 'LR2_LEAD_DECISIONS.tsv')


def load_lr2_decisions(study, path=None):
    """{task_id: {'decision': 'none'|'a'|'b', 'sort_keys': [...], ...}}; {} if the default file does not exist. Raises
    OrderPhraseError for a malformed file, so a bad record stops the validator (exit 2) instead of being ignored."""
    p = path or os.path.join(study, LR2_DECISIONS_FILE)
    if not os.path.exists(p):
        if path:
            raise OrderPhraseError('LR2 decisions file not found: %s' % p)
        return {}
    with open(p, encoding='utf-8') as f:
        lines = [ln for ln in f if not ln.startswith('#') and ln.strip()]
    if not lines:
        raise OrderPhraseError('%s: no header line' % p)
    rd = csv.DictReader(lines, delimiter='\t')
    if rd.fieldnames != LR2_DECISION_COLUMNS:
        raise OrderPhraseError('%s: header must be %s' % (p, '\t'.join(LR2_DECISION_COLUMNS)))
    out = {}
    for r in rd:
        tid = (r.get('task_id') or '').strip()
        dec = (r.get('lead_decision') or '').strip()
        if not tid or tid in out:
            raise OrderPhraseError('%s: empty or repeated task_id %r' % (p, tid))
        if dec not in ('none', 'a', 'b'):
            raise OrderPhraseError('%s: %s: lead_decision must be none, a or b' % (p, tid))
        try:
            keys = json.loads(r.get('sort_keys') or '[]')
        except ValueError:
            raise OrderPhraseError('%s: %s: sort_keys is not a JSON list' % (p, tid))
        if not isinstance(keys, list) or not all(isinstance(k, str) and k for k in keys):
            raise OrderPhraseError('%s: %s: sort_keys is not a JSON list of names' % (p, tid))
        # REPAIR6 2026-11-12 (lead ruling LR14 as adopted, FULL_PREREG_AMENDMENT_11.md): a key that the text makes the index of the
        # result stays `__index__`, so a decision of kind (a) may carry exactly [`__index__`] (a sort by the index key; card unchanged).
        if (dec == 'none' and keys) or (dec == 'b' and keys != LR2_IDENTITY) or (dec == 'a' and not keys):
            raise OrderPhraseError('%s: %s: sort_keys %s do not fit lead_decision %s' % (p, tid, keys, dec))
        for k in ('decided_at', 'decided_by', 'reason'):
            if not (r.get(k) or '').strip():
                raise OrderPhraseError('%s: %s: %s is empty' % (p, tid, k))
        out[tid] = {'decision': dec, 'sort_keys': keys, 'decided_at': r['decided_at'].strip(), 'decided_by': r['decided_by'].strip()}
    return out


def lr2_flag_check(task, phrases, decision=None):
    """(errors, notes) of LR2 for one card. Error: the text matches the closed list, the card is not kind (a), and it is not
    flagged kind (b). Notes: a kind (b) flag with no phrase (left for the LR2.3 reader check, not removed); a kind (a) card whose
    text matches a phrase (kept, LR2.2). `decision` (MF2): the lead's LR2.3 decision for this card, which replaces the phrase rule."""
    E, N = [], []
    tid = task.get('id', '?')
    t = (task.get('task_text') or '').lower()
    hits = ['%s="%s"' % (name, m.group(0)) for name, rx in phrases for m in [rx.search(t)] if m]
    flagged = bool(task.get('order_significant'))
    keys = list(task.get('sort_keys') or [])
    kind_a = flagged and keys != LR2_IDENTITY
    kind_b = flagged and keys == LR2_IDENTITY
    if decision is not None:
        kind = 'a' if kind_a else ('b' if kind_b else 'none')
        dec = decision['decision']
        if dec == 'a' and decision['sort_keys'] == LR2_IDENTITY and kind_b:
            kind = 'a'                      # REPAIR6 (LR14): kind (a) by the index key is encoded like kind (b): flagged, [`__index__`]
        if kind != dec or (dec == 'a' and keys != decision['sort_keys']):
            E.append('%s: LR2: the lead decided %s %s (LR2.3, %s, %s) but the card is %s %s'
                     % (tid, dec, json.dumps(decision['sort_keys']), decision['decided_by'], decision['decided_at'], kind,
                        json.dumps(keys)))
        else:
            N.append('%s: LR2: card follows the lead\'s LR2.3 decision %s (%s)%s'
                     % (tid, dec, decision['decided_at'], ('; phrase match %s not applied' % '; '.join(hits)) if hits else ''))
        return E, N
    if hits and not kind_a and not kind_b:
        E.append('%s: LR2: task text matches %s of the closed phrase list, so the card must be kind (b) '
                 '(order_significant true, sort_keys ["__index__"], row_order ties_only)' % (tid, '; '.join(hits)))
    if kind_b and not hits:
        N.append('%s: LR2: kind (b) flag (sort_keys ["__index__"]) but no phrase of the closed list in the task text; '
                 'kept, for the LR2.3 reader check' % tid)
    if kind_a and hits:
        N.append('%s: LR2: kind (a) card whose task text matches %s; kept (LR2.2)' % (tid, '; '.join(hits)))
    return E, N


# ------------------------------------------------------------------ pilot overlap (section 4.5)
def words(text):
    return re.findall(r'[a-z0-9]+', (text or '').lower())


def ngrams(text, n=NGRAM):
    w = words(text)
    return {' '.join(w[i:i + n]) for i in range(len(w) - n + 1)}


def load_pilot_ngrams(pilot):
    """8-grams of every pilot task text, file description and prompt, minus 8-grams of the prompt templates."""
    tj = os.path.join(pilot, 'data', 'tasks', 'tasks.json')
    if not os.path.exists(tj):
        raise FileNotFoundError('pilot tasks.json not found: %s (needed for the section 4.5 overlap check)' % tj)
    d = _jload(tj, encoding='utf-8')
    grams = set()
    for t in d.get('tasks', []):
        grams |= ngrams(t.get('task', ''))
    for desc in (d.get('files') or {}).values():
        grams |= ngrams(desc)
    for p in sorted(glob.glob(os.path.join(pilot, 'data', 'prompts', '*.txt'))):
        grams |= ngrams(_slurp(p, encoding='utf-8'))
    template = ngrams(d.get('template', '').replace('{files}', ' ').replace('{task}', ' '))
    dummy = {'id': 'X', 'files': [{'path': 'GEN/x.csv', 'description': 'placeholder line'}],
             'task_text': 'placeholder task text'}
    template |= ngrams(render(dummy)) | ngrams(render(dummy, hint=True))
    return grams - template


# ------------------------------------------------------------------ per-task checks
def validate_task(task, task_dir, ctx):
    """Return (errors, notes) for one task dict; task_dir is its folder (or None for tasks.json input)."""
    E, N = [], []
    tid = task.get('id', '?')
    E += schema_errors(task, ctx.schema)
    if E:
        # still report the two flags explicitly (acceptance: the validator rejects a task missing a flag)
        for flag in ('order_significant', 'dtype_significant'):
            if flag not in task:
                E.append('%s: missing flag %s' % (tid, flag))
        return E, N
    st = task['stratum']
    # ---- id, stratum, family
    if RE_EX.match(tid):
        if not ctx.example:
            E.append('%s: example ids (EX_*) are not allowed in the study set' % tid)
    elif ctx.example:
        E.append('%s: example mode accepts only EX_* ids' % tid)
    else:
        if st == 'M':
            m = RE_M.match(tid)
            if not m:
                E.append('%s: stratum M needs an id M_QFn_nn' % tid)
            elif task['family'] != FAM_BY_CODE[m.group(1)]:
                E.append('%s: family %s does not match id' % (tid, task['family']))
        elif st == 'R' and not RE_R.match(tid):
            E.append('%s: stratum R needs an id R_nn' % tid)
        elif st == 'A':
            m = RE_A.match(tid)
            if not m:
                E.append('%s: stratum A needs an id A_<FAM>_nn' % tid)
            elif task['generic_family'] != m.group(1):
                E.append('%s: generic_family %s does not match id' % (tid, task['generic_family']))
    if task_dir is not None and os.path.basename(os.path.normpath(task_dir)) != tid:
        E.append('%s: folder name %s differs from id' % (tid, os.path.basename(task_dir)))
    # ---- per-stratum fields
    r_fields = ('so_question_id', 'so_url', 'so_creation_date', 'so_score', 'so_licence', 'intent_summary',
                'column_map')
    if st == 'M':
        if task['family'] is None:
            E.append('%s: M task needs family' % tid)
        if task['generic_family'] is not None:
            E.append('%s: M task must have generic_family null' % tid)
        if task['catalogue_row'] is None:
            E.append('%s: M task needs catalogue_row' % tid)
        elif task['catalogue_row'] not in task['invited_ids_author']:
            E.append('%s: catalogue_row %s not in invited_ids_author' % (tid, task['catalogue_row']))
        if task['predicted_direction'] is None:
            E.append('%s: M task needs predicted_direction (HARM/FIX/BOTH + reason)' % tid)
        if task['naive_path'] != 'naive.py':
            E.append('%s: M task needs naive_path "naive.py"' % tid)
        if ctx.catalogue and task['catalogue_row'] in ctx.catalogue:
            row = ctx.catalogue[task['catalogue_row']]
            if row.get('scope') != 'SILENT' or row.get('quota_family') != task['family']:
                E.append('%s: catalogue_row %s is not a SILENT row of %s' % (tid, task['catalogue_row'],
                                                                             task['family']))
    else:
        for k in ('catalogue_row', 'predicted_direction', 'naive_path', 'family', 'invitation_strength'):
            if task.get(k) is not None:
                E.append('%s: %s must be null for stratum %s' % (tid, k, st))
        if st == 'A' and task['generic_family'] is None:
            E.append('%s: A task needs generic_family' % tid)
    if st == 'R':
        for k in r_fields:
            if task.get(k) is None:
                E.append('%s: R task needs %s' % (tid, k))
        if task.get('so_question_id') and task.get('so_url') and \
                task['so_url'] != 'https://stackoverflow.com/q/%d' % task['so_question_id']:
            E.append('%s: so_url does not match so_question_id' % tid)
        if task.get('so_creation_date') and task['so_creation_date'] < R_MIN_DATE:
            E.append('%s: so_creation_date before %s' % (tid, R_MIN_DATE))
    else:
        for k in r_fields + ('fidelity',):
            if task.get(k) is not None:
                E.append('%s: %s must be null outside stratum R' % (tid, k))
    # ---- flags and variants (section 3, 10.1)
    if task['order_significant'] and not task['sort_keys']:
        E.append('%s: order_significant needs sort_keys' % tid)
    if not task['order_significant'] and task['sort_keys']:
        E.append('%s: sort_keys given but order_significant is false' % tid)
    av = task['acceptable_variants']
    want = 'ties_only' if task['order_significant'] else 'any'
    if av['row_order'] != want:
        E.append('%s: acceptable_variants.row_order must be %r' % (tid, want))
    if av['rounding_sig_digits'] != 6:
        E.append('%s: rounding_sig_digits must be 6 (section 10.1)' % tid)
    # ---- lead ruling LR2 (Amendment 10; conventions/CONVENTIONS.md section 5.2 addendum of 2026-11-11)
    if ctx.order_phrases is not None and not ctx.example:
        e2, n2 = lr2_flag_check(task, ctx.order_phrases, (getattr(ctx, 'lr2_decisions', None) or {}).get(tid))
        E += e2
        N += n2
    # ---- property checks
    names = [pc['check'] for pc in task['property_checks']]
    exempt = getattr(ctx, 'ruled_generic_exemptions', None) or {}           # LR57: ruled exemptions, every mode
    for g in GENERIC_CHECKS:
        ruled = exempt.get((tid, g))
        if g not in names and ruled is not None:
            N.append('%s: generic property check %s left off by lead ruling(s) %s (%s, %s)'
                     % (tid, g, ', '.join(ruled['ruling']), RULED_EXEMPT_FILE.replace(os.sep, '/'), ruled['date']))
        elif g not in names:
            E.append('%s: generic property check %s missing' % (tid, g))
        elif ruled is not None:
            E.append('%s: listed in %s for %s but the card still carries the check'
                     % (tid, RULED_EXEMPT_FILE.replace(os.sep, '/'), g))
    if len(names) == len(GENERIC_CHECKS):
        N.append('%s: no task-specific property check' % tid)
    for pc in task['property_checks']:
        E += ['%s: %s' % (tid, e) for e in check_property_args(pc)]
    if task['order_significant'] and 'sorted_by' not in names:
        N.append('%s: order_significant task without a sorted_by property check' % tid)
    # ---- provenance (common rule 9)
    if task['drafted_by'].startswith('pkg:') and task['status'] != DRAFT_STATUS:
        E.append('%s: drafted task must have status %r' % (tid, DRAFT_STATUS))
    # ---- catalogue ids exist
    if ctx.catalogue:
        for cid in list(task['invited_ids_author']) + list(task.get('invited_ids_reviewer') or []):
            if cid not in ctx.catalogue:
                E.append('%s: unknown catalogue id %s' % (tid, cid))
    # ---- files and descriptions
    bases = [os.path.basename(f['path']) for f in task['files']]
    if len(set(bases)) != len(bases):
        E.append('%s: two files share a basename' % tid)
    if os.path.isdir(ctx.fixtures):
        for f in task['files']:
            for var in ('main', 'clean', 'dirty'):
                if not os.path.exists(os.path.join(ctx.fixtures, var, f['path'])):
                    E.append('%s: fixture missing: %s/%s' % (tid, var, f['path']))
        if ctx.descriptions is None:
            E.append('%s: fixtures/descriptions.tsv missing' % tid)
        else:
            for f in task['files']:
                d = ctx.descriptions.get(f['path'])
                if d is None:
                    E.append('%s: %s not in descriptions.tsv' % (tid, f['path']))
                elif d != f['description']:
                    E.append('%s: description of %s differs from descriptions.tsv' % (tid, f['path']))
    else:
        N.append('%s: fixtures folder %s not found; file checks skipped' % (tid, ctx.fixtures))
    # ---- files in the task folder
    if task_dir is not None:
        if not os.path.isfile(os.path.join(task_dir, 'reference.py')):
            E.append('%s: reference.py missing' % tid)
        has_naive = os.path.isfile(os.path.join(task_dir, 'naive.py'))
        if st == 'M' and not has_naive:
            E.append('%s: naive.py missing' % tid)
        if st != 'M' and has_naive:
            E.append('%s: naive.py only for stratum M' % tid)
    # ---- prompt render + lint (section 5)
    try:
        prompt = render(task)
    except RenderError as e:
        E.append('%s: render: %s' % (tid, e))
        prompt = None
    if prompt is not None and ctx.linter is not None:
        res = ctx.linter.lint(prompt, task['allowed_task_words'])
        for h in res['hits']:
            E.append('%s: banned word [%s] %r line %d' % (tid, h['label'], h['match'], h['line']))
        for h in res['exempted']:
            N.append('%s: EXEMPTED banned word [%s] %r via allowed word %r' % (tid, h['label'], h['match'],
                                                                               h['allowed_word']))
    if prompt is not None and task_dir is not None:
        pf = os.path.join(os.path.dirname(os.path.normpath(task_dir)), 'prompts', tid + '.txt')
        if os.path.exists(pf) and _slurp(pf, encoding='utf-8') != prompt:
            E.append('%s: %s differs from the rendered prompt (re-render)' % (tid, pf))
    # ---- pilot overlap (section 4.5)
    mine = ngrams(task['task_text'])
    for f in task['files']:
        mine |= ngrams(f['description'])
    common = sorted(mine & ctx.pilot_ngrams)
    if common:
        E.append('%s: %d 8-word overlap(s) with pilot text, e.g. %r' % (tid, len(common), common[0]))
    return E, N


# ------------------------------------------------------------------ set-level checks
def quota_checks(tasks, ctx, families, allow_incomplete=False):
    E, N = [], []
    if not os.path.exists(ctx.quota_path):
        return ['quota allocation not found: %s (written by FIX via allocate_quota.py)' % ctx.quota_path], N
    qrows = read_tsv(ctx.quota_path)
    E += tsv_errors(ctx.quota_path, load_schema('quota_allocation.tsv.schema.json'))
    slots = {}          # task id -> (family, row)
    dropped = set()
    for r in qrows:
        if r['row_id'] == 'NONE':
            dropped.add(r['family'])
            continue
        for s in [x for x in r['task_slots'].split(',') if x]:
            slots[s] = (r['family'], r['row_id'])
    m_tasks = {t['id']: t for t in tasks if t.get('stratum') == 'M' and RE_M.match(t.get('id', ''))}
    for tid, t in sorted(m_tasks.items()):
        if t['family'] in dropped:
            E.append('%s: family %s was dropped (no confirmed row); no tasks allowed' % (tid, t['family']))
        elif tid not in slots:
            E.append('%s: not a slot in quota_allocation.tsv' % tid)
        elif slots[tid][1] != t.get('catalogue_row'):
            E.append('%s: slot belongs to row %s, task says %s' % (tid, slots[tid][1], t.get('catalogue_row')))
    for s, (fam, row) in sorted(slots.items()):
        if fam in families and s not in m_tasks:
            (N if allow_incomplete else E).append('%s: quota slot of %s/%s has no task' % (s, fam, row))
    return E, N


def full_set_checks(tasks):
    E = []
    r_ids = sorted(t['id'] for t in tasks if t.get('stratum') == 'R')
    a_ids = sorted(t['id'] for t in tasks if t.get('stratum') == 'A')
    if len(r_ids) > R_MAX:
        E.append('|R| = %d > %d' % (len(r_ids), R_MAX))
    if r_ids != ['R_%02d' % i for i in range(1, len(r_ids) + 1)]:
        E.append('R ids are not contiguous R_01..R_%02d in selection order' % len(r_ids))
    if len(r_ids) + len(a_ids) != RA_TOTAL:
        E.append('|R| + |A| = %d, expected %d' % (len(r_ids) + len(a_ids), RA_TOTAL))
    counts = {}
    for i in a_ids:
        fam = RE_A.match(i).group(1)
        counts.setdefault(fam, []).append(i)
    for fam in GENERIC:
        ids = sorted(counts.get(fam, []))
        if ids != ['A_%s_%02d' % (fam, k) for k in range(1, len(ids) + 1)]:
            E.append('A ids of %s are not contiguous from 01' % fam)
    n = [len(counts.get(f, [])) for f in GENERIC]
    if a_ids and (max(n) - min(n) > 1 or any(n[i] < n[i + 1] for i in range(len(n) - 1))):
        E.append('A tasks are not round-robin over %s: counts %s' % (' '.join(GENERIC), n))
    return E


# REPAIR9 2026-11-13 (lead ruling LR43, LEAD_RULINGS_LR42-LR56_2026-11-13.md; deviation R9-1 of deviations/REPAIR9.md): the exit
# code means "nothing is open that a ruling has not settled". With the blind fields required, a fidelity FAIL of an R task is accepted
# (printed as a NOTE) only if the task is listed in tasks/RULED_FIDELITY_FAILS.tsv (columns task_id, ruling, date), whose sha256 is
# pinned in MANIFEST.sha256. Any other FAIL, an empty fidelity field, or a listed task whose field does not say FAIL is an ERROR; so
# is a listed task that is not an R task of the set, and a file that is malformed or not pinned (its rows are then not accepted).
RULED_FAILS_FILE = os.path.join('tasks', 'RULED_FIDELITY_FAILS.tsv')
RULED_FAILS_COLUMNS = ['task_id', 'ruling', 'date']
RE_RULING = re.compile(r'^LR[0-9]+$')
RE_DATE = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')


def _manifest_hash(study, relpath):
    """sha256 recorded for relpath in study/MANIFEST.sha256, or None."""
    mp = os.path.join(study, 'MANIFEST.sha256')
    if not os.path.exists(mp):
        return None
    for ln in _slurp(mp).splitlines():
        parts = ln.strip().split(None, 1)
        if len(parts) == 2 and parts[1].lstrip('*').strip() in (relpath, './' + relpath):
            return parts[0].lower()
    return None


def load_ruled_fidelity_fails(study, path=None):
    """-> ({task_id: {'ruling': [...], 'date': ...}}, [errors]). ({}, []) when the default file does not exist."""
    import hashlib
    explicit = path is not None
    p = path or os.path.join(study, RULED_FAILS_FILE)
    if not os.path.exists(p):
        return {}, (['LR43: ruled fidelity FAIL file not found: %s' % p] if explicit else [])
    rel = os.path.relpath(os.path.abspath(p), os.path.abspath(study)).replace(os.sep, '/')
    with open(p, 'rb') as f:
        data = f.read()
    errs = []
    pinned = _manifest_hash(study, rel)
    if pinned is None:
        errs.append('LR43: %s is not pinned in MANIFEST.sha256' % rel)
    elif pinned != hashlib.sha256(data).hexdigest():
        errs.append('LR43: %s does not match its MANIFEST.sha256 line' % rel)
    rows = [ln for ln in data.decode('utf-8').splitlines() if ln.strip() and not ln.startswith('#')]
    if not rows or rows[0].split('\t') != RULED_FAILS_COLUMNS:
        errs.append('LR43: %s: header must be %s' % (rel, '\\t'.join(RULED_FAILS_COLUMNS)))
        return {}, errs
    out = {}
    for ln in rows[1:]:
        c = ln.split('\t')
        if len(c) != 3:
            errs.append('LR43: %s: malformed row %r' % (rel, ln))
            continue
        tid, rulings, date = c[0].strip(), [x.strip() for x in c[1].split(',')], c[2].strip()
        if not RE_R.match(tid) or not all(RE_RULING.match(x) for x in rulings) or not RE_DATE.match(date):
            errs.append('LR43: %s: malformed row %r' % (rel, ln))
            continue
        if tid in out:
            errs.append('LR43: %s: task %s listed twice' % (rel, tid))
            continue
        out[tid] = {'ruling': rulings, 'date': date}
    if errs:
        return {}, errs
    return out, []


# REPAIR10 2026-11-13 (lead ruling LR57, LEAD_RULINGS_LR57-LR63_2026-11-13.md; deviation R10-1 of deviations/REPAIR10.md): the two
# generic checks are on every card, except where a ruling that names the card leaves a check off because the task text itself allows a
# result the check forbids. Such cards are read from tasks/RULED_GENERIC_CHECK_EXEMPTIONS.tsv (columns task_id, check, ruling, date),
# whose sha256 is pinned in MANIFEST.sha256, and each is printed as a NOTE. A listed card that still carries the check, a card that
# lacks a generic check without being listed, and a file that is malformed, not pinned or of another hash are ERRORs (its rows are
# then not accepted). This holds in every mode of the validator. In full mode a listed task that is not in the set is also an ERROR.
RULED_EXEMPT_FILE = os.path.join('tasks', 'RULED_GENERIC_CHECK_EXEMPTIONS.tsv')
RULED_EXEMPT_COLUMNS = ['task_id', 'check', 'ruling', 'date']
RE_ANY_ID = re.compile(r'^(M_QF[0-9]_[0-9]{2}|R_[0-9]{2}|A_[A-Z]+_[0-9]{2})$')


def load_ruled_generic_exemptions(study, path=None):
    """-> ({(task_id, check): {'ruling': [...], 'date': ...}}, [errors]). ({}, []) when the default file does not exist."""
    import hashlib
    explicit = path is not None
    p = path or os.path.join(study, RULED_EXEMPT_FILE)
    if not os.path.exists(p):
        return {}, (['LR57: ruled generic-check exemption file not found: %s' % p] if explicit else [])
    rel = os.path.relpath(os.path.abspath(p), os.path.abspath(study)).replace(os.sep, '/')
    with open(p, 'rb') as f:
        data = f.read()
    errs = []
    pinned = _manifest_hash(study, rel)
    if pinned is None:
        errs.append('LR57: %s is not pinned in MANIFEST.sha256' % rel)
    elif pinned != hashlib.sha256(data).hexdigest():
        errs.append('LR57: %s does not match its MANIFEST.sha256 line' % rel)
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        return {}, errs + ['LR57: %s is not UTF-8 text' % rel]
    rows = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith('#')]
    if not rows or rows[0].split('\t') != RULED_EXEMPT_COLUMNS:
        errs.append('LR57: %s: header must be %s' % (rel, '\\t'.join(RULED_EXEMPT_COLUMNS)))
        return {}, errs
    out = {}
    for ln in rows[1:]:
        c = ln.split('\t')
        if len(c) != 4:
            errs.append('LR57: %s: malformed row %r' % (rel, ln))
            continue
        tid, chk, rulings, date = c[0].strip(), c[1].strip(), [x.strip() for x in c[2].split(',')], c[3].strip()
        if (not RE_ANY_ID.match(tid) or chk not in GENERIC_CHECKS or not all(RE_RULING.match(x) for x in rulings)
                or not RE_DATE.match(date)):
            errs.append('LR57: %s: malformed row %r' % (rel, ln))
            continue
        if (tid, chk) in out:
            errs.append('LR57: %s: %s %s listed twice' % (rel, tid, chk))
            continue
        out[(tid, chk)] = {'ruling': rulings, 'date': date}
    if errs:
        return {}, errs
    return out, []


def validate(items, ctx, families=(), full=False, allow_incomplete=False, require_blind=False):
    """items: list of (task_dict, task_dir_or_None). Returns report dict."""
    errors, notes, ids = [], [], {}
    for task, tdir in items:
        tid = task.get('id', '?')
        if tid in ids:
            errors.append('%s: duplicate id (%s and %s)' % (tid, ids[tid], tdir))
        ids[tid] = tdir
        e, n = validate_task(task, tdir, ctx)
        errors += e
        notes += n
        if require_blind and not e:
            st = task['stratum']
            if st == 'M' and task.get('invitation_strength') is None:
                errors.append('%s: invitation_strength not filled' % tid)
            if st in ('R', 'A') and task.get('invited_ids_reviewer') is None:
                errors.append('%s: invited_ids_reviewer not filled' % tid)
            if st == 'R':                                      # LR43: a FAIL is open unless a ruling listed in the file settles it
                res = (task.get('fidelity') or {}).get('result')
                ruled = (getattr(ctx, 'ruled_fidelity_fails', None) or {}).get(tid)
                if ruled is not None:
                    if res == 'FAIL':
                        notes.append('%s: fidelity FAIL settled by lead ruling(s) %s (%s, %s)'
                                     % (tid, ', '.join(ruled['ruling']), RULED_FAILS_FILE.replace(os.sep, '/'), ruled['date']))
                    else:
                        errors.append('%s: listed in %s but its fidelity field does not say FAIL (%r)'
                                      % (tid, RULED_FAILS_FILE.replace(os.sep, '/'), res))
                elif not res:
                    errors.append('%s: fidelity check not PASS (field empty)' % tid)
                elif res != 'PASS':
                    errors.append('%s: fidelity check not PASS' % tid)
    if require_blind:                                          # LR43: the file itself
        errors += list(getattr(ctx, 'ruled_fidelity_fails_errors', None) or [])
        r_ids = {t.get('id') for t, _ in items if t.get('stratum') == 'R'}
        for tid in sorted(set(getattr(ctx, 'ruled_fidelity_fails', None) or {}) - r_ids):
            errors.append('%s: listed in %s but not an R task of the set' % (tid, RULED_FAILS_FILE.replace(os.sep, '/')))
    errors += list(getattr(ctx, 'ruled_generic_exemptions_errors', None) or [])      # LR57: the file itself, every mode
    if full and not ctx.example:
        for tid, chk in sorted(set(getattr(ctx, 'ruled_generic_exemptions', None) or {})):
            if tid not in ids:
                errors.append('%s: listed in %s for %s but not a task of the set'
                              % (tid, RULED_EXEMPT_FILE.replace(os.sep, '/'), chk))
    tasks = [t for t, _ in items]
    if not ctx.example and families:
        e, n = quota_checks(tasks, ctx, set(families), allow_incomplete)
        errors += e
        notes += n
    if full and not ctx.example:
        errors += full_set_checks(tasks)
        for tid in sorted(set(getattr(ctx, 'lr2_decisions', None) or {}) - set(ids)):     # MF2: a decision for no card
            errors.append('%s: LR2: a lead decision is recorded for a task that is not in the set' % tid)
    return {'n_tasks': len(items), 'n_errors': len(errors), 'errors': errors, 'notes': notes,
            'exempted': [n for n in notes if 'EXEMPTED' in n]}


# REPAIR 2026-11-11 (STAGE2_BUILD_REVIEW MF4): tasks/tasks.json (read by analyze_full.py) and each task folder's task.json (used by job
# files for run_programs.py --trace-drift) must hold ONE card. Every field except the blind-attached ones must be equal.
BLIND_ATTACHED = ('blind_provenance', 'invited_ids_reviewer', 'invitation_strength', 'independent_card_ref', 'fidelity')


def card_source_errors(study, tasks_json):
    """Errors for every card field that differs between tasks.json and tasks/<PKG>/<id>/task.json (and for missing folder cards)."""
    errs = []
    for t in _jload(tasks_json, encoding='utf-8')['tasks']:
        pkg = pkg_of(t.get('id', ''))
        p = os.path.join(study, 'tasks', pkg, t['id'], 'task.json') if pkg else None
        if not p or not os.path.exists(p):
            errs.append('%s: card source mismatch: no folder task.json' % t.get('id'))
            continue
        f = _jload(p, encoding='utf-8')
        diff = sorted(k for k in set(f) | set(t) if k not in BLIND_ATTACHED and f.get(k, '<absent>') != t.get(k, '<absent>'))
        if diff:
            errs.append('%s: card source mismatch between tasks.json and %s in field(s) %s' % (t['id'], os.path.relpath(p, study),
                                                                                                ', '.join(diff)))
    return errs


def collect(study, pkgs, tasks_json=None, example_dirs=()):
    items = []
    for pkg in pkgs:
        for p in sorted(glob.glob(os.path.join(study, 'tasks', pkg, '*', 'task.json'))):
            items.append((_jload(p, encoding='utf-8'), os.path.dirname(p)))
    if tasks_json:
        d = _jload(tasks_json, encoding='utf-8')
        for t in d['tasks']:
            pkg = pkg_of(t.get('id', ''))
            tdir = os.path.join(study, 'tasks', pkg, t['id']) if pkg else None
            items.append((t, tdir if tdir and os.path.isdir(tdir) else None))
    for ex in example_dirs:
        for p in sorted(glob.glob(os.path.join(ex, '*', 'task.json'))):
            items.append((_jload(p, encoding='utf-8'), os.path.dirname(p)))
    return items


def main(argv=None):
    ap = argparse.ArgumentParser(description='Validate study tasks.')
    ap.add_argument('--study', default=STUDY)
    ap.add_argument('--pkg', action='append', default=[], help='M1, M2, R or A (repeatable)')
    ap.add_argument('--tasks-json', help='merged tasks/tasks.json')
    ap.add_argument('--example', action='append', default=[], help='folder of fictitious EX_* task folders')
    ap.add_argument('--full', action='store_true', help='whole-set checks (all quotas, |R|<=40, |R|+|A|=72)')
    ap.add_argument('--allow-incomplete', action='store_true', help='unfilled quota slots are notes, not errors')
    ap.add_argument('--require-blind', action='store_true', help='blind fields must be filled (INTEGRATE)')
    ap.add_argument('--fixtures')
    ap.add_argument('--catalogue')
    ap.add_argument('--quota')
    ap.add_argument('--pilot')
    ap.add_argument('--option-names')
    ap.add_argument('--order-phrases', help='LR2 phrase file (default tools/order_flag_phrases.txt)')
    ap.add_argument('--lr2-decisions', help="lead's LR2.3 decisions (default tasks/LR2_LEAD_DECISIONS.tsv; MF2)")
    ap.add_argument('--ruled-fidelity-fails', help='R tasks whose fidelity FAIL a ruling settled (default '
                                                   'tasks/RULED_FIDELITY_FAILS.tsv; lead ruling LR43)')
    ap.add_argument('--ruled-generic-exemptions', help='cards from which a ruling leaves a generic check off (default '
                                                       'tasks/RULED_GENERIC_CHECK_EXEMPTIONS.tsv; lead ruling LR57)')
    ap.add_argument('--report', help='write JSON report here')
    a = ap.parse_args(argv)
    try:
        ctx = Context(a.study, fixtures=a.fixtures, catalogue=a.catalogue, quota=a.quota, pilot=a.pilot,
                      option_names=a.option_names, example=bool(a.example), order_phrases=a.order_phrases,
                      lr2_decisions=a.lr2_decisions, ruled_fidelity_fails=a.ruled_fidelity_fails,
                      ruled_generic_exemptions=a.ruled_generic_exemptions)
    except (lint_prompts.LintSetupError, FileNotFoundError, OrderPhraseError) as e:
        print('SETUP ERROR:', e, file=sys.stderr)
        return 2
    items = collect(a.study, a.pkg, a.tasks_json, a.example)
    if not items:
        print('no tasks found', file=sys.stderr)
        return 2
    fams = []
    if a.full:
        fams = FAMILIES
    else:
        for p in a.pkg:
            fams += PKG_FAMILIES.get(p, [])
        if a.tasks_json:
            fams = FAMILIES
    rep = validate(items, ctx, families=fams, full=a.full, allow_incomplete=a.allow_incomplete,
                   require_blind=a.require_blind)
    if a.tasks_json:                                           # REPAIR MF4: one card in both sources
        cse = card_source_errors(a.study, a.tasks_json)
        rep['errors'] += cse
        rep['n_errors'] += len(cse)
        rep['card_source_mismatches'] = len(cse)
    for e in rep['errors']:
        print('ERROR', e)
    for n in rep['notes']:
        print('NOTE ', n)
    print('validated %d task(s): %d error(s), %d note(s), %d exempted banned-word hit(s)'
          % (rep['n_tasks'], rep['n_errors'], len(rep['notes']), len(rep['exempted'])))
    if a.report:
        with open(a.report, 'w', encoding='utf-8') as f:
            json.dump(rep, f, indent=1)
    return 1 if rep['n_errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
