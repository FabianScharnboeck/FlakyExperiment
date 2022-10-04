import argparse
import os

import numpy as np
import pandas as pd
from pandas import DataFrame


def parse_csv(path: str, output: str):
    df: DataFrame = pd.read_csv(path)
    df_new = df.copy()
    df_new["CHUNK_PATH"] = np.NaN
    df_new["GEN_TEST_MODULES"] = np.NaN
    df_new["GEN_TEST_NUM"] = np.NaN
    df_new.apply(axis=0, func=search_tests, result_type="expand")
    df_new.to_csv(output)


def search_tests(row):
    proj_path: str = row["OUTPUT_DIR_PHYSICAL"]
    row["CHUNK_PATH"] = proj_path
    if len(os.listdir(path=proj_path)) != 0:
        row["GEN_TEST_MODULES"] = os.listdir(path=proj_path)
        row["GEN_TEST_NUM"] = len(os.listdir(path=proj_path))
    else:
        row["GEN_TEST_MODULES"] = []
        row["GEN_TEST_NUM"] = 0


if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--path",
        dest="path",
        required=True,
        help="Path to CSV."
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        required=True,
        help="Path/name to output csv."
    )

    args = parser.parse_args()
    path: str = args.path
    output: str = args.output

    parse_csv(path=path, output=output)

