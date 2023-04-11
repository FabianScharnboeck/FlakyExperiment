# Setup for Experimenting with Pynguin and FlaPy for Flaky analysis

## Prerequisites
### Project structure
This project must be cloned into a root folder of your choice
- Make sure you have the following structure: ROOT_FOLDER/this_project
- Furthermore ROOT_FOLDER must have another child directory: ROOT_FOLDER/projects

If you meet this conditions, the project structure is complete and you can proceed.
### Install
Before you begin, make sure you meet the following requirements:
- `Python 3.8` is installed and you have set up a venv.
- `pip` is installed
- `podman` is installed (alternative for docker)
- `poetry` is installed

## Setting up the data (not required if you want to use already set up repos_test.csv)
- https://github.com/se2p/FlaPy

The creator of the tool FlaPy has a module **"results_parser"**.
By using FlaPy, you run a project with **1 iteration and 1 rerun**.
This will lead to a results directory with one folder per project.
The results_parser can now search for the requirements files and all other important metadata in the resulting directories.
The result is a CSV file like `repos_test.csv` here in this project.

### Excursus - Using FlaPys results_parser
It is assumed you are either cd'd into FlaPy by now (https://github.com/se2p/FlaPy) or you invoke FlaPy by other means.
```bash
results_parser ResultsDirCollection --path PATH_TO_FLAPY_RESULTS_DIR get_meta_overview add sut_modules _df to_csv > OUTPUT_DIRECTORY_OF_YOUR_CHOICE
```

- ```ResultsDirCollection``` collects all necessary information out of the directory with the projects, which FlaPy has created.
- ```--path``` is the path to the previously mentioned results directory
- ```get_meta_overview``` creates a data frame with necessary information to proceed with the FlakyExperiment project
- ```add sut_modules _df to_csv``` adds the sut_modules as a column, which are all modules of a project **that do not contain tests**

After creating this repo CSV, you can finally proceed in this project by creating the necessary pynguin CSV and invoking the test generation,
which is described below.

## Creating the pynguin CSV's
Prerequisites: It is assumed you are cd'd in the root folder of this project.
The following example uses ``repos_test.csv`` and `exp_flakiness.xml` to create a pynguin_csv file.
```bash
python3 ./setup_tools/tools.py CreatePynguinCSV load repos_test.csv exp_flakiness.xml to_csv ./src/pynguin_csv/pynguin_test.csv
```
You should now have a CSV in the pynguin_csv folder and test_package-subfolders containing `package.txt` containing the dependencies
of the projects\
- Consider using the absolute path to the XML and CSV file if necessary. `exp_flakiness.xml` has the required
options for pynguin to use (do not change anything except the pynguin configurations and global configurations, as 
this XML file only targets those lines. All other tags are legacy and are not used anymore).
## Starting the pynguin test generation (SLURM)
- Please roll out a pynguin / flapy image (podman) before trying to run the scipts!

Now that the pynguin CSVs are generated in `./src/pynguin_csv`-
we have one CSV for every project and a CSV called `merged.csv` with all projects inside -
the setup for starting pynguin test generation is complete.
### Calling pynguin
````bash
./run_pynguin_csv cluster ABSOLUTE_PATH_TO/src/pynguin_csv/pynguin_test.csv
````
The script will automatically clone the projects inside your `ROOT_FOLDER/projects` folder and use this
as project input path for pynguin. It generates a directory inside it where it puts the tests.

- Note that the ``local`` option does not work at the moment and is yet to be fixed.
- Only ``cluster`` is a viable option at the moment.

## Starting the flapy test analysis (SLURM)
Create a FlaPy CSV

`````bash
python3 ./setup_tools/tools.py CreateFlapyCSV load_csv ./src/pynguin_csv/pynguin_test.csv set_num_runs 30 set_iterations 10 to_csv ./src/flapy_csv/flapy_test.csv
`````
### Calling flapy
````bash
./run_csv cluster ABSOLUTE_PATH_TO/src/flapy_csv/flapy_test.csv false "" RESULTS_FOLDER
````


## File structure
```bash
# The pynguin and flapy scripts are marked with MAIN, which means users should
# use this script, IGNORE means those are only helper scripts which can
# be ignored by users.
.
├── README.md
├── csv
│   ├── flapy_input_flakyProj_2020.csv # legacy
│   ├── martin_frozen_requirements.csv # legacy
│   ├── martin_frozen_requirements_2.csv # legacy
│   ├── nod_flaky_proj_pivot.csv # legacy
│   ├── nod_flaky_proj_pivot_test.csv # legacy
│   ├── owain_parry_projects.csv # legacy
│   ├── own_searched_projects.csv # legacy
│   ├── python_top_200.csv # legacy
│   ├── repos.csv # legacy
│   └── software_eng_chair_uni_passau.csv # legacy
├── exp_flakiness.xml # XML File containing Pynguin configurations.
├── macos_podman_fix.sh
├── poetry.lock
├── pyproject.toml
├── repos_sut_modules.csv # Big CSV
├── repos_sut_modules_no_setup.csv # Big CSV
├── repos_test.csv # Example CSV to test the scripts.
├── run_container.sh # IGNORE flapy run script
├── run_csv.sh # -- MAIN Run script for FlaPy --
├── run_line.sh # IGNORE flapy run script
├── run_pynguin_container.sh # IGNORE pynguin run script
├── run_pynguin_csv.sh # -- MAIN Run script for Pynguin --
├── run_pynguin_line.sh # IGNORE pynguin run script
├── setup_tools
│   ├── __init__.py
│   ├── add_frozen_requirements.py # legacy
│   ├── create_experiment.py # legacy
│   ├── create_flapy_csv.py # legacy
│   ├── create_flapy_csv_from_pynguin_csv.py # legacy
│   ├── create_frozen_requirements.py # legacy
│   ├── findpackages.py # legacy
│   ├── ignore_frozen_requirements.py # legacy
│   ├── merge_csv.py # legacy
│   ├── merge_repo_csv.py # legacy
│   ├── tag_matcher.py # legacy
│   └── tools.py # Use this for creating pynguin & flapy csv files. Need help?: Here is a Python Fire guide: https://google.github.io/python-fire/guide/
└── src
    ├── flapy_csv
    │   └── flapy_test.csv # A generated flapy file
    ├── pynguin_csv
    │   └── pynguin_test.csv # A generated pynguin file
    ├── results # Logs are saved here
    └── test_package # Requirements files for pynguin are saved here

```
