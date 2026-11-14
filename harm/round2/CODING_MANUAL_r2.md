# Harm coding manual (one page), revision r2

Written 2026-11-11 14:50 JST, revised once (r2) 2026-11-13 from the five training items and the three LLM coders' replies to them only;
changes and reasons in `REVISION_NOTE_r2.md`. drafted_by: pkg:ATTRIB_HARM. **status: prepared.** Frozen
with the study materials (FULL_PREREG section 10.3). For coder A and coder B (a second person, or an LLM from outside the
study set, which gets the same rules in `harm/round2/PROMPT_r2.txt`).

**Your job.** A Python program was written for a data task and run twice on the same input files, in two software environments. The two
results differ. For each item decide whether result A, result B, both or neither is a correct answer to the task. You are not told which
environment produced which result; it does not matter. Each item page shows the task, the file description, the acceptable variants,
the property checks, the program, results A and B (differing cells marked, a summary of every column) and a list of the differences.
Judge the results, not the program: the program only explains how a value was produced, and a suspected flaw in it counts only if it
shows in a result (a wrong value in the rows or summaries shown, or a failed property check).

**Codes** (exactly one per item; write it in the answer sheet with a short note):
`A_ONLY_CORRECT` A is correct and B is not. `B_ONLY_CORRECT` B is correct and A is not. `BOTH_ACCEPTABLE` both are correct.
`NEITHER` neither is correct. `UNDETERMINABLE` the information shown does not allow a decision.

**Rules.**
1. Judge the whole result, not only the marked cells; use the column summaries for rows that are not shown. If both results share an
   error (in the rows or the summaries), neither is correct, even when the marked cells favour one. A shared point that no rule makes an
   error (for example an open point both read the same reasonable way) is not a shared error.
2. Correct = gives what the task asks for, allowing the acceptable variants. Do not demand anything the task does not ask for.
   Presentation alone is not an error (a whole number with or without ".0", a date with or without a time 00:00:00).
3. A missing value is fine where the input gives nothing to compute it from (missing input, a group with no rows) and the task does not
   say how to fill it; left missing where the task asks to fill it or the input allows computing it, it is an error. The text "nan",
   "None", "NaT" or "<NA>" standing in for a missing value is an error unless the task asks for it.
4. Implausible values are errors: dates far outside the data's years, Unix timestamps in seconds that are 1000 times too small or too
   large, counts that do not add up, rates outside 0 to 1. A correct result passes every listed property check; a range check applies to
   the values present (missing values fall under rule 3).
5. Empty results, wrong row sets (one row per input row instead of per group), runs without a result and an answer column with no values
   at all are not correct.
6. A point is left open when the task, the file description and the variants do not say which of two forms is wanted (for example
   whether a group with no rows is listed). If A and B differ exactly on such a point and both are reasonable readings, code
   `BOTH_ACCEPTABLE` unless another error remains. If the task is unclear on a point where A and B agree, take the reasonable reading
   and decide on the points where they differ.
7. `UNDETERMINABLE` only when the information shown cannot decide (deciding rows not shown, unreadable object), never because it is hard.

**Procedure.** Read the task and the file line; read the variants and checks; read the list of differences; inspect both tables and the
summaries. Then, in this order: (a) find the errors in each whole result with rules 1-5 (what no rule makes an error is not one);
(b) apply rule 6 to the remaining differences; (c) code: no error in either, `BOTH_ACCEPTABLE`; errors in one only, the other is
correct; errors in both, `NEITHER`; `UNDETERMINABLE` only under rule 7. Write the code and one sentence. About 2 minutes per item. Do not
look up the key file, the program's origin or any other item's code.

**Five worked examples** (rendered with `harness/coding_sheet.py render`; pages in `worked_examples/items/`). They are the pilot's
exploratory drifts (`pilots/r3/data/exploratory/review_smoke/`, pilot program ids below), not study data. The review's original task texts
are not stored in the pilot, so the task texts and cards were reconstructed from each program's task tag and comments
(kept outside this folder, with the key, in `harm/_private/worked_examples/`, which coders do not receive). Property-check results: `logs/attrib/worked_examples_check_2026-11-11.txt`.

| Item | Pilot program | Task (short) | What differs | Code | Why |
|---|---|---|---|---|---|
| [C0001](../manual/worked_examples/items/C0001.html) | qwen_rv/tr09__s0 | days since signup and Unix timestamp in seconds | signup_ts of 291 rows: A about 1.7 billion, B about 1.7 million | `NEITHER` | B's seconds are 1000 times too small (rule 4); A is right there, but both give -9223372037 for the 9 customers without a signup date, seen only in the column summary (rules 1 and 4) |
| [C0002](../manual/worked_examples/items/C0002.html) | ministral_rv/tr01__s1 | clean name and city, keep all columns | 9 missing signup dates: A missing, B the text "nan" | `A_ONLY_CORRECT` | the task does not ask to change dates; B turns missing dates into the text "nan" (rule 3) |
| [C0003](../manual/worked_examples/items/C0003.html) | ministral_rv/tr02__s1 | fill missing values (median / most frequent) | 95 cells: A still missing, B filled | `B_ONLY_CORRECT` | A leaves the values the task asks to fill (rule 3; check "no missing values" fails); both leave signup_date missing, which a reasonable reading of "text columns" allows (rule 6, so not a shared error under rule 1) |
| [C0004](../manual/worked_examples/items/C0004.html) | ministral_rv/tr04__s0 | average monthly_spend per age group | A lists the two empty groups with a missing average, B omits them | `BOTH_ACCEPTABLE` | the task does not say whether empty groups are listed; an empty group has nothing to average, so its missing average is allowed (rule 3) and the range check covers only values present (rule 4); the three non-empty groups agree (rule 6) |
| [C0005](../manual/worked_examples/items/C0005.html) | qwen_rv/tr03__s1 | churn rate per plan | A has no rate at all (all missing), B has rates near 0.3 | `B_ONLY_CORRECT` | an all-missing answer column is not an answer (rules 4 and 5) |

None of the seven exploratory drifts is a genuine `UNDETERMINABLE` case, so that code has no worked example (rule 7 defines it).
After coding, the A/B codes are translated with a separate key file (`coding_sheet.py decode`) that coders never see.
