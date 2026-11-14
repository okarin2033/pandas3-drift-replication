"""Builds mechanisms/confirm/status_A.tsv from runs/_A/summary_all_2026-11-11.tsv (harness outputs) and the catalogue.
pkg:MECH_A, 2026-11-11. Status rule (FULL_PREREG 4.3, STAGE2 T2.3): CONFIRMED if any attempt drifts on E0a~E1 or E0a~E2
(drift = ORDER_DRIFT, DTYPE_DRIFT, VALUE_DRIFT, NO_RESULT under the confirm card); a second attempt is written only when the first
did not drift; NOT_REPRODUCED after two attempts without such drift; L rows: LOUD_CONFIRMED if E1 is LOUD.
The deciding attempt is the first attempt that drifted (or, for NOT_REPRODUCED, the last attempt); never chosen by drift size."""
import csv, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
CONF = os.path.abspath(os.path.join(HERE, '..', '..'))
CAT = os.path.join(CONF, '..', 'catalogue.tsv')
SUM = os.path.join(HERE, 'summary_all_2026-11-11.tsv')
IDS = 'S01 S02 S03 S04 S05 S06 O01 D01 D02 D03 D04 D05 D06 D07 D08 D09 D10 C01 C02 C03 C04 C05 C06 L01 L02 L03 L04 L05 L06'.split()
PRIOR_YES = {'YES_DEFAULT', 'BY_ENFORCEMENT'}
PRIOR_NO = {'OPT_IN', 'NO_NOTE', 'NOT_STATED'}

NOTES = {  # hand-written by pkg:MECH_A from the run outputs in runs/_A/summary_all_2026-11-11.txt
 'S01': 'Text columns selected by dtype == object are cleaned on 2.3.3 (2 city groups) and skipped on 3.x (6 raw groups).',
 'S02': 'None written into the text column stays None on 2.3.3 and is mapped to "unknown"; on 3.x it is NaN, so the "unknown" group disappears and the missing group grows.',
 'S03': 'astype(str) gives a "Nan" group on 2.3.3; on 3.x the missing values stay missing and drop out of value_counts.',
 'S04': 'NOT_REPRODUCED in two attempts: attempt 1 (np.where on .values == "shipped") and attempt 2 (NumPy missing idiom values != values) both gave equal values on E1, E2, E3, E4 (DTYPE_ONLY: index dtype object vs str only).',
 'S05': 'NOT_REPRODUCED in two attempts: attempt 1 (str.extract r"^(\\w+)") and attempt 2 (str.contains r"^\\w+$") on accented names gave equal values on E1, E2 and also on E3/E4 (pyarrow); the catalogue expected a difference only on 3.0.x with pyarrow (E4), which would not confirm under 4.3 anyway.',
 'S06': 'Drift on E1 only (3.1.1): category labels of zero-padded codes become integers (00123 -> 123); E2 (3.0.6) identical, consistent with the catalogue "since 3.1.0".',
 'O01': 'to_json(orient="records") writes Decimal as a number on 2.3.3 and as text on 3.x ("1.25"); only the Decimal part of this composite row was tried.',
 'D01': 'astype("int64") // 10**9 of parsed dates gives Unix seconds on 2.3.3 and values 1000x smaller on 3.x (microsecond unit).',
 'D02': 'to_datetime(unit="s").astype("int64") gives ns on 2.3.3, us on 3.1.1 and s on 3.0.6: different values on both targets.',
 'D03': 'to_period("M").dt.end_time ends at .999999999 on 2.3.3 and .999999 on 3.x; the group-key labels differ.',
 'D04': 'date_range from date strings cast to int64: ns on 2.3.3, us on 3.x.',
 'D05': 'Attempt 1 (text of the column time zone) gave identical "US/Eastern" everywhere. Attempt 2 (to_pydatetime + timedelta(days=1) across a DST change) drifts: the 2.3.3 run keeps the pre-change UTC offset (09:00-05:00), the 3.x run gives the wall-clock offset (09:00-04:00). Decided by attempt 2.',
 'D06': 'Timestamp + offsets.Day(1) across DST: 2.3.3 adds 24 h (09:00 / 21:00 local), 3.x keeps the wall-clock time (08:00 / 22:00).',
 'D07': 'Attempt 1 (to_datetime(text, unit="s")) is LOUD on 3.x (DateParseError), not drift. Attempt 2 adds errors="coerce": 3.x returns all NaT, silent on the targets. 2.3.3 warns (FutureWarning) in both attempts, as the prior BY_ENFORCEMENT expects. Decided by attempt 2.',
 'D08': 'Drift on E1 only (3.1.1): select_dtypes("datetime64[ns]") selects no column, so dates are not reformatted; E2 (3.0.6) DTYPE_ONLY (same values), consistent with the catalogue "since 3.1.0".',
 'D09': 'Drift on E1 only: infer_freq gives QS-OCT on 2.3.3 and 3.0.6, QS-JAN on 3.1.1. Not silent: E1 emits a Pandas4Warning (infer_freq will return an offset) in the same run.',
 'D10': 'Positional [0] on to_pydatetime() after a sort gives the earliest login on 2.3.3 and label 0 on 3.1.1 (E1 drift). E2 (3.0.6) identical to 2.3.3 without a warning, although the catalogue says "since 3.0.0": the change was observed on 3.1.1 only. 2.3.3 warns (FutureWarning), as BY_ENFORCEMENT expects.',
 'C01': 'Chained assignment updates df on 2.3.3 (FutureWarning + SettingWithCopyWarning) and is lost on 3.x. Not silent on 3.x: E1 and E2 emit a pandas ChainedAssignmentError warning in the same run.',
 'C02': 'Chained inplace fillna updates df on 2.3.3 (FutureWarning) and is lost on 3.x. Not silent on 3.x: E1 and E2 emit a pandas ChainedAssignmentError warning in the same run.',
 'C03': 'Write through a column variable reaches df on 2.3.3 (sum 21.5) but not on 3.x (14.0), silent on the targets. 2.3.3 emits a SettingWithCopyWarning (a pandas warning, but not Future/Deprecation, so warn_233_measured = no under section 3; agrees with prior OPT_IN).',
 'C04': 'result = df.fillna(0, inplace=True) is None on 2.3.3 and the filled frame on 3.x (type drift).',
 'C05': 'astype(copy=False) shares data on 2.3.3 (write reaches df) and not on 3.x. Not silent: E1 and E2 emit a Pandas4Warning (copy keyword deprecated).',
 'C06': 'Attempt 1 (Index from df[col].to_numpy(), then write into the array) is LOUD on 3.x: the to_numpy() array is read-only ("assignment destination is read-only"), a copy-on-write effect, not the Index-copy mechanism. Attempt 2 uses an own NumPy array: 2.3.3 Index sees the in-place change, 3.x Index does not. Decided by attempt 2.',
 'L01': 'resample("M"): FutureWarning on 2.3.3; ValueError on E1 and E2.',
 'L02': 'fillna(method="ffill"): FutureWarning on 2.3.3; TypeError on E1 and E2.',
 'L03': 'to_numeric(errors="ignore"): FutureWarning on 2.3.3; ValueError on E1 and E2.',
 'L04': 'Setting a float into a text Series: no warning on 2.3.3 (object column accepts it); TypeError on E1 and E2. Prior NO_NOTE agrees.',
 'L05': 'applymap: FutureWarning on 2.3.3; AttributeError on E1 and E2.',
 'L06': 'groupby.apply reading the grouping column: FutureWarning on 2.3.3; KeyError on E1 and E2.',
}


def main():
    cat = {r['id']: r for r in csv.DictReader(open(CAT, encoding='utf-8'), delimiter='\t')}
    summ = {r['program']: r for r in csv.DictReader(open(SUM, encoding='utf-8'), delimiter='\t')}
    cols = ['id', 'family', 'scope', 'programs', 'attempts', 'drift_E1', 'drift_E2', 'warn_233_measured', 'warn_233_pilotdef',
            'warn_3x', 'loud', 'status', 'prior_py2x_warned', 'note', 'class_E1', 'class_E2']
    out = []
    for i in IDS:
        c = cat[i]
        att = [p for p in (i, i + '_b') if p in summ]
        for p in att:
            assert summ[p]['det_E0a_E0b'] == 'yes', p
        scope = c['scope']
        if scope == 'LOUD_CONTEXT':
            dec = summ[i]
            status = 'LOUD_CONFIRMED' if dec['loud_E1'] == 'yes' else 'NOT_REPRODUCED'
        else:
            drifting = [p for p in att if 'yes' in (summ[p]['drift_E0a~E1'], summ[p]['drift_E0a~E2'])]
            dec = summ[drifting[0]] if drifting else summ[att[-1]]
            status = 'CONFIRMED' if drifting else 'NOT_REPRODUCED'
            if status == 'NOT_REPRODUCED':
                assert len(att) == 2, i
        prior = c['py2x_warned']
        meas = dec['warn233_prereg']
        note = NOTES[i]
        disagree = (meas == 'yes' and prior in PRIOR_NO) or (meas == 'no' and prior in PRIOR_YES)
        if disagree:
            note = 'DISAGREES WITH PRIOR. ' + note
        out.append({'id': i, 'family': c['quota_family'] if scope == 'SILENT' else 'LOUD', 'scope': scope,
                    'programs': ';'.join(p + '.py' for p in att), 'attempts': str(len(att)),
                    'drift_E1': dec['drift_E0a~E1'], 'drift_E2': dec['drift_E0a~E2'],
                    'warn_233_measured': meas, 'warn_233_pilotdef': dec['warn233_pilot'], 'warn_3x': dec['warn3x_prereg'],
                    'loud': dec['loud_E1'], 'status': status, 'prior_py2x_warned': prior, 'note': note,
                    'class_E1': dec['class_E0a~E1'], 'class_E2': dec['class_E0a~E2']})
    with open(os.path.join(CONF, 'status_A.tsv'), 'w', encoding='utf-8', newline='') as f:
        f.write('\t'.join(cols) + '\n')
        for r in out:
            assert '\t' not in r['note']
            f.write('\t'.join(r[k] for k in cols) + '\n')
    fam = {}
    for r in out:
        if r['scope'] == 'SILENT':
            fam.setdefault(r['family'], [0, 0])
            fam[r['family']][1] += 1
            fam[r['family']][0] += r['status'] == 'CONFIRMED'
    for k, v in fam.items():
        print(k, 'confirmed', v[0], 'of', v[1])
    print('disagreements:', [r['id'] for r in out if r['note'].startswith('DISAGREES')])


if __name__ == '__main__':
    main()
