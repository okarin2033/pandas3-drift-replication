# VERIFY harm-prelabel wiring check: version-robust reference for the P+ program S01 (explicit cleaning of the city text).
import pandas as pd
df = pd.read_csv("customers.csv")
df["city"] = df["city"].str.strip().str.title()
result = df.groupby("city")["amount"].sum()
