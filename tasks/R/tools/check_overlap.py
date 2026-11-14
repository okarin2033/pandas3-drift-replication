"""No-copy check for stratum R (TASKS_RA brief step R3): no 8-word sequence (lower-cased [a-z0-9]+ tokens) of an R task text, intent
summary or column-map value may occur in the title or body (text and code) of ANY fetched question. Written 2026-11-11 by pkg:R_BUILD.
Reads tasks/R/INTENTS.tsv and the raw pages under --raw (local-only folder; data only). Prints counts and matching task ids only, never
question text. Usage: python3 -I -B check_overlap.py --raw <LOCAL>/tasks_R/downloads [--out FILE]
"""
import csv, html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
N = 8


def grams(text):
    t = re.findall(r'[a-z0-9]+', text.lower())
    return {tuple(t[i:i + N]) for i in range(len(t) - N + 1)}


def main():
    raw = sys.argv[sys.argv.index('--raw') + 1]
    qs = []
    for p in ('questions_p1.json', 'questions_p2.json'):
        qs += json.load(open(os.path.join(raw, p), encoding='utf-8'))['items']
    qgrams = set()
    for q in qs:
        qgrams |= grams(html.unescape(q['title']) + ' ' + html.unescape(re.sub(r'<[^>]+>', ' ', q['body'])))
    lines = ['# check_overlap.py: 8-word overlap of R texts with %d fetched questions (titles and bodies)' % len(qs)]
    bad = 0
    with open(os.path.join(PKG, 'INTENTS.tsv'), encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            parts = [r['task_text'], r['intent_summary']] + list(json.loads(r['column_map']).values())
            hit = sum(len(grams(p) & qgrams) for p in parts)
            bad += bool(hit)
            lines.append('%s\tso_question_id %s\tshared 8-grams: %d' % (r['id'], r['so_question_id'], hit))
    lines.append('tasks with any shared 8-gram: %d' % bad)
    text = '\n'.join(lines) + '\n'
    if '--out' in sys.argv:
        open(sys.argv[sys.argv.index('--out') + 1], 'w', encoding='utf-8').write(text)
    print(text)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
