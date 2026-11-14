"""Smoke test (own code, 2026-11-11): a few common operations run under -W error::ImportWarning-free default settings."""
import io, warnings, sys, json
import pandas as pd, numpy as np
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    df = pd.read_csv(io.StringIO("a,b,c,d\n1,x,2020-01-01,1.5\n2,y,2020-02-01,2.5\n3,x,2020-03-01,\n"), parse_dates=["c"])
    g = df.groupby("b")["a"].sum()
    m = df.merge(g.rename("s").reset_index(), on="b")
    p = df.pivot_table(index="b", values="a", aggfunc="sum")
    r = {"rows": len(m), "gsum": g.to_dict(), "pivot": p["a"].to_dict(), "dt": str(df["c"].dtype), "str": str(df["b"].dtype),
         "f_mean": float(df["d"].mean()), "np_ok": float(np.sum(df["a"].to_numpy())), "warnings": [str(x.category.__name__) for x in w]}
print(json.dumps(r))
