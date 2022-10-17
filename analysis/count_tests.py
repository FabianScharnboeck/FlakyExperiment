import argparse
import os

import numpy as np
import pandas as pd
from pandas import DataFrame


def parse_csv(path: str, output: str):
    df: DataFrame = pd.read_csv(path)
    df_mod: DataFrame = pd.DataFrame()
    df_mod["CHUNK_PATH"] = df["OUTPUT_DIR_PHYSICAL"]
    df_mod["PROJECT_URL"] = df["PROJECT_SOURCES"]
    df_mod["PROJECT_HASH"] = df["PROJ_HASH"]
    df_mod["GEN_TEST_MODULES"] = df["OUTPUT_DIR_PHYSICAL"].apply(func=os.listdir)
    df_mod["NUM_GEN_TEST_MODULES"] = df_mod["GEN_TEST_MODULES"].apply(func=len)
    df_mod.to_csv(output)


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

