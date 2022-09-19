import argparse
import pandas as pd


def merge(path: str, destination: str, name: str):
    left = pd.read_csv(path)
    right = pd.read_csv(destination)
    if right["PROJ_HASH"].str.endswith("\n").all():
        right["PROJ_HASH"] = right["PROJ_HASH"].str[:-1]
    elif not right["PROJ_HASH"].str.endswith("\n").any():
        pass
    else:
        raise ValueError("There is an inconsistency in the CSV file (column: PROJ_HASH)")
    merged = pd.merge(left, right, how="right", left_on=["Project_Name", "Project_URL", "Project_Hash"],
                      right_on=["PROJ_NAME", "PROJECT_SOURCES", "PROJ_HASH"])

    merged = merged.drop(["Project_Name", "Project_URL", "Project_Hash"], axis=1)
    merged["frozen_requirements"] = merged["frozen_requirements"].str.replace("\n", " ")
    print(left['Project_Hash'])
    print(right['PROJ_HASH'])
    print(merged["frozen_requirements"])

    # Rearrange columns as frozen_reqs is first
    cols = merged.columns.tolist()
    cols = cols[1:] + cols[:1]
    merged_new = merged[cols]

    merged_new.to_csv(name, index=False)


if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--path",
        dest="path",
        required=True,
        help="Path to CSV having the requirements."
    )
    parser.add_argument(
        "-d",
        "--destination",
        dest="destination",
        required=True,
        help="Path to Pynguin CSV file to add the frozen requirements to."
    )
    parser.add_argument(
        "-n",
        "--name",
        dest="name",
        required=True,
        help="Name of file with frozen reqs."
    )

    args = parser.parse_args()
    path: str = args.path
    destination: str = args.destination
    name:str = args.name

    merge(path, destination, name)
