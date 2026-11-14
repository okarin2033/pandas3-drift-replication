### B.05 Warning-only programs by warning category (run records)

- **Label: exploratory** (source: 17 l.598; C-1 default, the plan gives no label).
- Inputs (sha256, first 12): models.tsv 93fc8c7f6f8f, per_program.jsonl dfd3b7dc406f, summary.json 064443d62d3e, tasks.json ac38b0787351
- B = 10000, seed = 20261111, tool sec_runrecords.py (204821872e53), created 2026-11-13T16:34:44+0900.
- Warning-only = the frozen flag of the pair block (class IDENTICAL or DTYPE_ONLY and a pandas warning signature on the target that the baseline run lacks). Category = category_qualname of those new warnings; a program with several categories is counted once in each, so the rows do not add up to the program count. Stratum-R rows are repeated without the ruled R tasks (LR61/LR70).

| variant | pair | model | stratum | category | programs | warning_only_programs |
|---|---|---|---|---|---|---|
| all tasks | E0a~E1 | anthropic__claude-haiku-4.5 | A | (any Future/Deprecation/PendingDeprecation) | 7 | 7 |
| all tasks | E0a~E1 | anthropic__claude-haiku-4.5 | A | Pandas4Warning | 7 | 7 |
| all tasks | E0a~E1 | anthropic__claude-haiku-4.5 | M | (any Future/Deprecation/PendingDeprecation) | 27 | 27 |
| all tasks | E0a~E1 | anthropic__claude-haiku-4.5 | M | Pandas4Warning | 27 | 27 |
| all tasks | E0a~E1 | anthropic__claude-haiku-5.5 | M | (any Future/Deprecation/PendingDeprecation) | 17 | 17 |
| all tasks | E0a~E1 | anthropic__claude-haiku-5.5 | M | Pandas4Warning | 17 | 17 |
| all tasks | E0a~E1 | anthropic__claude-sonnet-5.5 | M | (any Future/Deprecation/PendingDeprecation) | 5 | 5 |
| all tasks | E0a~E1 | anthropic__claude-sonnet-5.5 | M | Pandas4Warning | 5 | 5 |
| all tasks | E0a~E1 | deepseek__deepseek-v3.2 | A | (any Future/Deprecation/PendingDeprecation) | 5 | 5 |
| all tasks | E0a~E1 | deepseek__deepseek-v3.2 | A | Pandas4Warning | 5 | 5 |
| all tasks | E0a~E1 | deepseek__deepseek-v3.2 | M | (any Future/Deprecation/PendingDeprecation) | 6 | 6 |
| all tasks | E0a~E1 | deepseek__deepseek-v3.2 | M | Pandas4Warning | 6 | 6 |
| all tasks | E0a~E1 | google__gemma-4-31b-it | A | (any Future/Deprecation/PendingDeprecation) | 8 | 8 |
| all tasks | E0a~E1 | google__gemma-4-31b-it | A | Pandas4Warning | 8 | 8 |
| all tasks | E0a~E1 | google__gemma-4-31b-it | M | (any Future/Deprecation/PendingDeprecation) | 27 | 27 |
| all tasks | E0a~E1 | google__gemma-4-31b-it | M | Pandas4Warning | 27 | 27 |
| all tasks | E0a~E1 | openai__gpt-5.4-mini | M | (any Future/Deprecation/PendingDeprecation) | 8 | 8 |
| all tasks | E0a~E1 | openai__gpt-5.4-mini | M | Pandas4Warning | 8 | 8 |
| all tasks | E0a~E1 | openai__gpt-5.6-terra | A | (any Future/Deprecation/PendingDeprecation) | 1 | 1 |
| all tasks | E0a~E1 | openai__gpt-5.6-terra | A | Pandas4Warning | 1 | 1 |
| all tasks | E0a~E1 | openai__gpt-5.6-terra | M | (any Future/Deprecation/PendingDeprecation) | 9 | 9 |
| all tasks | E0a~E1 | openai__gpt-5.6-terra | M | Pandas4Warning | 9 | 9 |
| all tasks | E0a~E1 | openai__gpt-oss-20b | A | (any Future/Deprecation/PendingDeprecation) | 5 | 5 |
| all tasks | E0a~E1 | openai__gpt-oss-20b | A | Pandas4Warning | 5 | 5 |
| all tasks | E0a~E1 | openai__gpt-oss-20b | M | (any Future/Deprecation/PendingDeprecation) | 43 | 43 |
| all tasks | E0a~E1 | openai__gpt-oss-20b | M | Pandas4Warning | 43 | 43 |
| all tasks | E0a~E1 | qwen__qwen3.5-9b | A | (any Future/Deprecation/PendingDeprecation) | 8 | 8 |
| all tasks | E0a~E1 | qwen__qwen3.5-9b | A | Pandas4Warning | 8 | 8 |
| all tasks | E0a~E1 | qwen__qwen3.5-9b | M | (any Future/Deprecation/PendingDeprecation) | 6 | 6 |
| all tasks | E0a~E1 | qwen__qwen3.5-9b | M | Pandas4Warning | 6 | 6 |
| all tasks | E0a~E1 | qwen__qwen3.6-35b-a3b | A | (any Future/Deprecation/PendingDeprecation) | 11 | 11 |
| all tasks | E0a~E1 | qwen__qwen3.6-35b-a3b | A | Pandas4Warning | 11 | 11 |
| all tasks | E0a~E1 | qwen__qwen3.6-35b-a3b | M | (any Future/Deprecation/PendingDeprecation) | 30 | 30 |
| all tasks | E0a~E1 | qwen__qwen3.6-35b-a3b | M | Pandas4Warning | 30 | 30 |
| all tasks | E0a~E2 | anthropic__claude-haiku-4.5 | M | (any Future/Deprecation/PendingDeprecation) | 3 | 3 |
| all tasks | E0a~E2 | anthropic__claude-haiku-4.5 | M | Pandas4Warning | 3 | 3 |
| all tasks | E0a~E2 | anthropic__claude-haiku-5.5 | M | (any Future/Deprecation/PendingDeprecation) | 17 | 17 |
| all tasks | E0a~E2 | anthropic__claude-haiku-5.5 | M | Pandas4Warning | 17 | 17 |
| all tasks | E0a~E2 | anthropic__claude-sonnet-5.5 | M | (any Future/Deprecation/PendingDeprecation) | 5 | 5 |
| all tasks | E0a~E2 | anthropic__claude-sonnet-5.5 | M | Pandas4Warning | 5 | 5 |
| all tasks | E0a~E2 | deepseek__deepseek-v3.2 | M | (any Future/Deprecation/PendingDeprecation) | 3 | 3 |
| all tasks | E0a~E2 | deepseek__deepseek-v3.2 | M | Pandas4Warning | 3 | 3 |
| all tasks | E0a~E2 | google__gemma-4-31b-it | M | (any Future/Deprecation/PendingDeprecation) | 4 | 4 |
| all tasks | E0a~E2 | google__gemma-4-31b-it | M | Pandas4Warning | 4 | 4 |
| all tasks | E0a~E2 | openai__gpt-5.4-mini | M | (any Future/Deprecation/PendingDeprecation) | 8 | 8 |
| all tasks | E0a~E2 | openai__gpt-5.4-mini | M | Pandas4Warning | 8 | 8 |
| all tasks | E0a~E2 | openai__gpt-5.6-terra | A | (any Future/Deprecation/PendingDeprecation) | 1 | 1 |
| all tasks | E0a~E2 | openai__gpt-5.6-terra | A | Pandas4Warning | 1 | 1 |
| all tasks | E0a~E2 | openai__gpt-5.6-terra | M | (any Future/Deprecation/PendingDeprecation) | 9 | 9 |
| all tasks | E0a~E2 | openai__gpt-5.6-terra | M | Pandas4Warning | 9 | 9 |
| all tasks | E0a~E2 | qwen__qwen3.5-9b | A | (any Future/Deprecation/PendingDeprecation) | 1 | 1 |
| all tasks | E0a~E2 | qwen__qwen3.5-9b | A | Pandas4Warning | 1 | 1 |
| all tasks | E0a~E2 | qwen__qwen3.5-9b | M | (any Future/Deprecation/PendingDeprecation) | 1 | 1 |
| all tasks | E0a~E2 | qwen__qwen3.5-9b | M | Pandas4Warning | 1 | 1 |
| all tasks | E0a~E2 | qwen__qwen3.6-35b-a3b | A | (any Future/Deprecation/PendingDeprecation) | 1 | 1 |
| all tasks | E0a~E2 | qwen__qwen3.6-35b-a3b | A | Pandas4Warning | 1 | 1 |
| all tasks | E0a~E2 | qwen__qwen3.6-35b-a3b | M | (any Future/Deprecation/PendingDeprecation) | 8 | 8 |
| all tasks | E0a~E2 | qwen__qwen3.6-35b-a3b | M | Pandas4Warning | 8 | 8 |

Warning-only programs per cell:

| variant | pair | model | stratum | warning_only_programs |
|---|---|---|---|---|
| all tasks | E0a~E1 | anthropic__claude-haiku-4.5 | A | 7 |
| all tasks | E0a~E1 | anthropic__claude-haiku-4.5 | M | 27 |
| all tasks | E0a~E1 | anthropic__claude-haiku-5.5 | M | 17 |
| all tasks | E0a~E1 | anthropic__claude-sonnet-5.5 | M | 5 |
| all tasks | E0a~E1 | deepseek__deepseek-v3.2 | A | 5 |
| all tasks | E0a~E1 | deepseek__deepseek-v3.2 | M | 6 |
| all tasks | E0a~E1 | google__gemma-4-31b-it | A | 8 |
| all tasks | E0a~E1 | google__gemma-4-31b-it | M | 27 |
| all tasks | E0a~E1 | openai__gpt-5.4-mini | M | 8 |
| all tasks | E0a~E1 | openai__gpt-5.6-terra | A | 1 |
| all tasks | E0a~E1 | openai__gpt-5.6-terra | M | 9 |
| all tasks | E0a~E1 | openai__gpt-oss-20b | A | 5 |
| all tasks | E0a~E1 | openai__gpt-oss-20b | M | 43 |
| all tasks | E0a~E1 | qwen__qwen3.5-9b | A | 8 |
| all tasks | E0a~E1 | qwen__qwen3.5-9b | M | 6 |
| all tasks | E0a~E1 | qwen__qwen3.6-35b-a3b | A | 11 |
| all tasks | E0a~E1 | qwen__qwen3.6-35b-a3b | M | 30 |
| all tasks | E0a~E2 | anthropic__claude-haiku-4.5 | M | 3 |
| all tasks | E0a~E2 | anthropic__claude-haiku-5.5 | M | 17 |
| all tasks | E0a~E2 | anthropic__claude-sonnet-5.5 | M | 5 |
| all tasks | E0a~E2 | deepseek__deepseek-v3.2 | M | 3 |
| all tasks | E0a~E2 | google__gemma-4-31b-it | M | 4 |
| all tasks | E0a~E2 | openai__gpt-5.4-mini | M | 8 |
| all tasks | E0a~E2 | openai__gpt-5.6-terra | A | 1 |
| all tasks | E0a~E2 | openai__gpt-5.6-terra | M | 9 |
| all tasks | E0a~E2 | qwen__qwen3.5-9b | A | 1 |
| all tasks | E0a~E2 | qwen__qwen3.5-9b | M | 1 |
| all tasks | E0a~E2 | qwen__qwen3.6-35b-a3b | A | 1 |
| all tasks | E0a~E2 | qwen__qwen3.6-35b-a3b | M | 8 |
