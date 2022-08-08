import argparse
import csv
import glob
import os
import sys
import pandas as pd
from pathlib import Path
from typing import List


def merge_csv(path: Path, name: str) -> None:
    """
    Merges all CSV files in a given path that match the given name.
    :param path: Path to the CSV files.
    :param name: Name regex to filter the CSV files.
    :return: None
    """
    hi = ""
    """Combine path and name regex"""
    files = os.path.join(path, name)
    """Find all CSV's and return a list of them"""
    files = glob.glob(files)
    """Concatenate the CSV's"""
    df = pd.concat(map(pd.read_csv, files), ignore_index=True).drop_duplicates()

    """Write the merged CSV dataframe into a combined CSV file"""
    csv_file = Path(str(path) + "/merged.csv")
    df.to_csv(path_or_buf=csv_file, index=False)


def main(argv: List[str]) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--path",
        dest="path",
        required=True,
        help="Path to CSV files to merge.",
    )
    parser.add_argument(
        "-n",
        "--name",
        dest="name",
        required=True,
        help="File name Regex (e.g. sales_* for sales_1 sales_2 ...).",
    )

    args = parser.parse_args()
    path = args.path
    name = args.name
    merge_csv(path=path, name=name)


if __name__ == "__main__":
    main(sys.argv)
