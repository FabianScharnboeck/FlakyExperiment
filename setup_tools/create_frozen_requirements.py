import argparse
import csv
import os.path


def write_requirements(path: str):
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not os.path.exists(row["PACKAGE_DIR_PHYSICAL"]):
                os.makedirs(row["PACKAGE_DIR_PHYSICAL"])
            with open(row["PACKAGE_DIR_PHYSICAL"]+"/package.txt", "w") as d:
                reqs: str = row["frozen_requirements"]
                d.write(reqs)


if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--path",
        dest="path",
        required=True,
        help="Path to CSV having the requirements."
    )

    args = parser.parse_args()
    path: str = args.path
    destination: str = args.destination
    name: str = args.name

    write_requirements(path)
