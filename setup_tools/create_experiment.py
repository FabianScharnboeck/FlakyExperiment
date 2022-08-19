#!/usr/bin/env python3
import csv
import dataclasses

from typing import Set, Tuple
from findpackages import find_modules, error_print
import sys
from pathlib import Path
import tag_matcher

base_path = Path(".").absolute()
csv_output_name = "repositories_python_top_200.csv"


@dataclasses.dataclass
class Project:
    project_path: str
    project_modules: Set[str]
    url: str
    hash: str
    name: str
    pypi_version: str
    tag_status: str


def find_folders(path: str, url: str, hash: str, name: str) -> Project:
    """Find the modules to the corresponding project"""
    search_path = f"{base_path}/{path}"
    print("SEARCHPATH: " + search_path)
    modules = find_modules(path)
    if modules.__len__() == 0:
        return None
    if path.startswith("../"):
        path = path[3:]
    if path.startswith("/"):
        path = path[1:]
    tags: Tuple[str, str, str] = tag_matcher.get_tags(package=name, package_url=url)
    project = Project(project_path=path, project_modules=modules, url=url, hash=tags[1], name=name,
                      pypi_version=tags[0], tag_status=tags[2])
    return project


def write_csv(project: Project):
    """Creates an xml file for the project setup"""
    header = ["PATH", "URL", "HASH", "MODULES", "NAME", "PYPI_VERSION", "TAG_STATUS"]
    csv_data = [project.project_path, project.url, project.hash, project.project_modules, project.name,
                project.pypi_version, project.tag_status]

    with open(base_path / csv_output_name, mode="a") as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(header)
        writer.writerow(csv_data)


if __name__ == "__main__":
    if sys.version_info < (3, 6, 0):
        error_print("Requires at least Python 3.6.0")
        sys.exit(1)
    print("FINDING MODULES FOR: " + sys.argv[1].strip(), sys.argv[2].strip(), sys.argv[3].strip(), sys.argv[4].strip())
    project = find_folders(sys.argv[1].strip(), sys.argv[2].strip(), sys.argv[3].strip(), sys.argv[4].strip())
    print(project)
    if project is not None:
        write_csv(project)
