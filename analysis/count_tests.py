import argparse
import os

import numpy as np
import pandas as pd
from pandas import DataFrame


def parse_csv(path: str, output: str, mode: str, logs: str):
    df: DataFrame = pd.read_csv(path)
    df_mod: DataFrame = pd.DataFrame()
    df_mod["CHUNK_PATH"] = df["OUTPUT_DIR_PHYSICAL"]
    df_mod["PROJECT_URL"] = df["PROJECT_SOURCES"]
    df_mod["PROJECT_HASH"] = df["PROJ_HASH"]
    df_mod["CAUSE"] = ""
    df_mod["CAUSE_GROUP"] = ""
    df_mod["COMMENT"] = ""

    if mode=="PROJECTS":
        # Takes the input.csv, counts every created test found and put them in a list.
        # PROJECT LEVEL -- CREATED TESTS
        print("Finding and counting all generated tests on project level...")
        df_mod["GEN_TEST_MODULES"] = df["OUTPUT_DIR_PHYSICAL"].apply(func=os.listdir)
        df_mod["NUM_GEN_TEST_MODULES"] = df_mod["GEN_TEST_MODULES"].apply(func=len)
        df_mod.to_csv(output)
    elif mode=="MODULES":
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
        df_mod["PROJ_LOGS"] = logs + "/" + df_mod["PROJ_LOGS"] + "/" + df_mod["MODULES"]
        df_mod["EXIT_CODE_PATH"] = df_mod["PROJ_LOGS"] + "/" + df_mod["MODULES"] + "-EXIT_CODE.log"

        # Read the exit code files and write exit code in row. 
        df_mod = df_mod.reset_index()
        for i, row in df_mod.iterrows():
            try:
                with open (row["EXIT_CODE_PATH"], "r") as f:
                    df_mod.loc[i, "EXIT_CODE"] = f.read().strip()
            except:
                # There have been observed two types of errors. The file can't be found or the file
                # to be read was nan. Either of these are valid errors because sometimes there was
                # no associating module for a project (NaN in input.csv) resulting in a nan exit log path and sometimes
                # there was a module to be tested (Module name in input.csv but no log file created) 
                # but pynguin wasn't able to (bc. of SLURM timeout or sth else) which reads to no
                # exit code log file to be created to the best of my knowledge.
                #print("Error reading file: " + str(row["EXIT_CODE_PATH"]))
                df_mod.loc[i, "EXIT_CODE"] = "EXIT_CODE: NO EXIT CODE"

        # To CSV.
        df_mod.to_csv(output)
    elif mode=="INPUT_MODULES":
        # Takes the input.csv and explodes over EVERY module (even those not created in a run)
        # MODULE LEVEL -- CREATED & NOT CREATED TESTS
        print("Exploding input CSV file for categorizing every test module (in terms of pynguin bugs...)")
        df["CAUSE"] = ""
        df["CAUSE_GROUP"] = ""
        df["COMMENT"] = ""
        df["PROJ_MODULES"] = df["PROJ_MODULES"].str.split()
        df = df.explode("PROJ_MODULES")
        df.to_csv(output)
    else:
        raise ValueError("--mode / -m PROJECTS/MODULES/INPUT_MODULES permitted only.")


if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--path",
        dest="path",
        required=True,
        help="Path to CSV."
    )
    parser.add_argument(
            "-l",
            "--logs",
            dest="logs",
            required=True,
            help="Path to logs."
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        required=True,
        help="Path/name to output csv."
    )
    parser.add_argument(
            "-m",
            "--mode",
            dest="mode",
            required=True,
            help="Should the test count be on module level? True / False")

    args = parser.parse_args()
    path: str = args.path
    output: str = args.output
    mode: str = args.mode
    logs: str = args.logs

    parse_csv(path=path, output=output, mode=mode, logs=logs)

