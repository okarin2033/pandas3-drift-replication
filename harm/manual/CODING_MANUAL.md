# Harm coding manual (one page)

Written 2026-11-11 14:50 JST. drafted_by: pkg:ATTRIB_HARM. **status: prepared.** Frozen with the
study materials (FULL_PREREG section 10.3). For coder A and coder B (a second person, or an LLM from outside the study set,
which gets the same rules in `harm/coder_llm/PROMPT.txt`).

**Your job.** A Python program was written for a data task and run twice on the same input files, in two software environments. The two
results differ. For each item decide whether result A, result B, both or neither is a correct answer to the task. You are not told which
environment produced which result; it does not matter. Each item page shows the task, the file description, the acceptable variants,
the property checks, the program, results A and B (differing cells marked, a summary of every column) and a list of the differences.

**Codes** (exactly one per item; write it in the answer sheet with a short note):
`A_ONLY_CORRECT` A is correct and B is not. `B_ONLY_CORRECT` B is correct and A is not. `BOTH_ACCEPTABLE` both are correct.
`NEITHER` neither is correct. `UNDETERMINABLE` the information shown does not allow a decision.

**Rules.**
1. Judge the whole result, not only the marked cells; use the column summaries for rows that are not shown. If both results share an
   error, neither is correct.
2. Correct = gives what the task asks for, allowing the acceptable variants. Do not demand anything the task does not ask for.
3. A missing value that comes from missing input is fine where the task does not say how to fill it. The text "nan", "None", "NaT" or
   "<NA>" standing in for a missing value is an error unless the task asks for it.
4. Implausible values are errors: dates far outside the data's years, Unix timestamps in seconds that are 1000 times too small or too
   large, counts that do not add up, rates outside 0 to 1. A correct result passes every listed property check.
5. Empty results, wrong row sets (one row per input row instead of per group) and runs without a result are not correct.
6. If the task leaves open exactly the point where A and B differ and both are reasonable readings, code `BOTH_ACCEPTABLE`. If the task
   is unclear on a point where A and B agree, take the reasonable reading and decide on the points where they differ.
7. `UNDETERMINABLE` only when the information shown cannot decide (deciding rows not shown, unreadable object), never because it is hard.

**Procedure.** Read the task and the file line; read the variants and checks; read the list of differences; inspect both tables and the
summaries; apply rules 1-7 in order; write the code and one sentence. About 2 minutes per item. Do not look up the key file, the
program's origin or any other item's code.

**Five worked examples** (rendered with `harness/coding_sheet.py render`; pages in `worked_examples/items/`). They are the pilot's
exploratory drifts (`pilots/r3/data/exploratory/review_smoke/`, pilot program ids below), not study data. The review's original task texts
are not stored in the pilot, so the task texts and cards were reconstructed from each program's task tag and comments
(kept outside this folder, with the key, in `harm/_private/worked_examples/`, which coders do not receive). Property-check results: `logs/attrib/worked_examples_check_2026-11-11.txt`.

| Item | Pilot program | Task (short) | What differs | Code | Why |
|---|---|---|---|---|---|
| [C0001](worked_examples/items/C0001.html) | qwen_rv/tr09__s0 | days since signup and Unix timestamp in seconds | signup_ts of 291 rows: A about 1.7 billion, B about 1.7 million | `NEITHER` | B's seconds are 1000 times too small (rule 4); A is right there, but both give -9223372037 for the 9 customers without a signup date (column summary, rule 1) |
| [C0002](worked_examples/items/C0002.html) | ministral_rv/tr01__s1 | clean name and city, keep all columns | 9 missing signup dates: A missing, B the text "nan" | `A_ONLY_CORRECT` | the task does not ask to change dates; B turns missing dates into the text "nan" (rule 3) |
| [C0003](worked_examples/items/C0003.html) | ministral_rv/tr02__s1 | fill missing values (median / most frequent) | 95 cells: A still missing, B filled | `B_ONLY_CORRECT` | A leaves the values the task asks to fill (check "no missing values" fails); both leave signup_date missing, which a reasonable reading of "text columns" allows (rule 6) |
| [C0004](worked_examples/items/C0004.html) | ministral_rv/tr04__s0 | average monthly_spend per age group | A lists the two empty groups with a missing average, B omits them | `BOTH_ACCEPTABLE` | the task does not say whether empty groups are listed; the three non-empty groups agree (rule 6) |
| [C0005](worked_examples/items/C0005.html) | qwen_rv/tr03__s1 | churn rate per plan | A has no rate at all (all missing), B has rates near 0.3 | `B_ONLY_CORRECT` | an all-missing answer column is not an answer (rules 4 and 5) |

None of the seven exploratory drifts is a genuine `UNDETERMINABLE` case, so that code has no worked example (rule 7 defines it).
After coding, the A/B codes are translated with a separate key file (`coding_sheet.py decode`) that coders never see.
