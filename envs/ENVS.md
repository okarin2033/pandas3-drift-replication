# Environments (STAGE2 T1, package ENV_TERMS)

Written 2026-11-11 13:35 JST by pkg:ENV_TERMS (status: built; evidence files listed at the end). Build script `envs/build_envs.sh`,
probe `envs/probe_env.py`, runner `envs/run_probes.sh`; all re-runnable. uv 0.12.2 (`/opt/homebrew/bin/uv`, "uv 0.12.2 (Homebrew 2026-08-05 aarch64-apple-darwin)").
Index: PyPI only (`UV_DEFAULT_INDEX=https://pypi.org/simple`, `UV_NO_CONFIG=1`), `--only-binary :all:`, exact `==` pins, no extra index,
no `uv python install`. The uv cache lived in `envs/.uv-cache` during the build and was deleted afterwards.

## 1. Interpreter
- CPython **3.12.13** from the existing `~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/` (read-only use; same build as the pilot). `pyvenv.cfg` of each venv points at the minor-version link `cpython-3.12-macos-aarch64-none`, which currently resolves to 3.12.13; every program run must record `sys.version` (the run record schema has the field) so a later change of that link would be seen.
- **Deviation (DEVIATIONS.md entry written):** prereg §6 says "latest patch". The python.org downloads page (accessed 2026-11-11 13:31 JST) lists 3.12.14 (Aug 12, 2026), 3.12.15 (Sept 30, 2026) and 3.12.16 (Oct 25, 2026). The 3.12.16 release page offers source tarballs only (no macOS installer), and `uv python list --only-downloads 3.12` offers 3.12.13 as the newest uv-managed build. Installing a newer patch would need a source build or `uv python install`; both are outside this package's rules, so 3.12.13 is used. Not definitional.

## 2. Versions and PyPI upload dates (accessed 2026-11-11, `downloads/*.json` untrusted, read with `python3 -I`; sha256 in `downloads_sha256.txt`)
`https://pypi.org/pypi/pandas/json` saved as `downloads/pandas.json` sha256 `fdc4efa1ffd6b3849a055b69ee1d220dcf367f3eb0ccb23c916180024b0c3cb0`
(matches the reviewer's "fdc4efa1...3cb0"; FULL_PREREG §15 row 3 prints it as "...0cb0", a one-character typo of the abbreviation, not of the data).

| package | pinned | first upload (UTC) | yanked | latest on PyPI at access |
|---|---|---|---|---|
| pandas | 2.2.3 | 2024-09-20T13:08:42.347501Z | False | 3.1.1 |
| pandas | 2.3.3 | 2025-09-29T23:16:53.287821Z | False | 3.1.1 |
| pandas | 3.0.6 | 2026-09-17T23:20:20.960376Z | False | 3.1.1 |
| pandas | 3.1.1 | 2026-11-04T15:05:30.116324Z | False | 3.1.1 |
| numpy | 2.5.4 | 2026-10-10T20:02:40.843976Z | False | 2.5.4 |
| pyarrow | 26.0.1 | 2026-11-03T09:54:01.046378Z | False | 26.0.1 |
| python-dateutil | 4.0.0 | 2026-11-01T07:02:40.797470Z | False | 4.0.0 |
| tzdata | 2026.6 | 2026-10-28T09:57:07.276552Z | False | 2026.6 |
| pytz | 2026.6 | 2026-10-29T09:05:45.140432Z | False | 2026.6 |
| scipy | 1.18.1 | 2026-08-21T23:23:44.522812Z | False | 1.18.1 |
| statsmodels | 0.15.0 | 2026-08-27T10:34:19.376888Z | False | 0.15.0 |
| jsonschema | 4.26.0 | 2026-01-07T13:41:05.306692Z | False | 4.26.0 |

Selection checks from `downloads/pandas.json`: latest non-yanked 3.1.x = **3.1.1**; latest non-yanked 3.0.x = **3.0.6**; 3.0.4 is yanked and was not used.
Release list: 3.0.0 2026-01-21, 3.0.4 2026-06-28 (yanked), 3.0.5 2026-07-22, 3.0.6 2026-09-17, 3.1.0 2026-10-22, 3.1.1 2026-11-04.

## 3. Choice of the common pins (and why)
- **NumPy 2.5.4** (latest on PyPI, uploaded 2026-10-10). pandas 3.1.1 requires numpy >= 2.0.2, 3.0.6 >= 1.26.0, 2.3.3 and 2.2.3 >= 1.26.0 (Python 3.12), per `downloads/pandas_<v>.json` `requires_dist`; so one NumPy 2.x serves all. It installed from wheels (cp312 macosx arm64) in all eight venvs and every venv imports pandas and ran a read_csv/groupby/merge/pivot smoke test without warnings (`smoke_log.txt`). It is also the pilot's NumPy (`pilots/r3/envs/*.freeze.txt`), so pilot and study differ only in the points the study changes. Caveat: the pandas 2.x wheels were built against older NumPy; only the smoke test covers that combination, not pandas' own test suite.
- **pyarrow 26.0.1** (latest, 2026-11-03), only in `*pa`; pandas 3.1.1 needs >= 16, 3.0.6 >= 13. Same as pilot.
- **python-dateutil 4.0.0** and **tzdata 2026.6** identical in all eight venvs (same as pilot). pandas 3.x only requires tzdata on Windows, so it is installed explicitly there. pandas 2.x additionally requires **pytz**, pinned `2026.6` in pd233, pd233pa and pd223 (pandas 3.x venvs have no pytz); this is the only package-set difference apart from pandas and pyarrow.
- No other packages are in the study venvs (freeze files have 3 to 5 lines). `tools` (analysis only; never runs study programs): numpy 2.5.4, scipy 1.18.1, statsmodels 0.15.0, jsonschema 4.26.0, and pandas 3.1.1 (statsmodels requires pandas, pinned explicitly), plus their dependencies (see `tools.freeze.txt`).

## 4. Venvs
| venv | role | pandas | numpy | dateutil | tzdata | pytz | pyarrow | `import pyarrow` | size (KiB) | freeze file |
|---|---|---|---|---|---|---|---|---|---|---|
| pd233 | E0a, E0b, A1-A3, C1 partner, T0 | 2.3.3 | 2.5.4 | 4.0.0 | 2026.6 | 2026.6 | - | fails: ModuleNotFoundError: No mod | 69972 | `pd233.freeze.txt` |
| pd31x | E1, A4, T1, V-* | 3.1.1 | 2.5.4 | 4.0.0 | 2026.6 | - | - | fails: ModuleNotFoundError: No mod | 71116 | `pd31x.freeze.txt` |
| pd30x | E2 | 3.0.6 | 2.5.4 | 4.0.0 | 2026.6 | - | - | fails: ModuleNotFoundError: No mod | 66908 | `pd30x.freeze.txt` |
| pd233pa | E0pa | 2.3.3 | 2.5.4 | 4.0.0 | 2026.6 | 2026.6 | 26.0.1 | ok 26.0.1 | 198664 | `pd233pa.freeze.txt` |
| pd31xpa | E3 | 3.1.1 | 2.5.4 | 4.0.0 | 2026.6 | - | 26.0.1 | ok 26.0.1 | 199760 | `pd31xpa.freeze.txt` |
| pd30xpa | E4 | 3.0.6 | 2.5.4 | 4.0.0 | 2026.6 | - | 26.0.1 | ok 26.0.1 | 195556 | `pd30xpa.freeze.txt` |
| pd223 | C1 | 2.2.3 | 2.5.4 | 4.0.0 | 2026.6 | 2026.6 | - | fails: ModuleNotFoundError: No mod | 70888 | `pd223.freeze.txt` |
| tools | analysis only | 3.1.1 | 2.5.4 | 4.0.0 | 2026.6 | - | - | fails: ModuleNotFoundError: No mod | 194716 | `tools.freeze.txt` |

Acceptance evidence: `probe_log.txt` (one line per venv: expected pandas version, versions seen, import_pyarrow result, errors), `<venv>.probe.json`, `<venv>.freeze.txt` (`uv pip freeze`), `smoke_log.txt`.
All probes passed (`overall_fail=0`). pd223: **C1 installs and imports with the pinned NumPy** (pandas 2.2.3, numpy 2.5.4, smoke test OK), so "C1 not run" is not needed.
In every non-pa venv (pd233, pd31x, pd30x, pd223, tools) `import pyarrow` raises ModuleNotFoundError and `importlib.util.find_spec('pyarrow')` is None (asserted in the probe), so pyarrow is absent also as a transitive dependency. In the three pa venvs pyarrow 26.0.1 imports.

## 5. String dtype facts (T1.3, review N7)
- **pd233 (no pyarrow), `future.infer_string=True`**: works, no error. `Series(['a','b',None])` has dtype `<StringDtype(storage='python', na_value=nan)>` (storage `python`, `str(dtype)` = `str`); a DataFrame column gives the same repr, and a groupby sum over such a key works. Default (option off) dtype is `object`.
- **pd31x (3.1.1) and pd30x (3.0.6), no pyarrow, defaults**: `<StringDtype(storage='python', na_value=nan)>` (3.1.1) and `<StringDtype(storage='python', na_value=nan)>` (3.0.6); storage `python` in both (python, as expected).
- **pa venvs defaults**: pd31xpa `<StringDtype(na_value=nan)>` storage `pyarrow`; pd30xpa `<StringDtype(na_value=nan)>` storage `pyarrow`; pd233pa default is `object` (probe: `dtype('O')`).
- The option `mode.string_storage` is `auto` everywhere.

## 6. Facts the harness and attribution packages need
- **pandas 3.1.1: setting `future.infer_string=False` (config A4) works (dtype becomes object) but emits a `Pandas4Warning`** ("option is deprecated and will be removed in pandas 4.0"). It is emitted by the option call, not by program code; the harness must apply options before it starts recording program warnings (or classify it as harness noise). In pd30x (3.0.6) the same call emits no warning (checked 2026-11-11). Reading the option with `get_option` in 3.1.1 also warns.
- Option names for the banned-word lint: `pandas_option_names.txt` has the union of 77 dotted option names (`pandas._config.config._registered_options`; pd233 has 72, pd31x 75, pd30x 73). Differences: 3.0.6 and 3.1.1 have `future.distinguish_nan_and_na`, `future.python_scalars` and `mode.performance_warnings`, which 2.3.3 lacks; 3.1.1 additionally has `future.infer_freq_returns_offset` and `mode.max_threads`; 2.3.3 alone has `mode.data_manager` and `mode.use_inf_as_na`. The file lists full dotted names; a lint that wants single words must split on dots.
- Venv `bin/python` is a symlink into the uv Python directory. A sandbox profile needs read access to that real interpreter directory (`~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/`) as well as to the venv; the venv scripts embed absolute paths with spaces, so call `<venv>/bin/python` directly and do not move the folders.

## 7. Disk use (`du -sk`, logged)
- Before deleting the uv cache: total `envs/` 1537572 KiB (1.47 GiB, 1.57 GB decimal), cache 420.1 MiB. The 1.5 GB budget (including cache) was exceeded by about 5% during the build if GB is counted decimal, and met if counted as GiB.
- After deleting the cache: total `envs/` 1079104 KiB (about 1.03 GiB, 1.10 GB decimal); per venv in the table above (`disk_venvs_kb.txt`). The `terms/` folder is 8600 KiB at the time of writing.
- Reinstalling needs network and refills the cache (about 0.42 GB); the venvs themselves do not depend on the deleted cache (probes and smoke tests were re-run after the deletion and passed).

## 8. Files
`build_envs.sh`, `run_probes.sh`, `probe_env.py`, `smoke_env.py`, `list_options.py`, `probe_log.txt`, `smoke_log.txt`, `*.freeze.txt`, `*.probe.json`, `*.probe.err` (the three non-empty ones hold the Pandas4Warning from the probe's own `get_option` call), `pandas_option_names.txt`, `pins_upload_dates.tsv`, `downloads/` (PyPI JSON, python.org pages; untrusted), `downloads_sha256.txt`, `logs_*.log`, `disk_*_kb.txt`.
