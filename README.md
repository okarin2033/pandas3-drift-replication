# Replication package: Born Legacy, silent result drift of LLM-generated pandas code under pandas 3

Package version 1.0.0, built 2026-11-14. Author and licence holder: Evgenii Palii (ORCID 0009-0003-9031-0431).
Repository: https://github.com/okarin2033/pandas3-drift-replication. The DOI of the archived copy is added with the Zenodo deposit.
Citation: `CITATION.cff`. Licences: `LICENSE` (MIT, code) and `LICENSE-DATA` (CC BY 4.0, data, text and figures).

## Abstract
pandas 3.0.0 changed defaults; some changes alter the result of a program that still runs. This pre-registered study estimates how often version-agnostic pandas programs from large language models that run cleanly under pandas 2.3.3 return a different result under pandas 3.x without a warning. Ten models wrote five programs for each of 200 tasks (128 targeting confirmed changes, 9 real-question, 63 ordinary), and the 10,000 programs ran under pandas 2.3.3, 3.1.1 (primary) and 3.0.6. Silent drift affected 5.8% of clean programs on targeted tasks, 1.3% on ordinary tasks and 0 of 416 on real-question tasks. Two hypotheses were supported: drift concentrated in the string and datetime families (rate ratio 3.90, 95% interval 1.81 to 9.62), and pandas 2.3.3 warned about 1 of 38 drifting programs on untargeted tasks (97.4% unwarned, 75.0% to 100.0%). We did not detect a pilot's model gap (+1.20 percentage points, -2.63 to +5.06), a cutoff association (+0.99, -0.74 to +2.78) or a difference between two generations of one model line (+0.07, -1.85 to +2.23). Decisions were identical under pandas 3.0.6. Model coders (kappa 0.44, below threshold) judged only the 2.3.3 result correct in 71.2% of ordinary-task drift, too uncertain (0.0% to 94.1%) for a summary.

(Abstract of the article; numbers are those of the article.)

## Folder map
- `harness/`: the generation and run harness, the oracle, the analyzer (`analyze_full.py`), statistics, the fixture generator
  (`mkfix_full.py`), the task validator and the controls; `harness/gen_configs/`: the request settings of each model. `tools/`: helper
  code of the validator. `conventions/`: the schemas and the task template that the validator reads.
- `tasks/`: `tasks.json` is the task set of record (200 tasks with their specification cards). The task folders are under `tasks/M1`,
  `tasks/M2`, `tasks/R` and `tasks/A` (`task.json`, `reference.py` and, for stratum M, `naive.py`); `tasks/A_fresh` holds the 40
  candidate tasks from which 31 tasks of stratum A were taken. `prompts/` and `prompts_hint/`: the prompts as sent. Also the exposure
  patterns, the tables that the analyzer reads, the task build tools and the run records of the reference and naive solutions.
- `fixtures/`: the test data with its description. `mechanisms/`: the catalogue of documented behaviour changes with its confirmation
  programs (without copies of third-party pages). `models/`: the model list.
- `envs/`: definition files of the Python environments (freeze lists, probes, build script); no installed environments.
- `results/`: the registered analysis (hypothesis table `hypotheses.md`, `summary.json` and the per-program outcome table
  `per_program.jsonl`, stored as `per_program.jsonl.gz`; decompress it first). `results_t12/`: the same analysis with the resolved harm
  codes (source of the coded shares of H5). `results_round2/`: agreement of the second coding round. `results_hint/` and
  `results_sens/`: the version-hint ablation and the default-effort run, read by the secondary tools (the hypothesis table is produced
  for the main run only). `results_secondary/`: the secondary tables; `X-7.*` holds the provider data of the runs.
- `harm/`: coding of the harm of drifting programs (samples, the coders' codes, resolution, coding manuals, coder prompt and schema).
  The manuals are written for either kind of coder; all three coders were models (article, Section 3.6). `hand_attribution.tsv` holds
  the attribution that coder A gave for the double-coded sample; "hand attribution" is the registered name of this check.
- `generations_index/`: `program_hashes.tsv` (sha256 and size of every generated program: main run, version-hint ablation and
  default-effort run) and each model's `status.json` and `spend.json`. The programs and model replies themselves are not included.
- `logs/t11prep_2026-11-13/secondary/`: the tools of the secondary analyses. `logs/t11prep_2026-11-13/second_rating/second_rating.tsv`,
  `logs/t8_2026-11-13/h4_design.json` and `logs/repair5_2026-11-11/backup/oracle_before.py`: inputs of the analyzer command, kept at
  their study paths.
- `paper/`: the supplementary tables (`SUPPLEMENTARY_TABLES.md`), the figure data, the figures and the script `task_concentration.py`
  with its output.
- `MANIFEST_FREEZE.sha256`: the freeze manifest cited in the Supplement (hashes of the study files at the freeze, unchanged).
  `MANIFEST.sha256`: the two lines of the study manifest that pin the ruled lists the secondary tools check. `RUN_RECORDS.md`, `CHANGED_FILES.tsv`,
  `PACKAGE_MANIFEST.sha256`.

## Terms used in the files
`LRn`, "lead ruling": the numbered protocol decisions of the study, summarised in the Supplement. `REPAIRn`, `Tn`, `STAGE2`: dated build
and run steps; "brief": the written instruction of such a step. `pkg:NAME`, `drafted_by`, `status`: labels of the preparation workflow (names of work packages). Header comments give the
state at the time a file was written; the tools were run afterwards as the Supplement describes.

## Verify the files
`PACKAGE_MANIFEST.sha256` lists the sha256 of every file of this package (paths relative to the package root):
`( cd pandas3-drift-replication && shasum -a 256 -c PACKAGE_MANIFEST.sha256 )`.
Some files differ from the study copy: local paths were replaced by `<workspace>`, `<home>` or `<tmp>`, and internal labels and notes
of the preparation workflow were renamed or removed. `CHANGED_FILES.tsv` lists these files with the sha256 of the study copy and of this
copy. For a file of the freeze the study hash is the one in `MANIFEST_FREEZE.sha256`, with two exceptions, changed after the freeze and
before the registered analysis ran: `harness/analyze_full.py` (2026-11-13: one statement of `flatten()` corrected, so that the
denominators of the secondary pairs leave out programs whose own baseline did not run clean; the primary pairs are not affected) and
`harness/gen_configs/qwen__qwen3.5-9b.json` (provider setting). Section 1 of `MANIFEST_FREEZE.sha256` holds the sha256 of the plan, its
amendments and the rulings at the freeze; the dated files supplied on request can be checked against these hashes.
Files larger than 20 MB are stored gzip-compressed (`.gz`).

## Re-run the analysis
(1) The secondary tools (`logs/t11prep_2026-11-13/secondary/`) read `results/per_program.jsonl` and `results/summary.json` and run
from this package with a Python that has numpy (`envs/tools.freeze.txt`); they reproduce these tables of `results_secondary/`: B03,
B04, B05, B07, B09 to B17, B19, B20, B25 and B29 to B36. The other tables (B04_exc, B05_cat, B08, B10_new, B22, B38s, B40, X-1, X-3,
X-4, X-5, X-7) need the run records, the generated programs or the dated protocol files and cannot be re-run from the package.
(2) The per-program table itself is the output of the analyzer, which reads the raw run records (see `RUN_RECORDS.md`) and the
generated programs. The programs are not deposited, so this step is documented here and cannot be re-run from the package. The command
of record, run from the study folder (`$MODELS_CSV`: the ten model identifiers of `models/models.tsv`; `$SECOND_RATING`:
`logs/t11prep_2026-11-13/second_rating/second_rating.tsv`; `$D`: a log folder):
```
envs/tools/bin/python -I -B harness/analyze_full.py \
  --runs runs --tasks tasks/tasks.json --models "$MODELS_CSV" \
  --out results --gen-dir generations \
  --targets E0a~E1,E0a~E2 \
  --B 10000 --seed 20261111 \
  --h4-design logs/t8_2026-11-13/h4_design.json \
  --exposure tasks/exposure_regex.tsv \
  --dtype-signal default \
  --flags-before tasks/FLAGS_BEFORE_LR2.tsv \
  --flags-before-lr2-3 tasks/FLAGS_BEFORE_LR2_3.tsv \
  --card-variants-before-lr18 tasks/CARD_VARIANTS_BEFORE_LR18.json \
  --oracle-pre-lr1 logs/repair5_2026-11-11/backup/oracle_before.py \
  --second-rating $SECOND_RATING \
  > "$D/analyze_stdout.txt" 2> "$D/analyze_stderr.txt"
shasum -a 256 results/per_program.jsonl >> "$D/T11_LOG.md"        # C-25: the T12 identity check compares against this hash
```
The programs were run under pandas 2.3.3, 3.1.1 and 3.0.6; the environment definitions are in `envs/` (`pd233`, `pd31x`, `pd30x`, and
`pa` variants with pyarrow).

## What is not included
- Raw run records (`runs/`), see `RUN_RECORDS.md`.
- Generated programs and model replies: the hash table identifies each program.
- Installed Python environments, downloaded wheels and copies of third-party pages.
- Coding sheets with program texts and the stored replies of the coders.
- The unit tests of the harness and of the tools: they read files of the study folder that are not part of this package.
- The dated protocol files of the study (analysis plan, amendments, decision log), the step logs and the review files. The protocol is
  given in full in the Supplement of the article (Part A); the dated files are available from the author on request.
