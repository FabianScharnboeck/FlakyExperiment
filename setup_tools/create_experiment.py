#!/usr/bin/env python3
import argparse
import csv
import dataclasses

from typing import Set, Tuple
from findpackages import find_modules, error_print
import sys
from pathlib import Path
import tag_matcher

base_path = Path(".").absolute()


@dataclasses.dataclass
class Project:
    project_path: str
    project_modules: Set[str]
    url: str
    hash: str
    name: str
    pypi_version: str
    tag_status: str


def find_folders(path: str, url: str, hash: str, name: str, tag: str) -> Project:
    """Find the modules to the corresponding project"""
    search_path = f"{base_path}/{path}"
    print("SEARCHPATH: " + search_path)
    modules = find_modules(path)
    print("Modules: " + "\n" + str(modules))

    if modules.__len__() == 0:
        return None
    if path.startswith("../"):
        path = path[3:]
    if path.startswith("/"):
        path = path[1:]

    if hash == "" and tag == "":
        tags: Tuple[str, str, str] = tag_matcher.get_tags(package=name, package_url=url)
        project: Project = Project(project_path=path, project_modules=modules, url=url, hash=tags[1], name=name,
                                   pypi_version=tags[0], tag_status=tags[2])
    else:
        project: Project = Project(project_path=path, project_modules=modules, url=url, hash=hash, name=name,
                                   pypi_version=tag, tag_status="PGK_PATH_MODE")
    return project


def write_csv(project: Project, output: str):
    """Creates an csv file for the project setup"""
    header = ["PATH", "URL", "HASH", "MODULES", "NAME", "PYPI_VERSION", "TAG_STATUS"]
    csv_data = [project.project_path, project.url, project.hash, project.project_modules, project.name,
                project.pypi_version, project.tag_status]

    with open(output, mode="a") as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(header)
        writer.writerow(csv_data)


if __name__ == "__main__":
    if sys.version_info < (3, 6, 0):
        error_print("Requires at least Python 3.6.0")
        sys.exit(1)

    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--proj_path",
        dest="proj_path",
        required=True,
        help="Path to submodule."
    )
    parser.add_argument(
        "-u",
        "--proj_url",
        dest="proj_url",
        required=True,
        help="Project url."
    )
    parser.add_argument(
        "-g",
        "--proj_hash",
        dest="proj_hash",
        required=True,
        help="Project hash."
    )
    parser.add_argument(
        "-n",
        "--proj_name",
        dest="proj_name",
        required=True,
        help="Project name."
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        required=True,
        help="Output file path + name."
    )
    args = parser.parse_args()
    proj_path: str = args.proj_path
    proj_url: str = args.proj_url
    proj_hash: str = args.proj_hash
    proj_name: str = args.proj_name

    output: str = args.output

    project: Project = find_folders(path=proj_path, url=proj_url, hash=proj_hash, name=proj_name, tag="")
    print(project)
    if project is not None:
        write_csv(project, output)
