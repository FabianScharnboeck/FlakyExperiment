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
- `docker` is installed (for using SLURM, Podman should be preferred)
- `podman` is installed (alternative for docker)
- `poetry` is installed

## Setting up the data (not required if you want to use already set up repositories_flakiness.csv)
TODO Verweis auf FlaPy? 

## Creating the pynguin CSV's
Prerequisites: It is assumed you are cd'd in the root folder of this project.
The following example uses ``repos_test.csv`` and `exp_flakiness.xml` to create a pynguin_csv file.
```bash
python3 ./setup_tools/tools.py CreatePynguinCSV load test.csv exp_flakiness.xml to_csv ./src/pynguin_csv/pynguin_test.csv
```
Consider using the absolute path to the XML and CSV file if necessary. `exp_flakiness.xml` has the required
options for pynguin to use (do not change anything except the pynguin configurations and global configurations, as 
this XML file only targets those lines. All other tags are legacy and are not used anymore).
## Starting the pynguin test generation (SLURM)
Now that the pynguin CSVs are generated in `./src/pynguin_csv`-
we have one CSV for every project and a CSV called `merged.csv` with all projects inside -
the setup for starting pynguin test generation is complete.
### Calling pynguin
````bash
./run_pynguin_csv cluster ABSOLUTE_PATH_TO/src/pynguin_csv/pynguin_test.csv
````
The script will automatically clone the project inside your `ROOT_FOLDER/projects` folder and use this
as project input path for pynguin. It generates a directory inside it where it puts the tests.

## Starting the flapy test analysis (SLURM)
Create a FlaPy CSV

`````bash
python3 ./setup_tools/tools.py CreateFlaPyCSV load ./src/pynguin_csv/pynguin_test.csv set_num_runs 30 set_iterations 10 to_csv ./src/flapy_csv/flapy_test.csv
`````
### Calling flapy
````bash
./run_csv cluster ABSOLUTE_PATH_TO/src/flapy_csv/flapy_test.csv false "" RESULTS_FOLDER
````
