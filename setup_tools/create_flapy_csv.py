import argparse
import csv
import sys
from pathlib import Path
from typing import List


def generate_csv(name: str, url: str, proj_hash: str, pypi_tag:str, tests: str, runs: str, run_id: str, funcs_to_trace: str) -> None:
    '''
    Generates a CSV file with a format to be used by flapy.
    https://github.com/se2p/FlaPy
    :param name:
    :param url:
    :param proj_hash:
    :param pypi_tag:
    :param tests:
    :param runs:
    :param run_id:
    :param funcs_to_trace:
    :return: None
    '''
    base_path = Path(".").absolute()
    csv_file_path = base_path / "src" / "flapy_csv"
    csv_file_name = ("flapy_csv_" + run_id + ".csv").strip()

    header = ["PROJECT_NAME", "PROJECT_URL", "PROJECT_HASH", "PYPI_TAG", "FUNCS_TO_TRACE", "TESTS_TO_BE_RUN", "NUM_RUNS"]
    data = [name, url, proj_hash, pypi_tag, funcs_to_trace, tests, runs]

    f = open(csv_file_path/csv_file_name, "w")
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerow(data)


def main(argv: List[str]) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-n",
        "--name",
        dest="name",
        required=True,
        help="Project name.",
    )
    parser.add_argument(
        "-u",
        "--url",
        dest="url",
        required=True,
        help="Path to project.",
    )
    parser.add_argument(
        "-l",
        "--hash",
        dest="hash",
        required=True,
        help="Project hash.",
    )
    parser.add_argument(
        "-f",
        "--funcs_to_trace",
        dest="funcs_to_trace",
        required=True,
        help="Funcs to trace.",
    )
    parser.add_argument(
        "-t",
        "--tests",
        dest="tests",
        required=True,
        help="Tests to be run.",
    )
    parser.add_argument(
        "-r",
        "--runs",
        dest="runs",
        required=True,
        help="Number of runs.",
    )
    parser.add_argument(
        "-i",
        "--run_id",
        dest="run_id",
        required=True,
        help="Number of runs.",
    )
    parser.add_argument(
        "-p",
        "--pypi-tag",
        dest="pypi_tag",
        required=True,
        help="pypi-tag.",
    )

    args = parser.parse_args()
    project_name = args.name
    project_url = args.url
    project_hash = args.hash
    project_tests = args.tests
    project_runs = args.runs
    project_funcs_to_trace = args.funcs_to_trace
    run_id = args.run_id
    pypi_tag = args.pypi_tag
    generate_csv(name=project_name, url=project_url, proj_hash=project_hash, pypi_tag=pypi_tag, funcs_to_trace=project_funcs_to_trace, tests=project_tests, runs=project_runs, run_id=run_id)


if __name__ == "__main__":
    main(sys.argv)
