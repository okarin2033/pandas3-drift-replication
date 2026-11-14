"""Print every registered pandas option name, one per line (own code, 2026-11-11)."""
import pandas as pd
from pandas._config import config
for k in sorted(config._registered_options): print(k)
