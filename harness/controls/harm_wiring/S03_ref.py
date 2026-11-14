# VERIFY harm-prelabel wiring check: version-robust reference for the P+ program S03 (missing cities are not counted).
import pandas as pd
df = pd.read_csv("customers.csv")
result = df["city"].dropna().str.title().value_counts().sort_index()
