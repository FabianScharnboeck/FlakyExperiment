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
import setup_tools.merge_csv as merger


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


def _write_run_script(run: Run) -> None:
    base_path = Path(".").absolute()
    generated_scripts = "generated_run_scripts"
    project_path = base_path / "projects"
    test_name = run.module.replace(".", "_")
    script = f"""#!/bin/bash

MIN_PROC_ID=$(numactl --show | grep physcpubind | cut -d' ' -f2)

LOCAL_DIR="/local/${{USER}}"
SCRATCH_DIR="/scratch/${{USER}}"
RESULTS_BASE_DIR="${{SCRATCH_DIR}}/experiment-results/{run.project_name}"
RESULTS_DIR="${{RESULTS_BASE_DIR}}/{run.iteration}"

WORK_DIR=$(mktemp -d -p "${{LOCAL_DIR}}")

INPUT_DIR="{project_path / run.project_name}"
OUTPUT_DIR="${{WORK_DIR}}/pynguin-report"
PACKAGE_DIR="${{WORK_DIR}}"

LOCAL_DOCKER_ROOT="${{LOCAL_DIR}}/docker-root-${{MIN_PROC_ID}}"
PYNGUIN_DOCKER_IMAGE_PATH="{run.docker_images["pynguin"][0]}"

cleanup () {{
  cp "${{OUTPUT_DIR}}/statistics.csv" \\
    "${{RESULTS_BASE_DIR}}/statistics-{run.run_id}.csv" || true

  cwd=$(pwd)
  cd "${{OUTPUT_DIR}}" || true
  tar cJf "${{RESULTS_DIR}}/results-{run.run_id}.tar.xz" \\
    output.log \\
    pynguin.log \\
    statistics.csv \\
    hostinfos.json \\
    test_*.py || true
  cd "${{cwd}}" || true

  rm -rf "${{WORK_DIR}}" || true
}}
trap cleanup INT TERM HUP QUIT

mkdir -p "${{OUTPUT_DIR}}"
mkdir -p "${{RESULTS_DIR}}"
mkdir -p "${{LOCAL_DOCKER_ROOT}}"

echo "{run.project_name}=={run.project_version}" > "${{PACKAGE_DIR}}/package.txt"

cat << EOF > ${{OUTPUT_DIR}}/hostinfos.json
{{
  "hostname": "$(hostname)",
  "cpumodel": "$(cat /proc/cpuinfo | grep 'model name' | head -n1 | cut -d":" -f2 | xargs)",
  "totalmemkb": "$(cat /proc/meminfo | grep 'MemTotal' | cut -d":" -f2 | xargs | cut -d" " -f1)"
}}
EOF

dockerd-rootless-infosun \\
  --data-root "${{LOCAL_DOCKER_ROOT}}" \\
  -- \\
    docker load -i "${{PYNGUIN_DOCKER_IMAGE_PATH}}"

dockerd-rootless-infosun \\
  --data-root "${{LOCAL_DOCKER_ROOT}}" \\
  -- \\
    docker run \\
      --rm \\
      --name="pynguin-{run.run_id}" \\
      -v "${{INPUT_DIR}}":/input:ro \\
      -v "${{OUTPUT_DIR}}":/output \\
      -v "${{PACKAGE_DIR}}":/package:ro \\
      pynguin:{run.docker_images["pynguin"][1]} \\
        -q \\
        --configuration-id {run.configuration_name} \\
        --project-name {run.project_name} \\
        --module-name {run.module} \\
        --seed {run.iteration} \\
        --project-path /input \\
        --output-path /output \\
        --report-dir /output \\
        --log-file /output/pynguin.log \\
        {" ".join(run.configuration_options)}

cleanup 
"""

    with open(base_path / generated_scripts / f"run-{run.run_id}.sh", mode="w") as f:
        f.write(script)


def _write_array_job_script(constraint: str, num_total_runs: int) -> None:
    base_path = Path(".").absolute()
    generated_scripts = "generated_run_scripts"
    script = f"""#!/bin/bash
#SBATCH --partition=anywhere
#SBATCH --constraint={constraint}
#SBATCH --job-name=pynguin
#SBATCH --time=01:30:00
#SBATCH --mem=2GB
#SBATCH --nodes=1-1
#SBATCH --ntasks=1
#SBATCH --ntasks-per-socket=1
#SBATCH --mem-bind=local
#SBATCH --array=1-{num_total_runs}

n=${{SLURM_ARRAY_TASK_ID}}

function sighdl {{
  kill -INT "${{srunPid}}" || true
}}

mkdir -p "{base_path / "pynguin-runs"}"
OUT_FILE="{base_path / "pynguin-runs" / "${{n}}-out.txt"}"
ERR_FILE="{base_path / "pynguin-runs" / "${{n}}-err.txt"}"

srun \\
  --disable-status \\
  --mem-bind=local \\
  --output="${{OUT_FILE}}" \\
  --error="${{ERR_FILE}}" \\
  ./run-"${{n}}".sh \\
  & srunPid=$!

trap sighdl INT TERM HUP QUIT

while ! wait; do true; done
"""

    with open(base_path / generated_scripts / "array_job.sh", mode="w") as f:
        f.write(script)


def _write_main_script(num_total_runs: int) -> None:
    base_path = Path(".").absolute()
    generated_scripts = "generated_run_scripts"
    script = f"""#!/bin/bash
SLURM_JOB_ID=0
PID=$$

function sig_handler {{
  echo "Cancelling SLURM job..."
  if [[ "${{SLURM_JOB_ID}}" -gt 0 ]]
  then
    scancel "${{SLURM_JOB_ID}}"
  fi
  echo "Killing ${{0}} including its children..."
  pkill -TERM -P "${{PID}}"

  echo -e "Terminated: ${{0}}"
}}
trap sig_handler INT TERM HUP QUIT

IFS=',' read SLURM_JOB_ID rest < <(sbatch --parsable array_job.sh)
if [[ -z "${{SLURM_JOB_ID}}" ]]
then
  echo "Submitting the SLURM job failed!"
  exit 1
fi

echo "SLURM job with ID ${{SLURM_JOB_ID}} submitted!"
total=1
while [[ "${{total}}" -gt 0 ]]
do
  pending=$(squeue --noheader --array -j "${{SLURM_JOB_ID}}" -t PD | wc -l)
  running=$(squeue --noheader --array -j "${{SLURM_JOB_ID}}" -t R | wc -l)
  total=$(squeue --noheader --array -j "${{SLURM_JOB_ID}}" | wc -l)
  current_time=$(date)
  echo "${{current_time}}: Job ${{SLURM_JOB_ID}}: ${{total}} runs found (${{pending}} pending, ${{running}} running) of {num_total_runs} total jobs."
  if [[ "${{total}}" -gt 0 ]]
  then
    sleep 10
  fi
done
"""

    with open(base_path / generated_scripts / "run_cluster_job.sh", mode="w") as f:
        f.write(script)


def _write_simple_script(run: Run) -> None:
    base_path = Path(".").absolute()
    generated_scripts = "generated_scripts"
    scripts_path = base_path / "setup_tools"
    project_path = base_path.parent / "projects"
    package_path = "/src/test_package"
    pynguin_image_name = list(run.docker_images.keys())[0]
    pynguin_test_dir = "pynguin_auto_tests_" + str(round((time.time() * 1000))) + "_" + str(random.randint(1000000, 9999999))

    script = f"""
PYNGUIN_IMAGE={pynguin_image_name}
PYNGUIN_IMAGE_PATH={base_path}{run.docker_images[pynguin_image_name][0]}
PYNGUIN_CONTAINER=pyn-{run.run_id}

INPUT_DIR_PHYSICAL={project_path}/{run.project_name}
OUTPUT_DIR_PHYSICAL={project_path}/{run.project_name}/{pynguin_test_dir}
PACKAGE_DIR_PHYSICAL={base_path}/src/test_package/
BASE_PATH={base_path}

TESTS_TO_BE_RUN={pynguin_test_dir}
PROJECT_NAME={run.project_name}
NUM_RUNS=20
HASH={run.project_hash}
PYPI_TAG={run.project_pypi_version}

echo PYNGUIN_IMAGE = $PYNGUIN_IMAGE
echo PYNGUIN_CONTAINER = $PYNGUIN_CONTAINER

function echo_blue {{
  BLUE="\\033[1;34m"
  NC="\\033[0m"
  echo -e "${{BLUE}}${1}${{NC}}\n"
}}

function create_and_run_pynguin_container {{
    download_dependencies
    echo_blue "Creating and starting container with name ${{PYNGUIN_CONTAINER}} with project '{run.project_name}' and modules '{run.modules}'"
    docker run --name $PYNGUIN_CONTAINER \\
    --rm -v $INPUT_DIR_PHYSICAL:/input:ro \\
    -v $OUTPUT_DIR_PHYSICAL:/output \\
    -v $PACKAGE_DIR_PHYSICAL:/package:ro \\
    $PYNGUIN_IMAGE \\
    -v \\
    --project-path /input \\
    --output-path /output \\
    --configuration-id {run.configuration_name} \\
    {" ".join(run.configuration_options)} \\
    --project-name {run.project_name} \\
    --module-name "$1" \\
    --seed {run.iteration} 
}}

function load_pynguin_image {{
    echo_blue "Loading Image ${{PYNGUIN_IMAGE}} from ${{PYNGUIN_IMAGE_PATH}}"
    docker load -i $PYNGUIN_IMAGE_PATH
    echo_blue "DONE LOADING PYNGUIN IMAGE..."
}}

function clone_project {{
  echo_blue "Adding project {run.project_name} into destination folder {project_path}"
  git clone {run.project_sources} {project_path}/{run.project_name}
  cd ${{INPUT_DIR_PHYSICAL}}
  if [ -n "${{HASH}}" ]
  then git reset --hard "${{HASH}}"
  echo_blue "Resetting to hash: ${{HASH}}"
  fi
  cd ${{BASE_PATH}}/generated_scripts
}}

function delete_project {{
rm -rf {project_path}/*
}}

function download_dependencies {{
    tag=${{PYPI_TAG}}
    echo_blue "Writing dependency into requirements file..."
    if [ -z "${{tag}}" ]
    then echo "{run.project_name}" > ${{BASE_PATH}}/src/test_package/package.txt
    else
    echo "{run.project_name}==${{tag}}" > ${{BASE_PATH}}{package_path}/package.txt
    fi
    echo_blue "Dependencies written to requirements file..."
}}

load_pynguin_image
clone_project
download_dependencies
"""
    csv_script = f"""
        \npython {scripts_path}/create_flapy_csv.py --name {run.project_name} --url ${{INPUT_DIR_PHYSICAL}} --hash ${{HASH}} --funcs_to_trace "" --tests {pynguin_test_dir} --runs ${{NUM_RUNS}} --run_id {run.run_id}
        """

    script += csv_script

    modules_to_run = "\ncreate_and_run_pynguin_container "
    modules_to_run += "\ncreate_and_run_pynguin_container ".join(run.modules)
    script += modules_to_run

    with open(base_path / generated_scripts / f"run_{run.run_id}.sh", mode="w") as f:
        f.write(script)


def write_csv(run: Run):
    """Creates an xml file for the pynguin run setup by csv"""
    base_path = Path(".").absolute()
    generated_scripts: str = "generated_scripts"
    scripts_path: str = base_path / "setup_tools"
    project_path = base_path.parent / "projects"
    package_path: str = f"src/test_package/{run.project_name}_" + str(round((time.time() * 1000))) + "_" + str(random.randint(1000000, 9999999))
    pynguin_image_name = list(run.docker_images.keys())[0]
    pynguin_test_dir: str = "pynguin_auto_tests_" + str(round((time.time() * 1000))) + "_" + str(random.randint(1000000, 9999999))

    input_dir_physical = project_path / run.project_name
    output_dir_physical = project_path / run.project_name / pynguin_test_dir
    package_dir_physical = base_path / package_path

    base_path = Path(".").absolute()
    csv_output_name: str = f"src/pynguin_csv/pynguin_run_{run.run_id}.csv"
    header: List[str] = ["INPUT_DIR_PHYSICAL", "OUTPUT_DIR_PHYSICAL", "PACKAGE_DIR_PHYSICAL", "BASE_PATH", "PROJ_NAME",
                         "PROJECT_SOURCES", "PROJ_HASH", "PYPI_TAG", "PROJ_MODULES", "CONFIG_NAME",
                         "CONFIGURATION_OPTIONS", "TESTS_TO_BE_RUN", "FUNCS_TO_TRACE", "THIRD_PARTY_COVERAGE",
                         "NUM_FLAPY_RUNS", "SEED"]

    csv_data: List[str] = [input_dir_physical, output_dir_physical, package_dir_physical, base_path, run.project_name,
                           run.project_sources, run.project_hash, run.project_pypi_version, " ".join(run.modules),
                           run.configuration_name, " ".join(run.configuration_options), pynguin_test_dir, run.flapy_config[1], run.flapy_config[1], run.flapy_config[2],
                           run.run_id]
    with open(base_path / csv_output_name, mode="a") as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(header)
        writer.writerow(csv_data)


def main(argv: List[str]) -> None:
    base_path = Path(".").absolute()
    merge_path = base_path / "src/pynguin_csv"
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
    args = parser.parse_args()
    config = args.definition
    repos = args.repositories
    slurm_setup, run_configurations, projects, flapy_config = _parse_xml(config, repos)
    runs: List[Run] = _create_runs(slurm_setup, run_configurations, projects, flapy_config)
    for run in runs:
       # _write_simple_script(run)
        write_csv(run)
    merger.merge_csv(merge_path, "*")
    #    _write_run_script(run)
    # _write_array_job_script(slurm_setup.constraint, len(runs))


# _write_main_script(len(runs))


if __name__ == '__main__':
    main(sys.argv)
