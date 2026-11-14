# Prompt renderer for the full study (FULL_PREREG.md section 5). Standard library only.
# Written 2026-11-11 by pkg:SHARED. Conventions: conventions/CONVENTIONS.md section 6.
#
# usage:
#   python3 -I harness/render_prompts.py --pkg M1                 # tasks/M1/*/task.json -> tasks/M1/prompts/<id>.txt
#   python3 -I harness/render_prompts.py --pkg M1 --hint --out tasks/prompts_hint   # ablation prompts
#   python3 -I harness/render_prompts.py --task path/to/task.json [--task ...] --out DIR
#   python3 -I harness/render_prompts.py --pkg M1 --check          # verify existing prompt files, write nothing
#
# A prompt file holds exactly the user message: UTF-8, LF line ends, no trailing newline (as in the pilot).
import argparse, glob, json, os, sys


def _slurp(path, encoding='utf-8'):
    with open(path, encoding=encoding) as f:
        return f.read()


def _jload(path, encoding='utf-8'):
    with open(path, encoding=encoding) as f:
        return json.load(f)

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)

HEADER = 'You are given CSV file(s) in the current working directory:'
REQUIREMENTS = [
    '- Write a complete Python script that reads the file(s) from the current directory.',
    '- Use only pandas, numpy and the Python standard library.',
    '- Store the final answer in a top-level variable named `result`.',
    '- Reply with a single Python code block.',
]
HINT_SENTENCE = '- The script will run with the latest pandas 3 release.'


class RenderError(ValueError):
    pass


def file_line(f):
    """'- <file>: <description>' where <file> is the basename the program sees in its working directory."""
    path = f.get('path') if isinstance(f, dict) else None
    desc = f.get('description') if isinstance(f, dict) else None
    if not path or not isinstance(path, str):
        raise RenderError('file entry without path: %r' % (f,))
    if not desc or not isinstance(desc, str) or not desc.strip():
        raise RenderError('file %s has no description line' % path)
    if '\n' in desc or '\r' in desc:
        raise RenderError('description of %s must be one line' % path)
    return '- %s: %s' % (os.path.basename(path), desc.strip())


def render(task, hint=False):
    """Render the section-5 prompt of one task dict. hint=True adds only the ablation sentence after Requirements."""
    files = task.get('files') or []
    if not files:
        raise RenderError('%s: no files' % task.get('id'))
    names = [os.path.basename(f.get('path', '')) for f in files]
    if len(set(names)) != len(names):
        raise RenderError('%s: two files share a basename' % task.get('id'))
    text = task.get('task_text')
    if not text or not isinstance(text, str) or not text.strip():
        raise RenderError('%s: empty task_text' % task.get('id'))
    lines = [HEADER, '']
    lines += [file_line(f) for f in files]
    lines += ['', 'Task: ' + text.strip(), '', 'Requirements:']
    lines += REQUIREMENTS
    if hint:
        lines.append(HINT_SENTENCE)
    return '\n'.join(lines)


def load_task(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def pkg_task_paths(study, pkg):
    return sorted(glob.glob(os.path.join(study, 'tasks', pkg, '*', 'task.json')))


def write_prompt(out_dir, task_id, text):
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, task_id + '.txt')
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    os.replace(tmp, p)
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(description='Render section-5 prompts.')
    ap.add_argument('--study', default=STUDY, help='study folder (default: parent of harness/)')
    ap.add_argument('--pkg', help='package folder under tasks/ (M1, M2, R, A)')
    ap.add_argument('--task', action='append', default=[], help='explicit task.json path (repeatable)')
    ap.add_argument('--out', help='output folder (default tasks/<pkg>/prompts, or tasks/<pkg>/prompts_hint with --hint)')
    ap.add_argument('--hint', action='store_true', help='add the version-hint sentence (ablation only)')
    ap.add_argument('--only', help='file with task ids to render (one per line), e.g. tasks/ABLATION_SAMPLE.tsv col 2')
    ap.add_argument('--check', action='store_true', help='compare with existing files; write nothing')
    a = ap.parse_args(argv)
    paths = list(a.task)
    if a.pkg:
        paths += pkg_task_paths(a.study, a.pkg)
    if not paths:
        ap.error('no tasks: give --pkg or --task')
    out = a.out
    if out is None:
        if not a.pkg:
            ap.error('--out is required with --task')
        out = os.path.join(a.study, 'tasks', a.pkg, 'prompts_hint' if a.hint else 'prompts')
    elif not os.path.isabs(out):
        out = os.path.join(a.study, out)
    only = None
    if a.only:
        only = set()
        for line in _slurp(a.only, encoding='utf-8').splitlines(True):
            for tok in line.strip().split('\t'):
                if tok and not tok.startswith('#'):
                    only.add(tok)
    n, bad = 0, 0
    for p in paths:
        t = load_task(p)
        if only is not None and t.get('id') not in only:
            continue
        try:
            text = render(t, hint=a.hint)
        except RenderError as e:
            print('ERROR', p, e)
            bad += 1
            continue
        if a.check:
            q = os.path.join(out, t['id'] + '.txt')
            cur = _slurp(q, encoding='utf-8') if os.path.exists(q) else None
            if cur != text:
                print('MISMATCH', t['id'], q)
                bad += 1
        else:
            write_prompt(out, t['id'], text)
        n += 1
    print('%s %d prompt(s)%s; %d error(s)' % ('checked' if a.check else 'rendered', n,
                                              ' (hint)' if a.hint else '', bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
