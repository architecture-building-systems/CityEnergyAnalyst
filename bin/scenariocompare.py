"""
Scenariocompare: compare two scenarios, concentrating on csv files in the outputs/data subfolders
"""

import os
import pathlib
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error


def main(s1, s2):
    print("FILE, FIELD, RMSE, ERROR")
    after_root = pathlib.Path(s2)
    for before in pathlib.Path(s1).rglob("*.csv"):
        if r"building-properties\\schedules" in str(before):
            # exclude these as they're not really .csv files
            continue
        if r"technology\\archetypes\\use_types" in str(before):
            # exclude these as they're not really .csv files
            continue

        rel_path = before.relative_to(s1)

        try:
            before_df = pd.read_csv(before)
        except pd.errors.EmptyDataError:
            # No columns to parse from file
            continue
        except FileNotFoundError:
            print(f"Error: The specified input file '{before}' was not found. Please check the file path and try again.", file=sys.stderr)
            sys.exit(1)

        diff_df = before_df.copy()

        after = after_root.joinpath(rel_path)
        if after.exists():
            try:
                after_df = pd.read_csv(after)
            except FileNotFoundError:
                # file disappeared after existence check
                after_df = None
            except pd.errors.EmptyDataError:
                after_df = None
        else:
            after_df = None

        # save after_df back to .csv with same ordering of fields (makes it easier to debug the files manually)
        if after_df is not None:
            after_df.to_csv(after, columns=before_df.columns, index=False)

        float_fields = [f for f in before_df.dtypes.index if before_df.dtypes[f] == "float64"]
        for f in float_fields:
            if after_df is None or f not in after_df:
                error = "left only"
                rmse = np.nan
                diff_df[f] = np.nan
            else:
                try:
                    error = "ok"
                    rmse = mean_squared_error(after_df[f], before_df[f])
                    diff_df[f] = round(before_df[f] - after_df[f], 5)

                except Exception as e:
                    error = e
                    rmse = np.nan
            print(f"{rel_path}, {f}, {rmse:.10f}, {str(error).replace(',', '_')}")

        try:
            diff_df.to_csv(f"{after}-diff.csv", columns=before_df.columns, index=False)
        except FileNotFoundError:
            # just ignore this - folder might not exist if the after file was not written
            pass


if __name__ == "__main__":
    s1, s2 = map(os.path.abspath, sys.argv[1:])  # note: this will fail if not used correctly...
    main(s1, s2)