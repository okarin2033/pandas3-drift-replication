# Design-implied H4 value (FULL_PREREG section 7, H4 paragraph (iii); STAGE2 T5.8/T8): the share of drift with no pandas
# warning on 2.3.3 that the stratum-M design implies BEFORE any generation, from the measured per-row warning status of
# T2 weighted by the M quotas. Written 2026-11-11 by pkg:HSTAT_GEN. Status: prepared.
#
# usage: python3 -I harness/h4_design.py --status mechanisms/confirm/status.tsv --quota mechanisms/confirm/quota_allocation.tsv
#            [--out logs/hstat/h4_design.json]
# NOT run on study files in the build stage (the final status.tsv / quota_allocation.tsv exist only after FIX); it is run
# at T8 (freeze) and its value is recorded as a freeze item (section 14). Tested on a synthetic status file.
#
# Definition (an assumption, stated): every M task whose catalogue row drifts on E1 (status column drift_E1 = yes) is one
# unit of drift; a unit is "warned" when the row's measured E0a warning status (warn_233_measured, section 3 definition)
# is yes. design-implied H4(M) = (sum of n_tasks over rows with drift_E1 = yes and warn_233_measured = no) / (sum of
# n_tasks over rows with drift_E1 = yes and warn_233_measured in {yes, no}). Rows whose warning status is 'na' are left out
# of both sums and listed. The same value is given under the pilot warning definition (warn_233_pilotdef) and per family.
# It is NOT a prediction of the observed M value: programs differ from the naive solution, and models drift on a task only
# when they use the invited idiom (the observed value is reported next to it, T11).
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def read_tsv(path):
    with open(path, encoding='utf-8') as f:
        lines = [ln.rstrip('\n') for ln in f if ln.strip()]
    head = lines[0].split('\t')
    return [dict(zip(head, ln.split('\t'))) for ln in lines[1:]]


def design_h4(status_rows, quota_rows, warn_col='warn_233_measured', drift_col='drift_E1'):
    status = {r['id']: r for r in status_rows}
    per_family, listed = {}, {'warn_na': [], 'drift_E2_only': [], 'not_drifting_E1': [], 'unconfirmed': []}
    for q in quota_rows:
        rid, fam, n = q['row_id'], q['family'], int(q['n_tasks'])
        if rid == 'NONE' or n == 0:
            continue
        if rid not in status:
            raise ValueError('quota row %s (family %s) has no line in the status file' % (rid, fam))
        s = status[rid]
        f = per_family.setdefault(fam, {'tasks': 0, 'drift_units': 0, 'unwarned_units': 0, 'unknown_units': 0})
        f['tasks'] += n
        if s.get('status') != 'CONFIRMED':
            listed['unconfirmed'].append(rid)
            continue
        if s.get(drift_col) != 'yes':
            (listed['drift_E2_only'] if s.get('drift_E2') == 'yes' else listed['not_drifting_E1']).append(rid)
            continue
        w = s.get(warn_col)
        if w == 'na' or w not in ('yes', 'no'):
            f['unknown_units'] += n
            listed['warn_na'].append(rid)
            continue
        f['drift_units'] += n
        if w == 'no':
            f['unwarned_units'] += n
    tot_d = sum(f['drift_units'] for f in per_family.values())
    tot_u = sum(f['unwarned_units'] for f in per_family.values())
    for f in per_family.values():
        f['share_unwarned'] = (f['unwarned_units'] / f['drift_units']) if f['drift_units'] else None
    return {'definition': warn_col, 'drift_column': drift_col, 'drift_units': tot_d, 'unwarned_units': tot_u,
            'design_implied_H4_M': (tot_u / tot_d) if tot_d else None, 'per_family': per_family, 'listed': listed}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--status', required=True)
    ap.add_argument('--quota', required=True)
    ap.add_argument('--out', default=None)
    a = ap.parse_args(argv)
    st, qu = read_tsv(a.status), read_tsv(a.quota)
    res = {'prereg_definition': design_h4(st, qu, 'warn_233_measured'),
           'pilot_definition_sensitivity': design_h4(st, qu, 'warn_233_pilotdef'),
           'target_E2_sensitivity': design_h4(st, qu, 'warn_233_measured', 'drift_E2'),
           'status_file': a.status, 'quota_file': a.quota,
           'note': 'design-implied value for stratum M, assumption of one unit of drift per task on a drifting row; '
                   'recorded at the freeze (section 14) and reported next to the observed M value (section 7)'}
    v = res['prereg_definition']['design_implied_H4_M']
    print('design-implied H4 (stratum M, E1, section 3 warning definition): %s (%d of %d drift units unwarned)' % (
        'n/a' if v is None else '%.4f' % v, res['prereg_definition']['unwarned_units'], res['prereg_definition']['drift_units']))
    for fam, f in res['prereg_definition']['per_family'].items():
        print('  %-18s tasks %2d drift units %2d unwarned %2d' % (fam, f['tasks'], f['drift_units'], f['unwarned_units']))
    for k, lst in res['prereg_definition']['listed'].items():
        if lst:
            print('  %s: %s' % (k, ','.join(lst)))
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, 'w', encoding='utf-8') as f:
            json.dump(res, f, indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
