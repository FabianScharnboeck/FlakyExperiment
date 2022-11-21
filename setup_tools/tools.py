from typing import Tuple

import fire
import pandas as pd
from pandas import DataFrame
import numpy as np
import os

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


def main() -> None:
    fire.Fire()


if __name__ == "__main__":
    main()
