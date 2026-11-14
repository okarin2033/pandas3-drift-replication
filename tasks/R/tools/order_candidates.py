"""Order the fetched stratum-R frame (FULL_PREREG section 4.3: score descending, ties by earlier creation) and apply the two
mechanical criteria: (1) content_license == 'CC BY-SA 4.0' (null or other values excluded) and (3) not one of the pilot's 12 questions.
Criterion (2), the four exclusion rules of the pilot's SELECTION.md, needs a reader and is recorded in screening.tsv by hand.

Written 2026-11-11 by pkg:R_BUILD. Reads the raw pages from --raw (the local-only folder; read with python3 -I, data only).
Writes:
  --study-out <S>/tasks/R/candidates.tsv : rank, question_id, url, creation_utc, score, licence, crit1, crit3 (no question text)
  --local-out <LOCAL>/tasks_R/reading_digest.txt : the same rows with title, tags and the body as plain text, for the reader
    (third-party text: local-only).
Usage: python3 -I -B order_candidates.py --raw <dir> --study-out <file> --local-out <file>
"""
import html, json, re, sys
from datetime import datetime, timezone

PILOT_12 = {79892823, 79911487, 79996919, 79939849, 79927393, 79937863, 79966342, 79890933, 79942986, 79950925, 79982061, 79899547}


def arg(k):
    return sys.argv[sys.argv.index(k) + 1]


def plain(body):
    t = re.sub(r'<pre[^>]*><code>', '\n[code]\n', body)
    t = re.sub(r'</code></pre>', '\n[/code]\n', t)
    t = re.sub(r'<[^>]+>', '', t)
    return html.unescape(t).strip()


def main():
    raw = arg('--raw')
    qs = []
    for p in ('questions_p1.json', 'questions_p2.json'):
        qs += json.load(open(raw + '/' + p, encoding='utf-8'))['items']
    assert len({q['question_id'] for q in qs}) == len(qs)
    qs.sort(key=lambda q: (-q['score'], q['creation_date'], q['question_id']))
    rows, dig = [], []
    for i, q in enumerate(qs, 1):
        lic = q.get('content_license')
        c1 = 'pass' if lic == 'CC BY-SA 4.0' else 'fail'
        c3 = 'fail' if q['question_id'] in PILOT_12 else 'pass'
        cd = datetime.fromtimestamp(q['creation_date'], timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        rows.append([str(i), str(q['question_id']), 'https://stackoverflow.com/q/%d' % q['question_id'], cd, str(q['score']),
                     lic if lic else 'null', c1, c3])
        dig.append('=' * 100 + '\n#%d  id %d  score %d  created %s  licence %s  closed %s  crit1 %s crit3 %s\nTITLE: %s\nTAGS: %s\n%s\n' % (
            i, q['question_id'], q['score'], cd, lic, q.get('closed_reason'), c1, c3, html.unescape(q['title']),
            ' '.join(q['tags']), plain(q['body'])))
    with open(arg('--study-out'), 'w', encoding='utf-8') as f:
        f.write('rank\tquestion_id\turl\tcreation_utc\tscore\tlicence\tcrit1_licence\tcrit3_not_pilot\n')
        for r in rows:
            f.write('\t'.join(r) + '\n')
    with open(arg('--local-out'), 'w', encoding='utf-8') as f:
        f.write(''.join(dig))
    print('ordered %d; crit1 pass %d; crit3 fail %d' % (len(rows), sum(r[6] == 'pass' for r in rows), sum(r[7] == 'fail' for r in rows)))


if __name__ == '__main__':
    main()
