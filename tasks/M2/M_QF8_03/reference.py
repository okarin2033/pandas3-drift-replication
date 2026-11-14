# M_QF8_03: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import math
import numpy as np
import pandas as pd

with open("daily_temps.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))
dates = [r["date"] for r in rows]
temp = [float(r["temp_c"]) if r["temp_c"].strip() != "" else None for r in rows]
hum = [float(r["humidity"]) if r["humidity"].strip() != "" else None for r in rows]


def sem(values):
    """sample sd / sqrt(n) of a list of floats (n >= 2)."""
    a = np.array(values, dtype="float64")
    return float(np.std(a, ddof=1) / math.sqrt(len(a)))


def rolling_sem(vals, window, min_periods=None):
    """Trailing windows of `window` rows; None when fewer than min_periods (default: window) values are present."""
    need = window if min_periods is None else min_periods
    out = []
    for i in range(len(vals)):
        win = [v for v in vals[max(0, i - window + 1):i + 1] if v is not None]
        out.append(sem(win) if len(win) >= max(need, 2) else None)
    return out


def date_index(ds):
    return pd.DatetimeIndex(pd.to_datetime(ds, format="%Y-%m-%d"), name="date")


def as_float(vals):
    return np.array([np.nan if v is None else v for v in vals], dtype="float64")
means, lows, ups = [], [], []
for i in range(len(temp)):
    win = temp[max(0, i - 6):i + 1]
    if i >= 6 and all(v is not None for v in win):
        m = float(np.mean(np.array(win, dtype="float64")))
        e = sem(win)
        means.append(m); lows.append(m - 1.96 * e); ups.append(m + 1.96 * e)
    else:
        means.append(None); lows.append(None); ups.append(None)
result = pd.DataFrame({"mean": as_float(means), "lower": as_float(lows), "upper": as_float(ups)}, index=date_index(dates))
