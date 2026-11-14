"""Write the stratum-R selection log (tasks/R/screening.tsv, tasks/R/SELECTION.md), the fetch record (tasks/R/fetch_log.json, URLs,
times, sizes, sha256 and quota fields only) and tasks/R/BODIES_SHA256.tsv. Written 2026-11-11 by pkg:R_BUILD.

DECISIONS holds the reader's screening decision for every candidate that passed the two mechanical criteria (licence, not a pilot
question), in the registered order, with the exclusion rule(s) of the pilot's SELECTION.md (1 = about versions, upgrades, warnings or
copy semantics / mentions their vocabulary; 2 = mainly about an error message or exception, or the title names an error or exception;
3 = not pandas data wrangling; 4 = cannot be expressed on the general fixture files without a new data source). The first listed rule is
the deciding one (rules checked in the order 1-4); further rules that also apply are listed. Reasons are our own short words; no question
text is stored. Reads the raw pages from --raw (local-only folder) only to hash the bodies.
Usage: python3 -I -B write_selection.py --raw <LOCAL>/tasks_R/downloads
"""
import csv, hashlib, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
KEEP = 'KEEP'
DECISIONS = {
 3: ([4], 'needs data sets whose column headers differ in capital letters; the general fixtures have one fixed lower-case header '
          '(the pilot, on its own fixtures, had listed this question as eligible)'),
 6: (KEEP, 'as-of alignment of two time-stamped tables'),
 7: ([3], 'database query through a driver'),
 8: ([1, 4], 'mentions FutureWarning and deprecation; sparse arrays'),
 10: (KEEP, 'sums over consecutive non-overlapping blocks'),
 12: ([3], 'plotting (box plots)'),
 13: ([1, 3], 'behaviour under pandas v2 and v3; xarray'),
 14: (KEEP, 'replacing codes through a lookup table'),
 15: ([3], 'linear algebra with numpy/sympy'),
 16: ([3], 'conversion from a dataset library'),
 17: ([3], 'database fetch speed'),
 19: ([2, 3], 'title names an exception; plotting and model fitting'),
 20: ([1], 'about an upgrade of pandas (versions named)'),
 21: ([1], 'uses the phrase new behavior; version printed'),
 22: ([4], 'needs a CSV whose records are broken over several lines'),
 23: ([1], 'about SettingWithCopyWarning'),
 24: ([4], 'needs timestamps with several UTC offsets in one column; fixture timestamps carry no zone'),
 25: ([3], 'web API and JSON serialisation'),
 26: ([4], 'needs two tables that share a two-column key'),
 27: ([4], 'needs a numeric coordinate axis with uneven spacing next to several integer columns; no fixture file has one'),
 30: ([3], 'geospatial library'),
 32: ([3], 'extension accessor API, not a wrangling task'),
 33: ([3], 'plotting'),
 34: ([1], 'update through a slice (copy semantics) and a warning'),
 35: ([2], 'title names an exception'),
 36: ([3], 'regression fit and plotting'),
 37: ([4], 'needs repeated ids with a name and two whole-number measures in one file; no fixture file has an id, a text column and '
           'two whole-number columns together'),
 39: ([3], 'speed of a custom window function as the main point; statsmodels'),
 40: ([3], 'plotting'),
 41: ([4], 'needs heights written as feet and inches text'),
 43: ([3], 'validation library'),
 44: ([3], 'PDB file format through a helper library'),
 46: ([4], 'needs a wide per-year table in which two named rows describe one entity'),
 47: ([3], 'LaTeX output styling'),
 48: ([2, 3], 'title names an error; BI tool'),
 49: ([4], 'needs repeated entities with several ordinal status columns and a severity order'),
 50: ([3], 'database API'),
 51: ([4], 'needs a table with a fixed number of filled cells per row spread over columns'),
 52: (KEEP, 'shifting the time of rows on chosen dates'),
 53: ([1, 3], 'names pandas 2.3; display of objects'),
 54: ([4], 'needs nested dictionaries'),
 55: ([2, 3], 'mainly about an exception; market-data download'),
 56: ([1, 2], 'names pandas 3; title names an error'),
 57: ([3], 'combining spreadsheet sheets'),
 58: ([3], 'map plotting'),
 59: ([1], 'copy-on-write; pandas 2.3.3 named'),
 60: ([3], 'plotting dashboard'),
 61: ([3], 'JSON normalisation (format other than CSV)'),
 65: ([3], 'measurement file format library'),
 67: ([2, 3], 'title names an exception; distributed computing'),
 68: ([2, 4], 'mainly about an exception in index slicing; needs a three-level hierarchical index'),
 69: ([3], 'styled table image and fonts'),
 70: ([4, 3], 'needs an external data set from a URL'),
 73: ([1, 4], 'reference versus copy of frames inside a loop; needs comma-separated list text'),
 74: ([3], 'database load inside a workflow tool'),
 76: ([4], 'needs X-Y coordinates and points of interest'),
 77: ([4], 'needs list-valued cells'),
 79: ([3], 'Spark and JSON'),
 80: ([3], 'semantics of apply/transform with list-likes, not a wrangling task'),
 81: ([3], 'spreadsheet and web automation'),
 82: ([3], 'constructor semantics, not a wrangling task'),
 83: ([4], 'needs two tables that share a two-column key'),
 84: ([3], 'report and plotting pipeline and survey practice as the main point (spreadsheet upload)'),
 85: ([3], 'model explanation library'),
 87: ([4], 'needs numeric column labels to stack and filter on'),
 88: ([1, 2, 3], 'names pandas 2.0.3; title names an error; HTML output'),
 89: ([3], 'machine-learning pipeline'),
 90: ([3], 'machine-learning pipeline'),
 91: ([4], 'needs ranked ballots of varying length'),
 92: ([4], 'needs many meter files with different units and rates'),
 93: (KEEP, 'long-to-wide with one column per category, values stacked from the top'),
 94: ([1, 3], 'names pandas 2.1.4; asynchronous HTTP requests'),
 95: ([1], 'chained assignment under pandas 3.0'),
 96: (KEEP, 'relative change against each of the previous rows'),
 97: ([3], 'measurement file format'),
 98: (KEEP, 'rolling bitwise AND'),
 99: ([3], 'measurement file format'),
 100: ([2, 3], 'mainly about an import error; installation'),
 101: ([2], 'title names an exception'),
 102: ([3], 'web app reading a spreadsheet'),
 103: ([4], 'needs daily delta files of status changes'),
 104: ([3], 'workflow advice, not a wrangling task'),
 105: ([3], 'HTML parsing'),
 107: ([1, 3], 'a pandas UserWarning; database API'),
 108: ([3], 'spreadsheet versus text file handling'),
 109: (KEEP, 'detecting a two-row sequence of states'),
 110: ([3], 'tool recommendation'),
 112: ([3], 'XML reading'),
 113: (KEEP, 'total, row count and totals per identifier'),
 114: ([3], 'type hints'),
 115: ([3], 'web app display'),
 118: ([4], 'needs a series of files with the same layout'),
 119: ([3], 'database insertion'),
 120: ([3], 'plotting as the main point'),
 122: ([4], 'needs a list in which header rows and item rows alternate'),
 123: ([3], 'image and OCR'),
 124: ([3], 'installation and imports'),
 125: ([4], 'needs one file with several id and text grouping columns, dates and amounts; the general fixtures have no such file'),
 126: ([4], 'needs comma-separated gene lists'),
 127: ([3], 'API introspection'),
 128: ([1], 'names pandas 3.0'),
 133: ([4], 'same grouping needs as the question ranked 125'),
}


def main():
    raw = sys.argv[sys.argv.index('--raw') + 1]
    with open(os.path.join(PKG, 'candidates.tsv'), encoding='utf-8', newline='') as f:
        cand = list(csv.DictReader(f, delimiter='\t'))
    rid = {}
    for r in csv.DictReader(open(os.path.join(PKG, 'mapping.tsv'), encoding='utf-8', newline=''), delimiter='\t'):
        rid[r['so_question_id']] = r['id']
    rows, kept = [], []
    cnt = {'crit1_licence': 0, 'crit3_pilot': 0, 'rule1': 0, 'rule2': 0, 'rule3': 0, 'rule4': 0, 'kept': 0}
    for c in cand:
        rank = int(c['rank'])
        if c['crit1_licence'] != 'pass':
            dec, rule, why = 'skip', 'criterion 1', 'content_license null (not CC BY-SA 4.0)'
            cnt['crit1_licence'] += 1
        elif c['crit3_not_pilot'] != 'pass':
            dec, rule, why = 'skip', 'criterion 3', 'one of the pilot\'s 12 questions'
            cnt['crit3_pilot'] += 1
        else:
            d = DECISIONS[rank]
            if d[0] == KEEP:
                dec, rule, why = 'keep', '', d[1]
                cnt['kept'] += 1
                kept.append((rid[c['question_id']], c))
            else:
                dec = 'skip'
                rule = 'criterion 2, rule %d' % d[0][0] + ('' if len(d[0]) == 1 else ' (also rule %s)' % ', '.join(map(str, d[0][1:])))
                why = d[1]
                cnt['rule%d' % d[0][0]] += 1
        rows.append([c['rank'], c['question_id'], c['url'], c['creation_utc'], c['score'], c['licence'], dec,
                     rid.get(c['question_id'], ''), rule, why])
    assert len(set(DECISIONS) - {int(c['rank']) for c in cand}) == 0
    assert len(rows) == 133 and cnt['kept'] == len(kept) == len(rid)
    with open(os.path.join(PKG, 'screening.tsv'), 'w', encoding='utf-8') as f:
        f.write('rank\tquestion_id\turl\tcreation_utc\tscore\tlicence\tdecision\tR_id\trule\treason\n')
        for r in rows:
            f.write('\t'.join(r) + '\n')
    # fetch record (no question text)
    log = json.load(open(os.path.join(raw, 'fetch_log.json'), encoding='utf-8'))
    with open(os.path.join(PKG, 'fetch_log.json'), 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=1)
    qs = []
    for p in ('questions_p1.json', 'questions_p2.json'):
        qs += json.load(open(os.path.join(raw, p), encoding='utf-8'))['items']
    with open(os.path.join(PKG, 'BODIES_SHA256.tsv'), 'w', encoding='utf-8') as f:
        f.write('# sha256 of each fetched question body (UTF-8, as returned by filter=withbody) and of each raw page; the texts are kept '
                'only in the local-only folder <LOCAL>/tasks_R/downloads/ (never in the study folder)\n')
        f.write('kind\tquestion_id_or_file\tsha256\n')
        for e in log['log']:
            f.write('page\t%s\t%s\n' % (e['file'], e['sha256']))
        for q in sorted(qs, key=lambda q: q['question_id']):
            f.write('body\t%d\t%s\n' % (q['question_id'], hashlib.sha256(q['body'].encode('utf-8')).hexdigest()))
    json.dump(cnt, open(os.path.join(PKG, 'logs', 'selection_counts.json'), 'w'), indent=1)
    print(json.dumps(cnt), [k for k, _ in kept])


if __name__ == '__main__':
    main()
