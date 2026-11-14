# M_QF7_13: naive solution using the invited idiom of catalogue row I01.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import numpy as np
import pandas as pd

df = pd.read_csv("order_lines.csv")
big = df[df["amount"] > 100]
result = np.var(big[["quantity", "amount"]])
