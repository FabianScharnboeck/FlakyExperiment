import os
import xml.etree.ElementTree as ET
import argparse
from typing import List
import sys
import pandas as pd
import multiprocessing
import re

def get_coverage(root):
        if "cov_report.xml" in root[2]:
            coverage_file = os.path.join(root[0], "cov_report.xml")
            if coverage_file:
                return coverage_file

def parse_cov_xml(file):
    if file is not None:
        tree = ET.parse(file)
        root = tree.getroot()
        sources = root.find("sources")
        info_dict = {"path": file, "branch-coverage": root.attrib["branch-rate"], "module": sources.find("source").text, "project_name": get_project_name(file)}
        return info_dict

def get_project_name(file):
    name = re.search("\/logs\/([a-zA-Z0-9_.-]+_[0-9]+)\/[a-zA-Z0-9_]*", file)
    if name:
        return name.group(1)
    else:
        print(file)
        return file

def to_csv(cov_list, to):
    cov_list = [val for val in cov_list if val is not None]
    df = pd.DataFrame(cov_list)
    df.to_csv(to)


def main(argv: List[str]) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-p",
            "--path",
            dest="path",
            required=True,
            help="Path ro root log directory to search for coverage files for"
            )
    parser.add_argument(
            "-t",
            "--to",
            dest="to",
            required=True,
            help="Where to store the csv file"
            )

    args = parser.parse_args()
    path: str = args.path
    to: str = args.to

    cov_list = []

    with multiprocessing.Pool() as pool:
        coverage_files = pool.map(get_coverage, os.walk(path))
        print(coverage_files)

    with multiprocessing.Pool() as pool_2:
        cov_list = pool_2.map(parse_cov_xml, coverage_files)
        print(cov_list)

    to_csv(cov_list, to)

if __name__ == "__main__":
    main(sys.argv)
