"""Stratum-R intents (STAGE2 T4.2 step R3; FULL_PREREG section 4.3 paraphrase rule). Written 2026-11-11 by pkg:R_BUILD; status: prepared.

Everything below is our own wording; no question text or code is copied (checked by check_overlap.py: no 8-word sequence shared with
any fetched question title or body). The column map follows the section 4.3 type table, read as recorded in tasks/R/SELECTION.md
section 3 (semantic type of each question column; files in the order of fixtures/descriptions.tsv; first file, or ordered pair of files,
that has every needed type and gives a non-degenerate answer; first unused column of the type in column order). Placeholder values of
a question are mapped by the same position rule (stated per task). Written BEFORE mechanisms/catalogue.tsv was opened.
Writes tasks/R/INTENTS.tsv. Usage: python3 -I -B tasks/R/tools/r_intents.py
"""
import csv, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)

INTENTS = [
 dict(id='R_01', qid=79883287, files=['GEN/riders.csv', 'GEN/stations.csv'],
      summary='Attach to every row of a first time-stamped table the value from a second time-stamped table whose time is the '
              'latest one at or before that row\'s time, keeping exactly the rows of the first table.',
      cmap={'first table: time': 'riders.csv:joined_on', 'first table: value carried along': 'riders.csv:birth_year',
            'second table: time': 'stations.csv:opened_on', 'second table: value attached': 'stations.csv:docks'},
      text='For every rider in riders.csv, find in stations.csv the station whose opened_on date is the latest one on or before '
           'the rider\'s joined_on date, and attach that station\'s docks to the rider. Keep exactly the riders\' rows, one per '
           'rider; a rider with an empty joined_on, or with no station opened on or before that date, gets an empty docks value. '
           '`result` should be a table with the columns joined_on, birth_year and docks.'),
 dict(id='R_02', qid=79949942, files=['GEN/riders.csv'],
      summary='Sum a column of whole numbers in consecutive, non-overlapping blocks of four values, one sum per block, the last '
              'block included.',
      cmap={'series of whole numbers': 'riders.csv:birth_year'},
      text='Cut the birth_year column of riders.csv, taken in file order, into consecutive blocks of four values (rows 1-4, rows '
           '5-8, and so on) and add up each block; an empty birth_year is left out of its block\'s sum. `result` should hold one '
           'sum per block (100 sums), in block order.'),
 dict(id='R_03', qid=80001493, files=['GEN/trips.csv', 'GEN/stations.csv'],
      summary='Replace the codes held in two columns of one table by the value that a second table gives for each code (code '
              'column to value column), leaving codes without a match as they are.',
      cmap={'first table: code column 1': 'trips.csv:start_station', 'first table: code column 2': 'trips.csv:end_station',
            'lookup table: code': 'stations.csv:station_code', 'lookup table: value': 'stations.csv:docks'},
      text='Use stations.csv as a lookup from station_code to docks and replace every station code in the start_station and '
           'end_station columns of trips.csv by the docks of that station; a code that does not appear in stations.csv stays as '
           'it is. `result` should be a table with the columns start_station and end_station, one row per trip.'),
 dict(id='R_04', qid=79879978, files=['GEN/trips.csv'],
      summary='For the rows that fall on two particular dates, move the recorded time back by one hour and leave all other rows '
              'unchanged.',
      cmap={'date': 'trips.csv:started_at (date part)', 'time of day': 'trips.csv:started_at (time part)',
            'the two dates to correct (2nd and 3rd date of the data)': '2025-09-02, 2025-09-03 (2nd and 3rd calendar day of trips.csv)'},
      text='In trips.csv, the started_at times of the trips that started on 2025-09-02 or on 2025-09-03 are one hour too late. '
           'Move those started_at values back by one hour and leave every other trip unchanged. `result` should be the corrected '
           'started_at column as timestamps, one value per trip in file order.'),
 dict(id='R_05', qid=79921372, files=['GEN/riders.csv'],
      summary='Turn a long table of category and value into a wide table with one column per category, each column listing that '
              'category\'s values from the top in their original order, shorter columns padded with missing values.',
      cmap={'category': 'riders.csv:home_district', 'value': 'riders.csv:birth_year'},
      text='Build a wide table from riders.csv with one column per home district (names trimmed and in lower case, columns in '
           'alphabetical order). Each column lists the birth_year values of that district\'s riders from the top, in file order: '
           'row 0 holds the district\'s first rider, row 1 its second, and so on. A rider with an empty birth_year keeps its '
           'place as an empty cell, and a district with fewer riders than the largest one is filled up with empty cells at the '
           'bottom. `result` should be that table, with as many rows as the largest district has riders.'),
 dict(id='R_06', qid=79925508, files=['GEN/riders.csv'],
      summary='For each row and for each of the N = 4 rows above it, compute the change of the current value relative to that '
              'earlier value as 1 minus earlier/current, in four new columns that are empty where there are not enough rows above.',
      cmap={'value column': 'riders.csv:birth_year', 'N': '4 (as in the question)'},
      text='Going down riders.csv in file order, add four columns change_1 to change_4 for every rider: change_k is 1 minus '
           '(the birth_year k rows above) divided by (this rider\'s birth_year). The first k riders have no change_k, and a value '
           'is empty when either birth_year involved is empty. `result` should be a table with the columns birth_year, change_1, '
           'change_2, change_3 and change_4, one row per rider in file order.'),
 dict(id='R_07', qid=79929046, files=['GEN/riders.csv'],
      summary='Over a column of whole numbers, compute the bitwise AND inside a rolling window of two consecutive values.',
      cmap={'series of whole numbers': 'riders.csv:birth_year', 'window size': '2 (as in the question)'},
      text='Going down riders.csv in file order, compute for each rider the bitwise AND of its birth_year and the birth_year of '
           'the rider just above it (a rolling window of two values). The first rider, and every rider where either of the two '
           'birth_year values is empty, gets an empty value. `result` should hold one value per rider, in file order.'),
 dict(id='R_08', qid=79960740, files=['GEN/riders.csv'],
      summary='In a column of text states, flag each row whose state is B while the row just before it has state A (a two-row '
              'sequence A then B).',
      cmap={'state column': 'riders.csv:home_district',
            'states A and B (placeholders)': 'A = riverbend, B = harbourside (first two distinct values in file order, compared '
                                             'without capital letters and stray spaces)'},
      text='Going down riders.csv in file order and comparing home_district values without regard to capital letters or '
           'surrounding spaces, mark every rider whose home_district is Harbourside while the rider just above has Riverbend. '
           '`result` should hold one True/False value per rider, in file order (False for the first rider).'),
 dict(id='R_09', qid=79968177, files=['GEN/trips.csv'],
      summary='From one table, compute the total of an amount column, the number of rows, and the total amount per identifier.',
      cmap={'amount': 'trips.csv:distance_km', 'identifier': 'trips.csv:rider_id',
            'file choice': 'riders.csv skipped: each rider_id occurs once there, so totals per identifier would be the values '
                           'themselves (degenerate)'},
      text='From trips.csv, compute the total of the distance_km column, the number of rows, and the total distance_km for each '
           'rider_id. `result` should be a dict with the keys "total", "row_count" and "per_rider", where "per_rider" holds one '
           'total per rider_id.'),
]


def main():
    out = os.path.join(PKG, 'INTENTS.tsv')
    with open(out, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
        w.writerow(['id', 'so_question_id', 'files', 'intent_summary', 'column_map', 'task_text'])
        for it in INTENTS:
            w.writerow([it['id'], it['qid'], ','.join(it['files']), it['summary'], json.dumps(it['cmap'], ensure_ascii=False),
                        it['text']])
    print('wrote %d intents to %s' % (len(INTENTS), os.path.relpath(out, os.path.dirname(os.path.dirname(PKG)))))


if __name__ == '__main__':
    main()
