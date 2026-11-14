# Supplementary tables

Supplementary tables (Part B of the supplementary material) of the article "Born Legacy: Silent Result Drift of LLM-Generated pandas Code under pandas 3".

Contents: Table S1 (protocol versions), Table S2 (spend), Tables S-R1 to S-R9 (results), and the data files of Figs. 1 to 4. Names and definitions follow the article: E0a = pandas 2.3.3 (baseline), E1 = pandas 3.1.1 (primary target), E2 = pandas 3.0.6, all without pyarrow; strata M (128 mechanism-targeted tasks), R (9 real-question tasks) and A (63 tasks not designed around a mechanism); "clean" = completes and is deterministic on 2.3.3; "silent" = SUBSTANTIVE value drift with no pandas warning in the target run. Intervals are task-cluster bootstrap 95% intervals unless marked otherwise.

## Table S1. Protocol versions: the dated amendments of the registered plan

| No. | Date (JST) | Content | Sections |
|---|---|---|---|
| 1 | 2026-11-11 | Applied in place after a critical review: primary target without pyarrow; order and dtype flags; SUBSTANTIVE silent drift as the primary outcome; H1 and H2 on stratum M; H4 on strata R and A; H5 by stratum with R as headline; exact bounds for the rare-drift branch; Haiku 4.5 lifecycle rule; H2b renamed; R paraphrase rule; version-hint ablation | 4.2 to 4.8 |
| 2 | 2026-11-11 | Per-family silent capacity of the naive solutions; H3 sensitivity on the 119 tasks with silent naive drift; third reading of H3 | 4.2 |
| 3 | 2026-11-11 | Order rule worded as the harness implements it; identity key `__index__` | 4.6 |
| 4 | 2026-11-11 | Dtype-propagation trace signal in attribution | 4.6 |
| 5 | 2026-11-11 | Python-originated warnings outside "pandas warning" | 4.6 |
| 6 | 2026-11-11 | CPython 3.12.13; run limits; at most two runs in parallel | 4.5 |
| 7 | 2026-11-11 | Blind invitation-strength ratings against the drifting idiom | 4.2 |
| 8 | 2026-11-11 | Terms of the Stack Exchange API; rule for a short R; writer of the remaining A intents | 4.2 |
| 9 | 2026-11-11 | Drafting and adoption of the materials; three card resolutions; coder B | 4.2, 4.8 |
| 10 | 2026-11-11 | Rulings LR1, LR2, LR3, LR7 and LR8: row identity in the order rule; one rule for `order_significant`; a reading of H3; additions to the Python-message list; seed of the spot-check sample | 4.2, 4.6, 4.7 |
| 11 | 2026-11-12 | Rulings LR13 to LR22: the order rule as a change of substance; rule for reader differences; six labelled sensitivities; card rule; novelty wording | 1, 4.2, 4.6 |
| 12 | 2026-11-13 | Rulings LR23 to LR66: decision rows; card sweep; scope of the card sensitivity and an added H5 report; blind fields; R_05 and R_08; validator rules; adoption; threat statement; independent cards; data facts in free-text fields | 4.1, 4.2, 4.8, 7 |
| 13 | 2026-11-13 | Calibration record (providers under rules P and P6, reasoning settings under rule T7.2a, token counts, k = 5, caps); rulings LR67 to LR76 (reading of a row identifier in the second rating; independent cards; report without R_08 on R + A; the freeze) | 4.2, 4.4 |
| 14 | 2026-11-13 | Rule P7 for a provider whose billed costs exceed its listed prices; provider of qwen/qwen3.5-9b set by it (SiliconFlow, fp8, place 3; 20 of 20 calibration calls) | 4.4, 7 |
| 15 | 2026-11-13 | Harm coding by model coders: coder A chosen by a fixed rule from the router's public model list, coder B as registered, a third model coder as tie-breaker with resolution by two of three; format check; attribution prompt for the double-coded sample; agreement labelled "model vs model" | 4.6, 4.8, 7 |

Amendments 14 and 15 change no hypothesis, threshold, sample size, studied model, statistic, task or generation prompt.

## Table S2. Spend by the generator's ledgers, in USD, against the caps of the protocol

| Item | Spent, USD | Cap, USD | Within cap |
|---|---|---|---|
| anthropic/claude-haiku-4.5 | 1.4074 | 4.53 | yes |
| anthropic/claude-haiku-5.5 | 0.1728 | 0.47 | yes |
| anthropic/claude-sonnet-5.5 | 3.6653 | 9.32 | yes |
| deepseek/deepseek-v3.2 | 2.3233 | 3.17 | yes |
| google/gemma-4-31b-it | 0.1340 | 0.39 | yes |
| openai/gpt-5.4-mini | 0.8980 | 3.98 | yes |
| openai/gpt-5.6-terra | 2.2100 | 10.61 | yes |
| openai/gpt-oss-20b | 0.0496 | 0.13 | yes |
| qwen/qwen3.5-9b | 0.1051 | 0.21 | yes |
| qwen/qwen3.6-35b-a3b | 0.0316 | 0.10 | yes |
| Main run, all models | 10.9973 | 30.00 | yes |
| Calibration | 0.2424 | 1.00 | yes |
| Version-hint ablation | 0.2710 | 1.00 | yes |
| Default-effort run | 0.2621 | 6.00 | yes |
| Harm coding (three model coders) | 12.8532 (coder A 11.8624, coder B 0.1863, third coder 0.8046; both rounds and the attribution) | 20.85 / 2.00 / 2.00 | yes / yes / yes |

The cap of coder A, 20.85 USD, follows the cost rule of ruling LR85.2 for the cap of Amendment 15 item 8: 0.2214 USD billed for the first eight items plus 1.5 times the projected 13.75 USD of the remaining 497 items (397 of the coding sample and 100 attribution items). A coder's cap covers both coding rounds (ruling LR87.4); coder A spent 9.6844 USD in the first round with the attribution and 2.1780 USD in the second round. The main-run total includes 0.00026 USD of calls to the second pin of qwen/qwen3.5-9b (Section 4.4 of the article). Calibration includes the calls of the earlier pins of two models and the 20 calls of the third provider of qwen/qwen3.5-9b.

## Table S-R1. Outcome distribution on E1 and generation process per model

| Model | IDENTICAL | DTYPE_ONLY | ORDER_ONLY | WARNING_ONLY | LOUD | Silent drift | Warned drift | Excluded on 2.3.3 | Calls logged | Empty extracted programs | Duplicate-body rate | Mean reasoning tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-20b | 224 | 527 | 0 | 48 | 48 | 59 | 9 | 85 | 1010 | 0 | 0.0% | 91.7 |
| gemma-4-31b-it | 241 | 636 | 0 | 35 | 22 | 53 | 5 | 8 | 2054 | 0 | 0.0% | 0.0 |
| claude-haiku-4.5 | 246 | 624 | 0 | 34 | 39 | 31 | 5 | 21 | 1000 | 0 | 3.8% | 0.0 |
| gpt-5.4-mini | 246 | 658 | 1 | 8 | 22 | 43 | 5 | 17 | 1006 | 2 | 1.4% | 0.0 |
| gpt-5.6-terra | 300 | 611 | 0 | 10 | 0 | 69 | 5 | 5 | 1001 | 0 | 9.8% | 0.0 |
| claude-haiku-5.5 | 257 | 692 | 0 | 17 | 3 | 25 | 5 | 1 | 1000 | 0 | 9.4% | 0.0 |
| claude-sonnet-5.5 | 264 | 704 | 0 | 5 | 3 | 19 | 5 | 0 | 1000 | 0 | 12.8% | 0.0 |
| qwen3.5-9b | 196 | 435 | 0 | 14 | 15 | 22 | 1 | 317 | 1007 | 2 | 0.0% | 0.0 |
| qwen3.6-35b-a3b | 252 | 592 | 0 | 41 | 26 | 37 | 5 | 47 | 1000 | 0 | 0.1% | 0.0 |
| deepseek-v3.2 | 255 | 673 | 0 | 11 | 5 | 34 | 4 | 18 | 1462 | 0 | 0.1% | 7061.1 |

Counts over the 1,000 generated programs of each model. No program was excluded for non-determinism. Calls logged: calls of the main run, including calls answered with an HTTP error. Empty extracted programs: replies from which the extraction rule gave no code. Duplicate-body rate: within-task rate of identical program bodies, as computed by the analysis. Mean reasoning tokens: per program, as reported by the endpoint.

## Table S-R2. Silent-drift rate per model and stratum: E1 in full, with the E2 counts

| Model | Stratum | E1 silent/clean | E1 rate | Wilson 95% | Bootstrap 95% | ICC | Design effect | Exact upper bound (design effect) | E2 silent/clean |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-20b | M | 49/591 | 8.3% | [6.3%, 10.8%] | [5.2%, 11.8%] | 0.506 | 2.831 | 12.14% | 42/591 |
| gpt-oss-20b | R | 0/38 | 0.0% | [0.0%, 9.2%] | [0.0%, 0.0%] | 0.000 | 1.750 | 12.89% | 0/38 |
| gpt-oss-20b | A | 10/286 | 3.5% | [1.9%, 6.3%] | [0.7%, 7.0%] | 0.363 | 2.285 | 7.56% | 10/286 |
| gemma-4-31b-it | M | 48/638 | 7.5% | [5.7%, 9.8%] | [4.1%, 11.4%] | 0.630 | 3.510 | 11.57% | 45/638 |
| gemma-4-31b-it | R | 0/41 | 0.0% | [0.0%, 8.6%] | [0.0%, 0.0%] | 0.000 | 1.711 | 11.75% | 0/41 |
| gemma-4-31b-it | A | 5/313 | 1.6% | [0.7%, 3.7%] | [0.0%, 4.8%] | 1.000 | 4.968 | 7.33% | 5/313 |
| claude-haiku-4.5 | M | 25/629 | 4.0% | [2.7%, 5.8%] | [1.4%, 6.9%] | 0.771 | 4.019 | 7.61% | 24/629 |
| claude-haiku-4.5 | R | 0/45 | 0.0% | [0.0%, 7.9%] | [0.0%, 0.0%] | 0.000 | 1.800 | 11.29% | 0/45 |
| claude-haiku-4.5 | A | 6/305 | 2.0% | [0.9%, 4.2%] | [0.0%, 5.7%] | 0.842 | 4.233 | 7.30% | 6/305 |
| gpt-5.4-mini | M | 43/635 | 6.8% | [5.1%, 9.0%] | [3.5%, 10.5%] | 0.702 | 3.780 | 10.87% | 35/635 |
| gpt-5.4-mini | R | 0/38 | 0.0% | [0.0%, 9.2%] | [0.0%, 0.0%] | 0.000 | 1.750 | 12.89% | 0/38 |
| gpt-5.4-mini | A | 0/310 | 0.0% | [0.0%, 1.2%] | [0.0%, 0.0%] | 0.000 | 1.784 | 1.71% | 0/310 |
| gpt-5.6-terra | M | 64/636 | 10.1% | [8.0%, 12.6%] | [5.8%, 14.8%] | 0.844 | 4.351 | 15.13% | 51/636 |
| gpt-5.6-terra | R | 0/45 | 0.0% | [0.0%, 7.9%] | [0.0%, 0.0%] | 0.000 | 1.800 | 11.29% | 0/45 |
| gpt-5.6-terra | A | 5/314 | 1.6% | [0.7%, 3.7%] | [0.0%, 4.8%] | 1.000 | 4.984 | 7.32% | 5/314 |
| claude-haiku-5.5 | M | 25/640 | 3.9% | [2.7%, 5.7%] | [1.4%, 6.7%] | 0.648 | 3.593 | 7.22% | 25/640 |
| claude-haiku-5.5 | R | 0/45 | 0.0% | [0.0%, 7.9%] | [0.0%, 0.0%] | 0.000 | 1.800 | 11.29% | 0/45 |
| claude-haiku-5.5 | A | 0/314 | 0.0% | [0.0%, 1.2%] | [0.0%, 0.0%] | 0.000 | 1.797 | 1.70% | 0/314 |
| claude-sonnet-5.5 | M | 19/640 | 3.0% | [1.9%, 4.6%] | [0.6%, 5.9%] | 0.865 | 4.461 | 6.51% | 14/640 |
| claude-sonnet-5.5 | R | 0/45 | 0.0% | [0.0%, 7.9%] | [0.0%, 0.0%] | 0.000 | 1.800 | 11.29% | 0/45 |
| claude-sonnet-5.5 | A | 0/315 | 0.0% | [0.0%, 1.2%] | [0.0%, 0.0%] | 0.000 | 1.800 | 1.70% | 0/315 |
| qwen3.5-9b | M | 19/456 | 4.2% | [2.7%, 6.4%] | [1.7%, 7.2%] | 0.531 | 2.375 | 7.39% | 18/456 |
| qwen3.5-9b | R | 0/32 | 0.0% | [0.0%, 10.7%] | [0.0%, 0.0%] | 0.000 | 1.511 | 13.19% | 0/32 |
| qwen3.5-9b | A | 3/195 | 1.5% | [0.5%, 4.4%] | [0.0%, 3.5%] | 0.131 | 1.419 | 4.63% | 3/195 |
| qwen3.6-35b-a3b | M | 30/612 | 4.9% | [3.5%, 6.9%] | [2.9%, 7.2%] | 0.300 | 2.134 | 7.55% | 30/612 |
| qwen3.6-35b-a3b | R | 0/43 | 0.0% | [0.0%, 8.2%] | [0.0%, 0.0%] | 0.000 | 1.756 | 11.51% | 0/43 |
| qwen3.6-35b-a3b | A | 7/298 | 2.3% | [1.1%, 4.8%] | [0.0%, 6.3%] | 0.725 | 3.705 | 7.42% | 7/298 |
| deepseek-v3.2 | M | 33/629 | 5.2% | [3.8%, 7.3%] | [2.7%, 8.0%] | 0.464 | 2.818 | 8.41% | 32/629 |
| deepseek-v3.2 | R | 0/44 | 0.0% | [0.0%, 8.0%] | [0.0%, 0.0%] | 0.000 | 1.778 | 11.40% | 0/44 |
| deepseek-v3.2 | A | 1/309 | 0.3% | [0.1%, 1.8%] | [0.0%, 1.0%] | 0.000 | 1.781 | 2.29% | 1/309 |

Wilson: naive 95% interval at program level. ICC: ANOVA estimator per model and stratum; design effect = 1 + (m - 1) x ICC with the ICC truncated at 0 and at least 0.20. Exact upper bound: one-sided 95% Clopper-Pearson bound on the design-effect-adjusted sample size.

## Table S-R3. Stratum R without task R_08 (added report; decides nothing)

| Model | Stratum R without R_08: silent/clean | Exact upper bound |
|---|---|---|
| gpt-oss-20b | 0/33 | 14.63% |
| gemma-4-31b-it | 0/36 | 13.19% |
| claude-haiku-4.5 | 0/40 | 12.61% |
| gpt-5.4-mini | 0/33 | 14.63% |
| gpt-5.6-terra | 0/40 | 12.61% |
| claude-haiku-5.5 | 0/40 | 12.61% |
| claude-sonnet-5.5 | 0/40 | 12.61% |
| qwen3.5-9b | 0/27 | 15.10% |
| qwen3.6-35b-a3b | 0/38 | 12.89% |
| deepseek-v3.2 | 0/39 | 12.75% |

R_08 carries a fidelity FAIL (Section 4.2 of the article); 50 programs are left out.

## Table S-R4. Silent drift on E1 per model and mechanism family, stratum M (silent/clean and rate)

| Model | QF1 | QF2 | QF3 | QF4 | QF5 | QF6 | QF7 | QF8 |
|---|---|---|---|---|---|---|---|---|
| gpt-oss-20b | 16/77 20.8% | 13/71 18.3% | 0/73 0.0% | 12/73 16.4% | 3/78 3.8% | 5/70 7.1% | 0/77 0.0% | 0/72 0.0% |
| gemma-4-31b-it | 12/80 15.0% | 9/80 11.2% | 0/80 0.0% | 5/80 6.2% | 7/80 8.8% | 15/80 18.8% | 0/80 0.0% | 0/78 0.0% |
| claude-haiku-4.5 | 4/75 5.3% | 9/79 11.4% | 0/80 0.0% | 0/80 0.0% | 0/80 0.0% | 12/77 15.6% | 0/80 0.0% | 0/78 0.0% |
| gpt-5.4-mini | 6/80 7.5% | 17/80 21.2% | 0/80 0.0% | 4/79 5.1% | 4/78 5.1% | 12/80 15.0% | 0/78 0.0% | 0/80 0.0% |
| gpt-5.6-terra | 11/79 13.9% | 20/80 25.0% | 0/80 0.0% | 4/78 5.1% | 7/80 8.8% | 22/80 27.5% | 0/79 0.0% | 0/80 0.0% |
| claude-haiku-5.5 | 0/80 0.0% | 14/80 17.5% | 0/80 0.0% | 1/80 1.2% | 3/80 3.8% | 7/80 8.8% | 0/80 0.0% | 0/80 0.0% |
| claude-sonnet-5.5 | 5/80 6.2% | 6/80 7.5% | 0/80 0.0% | 5/80 6.2% | 0/80 0.0% | 3/80 3.8% | 0/80 0.0% | 0/80 0.0% |
| qwen3.5-9b | 7/62 11.3% | 8/47 17.0% | 0/60 0.0% | 1/56 1.8% | 0/51 0.0% | 3/53 5.7% | 0/75 0.0% | 0/52 0.0% |
| qwen3.6-35b-a3b | 17/79 21.5% | 6/74 8.1% | 0/78 0.0% | 4/76 5.3% | 0/76 0.0% | 3/78 3.8% | 0/79 0.0% | 0/72 0.0% |
| deepseek-v3.2 | 5/79 6.3% | 13/76 17.1% | 1/79 1.3% | 2/78 2.6% | 1/79 1.3% | 11/80 13.8% | 0/79 0.0% | 0/79 0.0% |

## Table S-R5. Silent drift on E1 per catalogue row, stratum M (exploratory)

| Catalogue row | Silent/clean (ten models) | Model-equal rate [95% interval] |
|---|---|---|
| N06 | 87/176 | 47.8% [14.0%, 76.0%] |
| D07 | 19/50 | 38.0% [38.0%, 38.0%] |
| D04 | 29/86 | 30.5% [0.0%, 46.6%] |
| D01 | 29/96 | 30.3% [2.0%, 61.5%] |
| D03 | 28/92 | 29.1% [12.0%, 46.5%] |
| S06 | 32/145 | 22.0% [0.0%, 48.0%] |
| S02 | 27/144 | 19.2% [6.0%, 40.0%] |
| D08 | 9/49 | 18.0% [18.0%, 18.0%] |
| G02 | 19/140 | 13.0% [0.0%, 38.0%] |
| R05 | 17/199 | 8.5% [0.0%, 24.4%] |
| S01 | 16/196 | 8.1% [6.0%, 10.5%] |
| G06 | 6/94 | 6.8% [0.0%, 15.0%] |
| S03 | 8/142 | 5.3% [0.0%, 14.0%] |
| R04 | 8/189 | 4.0% [0.0%, 13.3%] |
| G01 | 5/141 | 3.6% [0.0%, 6.0%] |
| N02 | 6/194 | 3.1% [0.0%, 11.0%] |
| G03 | 4/143 | 2.8% [0.0%, 6.0%] |
| G05 | 2/95 | 2.5% [0.0%, 4.0%] |
| G04 | 2/147 | 1.3% [0.0%, 4.0%] |
| C06 | 1/94 | 1.0% [0.0%, 2.0%] |
| D02 | 1/96 | 1.0% [0.0%, 2.0%] |
| C01 | 0/147 | 0.0% [0.0%, 0.0%] |
| C02 | 0/146 | 0.0% [0.0%, 0.0%] |
| C03 | 0/144 | 0.0% [0.0%, 0.0%] |
| C04 | 0/147 | 0.0% [0.0%, 0.0%] |
| C05 | 0/92 | 0.0% [0.0%, 0.0%] |
| D05 | 0/87 | 0.0% [0.0%, 0.0%] |
| D06 | 0/96 | 0.0% [0.0%, 0.0%] |
| D09 | 0/47 | 0.0% [0.0%, 0.0%] |
| D10 | 0/48 | 0.0% [0.0%, 0.0%] |
| I01 | 0/200 | 0.0% [0.0%, 0.0%] |
| I02 | 0/197 | 0.0% [0.0%, 0.0%] |
| I05 | 0/196 | 0.0% [0.0%, 0.0%] |
| I06 | 0/194 | 0.0% [0.0%, 0.0%] |
| N01 | 0/192 | 0.0% [0.0%, 0.0%] |
| N05 | 0/196 | 0.0% [0.0%, 0.0%] |
| O01 | 0/144 | 0.0% [0.0%, 0.0%] |
| R01 | 0/188 | 0.0% [0.0%, 0.0%] |
| R02 | 0/186 | 0.0% [0.0%, 0.0%] |
| X01 | 0/383 | 0.0% [0.0%, 0.0%] |
| X02 | 0/368 | 0.0% [0.0%, 0.0%] |

Rows ordered by the model-equal rate. A row's tasks are the M tasks whose quota row it is; rows with one task have a degenerate interval.

## Table S-R6. Tasks that carry silent drift on E1

| Task | Stratum | Family | Silent programs (of 50) | Models with a silent program | Primary labels (count) |
|---|---|---|---|---|---|
| M_QF6_08 | M | QF6_NA_DTYPE | 30 | 9 | N06:30 |
| M_QF2_04 | M | QF2_DATETIME | 29 | 8 | D01:15;N04:4;D04:4;D05:3;R06:3 |
| M_QF2_01 | M | QF2_DATETIME | 28 | 9 | D01:18;S03:6;R06:3;D05:1 |
| M_QF6_16 | M | QF6_NA_DTYPE | 28 | 9 | N06:27;R06:1 |
| A_DATE_05 | A | DATE | 25 | 7 | D01:25 |
| M_QF1_04 | M | QF1_STRING | 24 | 8 | S06:11;UNATTRIBUTED:5;R05:4;G01:3;S03:1 |
| M_QF2_03 | M | QF2_DATETIME | 22 | 9 | D03:18;D01:4 |
| M_QF6_12 | M | QF6_NA_DTYPE | 22 | 7 | N06:22 |
| M_QF1_02 | M | QF1_STRING | 19 | 7 | QF1:15;S01:2;S02:2 |
| M_QF2_07 | M | QF2_DATETIME | 19 | 6 | D02:14;D01:4;S03:1 |
| M_QF4_08 | M | QF4_GROUPBY | 19 | 6 | G02:18;R06:1 |
| M_QF5_04 | M | QF5_ORDER | 15 | 4 | R05:15 |
| M_QF2_08 | M | QF2_DATETIME | 9 | 2 | D08:9 |
| M_QF1_14 | M | QF1_STRING | 8 | 2 | S03:2;G02:2;R05:1;R06:1;G01:1;S06:1 |
| M_QF5_15 | M | QF5_ORDER | 8 | 4 | R04:8 |
| M_QF1_03 | M | QF1_STRING | 7 | 3 | S03:7 |
| M_QF6_04 | M | QF6_NA_DTYPE | 7 | 3 | N06:7 |
| M_QF2_13 | M | QF2_DATETIME | 6 | 4 | D03:3;D01:3 |
| M_QF4_12 | M | QF4_GROUPBY | 6 | 3 | S03:6 |
| M_QF1_01 | M | QF1_STRING | 5 | 2 | S03:5 |
| M_QF1_07 | M | QF1_STRING | 5 | 2 | S03:5 |
| M_QF1_11 | M | QF1_STRING | 5 | 4 | S01:5 |
| A_TS_04 | A | TS | 4 | 4 | D03:4 |
| M_QF6_06 | M | QF6_NA_DTYPE | 4 | 2 | G07:4 |
| A_UPD_01 | A | UPD | 3 | 1 | QF1:3 |
| M_QF1_06 | M | QF1_STRING | 3 | 2 | S01:3 |
| M_QF1_12 | M | QF1_STRING | 3 | 3 | S03:3 |
| M_QF1_16 | M | QF1_STRING | 3 | 2 | S01:3 |
| M_QF4_13 | M | QF4_GROUPBY | 3 | 1 | G01:3 |
| M_QF4_15 | M | QF4_GROUPBY | 3 | 2 | S03:3 |
| M_QF4_01 | M | QF4_GROUPBY | 2 | 1 | G01:2 |
| M_QF4_04 | M | QF4_GROUPBY | 2 | 2 | S03:2 |
| M_QF4_11 | M | QF4_GROUPBY | 2 | 1 | S03:2 |
| M_QF6_10 | M | QF6_NA_DTYPE | 2 | 1 | N01:2 |
| A_DATE_01 | A | DATE | 1 | 1 | S03:1 |
| A_DATE_04 | A | DATE | 1 | 1 | S03:1 |
| A_MRG_05 | A | MRG | 1 | 1 | S01:1 |
| A_PIV_05 | A | PIV | 1 | 1 | QF1:1 |
| A_TXT_06 | A | TXT | 1 | 1 | N04:1 |
| M_QF1_08 | M | QF1_STRING | 1 | 1 | S03:1 |
| M_QF2_11 | M | QF2_DATETIME | 1 | 1 | D01:1 |
| M_QF2_12 | M | QF2_DATETIME | 1 | 1 | D01:1 |
| M_QF3_12 | M | QF3_COW | 1 | 1 | QF1:1 |
| M_QF4_03 | M | QF4_GROUPBY | 1 | 1 | QF1:1 |
| M_QF5_08 | M | QF5_ORDER | 1 | 1 | R05:1 |
| M_QF5_16 | M | QF5_ORDER | 1 | 1 | R05:1 |

Counted from the per-program outcome table (script `task_concentration.py` of the replication package). Primary labels: attribution of the silent programs of the task.

## Table S-R7. Harm of the programs that drift on E1, stratum M by family: automatic pre-label against the reference solutions and coded H5

| Family | Drift programs | Pre-label HARM_3X | Pre-label FIX_3X | Pre-label NEITHER | Coded H5 |
|---|---|---|---|---|---|
| QF1 | 83 | 63.9% [32.8%, 90.6%] | 19.3% [3.2%, 52.3%] | 16.9% [0.0%, 40.5%] | HARM_3X 71.7% [40.8%, 92.1%]; FIX_3X 19.0% [3.5%, 52.2%]; BOTH_ACCEPTABLE 0.0%; NEITHER 9.3% [0.0%, 23.3%]; UNDETERMINABLE 0.0% (74 coded) |
| QF2 | 159 | 67.9% [29.2%, 98.8%] | 29.6% [0.0%, 69.0%] | 2.5% [0.0%, 6.3%] | HARM_3X 49.9% [12.1%, 93.8%]; FIX_3X 2.9% [0.0%, 7.5%]; BOTH_ACCEPTABLE 46.5% [0.0%, 86.5%]; NEITHER 0.7% [0.0%, 2.3%]; UNDETERMINABLE 0.0% (144 coded) |
| QF3 | 5 | 100.0% [100.0%, 100.0%] | 0.0% [0.0%, 0.0%] | 0.0% [0.0%, 0.0%] | HARM_3X 80.0% [75.0%, 100.0%]; FIX_3X 0.0%; BOTH_ACCEPTABLE 0.0%; NEITHER 0.0%; UNDETERMINABLE 20.0% [0.0%, 25.0%] (5 coded) |
| QF4 | 38 | 10.5% [0.0%, 50.0%] | 76.3% [15.4%, 96.3%] | 13.2% [0.0%, 55.6%] | HARM_3X 2.9% [0.0%, 15.6%]; FIX_3X 85.6% [35.5%, 100.0%]; BOTH_ACCEPTABLE 8.6% [0.0%, 40.9%]; NEITHER 2.9% [0.0%, 19.5%]; UNDETERMINABLE 0.0% (36 coded) |
| QF5 | 25 | 96.0% [0.0%, 100.0%] | 0.0% [0.0%, 0.0%] | 4.0% [0.0%, 100.0%] | HARM_3X 96.0% [0.0%, 100.0%]; FIX_3X 0.0%; BOTH_ACCEPTABLE 4.0% [0.0%, 100.0%]; NEITHER 0.0%; UNDETERMINABLE 0.0% (23 coded) |
| QF6 | 93 | 0.0% [0.0%, 0.0%] | 96.8% [96.0%, 100.0%] | 3.2% [0.0%, 4.0%] | HARM_3X 0.0%; FIX_3X 96.4% [95.7%, 100.0%]; BOTH_ACCEPTABLE 0.0%; NEITHER 3.6% [0.0%, 4.3%]; UNDETERMINABLE 0.0% (85 coded) |
| QF7 | 0 | no drift program |  |  | no drift program |
| QF8 | 0 | no drift program |  |  | no drift program |

The pre-label is not the coded H5. HARM_3X: only the 2.3.3 result matches the reference; FIX_3X: only the 3.1.1 result matches.

## Table S-R8. Exception types of the LOUD programs on E1

| Exception type of LOUD programs on E1 | Programs |
|---|---|
| TypeError | 56 |
| KeyError | 36 |
| ValueError | 36 |
| ModuleNotFoundError | 25 |
| AttributeError | 19 |
| IntCastingNaNError | 6 |
| OSError | 4 |
| AssertionError | 1 |

All 183 LOUD programs on E1 ended with an exception (status "error"); no run reached a time or memory limit.

## Table S-R9. Agreement of coder A and coder B, model vs model, in the two coding rounds

| Round | Coder prompt | Programs | Cohen's kappa [95% interval] | Gwet's AC1 [95% interval] | Raw agreement [95% interval] | Threshold kappa >= 0.60 |
|---|---|---|---|---|---|---|
| 1 | manual as frozen | 100 (double-coded sample) | 0.437 [0.201, 0.661] | 0.531 [0.271, 0.757] | 61.0% [40.4%, 79.5%] | not met |
| 2 | manual revised once on the pilot's five worked examples | 100 (fresh sample, outside the round-1 double-coded sample) | 0.316 [0.076, 0.523] | 0.377 [0.112, 0.632] | 49.0% [28.4%, 69.4%] | not met |

Intervals: task-cluster bootstrap, B = 10,000. Round 1: the third coder coded the 39 programs on which the two coders differ; 38 were resolved to coder A's code and one is UNDETERMINABLE. Round 2 is coded by coder A and coder B only and is reported as agreement; coder A gave 98 of its 100 programs the code of its first round (an added descriptive figure, ruling LR87.5). H5 and all harm tables use the resolved codes of round 1.

## Data files of the figures

- `fig1_silent_rate_per_model.tsv` (Fig. 1): one row per model and stratum on E1 with silent and clean counts, rate, Wilson and bootstrap limits and the exact upper bound.
- `fig2_family_heatmap.tsv` (Fig. 2): one row per model and family of stratum M with silent and clean counts and the rate.
- `fig3_warning_status.tsv` (Fig. 3): one row per group (strata R + A; each family of stratum M) with the drift programs on E1 and their counts unwarned and warned on 2.3.3.
- Fig. 4 (harm shares by stratum): `fig4_harm_shares.tsv`: 24 rows, one per stratum (A, R + A, M), source and category (coded: the five codes; prelabel: HARM_3X, FIX_3X and NEITHER, the only pre-labels that occur), with the share and its interval.
