import argparse
from csv import DictReader, DictWriter
from dataclasses import dataclass

from typing import List


@dataclass
class Project:
    name: str
    url: str
    hash: str


def write_csv(path: str):
    new_name: str = path[:-4] + "_2" + path[-4:]
    with open(path, "r") as f:
        rd = DictReader(f)

        with open(new_name, "w") as w:
            fields = [
                "Project_Name",
                "Project_URL",
                "Project_Hash"
            ]
            wr = DictWriter(w, fieldnames=fields)
            wr.writeheader()
            for row in rd:
                project = Project(
                    name=row["Project_Name"],
                    url=row["Project_URL"],
                    hash=row["Project_Hash"]
                )
                wr.writerow({
                    "Project_Name": project.name,
                    "Project_URL": project.url,
                    "Project_Hash": project.hash
                })

    pass


if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--path",
        dest="path",
        required=True,
        help="Path to CSV."
    )

    args = parser.parse_args()
    path: str = args.path

    write_csv(path)
