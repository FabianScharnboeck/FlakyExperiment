import argparse
import dataclasses
import os
import random
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Union, Tuple, Dict, Optional
import pandas as pd
from pandas import DataFrame
import ast

SEED: int = 4105


@dataclasses.dataclass
class Project:
    name: str
    version: str
    sources: Union[str, os.PathLike]
    modules: List[str]
    project_hash: str
    project_pypi_version: str
    frozen_reqs: str


@dataclasses.dataclass
class Run:
    configuration_name: str
    configuration_options: List[str]
    flapy_config: List[str]
    project_name: str
    project_version: str
    project_sources: Union[str, os.PathLike]
    project_hash: str
    project_pypi_version: str
    project_frozen_reqs: str
    modules: List[str]
    run_id: int
    line: int


def _parse_xml(
        file_name: Union[str, os.PathLike], csv_file_name: Union[str, os.PathLike]
) -> Tuple[Dict[str, List[str]], List[Project]]:
    tree = ET.ElementTree(file=file_name)
    experiment = tree.getroot()

    setup = experiment.find("setup")
    configurations = setup.find("configurations")
    global_config, search_time = _get_global_config(configurations.find("global"))
    flapy_config = _get_flapy_config(configurations.find("flapy"))
    configs: Dict[str, List[str]] = {}
    for configuration in configurations.findall("configuration"):
        name, values = _get_configuration(configuration)
        configs[name] = values

    output_variables: List[str] = []
    for output_variable in setup.find("output-variables").findall("output-variable"):
        output_variables.append(output_variable.text)
    output_vars = "--output_variables " + ";".join(output_variables)
    global_config.append(output_vars)

    run_configurations: Dict[str, List[str]] = {}
    for config_name, configuration in configs.items():
        run_configurations[config_name] = global_config + configuration

    projects: List[Project] = []
    df_projects = pd.read_csv(csv_file_name)
    count = 0
    count_empty = 0
    for index, row in df_projects.iterrows():
        count += 1
        projects_split: List[Project] = _get_project(row, search_time)
        if projects_split == []:
            count_empty += 1
        projects.extend(projects_split)

    count_without_empty = count - count_empty
    return run_configurations, projects, flapy_config


def _get_global_config(element: Optional[ET.Element]) -> List[str]:
    if element is None:
        return [], 140
    result = []
    for option in element:
        if option.attrib["key"] == "maximum_search_time":
            max_search_time: int = int(option.attrib["value"])
            search_time_split: int = int((22 * 60 * 60) / max_search_time)
        result.append(
            f'--{option.attrib["key"]} {option.attrib["value"]}'
        )
    return result, search_time_split


def _get_flapy_config(element: Optional[ET.Element]) -> List[str]:
    if element is None:
        return []
    result = []
    for option in element:
        result.append(
            f'{option.attrib["value"]}'
        )
    return result


def _get_configuration(configuration: ET.Element) -> Tuple[str, List[str]]:
    name = configuration.attrib["id"]
    values: List[str] = []
    for option in configuration.findall("option"):
        values.append(
            f'--{option.attrib["key"]} {option.attrib["value"]}'
        )
    return name, values


def _get_project(row, search_time: int) -> List[Project]:
    name: str = row['project_name']
    sources: str = row['project_url']
    version: str = "unknown"
    project_hash: str = row['project_git_hash']
    project_pypi_version: str = ""
    project_frozen_reqs: str = row["project_reqs"]
    modules: List[str] = ast.literal_eval(row['sut_modules'])
    modules_split: List[str] = []

    if len(modules) == 0:
        return []

    # Split up the module if there are too many of them to be handled by SLURM.
    count: int = 0
    projects: List[Project] = []
    for value in modules:
        count += 1
        modules_split.append(value)
        if count >= search_time:
            count = 0
            proj: Project = Project(
                name=name,
                sources=sources,
                version=version,
                modules=modules_split,
                project_hash=project_hash,
                project_pypi_version=project_pypi_version,
                frozen_reqs=project_frozen_reqs
            )
            modules_split = []
            projects.append(proj)

    # Ersetzer modules durch modules_split wenn Kommentare weg.
    if len(modules_split) != 0:
        proj: Project = Project(
            name=name,
            sources=sources,
            version=version,
            modules=modules_split, # Hier auch modules_split dann
            project_hash=project_hash,
            project_pypi_version=project_pypi_version,
            frozen_reqs=project_frozen_reqs
        )
        projects.append(proj)

    return projects


def _create_runs(
        run_configurations: Dict[str, List[str]],
        projects: List[Project],
        flapy_config: List[str]
) -> List[Run]:
    runs: List[Run] = []
    i = 0
    for run_name, run_configuration in run_configurations.items():
        for project in projects:
            runs.append(Run(
                configuration_name=run_name,
                configuration_options=run_configuration,
                flapy_config=flapy_config,
                project_name=project.name,
                project_version=project.version,
                project_sources=project.sources,
                project_hash=project.project_hash,
                project_pypi_version=project.project_pypi_version,
                project_frozen_reqs=project.frozen_reqs,
                modules=project.modules,
                run_id=SEED,
                line=i
            ))
            i += 1
    return runs


def write_csv(runs: List[Run], output: str):
    """Creates an xml file for the pynguin run setup by csv"""
    header: List[str] = ["INPUT_DIR_PHYSICAL", "OUTPUT_DIR_PHYSICAL", "PACKAGE_DIR_PHYSICAL", "BASE_PATH",
                         "PROJ_NAME",
                         "PROJECT_SOURCES", "PROJ_HASH", "PYPI_TAG", "PROJ_MODULES", "CONFIG_NAME",
                         "CONFIGURATION_OPTIONS", "TESTS_TO_BE_RUN", "SEED"]
    df: DataFrame = pd.DataFrame(columns=header)
    for run in runs:
        base_path = Path(".").absolute()
        project_path = base_path.parent / "projects"
        package_path: str = f"src/test_package/{run.project_name}_" + str(round((time.time() * 1000))) + "_" + str(
            random.randint(1000000, 9999999))
        pynguin_test_dir: str = "pynguin_auto_tests_" + str(round((time.time() * 1000))) + "_" + str(
            random.randint(1000000, 9999999))

        input_dir_physical = project_path / (run.project_name + "_" + str(run.line))
        output_dir_physical = input_dir_physical / pynguin_test_dir
        package_dir_physical = base_path / package_path

        base_path = Path(".").absolute()

        csv_data_list: List[str] = [input_dir_physical, output_dir_physical, package_dir_physical, base_path,
                                    run.project_name, run.project_sources, run.project_hash, run.project_pypi_version,
                                    " ".join(run.modules), run.configuration_name, " ".join(run.configuration_options),
                                    pynguin_test_dir, run.run_id]

        csv_data_dict: Dict[str, str] = dict(zip(header, csv_data_list))
        df = df.append(csv_data_dict, ignore_index=True)

        # Write requirements
        if not os.path.exists(package_dir_physical):
            os.makedirs(package_dir_physical)
        with open(package_dir_physical/"package.txt", mode="a") as g:
            g.write(str(run.project_frozen_reqs))
    df.to_csv(path_or_buf=(base_path / output), index=False)


def main(argv: List[str]) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--definition",
        dest="definition",
        required=True,
        help="Path to run-definition XML file.",
    )
    parser.add_argument(
        "-r",
        "--repositories",
        dest="repositories",
        required=True,
        help="Path to repositories file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        required=True,
        help="Output CSV file + path"
    )

    args = parser.parse_args()
    config: str = args.definition
    repos: str = args.repositories
    output: str = args.output

    run_configurations, projects, flapy_config = _parse_xml(config, repos)
    runs: List[Run] = _create_runs(run_configurations, projects, flapy_config)

    write_csv(runs=runs, output=output)


if __name__ == '__main__':
    main(sys.argv)
