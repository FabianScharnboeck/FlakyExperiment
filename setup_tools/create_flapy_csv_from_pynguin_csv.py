import argparse
import csv
import sys
from pathlib import Path
from typing import List


def generate_csv(path: str) -> None:
    '''

    :param path: path to csv to be parsed
    :return: none
    '''

    with open(path) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        data_list = []
        for row in csv_reader:
            data = [row["PROJ_NAME"], row["INPUT_DIR_PHYSICAL"], row["PROJ_HASH"], row["PYPI_TAG"],
                    row["FUNCS_TO_TRACE"], row["TESTS_TO_BE_RUN"], row["NUM_FLAPY_RUNS"]]
            data_list.append(data)
    base_path = Path(".").absolute()
    csv_file_path = base_path / "src" / "flapy_csv"
    csv_file_name = ("run_flapy.csv").strip()

    header = ["PROJECT_NAME", "PROJECT_URL", "PROJECT_HASH", "PYPI_TAG", "FUNCS_TO_TRACE", "TESTS_TO_BE_RUN",
              "NUM_RUNS"]

    f = open(csv_file_path / csv_file_name, "w")
    writer = csv.writer(f)
    if f.tell() == 0:
        writer.writerow(header)
    for d in data_list:
        writer.writerow(d)


def generate_csv_with_multiple_iterations(path: str, iterations: int, num_runs: int) -> None:
    '''

    :param path: path to CSV to be parsed
    :param iterations: number of iterations
    :param num_runs: number of runs per iteration
    :return: none
    '''
    if iterations is None or num_runs is None:
        raise ValueError("iterations and num_runs must be ints!")
    with open(path) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        data_list = []
        for row in csv_reader:
            data = [row["PROJ_NAME"], row["INPUT_DIR_PHYSICAL"], row["PROJ_HASH"], row["PYPI_TAG"],
                    row["FUNCS_TO_TRACE"], row["TESTS_TO_BE_RUN"], num_runs]
            data_list.append(data)
    base_path = Path(".").absolute()
    csv_file_path = base_path / "src" / "flapy_csv"
    csv_file_name = ("run_flapy.csv").strip()

    header = ["PROJECT_NAME", "PROJECT_URL", "PROJECT_HASH", "PYPI_TAG", "FUNCS_TO_TRACE", "TESTS_TO_BE_RUN",
              "NUM_RUNS"]

    f = open(csv_file_path / csv_file_name, "w")
    writer = csv.writer(f)
    if f.tell() == 0:
        writer.writerow(header)
    for d in data_list:
        for number in range(iterations):
            writer.writerow(d)


def main(argv: List[str]) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--path",
        dest="path",
        required=True,
        help="path to csv",
    )
    parser.add_argument(
        "-n",
        "--number_runs",
        dest="number_runs",
        required=False,
        help="path to csv",
    )
    parser.add_argument(
        "-i",
        "--iteration",
        dest="iteration",
        required=False,
        help="path to csv",
    )

    args = parser.parse_args()
    iteration = int(args.iteration)
    number_runs = int(args.number_runs)
    path = args.path
    if iteration is None and number_runs is None:
        generate_csv(path=path)
    else:
        generate_csv_with_multiple_iterations(path=path, iterations=iteration, num_runs=number_runs)


if __name__ == "__main__":
    main(sys.argv)
