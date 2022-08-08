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
Looking at the `setup_experiment.sh` file, you see that it takes the `repos.csv` in `./csv`
and creates a new CSV file `repositories_flakiness_big.csv`. This file contains the relevant information
to start experimenting:
- Name of the project
- URL of the project
- Project Hash
- directory and module names of the project (e.g. `threescale_api.defaults` for the `defaults` module inside the project.)

It adds the projects as a submodule, searches for all existing modules and writes the output to `repositories_flakiness.csv`.
Afterwards it deletes the submodule to safe memory.

## Creating the pynguin CSV's
Prerequisites: It is assumed you cd into `flakyexperiments`
```bash
python3 experiment.py -d exp_flakiness.xml -r repositories_flakiness_big.csv
```
Consider using the absolute path to the XML and CSV file if necessary. `exp_flakiness.xml` has the required
options for pynguin to use (do not change anything except the pynguin configurations and global configurations, as 
this XML file only targets those lines. All other tags are legacy and are not used by `experiment.py`).
## Starting the pynguin test generation (SLURM)
Now that the pynguin CSVs are generated in `./src/pynguin_csv`-
we have one CSV for every project and a CSV called `merged.csv` with all projects inside -
the setup for starting pynguin test generation is complete.
### Calling pynguin
````bash
./run_pynguin_csv cluster ABSOLUTE_PATH_TO/src/pynguin_csv/your_pynguin.csv
````
The script will automatically clone the project inside your `ROOT_FOLDER/projects` folder and use this
as project input path for pynguin. It generates a directory inside it where it puts the tests.

## Starting the flapy test analysis (SLURM)
The previous step starting `run_pynguin_csv.sh` also took care of creating
CSVs for flapy to use afterwards. They are located at `./src/flapy_csv`.
### Calling flapy
````bash
./run_csv cluster ABSOLUTE_PATH_TO/src/flapy_csv/your_flapy_csv false "" RESULTS_FOLDER
````
NOTE: If you want flapy to run all projects you first have to create a merged.csv out of the 
flapy CSVs. Herefore invoke the script:
````bash
python3 ./setup_tools/merge_csv --path ABSOLUTE_PATH_TO/src/flapy_csv --name *
````
Note: `--name *` is a regex filtering the files you want to merge, which in our case is not required,
therefore we use *.


## Testing the Setup with less data
There is a file `repositories_flakiness.csv` with only a few repositories. If you want to test the setup, consider using this CSV.
You can also create your own CSVs with fewer projects if needed.
