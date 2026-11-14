### B.04 LOUD programs by target run status and exception type (run records)

- **Label: exploratory** (source: 17 l.598; 3 l.111; C-1 default, the plan gives no label).
- Inputs (sha256, first 12): models.tsv 93fc8c7f6f8f, per_program.jsonl dfd3b7dc406f, summary.json 064443d62d3e, tasks.json ac38b0787351
- B = 10000, seed = 20261111, tool sec_runrecords.py (204821872e53), created 2026-11-13T16:34:43+0900.
- LOUD = the frozen class of the pair block. exc_type is the exc_type of the target run record, for status error only. The LOUD rates are in the B.04 table of sec_pair_rates.py. Stratum-R rows are repeated without the ruled R tasks (LR61/LR70).

| variant | pair | model | stratum | target_status | exc_type | count |
|---|---|---|---|---|---|---|
| all tasks | E0a~E1 | anthropic__claude-haiku-4.5 | A | error | IntCastingNaNError | 2 |
| all tasks | E0a~E1 | anthropic__claude-haiku-4.5 | A | error | KeyError | 1 |
| all tasks | E0a~E1 | anthropic__claude-haiku-4.5 | A | error | ValueError | 2 |
| all tasks | E0a~E1 | anthropic__claude-haiku-4.5 | M | error | IntCastingNaNError | 1 |
| all tasks | E0a~E1 | anthropic__claude-haiku-4.5 | M | error | KeyError | 4 |
| all tasks | E0a~E1 | anthropic__claude-haiku-4.5 | M | error | ModuleNotFoundError | 14 |
| all tasks | E0a~E1 | anthropic__claude-haiku-4.5 | M | error | TypeError | 15 |
| all tasks | E0a~E1 | anthropic__claude-haiku-5.5 | M | error | KeyError | 3 |
| all tasks | E0a~E1 | anthropic__claude-sonnet-5.5 | M | error | KeyError | 1 |
| all tasks | E0a~E1 | anthropic__claude-sonnet-5.5 | M | error | TypeError | 2 |
| all tasks | E0a~E1 | deepseek__deepseek-v3.2 | A | error | IntCastingNaNError | 1 |
| all tasks | E0a~E1 | deepseek__deepseek-v3.2 | M | error | ValueError | 3 |
| all tasks | E0a~E1 | deepseek__deepseek-v3.2 | R | error | TypeError | 1 |
| all tasks | E0a~E1 | google__gemma-4-31b-it | A | error | ValueError | 5 |
| all tasks | E0a~E1 | google__gemma-4-31b-it | M | error | AttributeError | 4 |
| all tasks | E0a~E1 | google__gemma-4-31b-it | M | error | ModuleNotFoundError | 10 |
| all tasks | E0a~E1 | google__gemma-4-31b-it | M | error | TypeError | 2 |
| all tasks | E0a~E1 | google__gemma-4-31b-it | R | error | KeyError | 1 |
| all tasks | E0a~E1 | openai__gpt-5.4-mini | A | error | AttributeError | 5 |
| all tasks | E0a~E1 | openai__gpt-5.4-mini | A | error | ValueError | 9 |
| all tasks | E0a~E1 | openai__gpt-5.4-mini | M | error | AttributeError | 2 |
| all tasks | E0a~E1 | openai__gpt-5.4-mini | M | error | KeyError | 2 |
| all tasks | E0a~E1 | openai__gpt-5.4-mini | M | error | ValueError | 4 |
| all tasks | E0a~E1 | openai__gpt-oss-20b | A | error | IntCastingNaNError | 2 |
| all tasks | E0a~E1 | openai__gpt-oss-20b | A | error | KeyError | 7 |
| all tasks | E0a~E1 | openai__gpt-oss-20b | A | error | TypeError | 7 |
| all tasks | E0a~E1 | openai__gpt-oss-20b | A | error | ValueError | 4 |
| all tasks | E0a~E1 | openai__gpt-oss-20b | M | error | AttributeError | 4 |
| all tasks | E0a~E1 | openai__gpt-oss-20b | M | error | KeyError | 3 |
| all tasks | E0a~E1 | openai__gpt-oss-20b | M | error | OSError | 3 |
| all tasks | E0a~E1 | openai__gpt-oss-20b | M | error | TypeError | 11 |
| all tasks | E0a~E1 | openai__gpt-oss-20b | M | error | ValueError | 4 |
| all tasks | E0a~E1 | openai__gpt-oss-20b | R | error | TypeError | 3 |
| all tasks | E0a~E1 | qwen__qwen3.5-9b | A | error | AssertionError | 1 |
| all tasks | E0a~E1 | qwen__qwen3.5-9b | A | error | KeyError | 3 |
| all tasks | E0a~E1 | qwen__qwen3.5-9b | A | error | ValueError | 1 |
| all tasks | E0a~E1 | qwen__qwen3.5-9b | M | error | KeyError | 1 |
| all tasks | E0a~E1 | qwen__qwen3.5-9b | M | error | TypeError | 5 |
| all tasks | E0a~E1 | qwen__qwen3.5-9b | M | error | ValueError | 3 |
| all tasks | E0a~E1 | qwen__qwen3.5-9b | R | error | TypeError | 1 |
| all tasks | E0a~E1 | qwen__qwen3.6-35b-a3b | A | error | KeyError | 4 |
| all tasks | E0a~E1 | qwen__qwen3.6-35b-a3b | A | error | ValueError | 1 |
| all tasks | E0a~E1 | qwen__qwen3.6-35b-a3b | M | error | AttributeError | 3 |
| all tasks | E0a~E1 | qwen__qwen3.6-35b-a3b | M | error | KeyError | 6 |
| all tasks | E0a~E1 | qwen__qwen3.6-35b-a3b | M | error | ModuleNotFoundError | 1 |
| all tasks | E0a~E1 | qwen__qwen3.6-35b-a3b | M | error | OSError | 1 |
| all tasks | E0a~E1 | qwen__qwen3.6-35b-a3b | M | error | TypeError | 9 |
| all tasks | E0a~E1 | qwen__qwen3.6-35b-a3b | R | error | AttributeError | 1 |
| all tasks | E0a~E2 | anthropic__claude-haiku-4.5 | A | error | IntCastingNaNError | 2 |
| all tasks | E0a~E2 | anthropic__claude-haiku-4.5 | A | error | KeyError | 1 |
| all tasks | E0a~E2 | anthropic__claude-haiku-4.5 | A | error | ValueError | 2 |
| all tasks | E0a~E2 | anthropic__claude-haiku-4.5 | M | error | IntCastingNaNError | 1 |
| all tasks | E0a~E2 | anthropic__claude-haiku-4.5 | M | error | KeyError | 4 |
| all tasks | E0a~E2 | anthropic__claude-haiku-4.5 | M | error | ModuleNotFoundError | 14 |
| all tasks | E0a~E2 | anthropic__claude-haiku-4.5 | M | error | TypeError | 15 |
| all tasks | E0a~E2 | anthropic__claude-haiku-5.5 | M | error | KeyError | 3 |
| all tasks | E0a~E2 | anthropic__claude-sonnet-5.5 | M | error | KeyError | 1 |
| all tasks | E0a~E2 | anthropic__claude-sonnet-5.5 | M | error | TypeError | 2 |
| all tasks | E0a~E2 | deepseek__deepseek-v3.2 | A | error | IntCastingNaNError | 1 |
| all tasks | E0a~E2 | deepseek__deepseek-v3.2 | M | error | ValueError | 3 |
| all tasks | E0a~E2 | deepseek__deepseek-v3.2 | R | error | TypeError | 1 |
| all tasks | E0a~E2 | google__gemma-4-31b-it | A | error | ValueError | 5 |
| all tasks | E0a~E2 | google__gemma-4-31b-it | M | error | AttributeError | 4 |
| all tasks | E0a~E2 | google__gemma-4-31b-it | M | error | ModuleNotFoundError | 10 |
| all tasks | E0a~E2 | google__gemma-4-31b-it | M | error | TypeError | 2 |
| all tasks | E0a~E2 | google__gemma-4-31b-it | R | error | KeyError | 1 |
| all tasks | E0a~E2 | openai__gpt-5.4-mini | A | error | AttributeError | 5 |
| all tasks | E0a~E2 | openai__gpt-5.4-mini | A | error | ValueError | 9 |
| all tasks | E0a~E2 | openai__gpt-5.4-mini | M | error | AttributeError | 2 |
| all tasks | E0a~E2 | openai__gpt-5.4-mini | M | error | KeyError | 2 |
| all tasks | E0a~E2 | openai__gpt-5.4-mini | M | error | ValueError | 4 |
| all tasks | E0a~E2 | openai__gpt-5.6-terra | M | error | ValueError | 1 |
| all tasks | E0a~E2 | openai__gpt-oss-20b | A | error | IntCastingNaNError | 2 |
| all tasks | E0a~E2 | openai__gpt-oss-20b | A | error | KeyError | 7 |
| all tasks | E0a~E2 | openai__gpt-oss-20b | A | error | TypeError | 7 |
| all tasks | E0a~E2 | openai__gpt-oss-20b | A | error | ValueError | 4 |
| all tasks | E0a~E2 | openai__gpt-oss-20b | M | error | AttributeError | 4 |
| all tasks | E0a~E2 | openai__gpt-oss-20b | M | error | FileNotFoundError | 3 |
| all tasks | E0a~E2 | openai__gpt-oss-20b | M | error | KeyError | 3 |
| all tasks | E0a~E2 | openai__gpt-oss-20b | M | error | TypeError | 11 |
| all tasks | E0a~E2 | openai__gpt-oss-20b | M | error | ValueError | 4 |
| all tasks | E0a~E2 | openai__gpt-oss-20b | R | error | TypeError | 3 |
| all tasks | E0a~E2 | qwen__qwen3.5-9b | A | error | AssertionError | 1 |
| all tasks | E0a~E2 | qwen__qwen3.5-9b | A | error | AttributeError | 1 |
| all tasks | E0a~E2 | qwen__qwen3.5-9b | A | error | KeyError | 3 |
| all tasks | E0a~E2 | qwen__qwen3.5-9b | A | error | ValueError | 1 |
| all tasks | E0a~E2 | qwen__qwen3.5-9b | M | error | KeyError | 1 |
| all tasks | E0a~E2 | qwen__qwen3.5-9b | M | error | TypeError | 5 |
| all tasks | E0a~E2 | qwen__qwen3.5-9b | M | error | ValueError | 3 |
| all tasks | E0a~E2 | qwen__qwen3.5-9b | R | error | TypeError | 1 |
| all tasks | E0a~E2 | qwen__qwen3.6-35b-a3b | A | error | KeyError | 4 |
| all tasks | E0a~E2 | qwen__qwen3.6-35b-a3b | A | error | ValueError | 1 |
| all tasks | E0a~E2 | qwen__qwen3.6-35b-a3b | M | error | AttributeError | 3 |
| all tasks | E0a~E2 | qwen__qwen3.6-35b-a3b | M | error | FileNotFoundError | 1 |
| all tasks | E0a~E2 | qwen__qwen3.6-35b-a3b | M | error | KeyError | 6 |
| all tasks | E0a~E2 | qwen__qwen3.6-35b-a3b | M | error | ModuleNotFoundError | 1 |
| all tasks | E0a~E2 | qwen__qwen3.6-35b-a3b | M | error | TypeError | 9 |
| all tasks | E0a~E2 | qwen__qwen3.6-35b-a3b | R | error | AttributeError | 1 |
| without ruled R tasks (LR61/LR70) | E0a~E1 | deepseek__deepseek-v3.2 | R | error | TypeError | 1 |
| without ruled R tasks (LR61/LR70) | E0a~E1 | google__gemma-4-31b-it | R | error | KeyError | 1 |
| ... 8 more rows in the TSV | | | | | | |
