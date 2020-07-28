"""
Scenariocompare: compare two scenarios, concentrating on csv files in the outputs/data subfolders
"""

import sys
import os
import numpy as np
import pandas as pd
import pathlib
from sklearn.metrics import mean_squared_error

def main(s1, s2):
    print(f"FILE, FIELD, RMSE, ERROR")
    after_root = pathlib.Path(s2)
    for before in pathlib.Path(s1).rglob("*.csv"):
        rel_path = before.relative_to(s1)

        try:
            before_df = pd.read_csv(before)
        except pd.errors.EmptyDataError:
            # No columns to parse from file
            continue

        after = after_root.joinpath(rel_path)
        after_df = pd.read_csv(after) if after.exists() else None

        float_fields = [f for f in before_df.dtypes.index if before_df.dtypes[f] == "float64"]
        for f in float_fields:
            if after_df is None or not f in after_df:
                error = "left only"
                rmse = np.nan
            else:
                try:
                    error = "ok"
                    rmse = mean_squared_error(after_df[f], before_df[f])
                except Exception as e:
                    error = e
                    rmse = np.nan
            print(f"{rel_path}, {f}, {rmse:.10f}, {error}")




if __name__ == "__main__":
    s1, s2 = map(os.path.abspath, sys.argv[1:])  # note: this will fail if not used correctly...
    main(s1, s2)