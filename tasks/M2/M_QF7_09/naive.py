# M_QF7_09: naive solution using the invited idiom of catalogue row I01.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import numpy as np
import pandas as pd

df = pd.read_csv("order_lines.csv")
df["product"] = df["product"].str.strip().str.lower()
blender = df[df["product"] == "blender"]
result = np.sum(blender[["quantity", "amount"]])
