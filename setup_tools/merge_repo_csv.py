import argparse
import sys
import pandas as pd
from typing import List


def merge_csv(file: str, destination: str, source: str) -> None:
    '''
    Concatenate a file with a destination file. It is necessary that both files have the same columns, except the
    'source' column. This column is not mandatory as it will be added automatically when it concats the files.
    Note that duplicate rows will be removed by its project name. Therefore duplicate projects names will result in
    only choosing one of them for the result set.--
    :param file: The File containing the values to be added to the destination file
    :param destination: The file that the values should be added to
    :param source: String containing a reference to where your data has been collected from (e.g. an URL)
    :return: None
    '''
    file_df = pd.read_csv(file)
    destination_df = pd.read_csv(destination)
    file_df['source'] = source

    col_file = file_df.columns
    col_dest = destination_df.columns
    if not col_file.equals(col_dest):
        raise ValueError("The column names have to be identical.")
    if source is None or "":
        raise ValueError("source must not be None or empty.")

    merged_csv = pd.concat([file_df, destination_df], axis=0)
    merged_csv = merged_csv.drop_duplicates(subset=["Project_Name"])
    merged_csv.to_csv(destination, index=False)


def main(argv: List[str]) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--file",
        dest="file",
        required=True,
        help="CSV file to add.",
    )
    parser.add_argument(
        "-d",
        "--destination",
        dest="destination",
        required=True,
        help="Destination file to add the source csv file to",
    )
    parser.add_argument(
        "-s",
        "--source",
        dest="source",
        required=True,
        help="Destination file to add the source csv file to",
    )

    args = parser.parse_args()
    file = args.file
    destination = args.destination
    source = args.source
    merge_csv(file=file, destination=destination, source=source)


if __name__ == "__main__":
    main(sys.argv)
