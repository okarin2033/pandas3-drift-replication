"""ENV_TERMS probe (own code, 2026-11-11). Usage: <venv>/bin/python probe_env.py <venv_name> <expected_pandas> <pa:yes|no|tools>
Prints one JSON object; exit code 1 if an assertion fails."""
import sys, json, importlib, importlib.util, importlib.metadata as md, platform

name, exp_pd, pa = sys.argv[1], sys.argv[2], sys.argv[3]
out = {"venv": name, "python": platform.python_version(), "executable": sys.executable, "errors": []}
import numpy as np, pandas as pd
out["pandas"] = pd.__version__
out["numpy"] = np.__version__
for dist in ("python-dateutil", "tzdata", "pytz", "pyarrow", "scipy", "statsmodels", "jsonschema"):
    try: out[dist.replace("-", "_")] = md.version(dist)
    except md.PackageNotFoundError: out[dist.replace("-", "_")] = None
out["pyarrow_spec_found"] = importlib.util.find_spec("pyarrow") is not None
try:
    import pyarrow  # noqa
    out["import_pyarrow"] = "ok " + pyarrow.__version__
except Exception as e:
    out["import_pyarrow"] = "fails: " + type(e).__name__ + ": " + str(e)
if pa == "no":
    if not out["import_pyarrow"].startswith("fails"): out["errors"].append("pyarrow importable in a non-pa venv")
    if out["pyarrow_spec_found"]: out["errors"].append("pyarrow spec found in a non-pa venv")
if pa == "yes" and not out["import_pyarrow"].startswith("ok"): out["errors"].append("pyarrow missing in a pa venv")
if exp_pd != "any" and pd.__version__ != exp_pd: out["errors"].append(f"pandas {pd.__version__} != expected {exp_pd}")

def sdesc(s):
    d = s.dtype
    return {"repr": repr(d), "str": str(d), "storage": getattr(d, "storage", None), "na_value": repr(getattr(d, "na_value", None)),
            "type": type(d).__name__}

s = pd.Series(["a", "b", None])
out["default_string_dtype"] = sdesc(s)
out["default_df_columns_dtype"] = repr(pd.DataFrame({"c": ["x", "y"]}).dtypes["c"])
try: out["mode_string_storage_option"] = str(pd.get_option("mode.string_storage"))
except Exception as e: out["mode_string_storage_option"] = "n/a: " + type(e).__name__
if name in ("pd233", "pd233pa", "pd223"):
    try:
        pd.set_option("future.infer_string", True)
        s2 = pd.Series(["a", "b", None]); df2 = pd.DataFrame({"c": ["x", "y"]})
        out["future_infer_string_set"] = {"ok": True, "series_dtype": sdesc(s2), "frame_dtype": repr(df2.dtypes["c"]),
                                          "groupby_sum_ok": bool(df2.assign(v=[1, 2]).groupby("c")["v"].sum().sum() == 3)}
        if name == "pd233" and out["future_infer_string_set"]["series_dtype"]["storage"] == "pyarrow":
            out["errors"].append("future.infer_string without pyarrow gave pyarrow storage")
    except Exception as e:
        out["future_infer_string_set"] = {"ok": False, "error": type(e).__name__ + ": " + str(e)}
        if name == "pd233": out["errors"].append("future.infer_string failed in pd233")
else:
    try: out["future_infer_string_option"] = repr(pd.get_option("future.infer_string"))
    except Exception as e: out["future_infer_string_option"] = "n/a: " + type(e).__name__
    if pa == "no" and out["default_string_dtype"]["storage"] != "python":
        out["errors"].append("pandas 3 default string storage is not python in non-pa venv")
    if pa == "yes" and out["default_string_dtype"]["storage"] != "pyarrow":
        out["errors"].append("pandas 3 default string storage is not pyarrow in pa venv")
out["ok"] = not out["errors"]
print(json.dumps(out, indent=1, default=str))
sys.exit(0 if out["ok"] else 1)
