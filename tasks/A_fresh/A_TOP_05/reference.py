# Reference solution for A_TOP_05 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

st = pd.read_csv('stations.csv', dtype=str, keep_default_na=False)
rows = sorted((d.strip().lower(), -int(k), o, c, n, int(k)) for c, n, d, k, o in
              zip(st['station_code'].tolist(), st['station_name'].tolist(), st['district'].tolist(), st['docks'].tolist(),
                  st['opened_on'].tolist()))
seen, keep = {}, []
for r in rows:
    if seen.get(r[0], 0) < 2:
        keep.append(r)
        seen[r[0]] = seen.get(r[0], 0) + 1
result = pd.DataFrame({'district': [r[0] for r in keep], 'station_code': [r[3] for r in keep],
                       'station_name': [r[4] for r in keep], 'docks': [r[5] for r in keep]})
