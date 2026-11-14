### B.10 Static idiom shares, new regexes for the four examples of section 17

- **Label: secondary** (source: 16 W4 l.577; 17 l.599-600).
- Inputs (sha256, first 12): idiom_regex_sec17.tsv 527de9b530e4, models.tsv 93fc8c7f6f8f, per_program.jsonl dfd3b7dc406f, summary.json 064443d62d3e, tasks.json ac38b0787351
- B = 10000, seed = 20261111, tool sec_idioms_text.py (df98e87245f0), created 2026-11-13T16:49:52+0900.
- Denominator: generated non-empty programs (empty_source false) whose file was found, not pair-clean. Wilson 95% only. The clause "on columns with missing values" (section 17, astype(str)) is not expressible on program text: every astype(str) is counted, whether or not the column holds missing values. Programs scanned: 9996; program files not found: 0 (left out of the denominators). Stratum-R rows are repeated without the ruled R tasks (LR61/LR70). No cell is singled out in the text unless a rule fixed before T11 selects it. Note on the regex for integer epochs (N03, LR83.4 f, LR84.3 c): a text scan cannot see the unit of the datetime, so N03 matches every cast of a date or time to int64 on a line with a date or time word, and also some other casts to int64 (for example an int64 cast of a timedelta component on such a line). The share of N03 is a share of programs with such a cast, not of programs that compute epochs in seconds. The four regexes are fixed and were not revised after programs were read.

| variant | model | stratum | idiom | family | x | n | empty_programs | share | wilson_lo | wilson_hi |
|---|---|---|---|---|---|---|---|---|---|---|
| all tasks | anthropic__claude-haiku-4.5 | M | ANY |  | 42 | 640 | 0 | 0.066 | 0.049 | 0.088 |
| all tasks | anthropic__claude-haiku-4.5 | R | ANY |  | 0 | 45 | 0 | 0.000 | 0.000 | 0.079 |
| all tasks | anthropic__claude-haiku-4.5 | A | ANY |  | 60 | 315 | 0 | 0.190 | 0.151 | 0.237 |
| all tasks | anthropic__claude-haiku-5.5 | M | ANY |  | 234 | 640 | 0 | 0.366 | 0.329 | 0.404 |
| all tasks | anthropic__claude-haiku-5.5 | R | ANY |  | 6 | 45 | 0 | 0.133 | 0.063 | 0.262 |
| all tasks | anthropic__claude-haiku-5.5 | A | ANY |  | 186 | 315 | 0 | 0.590 | 0.535 | 0.643 |
| all tasks | anthropic__claude-sonnet-5.5 | M | ANY |  | 261 | 640 | 0 | 0.408 | 0.370 | 0.446 |
| all tasks | anthropic__claude-sonnet-5.5 | R | ANY |  | 0 | 45 | 0 | 0.000 | 0.000 | 0.079 |
| all tasks | anthropic__claude-sonnet-5.5 | A | ANY |  | 126 | 315 | 0 | 0.400 | 0.347 | 0.455 |
| all tasks | deepseek__deepseek-v3.2 | M | ANY |  | 199 | 640 | 0 | 0.311 | 0.276 | 0.348 |
| all tasks | deepseek__deepseek-v3.2 | R | ANY |  | 11 | 45 | 0 | 0.244 | 0.142 | 0.387 |
| all tasks | deepseek__deepseek-v3.2 | A | ANY |  | 128 | 315 | 0 | 0.406 | 0.354 | 0.461 |
| all tasks | google__gemma-4-31b-it | M | ANY |  | 92 | 640 | 0 | 0.144 | 0.119 | 0.173 |
| all tasks | google__gemma-4-31b-it | R | ANY |  | 5 | 45 | 0 | 0.111 | 0.048 | 0.235 |
| all tasks | google__gemma-4-31b-it | A | ANY |  | 73 | 315 | 0 | 0.232 | 0.189 | 0.281 |
| all tasks | openai__gpt-5.4-mini | M | ANY |  | 185 | 639 | 1 | 0.290 | 0.256 | 0.326 |
| all tasks | openai__gpt-5.4-mini | R | ANY |  | 11 | 45 | 0 | 0.244 | 0.142 | 0.387 |
| all tasks | openai__gpt-5.4-mini | A | ANY |  | 177 | 314 | 1 | 0.564 | 0.508 | 0.617 |
| all tasks | openai__gpt-5.6-terra | M | ANY |  | 125 | 640 | 0 | 0.195 | 0.166 | 0.228 |
| all tasks | openai__gpt-5.6-terra | R | ANY |  | 0 | 45 | 0 | 0.000 | 0.000 | 0.079 |
| all tasks | openai__gpt-5.6-terra | A | ANY |  | 33 | 315 | 0 | 0.105 | 0.076 | 0.143 |
| all tasks | openai__gpt-oss-20b | M | ANY |  | 74 | 640 | 0 | 0.116 | 0.093 | 0.143 |
| all tasks | openai__gpt-oss-20b | R | ANY |  | 1 | 45 | 0 | 0.022 | 0.004 | 0.116 |
| all tasks | openai__gpt-oss-20b | A | ANY |  | 61 | 315 | 0 | 0.194 | 0.154 | 0.241 |
| all tasks | qwen__qwen3.5-9b | M | ANY |  | 72 | 638 | 2 | 0.113 | 0.091 | 0.140 |
| all tasks | qwen__qwen3.5-9b | R | ANY |  | 8 | 45 | 0 | 0.178 | 0.093 | 0.313 |
| all tasks | qwen__qwen3.5-9b | A | ANY |  | 90 | 315 | 0 | 0.286 | 0.239 | 0.338 |
| all tasks | qwen__qwen3.6-35b-a3b | M | ANY |  | 120 | 640 | 0 | 0.188 | 0.159 | 0.220 |
| all tasks | qwen__qwen3.6-35b-a3b | R | ANY |  | 8 | 45 | 0 | 0.178 | 0.093 | 0.313 |
| all tasks | qwen__qwen3.6-35b-a3b | A | ANY |  | 115 | 315 | 0 | 0.365 | 0.314 | 0.420 |
| without ruled R tasks (LR61/LR70) | anthropic__claude-haiku-4.5 | R | ANY |  | 0 | 40 | 0 | 0.000 | 0.000 | 0.088 |
| without ruled R tasks (LR61/LR70) | anthropic__claude-haiku-5.5 | R | ANY |  | 5 | 40 | 0 | 0.125 | 0.055 | 0.261 |
| without ruled R tasks (LR61/LR70) | anthropic__claude-sonnet-5.5 | R | ANY |  | 0 | 40 | 0 | 0.000 | 0.000 | 0.088 |
| without ruled R tasks (LR61/LR70) | deepseek__deepseek-v3.2 | R | ANY |  | 9 | 40 | 0 | 0.225 | 0.123 | 0.375 |
| without ruled R tasks (LR61/LR70) | google__gemma-4-31b-it | R | ANY |  | 4 | 40 | 0 | 0.100 | 0.040 | 0.231 |
| without ruled R tasks (LR61/LR70) | openai__gpt-5.4-mini | R | ANY |  | 9 | 40 | 0 | 0.225 | 0.123 | 0.375 |
| without ruled R tasks (LR61/LR70) | openai__gpt-5.6-terra | R | ANY |  | 0 | 40 | 0 | 0.000 | 0.000 | 0.088 |
| without ruled R tasks (LR61/LR70) | openai__gpt-oss-20b | R | ANY |  | 1 | 40 | 0 | 0.025 | 0.004 | 0.129 |
| without ruled R tasks (LR61/LR70) | qwen__qwen3.5-9b | R | ANY |  | 6 | 40 | 0 | 0.150 | 0.071 | 0.291 |
| without ruled R tasks (LR61/LR70) | qwen__qwen3.6-35b-a3b | R | ANY |  | 7 | 40 | 0 | 0.175 | 0.087 | 0.319 |

Per idiom cells: TSV (200 rows).
