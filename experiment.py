import argparse
import dataclasses
import os
import random
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Union, Tuple, Dict, Optional
import csv


@dataclasses.dataclass
class SLURMSetup:
    iterations: int
    constraint: str
    docker_images: Dict[str, Tuple[Union[str, os.PathLike], str]]
    docker_images_flapy: Dict[str, Tuple[Union[str, os.PathLike], str]]


@dataclasses.dataclass
class Project:
    name: str
    version: str
    sources: Union[str, os.PathLike]
    modules: List[str]
    project_hash: str
    project_pypi_version: str


@dataclasses.dataclass
class Run:
    constraint: str
    docker_images: Dict[str, Tuple[Union[str, os.PathLike], str]]
    docker_images_flapy: Dict[str, Tuple[Union[str, os.PathLike], str]]
    configuration_name: str
    configuration_options: List[str]
    flapy_config: List[str]
    project_name: str
    project_version: str
    project_sources: Union[str, os.PathLike]
    project_hash: str
    project_pypi_version: str
    modules: List[str]
    iteration: int
    run_id: int


def _parse_xml(
        file_name: Union[str, os.PathLike], csv_file_name: Union[str, os.PathLike]
) -> Tuple[SLURMSetup, Dict[str, List[str]], List[Project]]:
    tree = ET.ElementTree(file=file_name)
    experiment = tree.getroot()
    slurm_setup = _get_slurm_setup(experiment)

    setup = experiment.find("setup")
    configurations = setup.find("configurations")
    global_config = _get_global_config(configurations.find("global"))
    flapy_config = _get_flapy_config(configurations.find("flapy"))
    configs: Dict[str, List[str]] = {}
    for configuration in configurations.findall("configuration"):
        name, values = _get_configuration(configuration)
        configs[name] = values

    output_variables: List[str] = []
    for output_variable in setup.find("output-variables").findall("output-variable"):
        output_variables.append(output_variable.text)
    output_vars = "--output_variables " + ",".join(output_variables)
    global_config.append(output_vars)

    run_configurations: Dict[str, List[str]] = {}
    for config_name, configuration in configs.items():
        run_configurations[config_name] = global_config + configuration

    projects: List[Project] = []
    with open(csv_file_name) as csvfile:
        reader = csv.DictReader(csvfile)
        for project in reader:
            projects.append(_get_project(project))

    return slurm_setup, run_configurations, projects, flapy_config


def _get_slurm_setup(experiment: ET.Element) -> SLURMSetup:
    iterations = experiment.attrib["iterations"]
    setup = experiment.find("setup")
    constraint = setup.find("constraint").text
    docker_images: Dict[str, Tuple[Union[str, os.PathLike], str]] = {}
    for docker in setup.findall("docker"):
        docker_images[docker.attrib["name"]] = (
            docker.attrib["path"], docker.attrib["version"]
        )
    docker_images_flapy: Dict[str, Tuple[Union[str, os.PathLike], str]] = {}
    for docker_flapy in setup.findall("dockerflapy"):
        docker_images_flapy[docker_flapy.attrib["name"]] = (
            docker_flapy.attrib["path"], docker_flapy.attrib["version"]
        )
    return SLURMSetup(
        iterations=int(iterations),
        constraint=constraint,
        docker_images=docker_images,
        docker_images_flapy=docker_images_flapy
    )


def _get_global_config(element: Optional[ET.Element]) -> List[str]:
    if element is None:
        return []
    result = []
    for option in element:
        result.append(
            f'--{option.attrib["key"]} {option.attrib["value"]}'
        )
    return result


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


def _get_project(row) -> Project:
    name: str = row['NAME']
    sources: str = row['URL']
    version: str = "unknown"
    project_hash: str = row['HASH']
    project_pypi_version: str = row['PYPI_VERSION']
    modules_str: str = row['MODULES']
    modules_str = modules_str.replace('{', '')
    modules_str = modules_str.replace('}', '')
    modules_str = modules_str.replace('\'', '')
    modules: List[str] = []
    for value in modules_str.split(','):
        value = value.strip()
        modules.append(value)
    return Project(
        name=name,
        sources=sources,
        version=version,
        modules=modules,
        project_hash=project_hash,
        project_pypi_version=project_pypi_version
    )


def _create_runs(
        slurm_setup: SLURMSetup,
        run_configurations: Dict[str, List[str]],
        projects: List[Project],
        flapy_config: List[str]
) -> List[Run]:
    runs: List[Run] = []
    i = 0
    for iteration in range(slurm_setup.iterations):
        for run_name, run_configuration in run_configurations.items():
            for project in projects:
                runs.append(Run(
                    constraint=slurm_setup.constraint,
                    docker_images=slurm_setup.docker_images,
                    docker_images_flapy=slurm_setup.docker_images_flapy,
                    configuration_name=run_name,
                    configuration_options=run_configuration,
                    flapy_config=flapy_config,
                    project_name=project.name,
                    project_version=project.version,
                    project_sources=project.sources,
                    project_hash=project.project_hash,
                    project_pypi_version=project.project_pypi_version,
                    modules=project.modules,
                    iteration=iteration,
                    run_id=i,
                ))
                i += 1
    return runs


def write_csv(runs: List[Run], output: str):
    """Creates an xml file for the pynguin run setup by csv"""
    for run in runs:
        base_path = Path(".").absolute()
        project_path = base_path.parent / "projects"
        package_path: str = f"src/test_package/{run.project_name}_" + str(round((time.time() * 1000))) + "_" + str(
            random.randint(1000000, 9999999))
        pynguin_test_dir: str = "pynguin_auto_tests_" + str(round((time.time() * 1000))) + "_" + str(
            random.randint(1000000, 9999999))

        input_dir_physical = project_path / run.project_name
        output_dir_physical = project_path / run.project_name / pynguin_test_dir
        package_dir_physical = base_path / package_path

        base_path = Path(".").absolute()
        header: List[str] = ["INPUT_DIR_PHYSICAL", "OUTPUT_DIR_PHYSICAL", "PACKAGE_DIR_PHYSICAL", "BASE_PATH",
                             "PROJ_NAME",
                             "PROJECT_SOURCES", "PROJ_HASH", "PYPI_TAG", "PROJ_MODULES", "CONFIG_NAME",
                             "CONFIGURATION_OPTIONS", "TESTS_TO_BE_RUN", "FUNCS_TO_TRACE", "THIRD_PARTY_COVERAGE",
                             "NUM_FLAPY_RUNS", "SEED"]

        csv_data: List[str] = [input_dir_physical, output_dir_physical, package_dir_physical, base_path,
                               run.project_name,
                               run.project_sources, run.project_hash, run.project_pypi_version, " ".join(run.modules),
                               run.configuration_name, " ".join(run.configuration_options), pynguin_test_dir,
                               run.flapy_config[1], run.flapy_config[1], run.flapy_config[2],
                               run.run_id]
        with open(base_path / output, mode="a") as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow(header)
            writer.writerow(csv_data)


def main(argv: List[str]) -> None:
    base_path = Path(".").absolute()
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
    slurm_setup, run_configurations, projects, flapy_config = _parse_xml(config, repos)
    runs: List[Run] = _create_runs(slurm_setup, run_configurations, projects, flapy_config)

    write_csv(runs=runs, output=output)


if __name__ == '__main__':
    main(sys.argv)
