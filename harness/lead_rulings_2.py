# Additions of the lead's rulings LR13 to LR22 to the analyzer (FULL_PREREG_AMENDMENT_11.md; LEAD_RULINGS_LR13-LR22_2026-11-12.md read
# with LEAD_RULINGS_PROPOSED_LR13plus_2026-11-12.md). Written 2026-11-12 (REPAIR6 step 1). Standard
# library only (+ the study's stats / analyze_full / lead_rulings / oracle).
#
# Nothing here changes the primary analysis: analyze_full.build_per_program, flatten, run_tests, summarize, the registered sensitivities,
# the LR2/LR3 additions (lead_rulings.py) and per_program.jsonl are untouched. analyze_full.main() calls compute_all() after
# lead_rulings.compute_all() and stores the result under the top-level key 'lead_ruling_additions_2' of summary.json (and writes
# lead_ruling_additions_2.md). Every sensitivity recomputes every confirmatory statistic of run_tests (H1, H2a, H2b, H3, H4 and the
# registered secondary statistics) on per-program rows rebuilt under its own reading, and counts the results (program x target pair)
# whose class differs from the primary analysis. Labels are exactly those of the rulings:
#  - LR13 (a) "added by lead ruling LR13 before any study generation": the pre-LR1 key rule (the sealed oracle copy
#            logs/repair5_2026-11-11/backup/oracle_before.py, checked against logs/repair6_2026-11-12/oracle_before_LR1.sha256) with the
#            current flags. The two oracles differ only in the order rule (applied only to order_significant cards), so only the programs
#            of flagged tasks are reclassified.
#  - LR13 (b) same label: the pre-LR1 key rule with the flags hashed before LR2 (tasks/FLAGS_BEFORE_LR2.tsv, existed_before_rulings = yes).
#  - LR14 "added by lead ruling LR14 before any study generation": the flags of tasks/FLAGS_BEFORE_LR2_3.tsv (all rows) with the
#            current oracle.
#  - LR16 (a) and (b) "added by lead ruling LR16 before any study generation": the oracle's LR16 switches (harness/oracle.py), with the
#            number of comparisons in which each case occurs, by model and family (M family code; R and A as their stratum).
#  - LR17 "added by lead ruling LR17 before any study generation": the flags of tasks/FLAGS_BEFORE_LR2.tsv for all 200 tasks (also the
#            existed_before_rulings = no rows); stratum R rates are given with the current flags and with these flags (RQ5).
#  - LR18 "added by lead ruling LR18 before any study generation": harm pre-labels (and the automatic-pre-label H5 table) under the
#            card notes sealed before the LR18 sweep (tasks/CARD_VARIANTS_BEFORE_LR18.json), next to those under the current cards.
#            REPAIR8 2026-11-13 (lead ruling LR26, LEAD_RULINGS_LR23-LR41_2026-11-13.md): the label stays; every report states the
#            scope in the ruling's words (SCOPE_LR26), next to the computed list of fields that differ.
#  - LR26 (REPAIR8 2026-11-13) "added analysis of lead ruling LR26, registered before any study generation and deciding nothing":
#            the H5 proportions (af.h5_tables, coded when a codes file is given, else the automatic pre-label basis) also without the
#            tasks whose acceptable_variants.notes differ from the LR18 snapshot, i.e. the tasks whose notes LR18 or LR25 changed.
#            REPAIR9 2026-11-13 (lead ruling LR48, LEAD_RULINGS_LR42-LR56_2026-11-13.md; deviation R9-5): a scope is stated by its
#            definition and its list, and the count is printed from the list. The LR18 report states the definition (SCOPE_LR48, which
#            replaces the words "the eight LR14 changes" of SCOPE_LR26) and prints the list of tasks whose pre-label fields differ from
#            the snapshot with its length (prelabel_fields_changed_tasks); the LR26 report leaves out the tasks whose notes OR intended
#            computation changed after the snapshot (notes_or_ic_changed_tasks; the intended computation of the snapshot is read from the
#            tasks.json whose sha256 the snapshot names as its source, LR18_SNAPSHOT_TASKS_FILE, checked before use).
#  - LR15: the number of name-only changes (index-level or column-axis names differ, no row moved, values equal; not drift) by model
#            and family (a reported count, not a sensitivity).
#  - LR22 (3): exclusions_table(): the outcome / exclusions table of each target pair with external-SIGKILL harness errors as their own
#            row (computed by analyze_full.main() always, also without sensitivities).
#  - T8 preparation 2026-11-13 (lead rulings LR42, LR61; deviation T8P-LR61-1 of deviations/T8PREP.md): every result reported here for
#            stratum R (H4_stratum_R_only of each alt_analysis; LR16 and LR15 counts of family R; LR17 RQ5 stratum R rates; LR18 and
#            LR26 H5 groups R and R+A) is also given without the tasks of tasks/RULED_FIDELITY_FAILS.tsv by harness/lr61_report.py
#            (key added_report_LR42_LR61 beside it); the results themselves are not changed.
#  - T8 apply 2 2026-11-13 (lead ruling LR70, LEAD_RULINGS_LR69-LR76_2026-11-13.md; deviation T8A2-LR70-1 of deviations/T8APPLY.md):
#            the H4 on R+A of each alt_analysis (LR13 a, LR13 b, LR14, LR16 a, LR16 b, LR17), with its companion and the R+A testability
#            count, is also given without the listed tasks (lead_rulings.added_h4_ra: one lr61_report.without_ruled call per sensitivity
#            and pair; key H4_RA_added_report_LR42_LR61), and one marked block follows each pair's table in lead_ruling_additions_2.md.
import collections
import copy
import csv
import hashlib
import json
import os
import sys
import types

import analyze_full as af
import lead_rulings as lr
import lr61_report as lr61

STUDY = os.path.dirname(af.HERE)
LABEL = {r: 'added by lead ruling %s before any study generation' % r for r in ('LR13', 'LR14', 'LR16', 'LR17', 'LR18')}
# REPAIR8 2026-11-13 (lead ruling LR26): the label of the LR18 sensitivity stays; its scope is stated in every report in these words.
# REPAIR9 2026-11-13: superseded in the reports by SCOPE_LR48 (lead ruling LR48 replaces the words "the eight LR14 changes"); kept as
# the record of the earlier words and no longer printed.
SCOPE_LR26 = ('it shows the effect of the eight LR14 changes on the automatic pre-labels, while the changes of notes act on the human '
              'coding (lead ruling LR26)')
LABEL['LR26'] = 'added analysis of lead ruling LR26, registered before any study generation and deciding nothing'
# REPAIR9 2026-11-13 (lead ruling LR48): the scope by its definition; the list and its length are printed next to it in every report.
SCOPE_LR48 = ('it shows the effect, on the automatic pre-labels, of every difference in pre-label fields between the LR18 snapshot and '
              'the frozen cards (the tasks are listed below with their number), while the changes of notes act on the human coding '
              '(lead rulings LR26, LR48)')
DEFINITION_LR48_H5 = ('tasks whose acceptable_variants.notes or intended_computation differ from the LR18 snapshot (lead rulings '
                      'LR26, LR48)')
LR18_SNAPSHOT_TASKS_FILE = os.path.join(STUDY, 'logs', 'repair6_step3_2026-11-12', 'backup', 'tasks.json')
ORACLE_PRE_LR1 = os.path.join(STUDY, 'logs', 'repair5_2026-11-11', 'backup', 'oracle_before.py')
ORACLE_PRE_LR1_SEAL = os.path.join(STUDY, 'logs', 'repair6_2026-11-12', 'oracle_before_LR1.sha256')
FLAGS_BEFORE_LR2_FILE = lr.FLAGS_BEFORE_FILE
FLAGS_BEFORE_LR2_3_FILE = os.path.join(STUDY, 'tasks', 'FLAGS_BEFORE_LR2_3.tsv')
CARD_VARIANTS_BEFORE_LR18_FILE = os.path.join(STUDY, 'tasks', 'CARD_VARIANTS_BEFORE_LR18.json')
HARM_FIELDS = ('order_significant', 'sort_keys', 'dtype_significant', 'acceptable_variants', 'property_checks')
EXTERNAL_KILL_ROW = 'HARNESS_ERROR_EXTERNAL_SIGKILL'


class SealError(Exception):
    pass


# ------------------------------------------------------------------------------------------------ inputs
def load_flags_all(path):
    """{task_id: flags} for every row of a flag snapshot (existed_before_rulings ignored). Empty dict if the file does not exist."""
    if not path or not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        lines = [ln for ln in f if not ln.startswith('#')]
    return {r['task_id']: {'order_significant': r['order_significant'].strip().lower() == 'true',
                           'sort_keys': json.loads(r['sort_keys']), 'row_order': r['row_order']}
            for r in csv.DictReader(lines, delimiter='\t')}


def load_card_variants(path):
    """{task_id: {field: value}} of the LR18 snapshot; {} if the file does not exist."""
    if not path or not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    return {c['id']: {k: c.get(k) for k in HARM_FIELDS} for c in d.get('cards', [])}


def _sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def load_pre_lr1_oracle(path=ORACLE_PRE_LR1, seal=ORACLE_PRE_LR1_SEAL):
    """The sealed pre-LR1 oracle copy as a module (no bytecode file is written). Raises SealError if the copy or its seal is missing or
    the hash differs: the LR13 sensitivity is never computed with an unverified rule."""
    if not os.path.exists(path):
        raise SealError('LR13: pre-LR1 oracle copy not found: %s' % path)
    if seal is not None:
        if not os.path.exists(seal):
            raise SealError('LR13: seal not found: %s' % seal)
        with open(seal, encoding='utf-8') as f:
            want = [ln.split()[0] for ln in f if ln.strip() and not ln.startswith('#')]
        if _sha(path) not in want:
            raise SealError('LR13: sha256 of %s does not match its seal %s' % (path, seal))
    with open(path, encoding='utf-8') as f:
        src = f.read()
    mod = types.ModuleType('oracle_pre_lr1')
    mod.__file__ = path
    saved = list(sys.path)
    if af.HERE not in sys.path:
        sys.path.insert(0, af.HERE)
    try:
        exec(compile(src, path, 'exec'), mod.__dict__)
    finally:
        sys.path[:] = saved
    return mod


def _deps_with(deps, classify_program):
    return af.Deps(classify_program, deps.attribute, deps.harm_prelabel, deps.scan, deps.load_record, deps.exposure_rows,
                   load_trace=deps.load_trace, first_divergent_line=deps.first_divergent_line)


def fam_key(p):
    return (af.family_code(p) or 'M?') if p.get('stratum') == 'M' else p.get('stratum')


# ------------------------------------------------------------------------------------------------ generic sensitivity
def alt_analysis(label, ruling, reading, runs, alt_tasks, rebuild_ids, models, deps_alt, gen_dir, per_program, plan, targets, B, seed,
                 primary_tests=None, use_numpy=None, extra=None, ruled=None):
    """Rebuild the per-program rows of the tasks in `rebuild_ids` with `alt_tasks` (cards) and `deps_alt` (oracle), keep the others,
    recompute run_tests on every target pair and count the results whose class differs. -> (summary dict, rebuilt rows)."""
    rebuild_ids = set(rebuild_ids)
    out = {'label': label, 'ruling': ruling, 'reading': reading, 'outside_decision_rules': True}
    if extra:
        out.update(extra)
    rebuilt = af.build_per_program(runs, [t for t in alt_tasks if t['id'] in rebuild_ids], models, deps_alt, gen_dir) \
        if rebuild_ids else []
    rb = {p['program_id']: p for p in rebuilt}
    alt_pp = [rb.get(p['program_id'], p) for p in per_program]
    diffs = []
    for p in per_program:
        q = rb.get(p['program_id'])
        if q is None:
            continue
        for pair in targets:
            a, b = p['targets'].get(pair) or {}, q['targets'].get(pair) or {}
            va, vb = tuple(a.get(k) for k in lr.CLASS_FIELDS), tuple(b.get(k) for k in lr.CLASS_FIELDS)
            if va != vb or p['clean_on_233'] != q['clean_on_233']:
                diffs.append({'program_id': p['program_id'], 'model': p['model'], 'family': fam_key(p), 'pair': pair,
                              'primary': dict(zip(lr.CLASS_FIELDS, va)), 'sensitivity': dict(zip(lr.CLASS_FIELDS, vb))})
    out['n_tasks_reclassified'] = len(rebuild_ids & {t['id'] for t in alt_tasks})
    out['n_programs_reclassified'] = len(rebuilt)
    out['n_results_class_differs'] = len(diffs)
    out['n_results_class_differs_by_pair'] = {pair: sum(1 for d in diffs if d['pair'] == pair) for pair in targets}
    out['results_class_differs'] = diffs
    amap = {t['id']: t for t in alt_tasks}
    univ = lr._univ(alt_tasks)
    models_all = lr._models_all(plan, alt_pp)
    out['targets'] = {}
    for pair in targets:
        flat = [af.flatten(p, pair, amap) for p in alt_pp]
        res = af.run_tests(flat, plan, models_all, univ, B, seed, use_numpy)
        ent = {'tests': lr._summ_tests(res['tests']), 'secondary': lr._summ_tests(res['secondary'])}
        if primary_tests and pair in primary_tests:
            ent['estimate_differs_from_primary'] = {
                k: lr._est(ent['tests'][k].get('estimate')) != lr._est(primary_tests[pair].get(k, {}).get('estimate'))
                for k in ent['tests']}
        ent[lr61.ADDED_KEY] = lr.added_h4_r(alt_pp, alt_tasks, pair, plan, B, seed, use_numpy, ruled)   # T8 preparation (LR42, LR61)
        ent[lr.H4_RA_KEY] = lr.added_h4_ra(alt_pp, alt_tasks, pair, plan, B, seed, use_numpy, ruled)    # T8 apply 2 (LR70)
        out['targets'][pair] = ent
    return out, alt_pp


def _flagged_ids(tasks):
    return {t['id'] for t in tasks if t.get('order_significant')}


def _case_counts(rows, targets, field, value):
    """{pair: {'total', 'by_model', 'by_family', 'by_model_family'}} of target blocks whose `field` equals `value`."""
    out = {}
    for pair in targets:
        hits = [p for p in rows if ((p['targets'].get(pair) or {}).get(field) == value)]
        out[pair] = {'total': len(hits), 'by_model': dict(collections.Counter(p['model'] for p in hits)),
                     'by_family': dict(collections.Counter(fam_key(p) for p in hits)),
                     'by_model_family': dict(collections.Counter('%s|%s' % (p['model'], fam_key(p)) for p in hits))}
    return out


# ------------------------------------------------------------------------------------------------ LR13
def lr13(runs, tasks, models, deps, gen_dir, per_program, plan, targets, B, seed, flags_before_lr2, primary_tests, use_numpy=None,
         oracle_path=ORACLE_PRE_LR1, seal_path=ORACLE_PRE_LR1_SEAL, ruled=None):
    pre = load_pre_lr1_oracle(oracle_path, seal_path)
    dpre = _deps_with(deps, pre.classify_program)
    src = {'oracle_copy': os.path.relpath(oracle_path, STUDY) if oracle_path.startswith(STUDY) else os.path.basename(oracle_path),
           'oracle_copy_sha256': _sha(oracle_path)}
    a, _ = alt_analysis(LABEL['LR13'], 'LR13 (a)', 'pre-LR1 key rule with the current flags', runs, tasks, _flagged_ids(tasks),
                        models, dpre, gen_dir, per_program, plan, targets, B, seed, primary_tests, use_numpy, src, ruled=ruled)
    alt, changed = lr.tasks_with_flags(tasks, flags_before_lr2)
    b, _ = alt_analysis(LABEL['LR13'], 'LR13 (b)', 'pre-LR1 key rule with the flags hashed before LR2 (rows existed_before_rulings = yes)',
                        runs, alt, _flagged_ids(alt) | set(changed), models, dpre, gen_dir, per_program, plan, targets, B, seed,
                        primary_tests, use_numpy, dict(src, tasks_whose_flags_differ=changed,
                                                       n_tasks_with_pre_LR2_flags=len(flags_before_lr2)), ruled=ruled)
    return {'a_pre_LR1_rule_current_flags': a, 'b_pre_LR1_rule_flags_before_LR2': b}


# ------------------------------------------------------------------------------------------------ LR14 / LR17 (flag snapshots)
def flags_snapshot(label, ruling, reading, flags, runs, tasks, models, deps, gen_dir, per_program, plan, targets, B, seed, primary_tests,
                   use_numpy=None, flags_file=None, ruled=None):
    alt, changed = lr.tasks_with_flags(tasks, flags)
    out, alt_pp = alt_analysis(label, ruling, reading, runs, alt, changed, models, deps, gen_dir, per_program, plan, targets, B, seed,
                               primary_tests, use_numpy, {'flags_file': flags_file, 'n_tasks_in_snapshot': len(flags),
                                                          'n_tasks_in_run_in_snapshot': sum(1 for t in tasks if t['id'] in flags),
                                                          'tasks_whose_flags_differ': changed}, ruled=ruled)
    return out, alt, alt_pp


def stratum_rates(per_program, tasks, plan, stratum, B, seed, use_numpy=None, pair=af.PRIMARY_PAIR):
    tmap = {t['id']: t for t in tasks}
    flat = [af.flatten(p, pair, tmap) for p in per_program if p['stratum'] == stratum]
    univ = [u for u in lr._univ(tasks) if u['stratum'] == stratum]
    models_all = lr._models_all(plan, per_program)
    rates, _ = af.rate_tables(flat, models_all, univ, B, seed, use_numpy)
    return {m: {k: lr._est(v) for k, v in (d.get(stratum) or {}).items()} for m, d in rates.items() if d.get(stratum)}


# ------------------------------------------------------------------------------------------------ LR16
def lr16(runs, tasks, models, deps, gen_dir, per_program, plan, targets, B, seed, primary_tests, use_numpy=None, ruled=None):
    import oracle
    ruled = lr61.load_ruled() if ruled is None else ruled       # T8 preparation 2026-11-13 (LR42, LR61)
    out = {}
    for part, key, case, reading in (
            ('a', 'lr16_nonunique_whole_row', oracle.LR16A_CASE, 'index labels not unique: the whole row is the identity key'),
            ('b', 'lr16_not_found_order_only', oracle.LR16B_CASE, 'sort key located in neither result: read as ORDER_ONLY')):
        alt = [dict(t, **{key: True}) if t.get('order_significant') else t for t in tasks]
        res, alt_pp = alt_analysis(LABEL['LR16'], 'LR16 (%s)' % part, reading, runs, alt, _flagged_ids(tasks), models, deps, gen_dir,
                                   per_program, plan, targets, B, seed, primary_tests, use_numpy, ruled=ruled)
        res['case_counts'] = _case_counts(alt_pp, targets, 'lr16_case', case)
        res['case_counts_' + lr61.ADDED_KEY] = lr61.without_ruled(                  # T8 preparation 2026-11-13 (LR42, LR61)
            lambda pp, tk, case=case: _case_counts(pp, targets, 'lr16_case', case), alt_pp, alt, lr61.case_counts_r, ruled)
        if part == 'b':
            res['primary_order_note_sort_key_not_found'] = _case_counts(per_program, targets, 'order_note', oracle.NOTE_H1)
            res['primary_order_note_sort_key_not_found_' + lr61.ADDED_KEY] = lr61.without_ruled(
                lambda pp, tk: _case_counts(pp, targets, 'order_note', oracle.NOTE_H1), per_program, tasks, lr61.case_counts_r, ruled)
        out['%s_%s' % (part, 'nonunique_index_whole_row' if part == 'a' else 'key_not_found_order_only')] = res
    return out


# ------------------------------------------------------------------------------------------------ LR18
def _harm_field_diffs(card, before):
    """REPAIR6 fixes: sorted list of the harm-relevant fields that differ between the current card and the LR18 snapshot; inside
    acceptable_variants each sub-key is listed as 'acceptable_variants.<key>'."""
    def j(x):
        return json.dumps(x, sort_keys=True)
    out = []
    for k in HARM_FIELDS:
        a, b = card.get(k), before.get(k)
        if k == 'acceptable_variants' and isinstance(a or {}, dict) and isinstance(b or {}, dict):
            a, b = a or {}, b or {}
            out += ['acceptable_variants.%s' % s for s in sorted(set(a) | set(b)) if j(a.get(s)) != j(b.get(s))]
        elif j(a) != j(b):
            out.append(k)
    return sorted(out)


def lr18(runs, tasks, per_program, deps, plan, B, seed, variants_before, use_numpy=None, ruled=None):
    """Harm pre-labels under the card notes sealed before the LR18 sweep. Only tasks whose harm-relevant fields differ from the snapshot
    are relabelled (for the others the labels are the same by construction)."""
    out = {'label': LABEL['LR18'], 'ruling': 'LR18', 'outside_decision_rules': True,
           'snapshot_tasks': len(variants_before), 'pairs': sorted(af.ATTRIB_TARGET)}
    tmap = {t['id']: t for t in tasks}
    changed = sorted(tid for tid, f in variants_before.items() if tid in tmap and
                     any(json.dumps(tmap[tid].get(k), sort_keys=True) != json.dumps(f.get(k), sort_keys=True) for k in HARM_FIELDS))
    out['tasks_whose_card_notes_differ'] = changed
    # REPAIR6 fixes (REPAIR6_REVIEW.md section 4): the label above stays the ruling's exact label. The automatic pre-label never reads
    # acceptable_variants.notes (harm_prelabel._variants reads only the structured variant keys; notes reach only the human H5 coding
    # sheet, coding_sheet.py "Also acceptable: ..."). The snapshot also holds the order flags as they were before the LR14 card edits.
    # So the pre-label differences below can come only from fields other than the notes; which fields differ is listed per task.
    fdiff = {tid: _harm_field_diffs(tmap[tid], variants_before[tid]) for tid in changed}
    out['scope_note'] = ('automatic pre-labels only; acceptable_variants.notes does not enter them (the notes changes act only on the '
                         'human H5 coding sheet); differences here come from the other harm-relevant fields of the snapshot, which '
                         'include the order flags before the LR14 card edits')
    out['scope_statement_LR48'] = SCOPE_LR48                  # REPAIR9 (LR48) replaces the words of SCOPE_LR26
    out['tasks_prelabel_fields_differ'] = prelabel_fields_changed_tasks(tasks, variants_before)
    out['n_tasks_prelabel_fields_differ'] = len(out['tasks_prelabel_fields_differ'])
    out['fields_differing_by_task'] = fdiff
    out['tasks_notes_only'] = sorted(t for t, f in fdiff.items() if f == ['acceptable_variants.notes'])
    out['tasks_fields_read_by_prelabel_differ'] = sorted(t for t, f in fdiff.items() if [x for x in f if x != 'acceptable_variants.notes'])
    # REPAIR8 (LR26): which of the pre-label fields differ, so that the report shows what the stated scope covers
    order_fields = ('order_significant', 'sort_keys', 'acceptable_variants.row_order')
    out['tasks_order_fields_differ'] = sorted(t for t, f in fdiff.items() if [x for x in f if x in order_fields])
    out['tasks_other_prelabel_fields_differ'] = sorted(t for t, f in fdiff.items()
                                                       if [x for x in f if x != 'acceptable_variants.notes' and x not in order_fields])
    alt_pp, diffs = [], []
    counts = {pair: {'current': collections.Counter(), 'before_LR18': collections.Counter()} for pair in af.ATTRIB_TARGET}
    for p in per_program:
        q = p
        if p['task_id'] in changed:
            q = copy.deepcopy(p)
            card = dict(tmap[p['task_id']], **variants_before[p['task_id']])
            ref = deps.load_record(runs, 'E0a', 'ref/' + p['task_id'])
            e0a = deps.load_record(runs, 'E0a', p['program_id'])
            for pair, (tgt, _) in af.ATTRIB_TARGET.items():
                t = q['targets'].get(pair)
                if not t or t.get('harm_prelabel') is None:
                    continue
                trec = deps.load_record(runs, tgt, p['program_id'])
                if ref is not None and e0a is not None and trec is not None:
                    t['harm_prelabel'] = deps.harm_prelabel(e0a, trec, ref, card).get('label')
                if t['harm_prelabel'] != p['targets'][pair]['harm_prelabel']:
                    diffs.append({'program_id': p['program_id'], 'pair': pair, 'current': p['targets'][pair]['harm_prelabel'],
                                  'before_LR18': t['harm_prelabel']})
        alt_pp.append(q)
        for pair in af.ATTRIB_TARGET:
            for name, src in (('current', p), ('before_LR18', q)):
                t = src['targets'].get(pair) or {}
                if src['clean_on_233'] and t.get('drift'):
                    counts[pair][name][t.get('harm_prelabel') or 'UNDETERMINABLE'] += 1
    out['labels'] = {pair: {k: dict(v) for k, v in c.items()} for pair, c in counts.items()}
    out['n_prelabels_differ'] = len(diffs)
    out['prelabels_differ'] = diffs
    univ = lr._univ(tasks)
    out['h5_automatic_prelabel_before_LR18'] = af.h5_tables(alt_pp, univ, plan, None, B, seed, use_numpy, af.PRIMARY_PAIR)
    out['h5_automatic_prelabel_before_LR18_' + lr61.ADDED_KEY] = lr61.without_ruled(     # T8 preparation 2026-11-13 (LR42, LR61)
        lambda pp, tk: af.h5_tables(pp, lr._univ(tk), plan, None, B, seed, use_numpy, af.PRIMARY_PAIR), alt_pp, tasks,
        lr61.h5_r_groups, ruled)
    return out


# ------------------------------------------------------------------------------------------------ LR26 (REPAIR8 2026-11-13)
def notes_changed_tasks(tasks, variants_before):
    """Ids of the tasks whose acceptable_variants.notes differ from the LR18 snapshot: the tasks whose notes LR18 or LR25 changed
    (the snapshot was sealed before the LR18 sweep; no other step has changed notes since)."""
    out = []
    for t in tasks:
        b = variants_before.get(t['id'])
        if b is None:
            continue
        if ((t.get('acceptable_variants') or {}).get('notes')) != ((b.get('acceptable_variants') or {}).get('notes')):
            out.append(t['id'])
    return sorted(out)


def prelabel_fields_changed_tasks(tasks, variants_before):
    """REPAIR9 (LR48): ids of the tasks whose pre-label fields (HARM_FIELDS other than acceptable_variants.notes) differ from the
    LR18 snapshot. The same definition as lr18()'s tasks_fields_read_by_prelabel_differ."""
    out = []
    for t in tasks:
        b = variants_before.get(t['id'])
        if b is not None and [x for x in _harm_field_diffs(t, b) if x != 'acceptable_variants.notes']:
            out.append(t['id'])
    return sorted(out)


def load_snapshot_ic(path, card_variants_path):
    """REPAIR9 (LR48): {task_id: intended_computation} of the tasks.json the LR18 snapshot names as its source ("tasks/tasks.json sha256
    <hex>"). Raises SealError if the file's sha256 is not that hash. None when path is None/'none' (synthetic use)."""
    if path in (None, 'none'):
        return None
    with open(card_variants_path, encoding='utf-8') as f:
        src = (json.load(f).get('source') or '').split()
    want = src[-1] if src else ''
    if _sha(path) != want:
        raise SealError('LR48: %s does not have the sha256 the LR18 snapshot names as its source (%s)' % (path, want or 'none named'))
    with open(path, encoding='utf-8') as f:
        return {t['id']: t.get('intended_computation') for t in json.load(f)['tasks']}


def notes_or_ic_changed_tasks(tasks, variants_before, ic_before):
    """REPAIR9 (LR48): ids of the tasks whose acceptable_variants.notes or intended_computation differ from the LR18 snapshot. With
    ic_before None only the notes are compared (as notes_changed_tasks)."""
    out = set(notes_changed_tasks(tasks, variants_before))
    if ic_before is not None:
        out |= {t['id'] for t in tasks if t['id'] in ic_before and t.get('intended_computation') != ic_before[t['id']]}
    return sorted(out)


def lr26(per_program, tasks, plan, codes, B, seed, variants_before, use_numpy=None, ic_before=None):
    """LR26: the H5 proportions (af.h5_tables, primary pair) also without the tasks whose notes LR18 or LR25 changed. Coded basis when
    `codes` is given, otherwise the automatic pre-label basis (as af.h5_tables states). Decides nothing; the primary H5 is untouched.
    REPAIR9 (LR48): left out are the tasks whose notes or intended computation differ from the snapshot (ic_before: the intended
    computation of the snapshot; None compares the notes only, and the output says so)."""
    excluded = notes_or_ic_changed_tasks(tasks, variants_before, ic_before)
    ex = set(excluded)
    keep_pp = [p for p in per_program if p['task_id'] not in ex]
    univ = [u for u in lr._univ(tasks) if u['task_id'] not in ex]
    return {'label': LABEL['LR26'], 'ruling': 'LR26', 'outside_decision_rules': True, 'pair': af.PRIMARY_PAIR,
            'definition_LR48': DEFINITION_LR48_H5 if ic_before is not None else
            DEFINITION_LR48_H5 + '; intended_computation NOT compared (no snapshot tasks file given)',
            'snapshot_tasks': len(variants_before), 'excluded_tasks': excluded, 'n_excluded_tasks': len(excluded),
            'n_tasks_kept': len(univ), 'n_programs_excluded': len(per_program) - len(keep_pp),
            'h5_without_notes_changed_tasks': af.h5_tables(keep_pp, univ, plan, codes, B, seed, use_numpy, af.PRIMARY_PAIR)}


# ------------------------------------------------------------------------------------------------ LR15
def lr15_name_only(runs, per_program, deps, targets):
    """Results whose two canonical values differ only in index-level or column-axis names (no row moved; values equal): ORDER_ONLY under
    the registered layer (not drift), or DTYPE_DRIFT when a dtype rule fires as well. Counted by model and family."""
    import oracle as O
    tgt_of = {'E0a~E1': 'E1', 'E0a~E2': 'E2'}
    hits = {pair: [] for pair in targets}
    for p in per_program:
        if not p['clean_on_233']:
            continue
        for pair in targets:
            t = p['targets'].get(pair) or {}
            if t.get('class') not in ('ORDER_ONLY', 'DTYPE_DRIFT') or pair not in tgt_of:
                continue
            a, b = deps.load_record(runs, 'E0a', p['program_id']), deps.load_record(runs, tgt_of[pair], p['program_id'])
            if not a or not b or 'result' not in a or 'result' not in b:
                continue
            va, vb = a['result'], b['result']
            if O.same_row_order(va, vb) and not O.eqv(va, vb, True):
                hits[pair].append(p)
    return {'ruling': 'LR15', 'what': 'name-only changes (index-level or column-axis names differ, no row moved, values equal); not '
                                      'drift under the registered ORDER_ONLY layer; reported count',
            'counts': {pair: {'total': len(h), 'by_model': dict(collections.Counter(p['model'] for p in h)),
                              'by_family': dict(collections.Counter(fam_key(p) for p in h)),
                              'by_model_family': dict(collections.Counter('%s|%s' % (p['model'], fam_key(p)) for p in h))}
                       for pair, h in hits.items()}}


# ------------------------------------------------------------------------------------------------ LR22 (3)
def _external_kill(rec):
    return bool(rec) and rec.get('status') == 'harness_error' and rec.get('harness_error_kind') == 'external_sigkill'


def external_kill_of(p, pair, runs, load_record):
    """True when the result of this program on this pair is an exclusion or run problem caused by an external-SIGKILL harness error
    (LR6) of E0a, E0b or the target run."""
    tgt_of = {'E0a~E1': 'E1', 'E0a~E2': 'E2'}
    if not p['clean_on_233']:
        det = p.get('exclusion_detail') or ''
        if 'harness_error' not in det:
            return False
        rc = 'E0b' if det.startswith('E0b') else 'E0a'
        return _external_kill(load_record(runs, rc, p['program_id']))
    t = p['targets'].get(pair)
    if t is None or t.get('run_problem') != 'HARNESS' or pair not in tgt_of:
        return False
    return _external_kill(load_record(runs, tgt_of[pair], p['program_id']))


def exclusions_table(per_program, runs, load_record, targets):
    """LR22 (3), review SF11: per target pair and model, the outcome / exclusions categories of analyze_full.outcome_label, with every
    program whose exclusion or run problem comes from an external-SIGKILL harness error (final after LR6's re-runs) moved to its own row
    HARNESS_ERROR_EXTERNAL_SIGKILL."""
    out = {'ruling': 'LR22 (3)', 'row_external': EXTERNAL_KILL_ROW, 'pairs': {}}
    for pair in targets:
        by_model = collections.defaultdict(collections.Counter)
        for p in per_program:
            lab = EXTERNAL_KILL_ROW if external_kill_of(p, pair, runs, load_record) else af.outcome_label(p, pair)
            by_model[p['model']][lab] += 1
        tot = collections.Counter()
        for c in by_model.values():
            tot.update(c)
        out['pairs'][pair] = {'by_model': {m: dict(c) for m, c in sorted(by_model.items())}, 'all_models': dict(tot)}
    return out


# ------------------------------------------------------------------------------------------------ all
def compute_all(runs, tasks, models, deps, gen_dir, per_program, plan, targets, B, seed, summary, use_numpy=None,
                flags_before_lr2_path=FLAGS_BEFORE_LR2_FILE, flags_before_lr2_3_path=FLAGS_BEFORE_LR2_3_FILE,
                card_variants_path=CARD_VARIANTS_BEFORE_LR18_FILE, oracle_pre_lr1_path=ORACLE_PRE_LR1,
                oracle_pre_lr1_seal=ORACLE_PRE_LR1_SEAL, codes=None, snapshot_tasks_path=LR18_SNAPSHOT_TASKS_FILE, ruled=None):
    ruled = lr61.load_ruled() if ruled is None else ruled       # T8 preparation 2026-11-13 (LR42, LR61): read and checked once
    primary_tests = {pair: (summary['targets'].get(pair) or {}).get('tests') or {} for pair in targets}
    out = {'note': 'lead rulings LR13 to LR22 (Amendment 11); sensitivities and counts outside the primary analysis and the decision rules'}
    yes = lr.load_flags_before(flags_before_lr2_path) if flags_before_lr2_path not in (None, 'none') else {}
    out['LR13'] = lr13(runs, tasks, models, deps, gen_dir, per_program, plan, targets, B, seed, yes, primary_tests, use_numpy,
                       oracle_pre_lr1_path, oracle_pre_lr1_seal, ruled=ruled)
    f23 = load_flags_all(flags_before_lr2_3_path) if flags_before_lr2_3_path not in (None, 'none') else {}
    out['LR14'], _, _ = flags_snapshot(LABEL['LR14'], 'LR14', 'flags sealed before the LR14/LR18 card edits (post-LR2-script flags)', f23,
                                       runs, tasks, models, deps, gen_dir, per_program, plan, targets, B, seed, primary_tests, use_numpy,
                                       os.path.basename(flags_before_lr2_3_path) if f23 else None, ruled=ruled)
    out['LR16'] = lr16(runs, tasks, models, deps, gen_dir, per_program, plan, targets, B, seed, primary_tests, use_numpy, ruled=ruled)
    fall = load_flags_all(flags_before_lr2_path) if flags_before_lr2_path not in (None, 'none') else {}
    s17, alt17, pp17 = flags_snapshot(LABEL['LR17'], 'LR17', 'flags before LR2 for all tasks, including the existed_before_rulings = no rows',
                                      fall, runs, tasks, models, deps, gen_dir, per_program, plan, targets, B, seed, primary_tests,
                                      use_numpy, os.path.basename(flags_before_lr2_path) if fall else None, ruled=ruled)
    s17['RQ5_stratum_R'] = {'pair': af.PRIMARY_PAIR,
                            'with_current_flags': stratum_rates(per_program, tasks, plan, 'R', B, seed, use_numpy),
                            'without_the_LR2_flags_of_new_tasks': stratum_rates(pp17, alt17, plan, 'R', B, seed, use_numpy)}
    s17['RQ5_stratum_R_' + lr61.ADDED_KEY] = {                 # T8 preparation 2026-11-13 (LR42, LR61)
        'with_current_flags': lr61.without_ruled(lambda pp, tk: stratum_rates(pp, tk, plan, 'R', B, seed, use_numpy), per_program, tasks,
                                                 ruled=ruled),
        'without_the_LR2_flags_of_new_tasks': lr61.without_ruled(lambda pp, tk: stratum_rates(pp, tk, plan, 'R', B, seed, use_numpy),
                                                                 pp17, alt17, ruled=ruled)}
    out['LR17'] = s17
    vb = load_card_variants(card_variants_path) if card_variants_path not in (None, 'none') else {}
    out['LR18'] = lr18(runs, tasks, per_program, deps, plan, B, seed, vb, use_numpy, ruled=ruled)
    icb = load_snapshot_ic(snapshot_tasks_path, card_variants_path) if vb else None   # REPAIR9 2026-11-13 (LR48)
    out['LR26'] = lr26(per_program, tasks, plan, codes, B, seed, vb, use_numpy, ic_before=icb)      # REPAIR8 2026-11-13
    out['LR26'][lr61.ADDED_KEY] = lr61.without_ruled(          # T8 preparation 2026-11-13 (LR42, LR61)
        lambda pp, tk: lr26(pp, tk, plan, codes, B, seed, vb, use_numpy, ic_before=icb), per_program, tasks,
        lambda res: dict(lr61.h5_r_groups(res['h5_without_notes_changed_tasks']), excluded_tasks_LR26=res['excluded_tasks']), ruled)
    out['LR15_name_only_changes'] = lr15_name_only(runs, per_program, deps, targets)
    out['LR15_name_only_changes'][lr61.ADDED_KEY] = lr61.without_ruled(   # T8 preparation (LR42, LR61); family R rows only are read
        lambda pp, tk: lr15_name_only(runs, [p for p in pp if p.get('stratum') == 'R'], deps, targets)['counts'], per_program, tasks,
        lr61.case_counts_r, ruled)
    return out


def _tests_table(L, ent):
    for pair, e in ent['targets'].items():
        L.append('| %s | estimate | lo | hi | p |' % pair)
        L.append('|---|---|---|---|---|')
        for k, v in e['tests'].items():
            L.append('| %s | %s | %s | %s | %s |' % (k, v.get('estimate'), v.get('lo'), v.get('hi'), v.get('p')))
        L.append('')
        if e.get(lr.H4_RA_KEY):                             # T8 apply 2 2026-11-13 (LR70)
            lr.md_h4_ra_added(L, e[lr.H4_RA_KEY], pair)


def _sens_md(L, title, s):
    L += ['## %s: "%s"' % (title, s['label']), '', '- reading: %s' % s['reading'],
          '- programs reclassified: %d; results (program x pair) whose class differs from the primary: %d %s'
          % (s['n_programs_reclassified'], s['n_results_class_differs'], json.dumps(s['n_results_class_differs_by_pair'])), '']
    if s.get('tasks_whose_flags_differ') is not None:
        L.insert(len(L) - 1, '- tasks whose flags differ from the current cards: %d' % len(s['tasks_whose_flags_differ']))
    _tests_table(L, s)


def write_md(add, path, exclusions=None):
    L = ['# Additions of lead rulings LR13 to LR22 (not the primary analysis; outside the decision rules)', '']
    _sens_md(L, 'LR13 (a)', add['LR13']['a_pre_LR1_rule_current_flags'])
    _sens_md(L, 'LR13 (b)', add['LR13']['b_pre_LR1_rule_flags_before_LR2'])
    _sens_md(L, 'LR14', add['LR14'])
    for k, s in add['LR16'].items():
        _sens_md(L, 'LR16 (%s)' % k[0], s)
        for pair, c in s['case_counts'].items():
            L.append('- %s: case occurs in %d comparisons; by model %s; by family %s' % (pair, c['total'], json.dumps(c['by_model']),
                                                                                          json.dumps(c['by_family'])))
        L.append('')
        ad = s.get('case_counts_' + lr61.ADDED_KEY)
        if ad:                                              # T8 preparation 2026-11-13 (LR42, LR61)
            L += [lr61.MD_START, '', '**%s.** Left out: %s.' % (ad['label'], ', '.join(ad['tasks_left_out']) or 'none'), '']
            for pair, c in ad['result'].items():
                L.append('- %s, family R without the listed tasks: case occurs in %d comparisons; by model %s'
                         % (pair, c['total_R'], json.dumps(c['by_model_R'])))
            L += ['', lr61.MD_END]
    _sens_md(L, 'LR17', add['LR17'])
    r = add['LR17']['RQ5_stratum_R']
    L += ['RQ5, stratum R on %s (silent / clean):' % r['pair'], '', '| model | with current flags | without the LR2 flags of new tasks |',
          '|---|---|---|']
    for m in sorted(set(r['with_current_flags']) | set(r['without_the_LR2_flags_of_new_tasks'])):
        a, b = r['with_current_flags'].get(m, {}), r['without_the_LR2_flags_of_new_tasks'].get(m, {})
        L.append('| %s | %s / %s | %s / %s |' % (m, a.get('x'), a.get('n'), b.get('x'), b.get('n')))
    L.append('')
    ad = add['LR17'].get('RQ5_stratum_R_' + lr61.ADDED_KEY)
    if ad:                                                  # T8 preparation 2026-11-13 (LR42, LR61)
        e0 = ad['with_current_flags']
        L += [lr61.MD_START, '', '**%s.** Left out: %s (%d programs).' % (e0['label'], ', '.join(e0['tasks_left_out']) or 'none',
                                                                            e0['n_programs_left_out']), '',
              '| model | with current flags | without the LR2 flags of new tasks |', '|---|---|---|']
        a_, b_ = e0['result'], ad['without_the_LR2_flags_of_new_tasks']['result']
        for m in sorted(set(a_) | set(b_)):
            a, b = a_.get(m, {}), b_.get(m, {})
            L.append('| %s | %s / %s | %s / %s |' % (m, a.get('x'), a.get('n'), b.get('x'), b.get('n')))
        L += ['', lr61.MD_END]
    s = add['LR18']
    L += ['## LR18: "%s"' % s['label'], '', '- tasks whose card notes differ from the sealed earlier notes: %d; pre-labels that differ: %d'
          % (len(s['tasks_whose_card_notes_differ']), s['n_prelabels_differ']), '- labels: %s' % json.dumps(s['labels'])]
    if 'scope_note' in s:                                   # REPAIR6 fixes: what this sensitivity can and cannot show
        L += ['- scope: %s' % s['scope_note'],
              '- tasks whose only difference is acceptable_variants.notes (pre-labels equal by construction): %d; tasks with a '
              'difference in a field the pre-label reads: %d' % (len(s['tasks_notes_only']), len(s['tasks_fields_read_by_prelabel_differ']))]
    if 'scope_statement_LR48' in s:                         # REPAIR9 2026-11-13 (LR48): definition, list and its length
        L += ['- scope (lead rulings LR26, LR48): %s' % s['scope_statement_LR48'],
              '- tasks whose pre-label fields differ from the LR18 snapshot: %d %s'
              % (s['n_tasks_prelabel_fields_differ'], json.dumps(s['tasks_prelabel_fields_differ']))]
    if 'tasks_order_fields_differ' in s:                    # REPAIR8 2026-11-13 (LR26): what differs
        L += ['- of these, tasks whose order flags differ from the snapshot: %d %s; tasks whose other pre-label fields differ: %d %s'
              % (len(s['tasks_order_fields_differ']), json.dumps(s['tasks_order_fields_differ']),
                 len(s['tasks_other_prelabel_fields_differ']), json.dumps(s['tasks_other_prelabel_fields_differ']))]
    L.append('')
    if add.get('LR26'):                                     # REPAIR8 2026-11-13 (LR26)
        s = add['LR26']
        h = s['h5_without_notes_changed_tasks']
        L += ['## LR26: "%s"' % s['label'], '',
              '- H5 proportions on %s without the %d %s (%d tasks kept; %d programs left out); basis: %s'
              % (s['pair'], s['n_excluded_tasks'], s.get('definition_LR48', 'tasks whose notes LR18 or LR25 changed'), s['n_tasks_kept'],
                 s['n_programs_excluded'], h['basis']),
              '- tasks left out (%d): %s' % (s['n_excluded_tasks'], ', '.join(s['excluded_tasks'])), '',
              '| group | n coded | ' + ' | '.join(af.CODES) + ' |', '|---|---|' + '---|' * len(af.CODES)]
        for g, e in h['by_group'].items():
            L.append('| %s | %s | %s |' % (g, e['n_coded'], ' | '.join(
                ('%.3f' % e['shares'][c]['est']) if e['shares'].get(c, {}).get('est') is not None else '-' for c in af.CODES)))
        L.append('')
        ad = s.get(lr61.ADDED_KEY)
        if ad:                                              # T8 preparation 2026-11-13 (LR42, LR61)
            L += [lr61.MD_START, '', '**%s.** Left out: %s (%d programs).' % (ad['label'], ', '.join(ad['tasks_left_out']) or 'none',
                                                                                ad['n_programs_left_out']), '',
                  '| group | n coded | ' + ' | '.join(af.CODES) + ' |', '|---|---|' + '---|' * len(af.CODES)]
            for g, e in ad['result']['by_group'].items():
                L.append('| %s without the listed tasks | %s | %s |' % (g, e['n_coded'], ' | '.join(
                    ('%.3f' % e['shares'][c]['est']) if e['shares'].get(c, {}).get('est') is not None else '-' for c in af.CODES)))
            L += ['', lr61.MD_END]
    c = add['LR15_name_only_changes']['counts']
    L += ['## LR15: name-only changes (not drift; reported count)', '']
    for pair, e in c.items():
        L.append('- %s: %d; by model %s; by family %s' % (pair, e['total'], json.dumps(e['by_model']), json.dumps(e['by_family'])))
    L.append('')
    ad = add['LR15_name_only_changes'].get(lr61.ADDED_KEY)
    if ad:                                                  # T8 preparation 2026-11-13 (LR42, LR61)
        L += [lr61.MD_START, '', '**%s.** Left out: %s.' % (ad['label'], ', '.join(ad['tasks_left_out']) or 'none'), '']
        for pair, e in ad['result'].items():
            L.append('- %s, family R without the listed tasks: %d; by model %s' % (pair, e['total_R'], json.dumps(e['by_model_R'])))
        L += ['', lr61.MD_END]
    if exclusions:
        write_exclusions(L, exclusions)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')


def write_exclusions(L, ex):
    L += ['## LR22 (3): outcome and exclusions table with external-SIGKILL harness errors as their own row', '']
    for pair, e in ex['pairs'].items():
        cats = sorted(e['all_models'])
        L.append('| %s | %s |' % (pair, ' | '.join(cats)))
        L.append('|---|%s' % ('---|' * len(cats)))
        for m, c in e['by_model'].items():
            L.append('| %s | %s |' % (m, ' | '.join(str(c.get(k, 0)) for k in cats)))
        L.append('| all | %s |' % ' | '.join(str(e['all_models'].get(k, 0)) for k in cats))
        L.append('')
