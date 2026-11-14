# Banned-word lint for rendered prompts (FULL_PREREG.md section 5). Standard library only.
# Written 2026-11-11 by pkg:SHARED. Conventions: conventions/CONVENTIONS.md section 7.
#
# usage:
#   python3 -I harness/lint_prompts.py tasks/M1/prompts/*.txt                 # lint prompt files
#   python3 -I harness/lint_prompts.py --pkg M1                              # prompts of tasks/M1, with each task's
#                                                                            # allowed_task_words exemptions
#   python3 -I harness/lint_prompts.py --hint tasks/prompts_hint/*.txt       # ablation prompts: only the hint
#                                                                            # sentence is exempt
#   python3 -I harness/lint_prompts.py --text "some description line"        # lint a single string
#   options: --option-names PATH (default envs/pandas_option_names.txt; the lint fails loudly if it is missing)
#            --json  (machine-readable report on stdout)
#
# Matching: every list regex is applied case-insensitively to the whole text (word boundaries are in the
# regexes). pandas option names: the full dotted name (e.g. display.max_rows) and, when it contains an
# underscore, its last segment (e.g. max_rows), bounded by non-word, non-dot characters.
# Exit code: 0 clean (exemptions allowed and reported), 1 at least one blocking hit, 2 usage/setup error.
import argparse, glob, json, os, re, sys


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
from render_prompts import HINT_SENTENCE, render  # noqa: E402

DEFAULT_LIST = os.path.join(HERE, 'banned_words.txt')
DEFAULT_OPTIONS = os.path.join(STUDY, 'envs', 'pandas_option_names.txt')


class LintSetupError(RuntimeError):
    pass


def load_banned(path=DEFAULT_LIST):
    rules = []
    with open(path, encoding='utf-8') as f:
        for n, line in enumerate(f, 1):
            line = line.rstrip('\n')
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) != 3 or parts[1] not in ('yes', 'no'):
                raise LintSetupError('%s:%d: expected label<TAB>yes|no<TAB>regex' % (path, n))
            rules.append((parts[0], parts[1] == 'yes', re.compile(parts[2], re.IGNORECASE)))
    if not rules:
        raise LintSetupError('empty banned-word list: ' + path)
    return rules


def load_option_names(path=DEFAULT_OPTIONS):
    if not path or not os.path.exists(path):
        raise LintSetupError('pandas option-name list not found: %s (written by ENV_TERMS; the lint cannot run '
                             'without it; tests pass a stub with --option-names)' % path)
    names = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            s = line.strip()
            if s and not s.startswith('#'):
                names.append(s)
    if not names:
        raise LintSetupError('pandas option-name list is empty: ' + path)
    return sorted(set(names))


def option_rules(names):
    """Rules for option names: full dotted name, plus the last segment when it contains '_'."""
    rules, seen = [], set()
    for name in names:
        forms = [name]
        last = name.rsplit('.', 1)[-1]
        if '_' in last and last != name:
            forms.append(last)
        for form in forms:
            key = form.lower()
            if key in seen:
                continue
            seen.add(key)
            rx = re.compile(r'(?<![\w.])' + re.escape(form) + r'(?![\w])', re.IGNORECASE)
            rules.append(('option:' + form, False, rx))
    return rules


class Linter:
    def __init__(self, list_path=DEFAULT_LIST, option_names_path=DEFAULT_OPTIONS):
        self.rules = load_banned(list_path) + option_rules(load_option_names(option_names_path))

    def lint(self, text, allowed_words=(), hint=False):
        """Return {'ok', 'hits', 'exempted', 'errors'}.

        hits     : blocking hits [{label, match, start, line}]
        exempted : hits of exemptible rules covered by an allowed_task_words phrase (reported, not blocking)
        errors   : structural problems (hint sentence missing or misplaced in --hint mode)
        """
        errors = []
        if hint:
            text, err = strip_hint(text)
            if err:
                errors.append(err)
        allowed_spans = []
        for w in allowed_words or ():
            w = (w or '').strip()
            if not w:
                continue
            for m in re.finditer(r'(?<!\w)' + re.escape(w) + r'(?!\w)', text, re.IGNORECASE):
                allowed_spans.append((m.start(), m.end(), w))
        hits, exempted = [], []
        for label, exemptible, rx in self.rules:
            for m in rx.finditer(text):
                h = {'label': label, 'match': m.group(0), 'start': m.start(),
                     'line': text.count('\n', 0, m.start()) + 1}
                cover = [w for s, e, w in allowed_spans if s <= m.start() and m.end() <= e]
                if cover and exemptible:
                    h['allowed_word'] = cover[0]
                    exempted.append(h)
                else:
                    if cover:
                        h['note'] = 'listed in allowed_task_words but this term is not exemptible'
                    hits.append(h)
        hits.sort(key=lambda h: (h['start'], h['label']))
        exempted.sort(key=lambda h: (h['start'], h['label']))
        return {'ok': not hits and not errors, 'hits': hits, 'exempted': exempted, 'errors': errors}


def strip_hint(text):
    """In --hint mode the hint sentence must be the last line, exactly once; it alone is removed before linting."""
    lines = text.split('\n')
    n = sum(1 for l in lines if l == HINT_SENTENCE)
    if n != 1:
        return text, 'hint sentence must occur exactly once (found %d)' % n
    if lines[-1] != HINT_SENTENCE:
        return text, 'hint sentence must be the last line, right after the Requirements list'
    return '\n'.join(lines[:-1]), None


def _report(name, res):
    out = []
    for h in res['hits']:
        out.append('HIT %s line %d [%s] %r%s' % (name, h['line'], h['label'], h['match'],
                                                (' (' + h['note'] + ')') if 'note' in h else ''))
    for h in res['exempted']:
        out.append('EXEMPT %s line %d [%s] %r via allowed word %r' % (name, h['line'], h['label'], h['match'],
                                                                     h['allowed_word']))
    for e in res['errors']:
        out.append('ERROR %s %s' % (name, e))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description='Banned-word lint (FULL_PREREG section 5).')
    ap.add_argument('files', nargs='*', help='prompt files')
    ap.add_argument('--study', default=STUDY)
    ap.add_argument('--pkg', help='lint the rendered prompts of tasks/<pkg>/*/task.json with their allowed words')
    ap.add_argument('--text', action='append', default=[], help='lint a literal string (repeatable)')
    ap.add_argument('--hint', action='store_true', help='ablation prompts: only the hint sentence is exempt')
    ap.add_argument('--allowed', action='append', default=[], help='allowed word for --text/files (repeatable)')
    ap.add_argument('--list', default=DEFAULT_LIST)
    ap.add_argument('--option-names', default=None)
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    opt = a.option_names or os.path.join(a.study, 'envs', 'pandas_option_names.txt')
    try:
        linter = Linter(a.list, opt)
    except LintSetupError as e:
        print('LINT SETUP ERROR:', e, file=sys.stderr)
        return 2
    items = []
    for f in a.files:
        items.append((f, _slurp(f, encoding='utf-8'), a.allowed))
    for i, t in enumerate(a.text):
        items.append(('text%d' % (i + 1), t, a.allowed))
    if a.pkg:
        for p in sorted(glob.glob(os.path.join(a.study, 'tasks', a.pkg, '*', 'task.json'))):
            t = _jload(p, encoding='utf-8')
            items.append((t.get('id', p), render(t, hint=a.hint), t.get('allowed_task_words') or []))
    if not items:
        ap.error('nothing to lint')
    report, bad, n_exempt = {}, 0, 0
    lines = []
    for name, text, allowed in items:
        res = linter.lint(text, allowed, hint=a.hint)
        report[name] = res
        bad += 0 if res['ok'] else 1
        n_exempt += len(res['exempted'])
        lines += _report(name, res)
    if a.json:
        print(json.dumps({'n': len(items), 'failed': bad, 'exempted': n_exempt, 'items': report}, indent=1))
    else:
        for l in lines:
            print(l)
        print('linted %d prompt(s): %d failed, %d exempted hit(s)%s' % (len(items), bad, n_exempt,
                                                                       ' (hint mode)' if a.hint else ''))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
