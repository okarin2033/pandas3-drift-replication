# Written 2026-11-11 by pkg:MECH_B (STAGE2 T2, package MECH_B). Status: prepared.
# Writes the tiny, synthetic CSV inputs of the MECH_B confirmation programs (catalogue ids G01-G08, R01-R07, N01-N07,
# I01-I06, X01-X02) into mechanisms/confirm/data/<id>/. Standard library only, fixed seed, byte-identical on re-run.
# Usage (from the study folder): python3 -I -B mechanisms/confirm/make_data_B.py
import csv
import io
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
SEED = 20261111


def write(cid, name, header, rows):
    d = os.path.join(DATA, cid)
    os.makedirs(d, exist_ok=True)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator='\n')
    w.writerow(header)
    for r in rows:
        w.writerow(['' if v is None else v for v in r])
    with open(os.path.join(d, name), 'w', encoding='utf-8', newline='') as f:
        f.write(buf.getvalue())


def main():
    rng = random.Random(SEED)

    # ---- QF4_GROUPBY
    # G01: ages with no one in the lowest bin and none in 45-59 (empty categories after pd.cut)
    ages = [22, 25, 27, 31, 33, 38, 41, 44, 62, 66, 70, 29]
    write('G01', 'customers.csv', ['customer_id', 'age', 'monthly_spend'],
          [[i + 1, a, round(20 + 3.5 * i, 2)] for i, a in enumerate(ages)])
    # G02: two keys; key1 will get an unused category 'west'
    rows = [['north', 'a', 5], ['north', 'b', 7], ['south', 'a', 3], ['north', 'a', 2], ['south', 'a', 4]]
    write('G02', 'sales.csv', ['region', 'channel', 'units'], rows)
    # G03: numeric grouping key
    rows = [[101, 2, 19.5], [102, 1, 5.0], [101, 3, 7.25], [103, 4, 12.0], [102, 2, 8.5]]
    write('G03', 'orders.csv', ['customer_id', 'quantity', 'amount'], rows)
    # G04: city names with mixed case
    rows = [['paris', 10.0], ['Paris', 5.5], ['LYON', 3.0], ['lyon', 4.0], ['nice', 2.5]]
    write('G04', 'orders.csv', ['city', 'amount'], rows)
    # G05: per-plan monthly spend
    rows = [['basic', 10.0], ['basic', 12.0], ['basic', 17.0], ['pro', 30.0], ['pro', 45.0], ['pro', 33.0], ['pro', 40.0]]
    write('G05', 'customers.csv', ['plan', 'monthly_spend'], rows)
    # G06: iterate over groups of one key given as a list
    rows = [['basic', 10.0], ['pro', 30.0], ['basic', 12.5], ['team', 50.0], ['pro', 31.0]]
    write('G06', 'orders.csv', ['plan', 'amount'], rows)
    # G07 attempt a: mixed-magnitude amounts (500 rows); attempt b: cancelling large and small values
    rows = []
    for i in range(500):
        k = 'a' if i % 2 == 0 else 'b'
        x = round(rng.uniform(0, 1e9), 2) if i % 3 else round(rng.uniform(0, 1), 4)
        rows.append([k, x])
    write('G07', 'readings.csv', ['k', 'x'], rows)
    rows = [['a', 1e16], ['a', 1.0], ['a', 1.0], ['a', 1.0], ['a', 1.0], ['a', -1e16],
            ['b', 0.1], ['b', 0.2], ['b', 0.3]]
    write('G07', 'ledger.csv', ['k', 'x'], rows)
    # G08 attempt a: large integers per group; attempt b: dates with blanks per group
    rows = [['x', 5000000000000000000], ['x', 5000000000000000000], ['y', 7], ['y', 8]]
    write('G08', 'accounts.csv', ['k', 'balance'], rows)
    rows = [['x', None], ['x', None], ['y', '2024-03-01'], ['y', None], ['z', '2024-01-05'], ['z', '2024-01-07']]
    write('G08', 'events.csv', ['k', 'when'], rows)

    # ---- QF5_ORDER
    # R01: two date-indexed tables, neither sorted, partly overlapping dates
    write('R01', 'left.csv', ['date', 'value'], [['2024-01-03', 1], ['2024-01-01', 2], ['2024-01-02', 3]])
    write('R01', 'right.csv', ['date', 'value'], [['2024-01-04', 10], ['2024-01-02', 20], ['2024-01-05', 30]])
    # R02: first-appearance order differs from sorted order
    rows = [['pro', 'oslo'], ['basic', 'rome'], ['pro', 'oslo'], ['team', 'bern'], ['basic', 'amsterdam'], ['basic', 'rome']]
    write('R02', 'customers.csv', ['plan', 'city'], rows)
    # R03 attempt a: ties at the top; attempt b: per-region ties, more rows
    rows = [[1, 50.0], [2, 80.0], [3, 80.0], [4, 30.0], [5, 80.0], [6, 20.0], [7, 50.0], [8, 80.0], [9, 10.0], [10, 50.0],
            [11, 80.0], [12, 5.0]]
    write('R03', 'orders.csv', ['order_id', 'amount'], rows)
    rows = []
    for i in range(60):
        rows.append([i + 1, ['north', 'south', 'east'][i % 3], float(rng.choice([10, 20, 20, 30, 30, 30]))])
    write('R03', 'regional.csv', ['order_id', 'region', 'amount'], rows)
    # R04: wide table with missing cells
    rows = [['ann', 7, None], ['bob', None, None], ['cy', 5, 9], ['dee', None, 4]]
    write('R04', 'scores.csv', ['student', 'math', 'art'], rows)
    # R05: one month with rows, one month with the header only
    write('R05', 'jan.csv', ['order_id', 'quantity', 'amount'], [[1, 2, 10.5], [2, 1, 3.0], [3, 5, 7.25]])
    write('R05', 'feb.csv', ['order_id', 'quantity', 'amount'], [])
    # R06 attempt a: amounts on quantile edges; attempt b: pivot_table with margins
    write('R06', 'orders.csv', ['order_id', 'amount'], [[i + 1, v] for i, v in enumerate([10, 20, 30, 40, 50, 60, 70, 80, 90])])
    rows = [['books', 'open', 10.0], ['books', 'closed', 5.0], ['toys', 'open', 7.0], ['toys', 'open', 3.0], ['games', 'closed', 4.0]]
    write('R06', 'tickets.csv', ['category', 'status', 'amount'], rows)
    # R07: integer keys on the left, text keys on the right
    write('R07', 'left.csv', ['key', 'x'], [[1, 1.5], [2, 2.5], [3, 3.5]])
    write('R07', 'right.csv', ['key', 'y'], [['1', 'a'], ['x2', 'b'], ['3', 'c']])

    # ---- QF6_NA_DTYPE
    rows = [[1, 'oslo', 'shipped'], [2, 'rome', 'pending'], [3, 'oslo', 'shipped'], [4, 'rome', 'shipped'], [5, 'bern', 'pending']]
    write('N01', 'orders.csv', ['order_id', 'city', 'status'], rows)
    write('N02', 'stores.csv', ['store', 'sales', 'visits'], [['s1', 0, 0], ['s2', 10, 0], ['s3', 5, 2], ['s4', 3, None], ['s5', 8, 4]])
    write('N03', 'items.csv', ['item', 'qty'], [['a', 3], ['b', 1], ['c', 4], ['d', 1], ['e', 5]])
    write('N04', 'orders.csv', ['order_id', 'qty'], [[1, 2], [2, 3], [3, 2], [4, 10], [5, 3], [6, 2]])
    write('N04', 'days.csv', ['order_id', 'day'], [[1, '2024-01-02'], [2, '2024-01-03'], [3, '2024-01-02'], [4, '2024-01-09']])
    write('N05', 'scores.csv', ['math', 'art'], [[7, 1], [None, 4], [3, None], [6, 5]])
    write('N06', 'values.csv', ['id', 'x'], [[1, 30], [2, None], [3, 10], [4, 20], [5, 10]])
    write('N07', 'grades.csv', ['student', 'grade'], [['ann', 'a'], ['bob', None], ['cy', 'b'], ['dee', 'a'], ['eve', None]])

    # ---- QF7_INDEX_REDUCE
    write('I01', 'orders.csv', ['quantity', 'amount'], [[2, 10.5], [1, 3.0], [5, 7.25]])
    rows = [[i + 1, round(5.5 + i, 1), 20 + (i * 7) % 40] for i in range(40)]
    write('I02', 'customers.csv', ['customer_id', 'monthly_spend', 'age'], rows)
    write('I03', 'people.csv', ['name', 'age'], [['ann', 31], ['bob', 45], ['cy', 28]])
    write('I03', 'seats.csv', ['seat', 'guest'], [['total', 'all'], ['2', 'bob'], ['0', 'ann'], ['1', 'cy']])
    write('I04', 'flags.csv', ['year', 'active', 'paid'], [[2019, True, False], [2021, True, True], [2022, False, True]])
    write('I05', 'items.csv', ['name', 'qty', 'old_code', 'new_code'], [['a', 2, 10, 10], ['b', 3, 20, 21], ['c', 4, 30, 30]])
    write('I06', 'rows.csv', ['flag', 'count'], [[True, 3], [False, 5], [True, 0]])
    write('I06', 'big.csv', ['flag', 'count'], [[True, 9223372036854775807], [False, 9223372036854775806], [True, 1]])

    # ---- QF8_NUMERIC
    xs = [round(rng.uniform(10, 20), 3) for _ in range(20)]
    write('X01', 'series.csv', ['day', 'x'], [[i + 1, x] for i, x in enumerate(xs)])
    rows = [['a', 1.0], ['a', 2.0], ['a', 3.0], ['a', 4.0], ['b', 10.0], ['b', 30.0], ['c', 5.0], ['c', 6.0], ['c', 7.0]]
    write('X02', 'scores.csv', ['k', 'x'], rows)
    write('X02', 'primary.csv', ['id', 'big'], [[1, 9007199254740993], [2, None], [3, 123]])
    write('X02', 'backup.csv', ['id', 'big'], [[1, 1], [2, 9007199254740995], [4, 5]])


if __name__ == '__main__':
    main()
