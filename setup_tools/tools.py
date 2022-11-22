from typing import Tuple

import fire
import pandas as pd
from pandas import DataFrame
import os
import argparse
import dataclasses
import random
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Union, Tuple, Dict, Optional
import ast


class TestCounter:
    def __init__(self, df: DataFrame):
        self._df_count_tests: DataFrame = None
        self._df: DataFrame = df.fillna("")

    @classmethod
    def load(cls, csv_file: str):
        _df: DataFrame = pd.read_csv(csv_file)
        return cls(_df)

    def count_tests_project(self):
        df, df_mod = self._create_df_mod(df=self._df)

        # Takes the input.csv, counts every created test found and put them in a list.
        # PROJECT LEVEL -- CREATED TESTS
        print("Finding and counting all generated tests on project level...")
        df_mod["GEN_TEST_MODULES"] = df["OUTPUT_DIR_PHYSICAL"].apply(func=os.listdir)
        df_mod["NUM_GEN_TEST_MODULES"] = df_mod["GEN_TEST_MODULES"].apply(func=len)

        self._df_count_tests = df_mod

    def count_tests_modules(self, log_path: str):

        df, df_mod = self._create_df_mod(df=self._df)

        print("Finding and counting all generated tests on module level...")
        # Takes the input.csv and explodes over all modules, Additionally searches in the log files
        # for the EXIT CODE if existing.
        # MODULE LEVEL -- CREATED TESTS & NOT CREATED TESTS (+ EXIT CODE in log files)

        # Offset of 2 in logging folders.
        df_mod["ROW_NUM"] = df.reset_index().index
        df_mod["ROW_NUM"] = df_mod["ROW_NUM"] + 2

        # Copy modules and explode.
        df_mod["MODULES"] = df["PROJ_MODULES"].dropna().apply(lambda x: str(x).split(" "))
        df_mod = df_mod.explode("MODULES")

        df_mod["PROJ_LOGS"] = df["PROJ_NAME"] + "_" + df_mod["ROW_NUM"].astype(str)
        df_mod["PROJ_LOGS"] = log_path + "/" + df_mod["PROJ_LOGS"] + "/" + df_mod["MODULES"]
        df_mod["EXIT_CODE_PATH"] = df_mod["PROJ_LOGS"] + "/" + df_mod["MODULES"] + "-EXIT_CODE.log"

        # Read the exit code files and write exit code in row.
        df_mod = df_mod.reset_index()

        for i, row in df_mod.iterrows():
            try:
                with open(row["EXIT_CODE_PATH"], "r") as f:
                    df_mod.loc[i, "EXIT_CODE"] = f.read().strip()
            except:
                # There have been observed two types of errors. The file can't be found or the file
                # to be read was nan. Either of these are valid errors because sometimes there was
                # no associating module for a project (NaN in input.csv) resulting in a nan exit log path and sometimes
                # there was a module to be tested (Module name in input.csv but no log file created)
                # but pynguin wasn't able to (bc. of SLURM timeout or sth else) which reads to no
                # exit code log file to be created to the best of my knowledge.
                # print("Error reading file: " + str(row["EXIT_CODE_PATH"]))
                df_mod.loc[i, "EXIT_CODE"] = "EXIT_CODE: NO EXIT CODE"

        self._df_count_tests = df_mod

    def count_tests_input_modules(self):
        df_project, df_mod = self._create_df_mod(df=self._df)

        # Takes the input.csv and explodes over EVERY module (even those not created in a run)
        # MODULE LEVEL -- CREATED & NOT CREATED TESTS
        print("Exploding input CSV file for categorizing every test module (in terms of pynguin bugs...)")
        df_project["CAUSE"] = ""
        df_project["CAUSE_GROUP"] = ""
        df_project["COMMENT"] = ""
        df_project["PROJ_MODULES"] = df_project["PROJ_MODULES"].str.split()
        df_project = df_project.explode("PROJ_MODULES")

        self._df_count_tests = df_project

    def _create_df_mod(self) -> Tuple[DataFrame, DataFrame]:
        df: DataFrame = self._df.copy(deep=True)
        df_mod: DataFrame = pd.DataFrame()
        df_mod["CHUNK_PATH"] = df["OUTPUT_DIR_PHYSICAL"]
        df_mod["PROJECT_URL"] = df["PROJECT_SOURCES"]
        df_mod["PROJECT_HASH"] = df["PROJ_HASH"]
        df_mod["CAUSE"] = ""
        df_mod["CAUSE_GROUP"] = ""
        df_mod["COMMENT"] = ""
        return df, df_mod

    def to_csv(self, path: str):
        self._df_count_tests.to_csv(path)


def _get_flapy_config(element: Optional[ET.Element]) -> List[str]:
    if element is None:
        return []
    result = []
    for option in element:
        result.append(
            f'{option.attrib["value"]}'
        )
    return result


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


class ExperimentCreator:
    def __init__(self, repos, config):
        self.SEED = 4105
        self.run_configurations, self.projects, self.flapy_config = self._parse_xml(config, repos)
        self.runs: List[ExperimentCreator.Run] = self._create_runs(self.run_configurations, self.projects,
                                                                   self.flapy_config)

    @classmethod
    def load(cls, repos: str, config: str):
        return cls(repos=repos, config=config)

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

    def _parse_xml(self, file_name: Union[str, os.PathLike], csv_file_name: Union[str, os.PathLike]
                   ) -> Tuple[Dict[str, List[str]], List[Project]]:
        tree = ET.ElementTree(file=file_name)
        experiment = tree.getroot()

        setup = experiment.find("setup")
        configurations = setup.find("configurations")
        global_config, search_time = _get_global_config(configurations.find("global"))
        flapy_config = _get_flapy_config(configurations.find("flapy"))
        configs: Dict[str, List[str]] = {}
        for configuration in configurations.findall("configuration"):
            name, values = self._get_configuration(configuration)
            configs[name] = values

        output_variables: List[str] = []
        for output_variable in setup.find("output-variables").findall("output-variable"):
            output_variables.append(output_variable.text)
        output_vars = "--output_variables " + ";".join(output_variables)
        global_config.append(output_vars)

        run_configurations: Dict[str, List[str]] = {}
        for config_name, configuration in configs.items():
            run_configurations[config_name] = global_config + configuration

        projects: List[ExperimentCreator.Project] = []
        df_projects = pd.read_csv(csv_file_name)
        count = 0
        count_empty = 0
        for index, row in df_projects.iterrows():
            count += 1
            projects_split: List[ExperimentCreator.Project] = self._get_project(row, search_time)
            if projects_split == []:
                count_empty += 1
            projects.extend(projects_split)

        return run_configurations, projects, flapy_config

    @staticmethod
    def _get_configuration(configuration: ET.Element) -> Tuple[str, List[str]]:
        name = configuration.attrib["id"]
        values: List[str] = []
        for option in configuration.findall("option"):
            values.append(
                f'--{option.attrib["key"]} {option.attrib["value"]}'
            )
        return name, values

    @staticmethod
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
        projects: List[ExperimentCreator.Project] = []
        for value in modules:
            count += 1
            modules_split.append(value)
            if count >= search_time:
                count = 0
                proj: ExperimentCreator.Project = ExperimentCreator.Project(
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
            proj: ExperimentCreator.Project = ExperimentCreator.Project(
                name=name,
                sources=sources,
                version=version,
                modules=modules_split,  # Hier auch modules_split dann
                project_hash=project_hash,
                project_pypi_version=project_pypi_version,
                frozen_reqs=project_frozen_reqs
            )
            projects.append(proj)

        return projects

    @staticmethod
    def _create_runs(run_configurations: Dict[str, List[str]],
                     projects: List[Project],
                     flapy_config: List[str]
                     ) -> List[Run]:
        runs: List[ExperimentCreator.Run] = []
        i = 0
        for run_name, run_configuration in run_configurations.items():
            for project in projects:
                runs.append(ExperimentCreator.Run(
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
                    run_id=4105,  # TODO not hardcoded
                    line=i
                ))
                i += 1
        return runs

    def to_csv(self, output: str):
        runs = self.runs
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
                                        run.project_name, run.project_sources, run.project_hash,
                                        run.project_pypi_version,
                                        " ".join(run.modules), run.configuration_name,
                                        " ".join(run.configuration_options),
                                        pynguin_test_dir, run.run_id]

            csv_data_dict: Dict[str, str] = dict(zip(header, csv_data_list))
            df = df.append(csv_data_dict, ignore_index=True)

            # Write requirements
            if not os.path.exists(package_dir_physical):
                os.makedirs(package_dir_physical)
            with open(package_dir_physical / "package.txt", mode="a") as g:
                g.write(str(run.project_frozen_reqs))
        df.to_csv(path_or_buf=(base_path / output), index=False)

def main() -> None:
    fire.Fire()


if __name__ == "__main__":
    main()
