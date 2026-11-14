# MECH_B confirmation program R03 (attempt b), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: nlargest with tied values (b: Series.nlargest on a column with many ties)
# Why a second attempt: attempt a (DataFrame.nlargest, 12 rows) gave DTYPE_ONLY; the 3.0 note is about Series.nlargest
import pandas as pd
df = pd.read_csv("regional.csv")
result = df.set_index("order_id")["amount"].nlargest(5)
