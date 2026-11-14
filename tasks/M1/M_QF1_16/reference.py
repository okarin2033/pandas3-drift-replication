# M_QF1_16 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("price_list.csv")
out = pd.DataFrame({
    "sku": [s.strip().upper() for s in df["sku"].tolist()],
    "item": [s.strip().upper() for s in df["item"].tolist()],
    "section": [s.strip().upper() for s in df["section"].tolist()],
    "price": df["price"].tolist(),
})
result = out.sort_values("sku", kind="mergesort").reset_index(drop=True)
