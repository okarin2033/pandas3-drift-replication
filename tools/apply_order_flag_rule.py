"""Lead ruling LR2 (FULL_PREREG_AMENDMENT_10.md): apply the one rule for the flag `order_significant`, kind (b), to the cards.

Written 2026-11-11 (REPAIR5). Standard library only. Tested on synthetic cards only
(tools/tests/test_apply_order_flag_rule.py); in REPAIR5 it was NOT run on the real cards.

Rule (Amendment 10, LR2.1-LR2.2):
- The phrase list is read from ONE data file (default tools/order_flag_phrases.txt), which must be a verbatim copy of the fenced
  block of the amendment (default FULL_PREREG_AMENDMENT_10.md); if the data file is not found byte for byte inside a ```text block
  of the amendment, the script refuses to run.
- Each expression is applied with re.search to the card's task_text in lower case.
- A kind (a) flag (order_significant true and sort_keys not exactly ["__index__"]) is never changed.
- Every other card with at least one match gets kind (b): order_significant true, sort_keys ["__index__"] and
  acceptable_variants.row_order "ties_only" (the variant that goes with a flag, conventions/CONVENTIONS.md 5.2).
- The script removes no flag: a card flagged ["__index__"] whose text matches no phrase is listed (action kind_b_no_phrase) and left
  unchanged, for the reader check of LR2.3 (second reading).
- All cards are processed at once (LR2.2: all 200; --expect-n, default 200, must equal the number of distinct card ids).

Card sources: --tasks-json (a file {"tasks": [...]}) and/or --cards (task.json files; shell globs are expanded by the script). A card id
that appears in several sources must have the same task_text and the same flags in all of them, else the script refuses.

Output: a change list (TSV) with every change (task id, old flag, new flag, matched phrase(s)) and, marked as not changed, the
kind (a) cards whose text matches a phrase and the kind_b_no_phrase cards.
Modes: --dry-run writes only the change list; --apply also writes the changed cards to every source that holds them, after copying
each file it will write into --backup-dir. Exactly one mode must be given.

usage: python3 -I -B tools/apply_order_flag_rule.py (--dry-run | --apply --backup-dir DIR) --changes OUT.tsv
           [--tasks-json tasks/tasks.json] [--cards 'tasks/A/*/task.json' ...] [--expect-n 200]
           [--phrases tools/order_flag_phrases.txt] [--amendment FULL_PREREG_AMENDMENT_10.md] [--study DIR]
"""
import argparse, datetime, glob, hashlib, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
IDENTITY = ['__index__']
FLAG_ROW_ORDER = 'ties_only'


class RuleError(Exception):
    pass


def sha256_file(p):
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def load_phrases(phrases_path, amendment_path):
    """-> [(name, compiled regex, source text)]. Refuses unless the data file is a verbatim ```text block of the amendment."""
    with open(phrases_path, 'rb') as f:
        data = f.read()
    with open(amendment_path, 'rb') as f:
        am = f.read()
    if b'```text\n' + data + b'```' not in am:
        raise RuleError('the phrase file %s is not a verbatim copy of a ```text block of %s' % (phrases_path, amendment_path))
    out = []
    for ln in data.decode('utf-8').splitlines():
        if not ln.strip() or ln.startswith('#'):
            continue
        if '\t' not in ln:
            raise RuleError('phrase line without a TAB: %r' % ln)
        name, rx = ln.split('\t', 1)
        out.append((name, re.compile(rx), rx))
    if not out:
        raise RuleError('empty phrase list')
    return out


def matches(text, phrases):
    """[(name, matched text)] for every expression that hits the lower-cased text."""
    t = (text or '').lower()
    hits = []
    for name, rx, _ in phrases:
        m = rx.search(t)
        if m:
            hits.append((name, m.group(0)))
    return hits


def flag_of(card):
    return {'order_significant': bool(card.get('order_significant')), 'sort_keys': list(card.get('sort_keys') or []),
            'row_order': (card.get('acceptable_variants') or {}).get('row_order')}


def is_kind_a(f):
    return f['order_significant'] and f['sort_keys'] != IDENTITY


def decide(card, phrases):
    """-> (action, old flag, new flag or None, hits). Actions: set_kind_b (change), keep_kind_a, already_kind_b, kind_b_no_phrase,
    none. A card already flagged ["__index__"] with a match but another row_order gets set_kind_b (row_order brought into line)."""
    f = flag_of(card)
    hits = matches(card.get('task_text'), phrases)
    new = {'order_significant': True, 'sort_keys': list(IDENTITY), 'row_order': FLAG_ROW_ORDER}
    if is_kind_a(f):
        return ('keep_kind_a' if hits else 'none'), f, None, hits
    if hits:
        if f == new:
            return 'already_kind_b', f, None, hits
        return 'set_kind_b', f, new, hits
    if f['order_significant']:
        return 'kind_b_no_phrase', f, None, hits
    return 'none', f, None, hits


def apply_flag(card, new):
    card['order_significant'] = new['order_significant']
    card['sort_keys'] = list(new['sort_keys'])
    av = card.get('acceptable_variants')
    if not isinstance(av, dict):
        av = {}
        card['acceptable_variants'] = av
    av['row_order'] = new['row_order']


def _read_json(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def _write_json(p, obj):
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write('\n')
    os.replace(tmp, p)


def load_sources(study, tasks_json, card_globs):
    """-> (sources, by_id). sources: [(path, kind 'tasks_json'|'card', loaded object)]; by_id: id -> [(source index, card dict)]."""
    sources, by_id = [], {}
    if tasks_json:
        p = tasks_json if os.path.isabs(tasks_json) else os.path.join(study, tasks_json)
        doc = _read_json(p)
        sources.append((p, 'tasks_json', doc))
        for c in doc['tasks']:
            by_id.setdefault(c['id'], []).append((len(sources) - 1, c))
    paths = []
    for g in card_globs or []:
        gg = g if os.path.isabs(g) else os.path.join(study, g)
        found = sorted(glob.glob(gg))
        if not found:
            raise RuleError('no card file matches %s' % g)
        paths += found
    for p in sorted(set(paths)):
        c = _read_json(p)
        sources.append((p, 'card', c))
        by_id.setdefault(c['id'], []).append((len(sources) - 1, c))
    for tid, lst in by_id.items():
        texts = {c.get('task_text') for _, c in lst}
        flags = {json.dumps(flag_of(c), sort_keys=True) for _, c in lst}
        if None in texts:
            raise RuleError('%s has no task_text' % tid)
        if len(texts) > 1 or len(flags) > 1:
            raise RuleError('%s differs between its sources (task_text or flags)' % tid)
    return sources, by_id


def run(study, tasks_json, card_globs, phrases_path, amendment_path, changes_path, mode, backup_dir=None, expect_n=200, log=print):
    if mode not in ('dry-run', 'apply'):
        raise RuleError('mode must be dry-run or apply')
    if mode == 'apply' and not backup_dir:
        raise RuleError('--apply needs --backup-dir')
    phrases = load_phrases(phrases_path, amendment_path)
    sources, by_id = load_sources(study, tasks_json, card_globs)
    if expect_n is not None and len(by_id) != expect_n:
        raise RuleError('%d distinct cards found, %d expected (LR2.2: all cards at once)' % (len(by_id), expect_n))
    rows, touched = [], set()
    for tid in sorted(by_id):
        lst = by_id[tid]
        action, old, new, hits = decide(lst[0][1], phrases)
        if action == 'none':
            continue
        rows.append((tid, ','.join(os.path.relpath(sources[i][0], study) for i, _ in lst), action, old, new, hits))
        if action == 'set_kind_b' and mode == 'apply':
            for i, c in lst:
                apply_flag(c, new)
                touched.add(i)
    if mode == 'apply':
        os.makedirs(backup_dir, exist_ok=True)
        for i in sorted(touched):
            p = sources[i][0]
            dst = os.path.join(backup_dir, os.path.relpath(p, study))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if not os.path.exists(dst):
                shutil.copy2(p, dst)
        for i in sorted(touched):
            _write_json(sources[i][0], sources[i][2])

    def fl(f):
        return '' if f is None else '%s|%s|%s' % (f['order_significant'], json.dumps(f['sort_keys']), f['row_order'])
    when = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    out = ['# lead ruling LR2 (FULL_PREREG_AMENDMENT_10.md), tools/apply_order_flag_rule.py, mode %s, %s; phrase file sha256 %s; '
           'amendment sha256 %s; %d distinct cards' % (mode, when, sha256_file(phrases_path), sha256_file(amendment_path), len(by_id)),
           '# flag = order_significant|sort_keys|row_order; action set_kind_b is a change, every other action is listed unchanged',
           'task_id\tsources\taction\told_flag\tnew_flag\tmatched_phrases']
    for tid, src, action, old, new, hits in rows:
        out.append('\t'.join([tid, src, action, fl(old), fl(new), ';'.join('%s="%s"' % h for h in hits)]))
    os.makedirs(os.path.dirname(os.path.abspath(changes_path)), exist_ok=True)
    with open(changes_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')
    n_change = sum(1 for r in rows if r[2] == 'set_kind_b')
    log('%s: %d cards, %d changes (set_kind_b), %d listed unchanged; files written: %d; change list %s'
        % (mode, len(by_id), n_change, len(rows) - n_change, len(touched) if mode == 'apply' else 0, changes_path))
    return {'n_cards': len(by_id), 'rows': rows, 'n_change': n_change, 'files_written': len(touched) if mode == 'apply' else 0}


def main(argv=None):
    ap = argparse.ArgumentParser(description='LR2: apply kind (b) of the order_significant rule (Amendment 10).')
    m = ap.add_mutually_exclusive_group(required=True)
    m.add_argument('--dry-run', action='store_true')
    m.add_argument('--apply', action='store_true')
    ap.add_argument('--study', default=STUDY)
    ap.add_argument('--tasks-json', default=None)
    ap.add_argument('--cards', nargs='*', default=[])
    ap.add_argument('--phrases', default=None)
    ap.add_argument('--amendment', default=None)
    ap.add_argument('--changes', required=True)
    ap.add_argument('--backup-dir', default=None)
    ap.add_argument('--expect-n', type=int, default=200)
    a = ap.parse_args(argv)
    phrases = a.phrases or os.path.join(a.study, 'tools', 'order_flag_phrases.txt')
    amendment = a.amendment or os.path.join(a.study, 'FULL_PREREG_AMENDMENT_10.md')
    try:
        run(a.study, a.tasks_json, a.cards, phrases, amendment, a.changes, 'apply' if a.apply else 'dry-run', a.backup_dir, a.expect_n)
    except RuleError as e:
        print('refused: %s' % e, file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
