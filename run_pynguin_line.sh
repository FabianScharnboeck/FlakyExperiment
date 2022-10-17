#!/usr/bin/env bash
#SBATCH --job-name=pynguin
#SBATCH --time=24:00:00
#SBATCH --mem=8GB

# -- CHECK IF ENVIRONMENT VARIABLES ARE DEFINED
if [[ -z "${PYNGUIN_CSV_FILE}" ]]; then
    echo "ERROR: PYNGUIN_CSV_FILE not defined"
    exit 1
fi
if [[ -z "${PYNGUIN_META_FILE}" ]]; then
    echo "ERROR: PYNGUIN_META_FILE not defined"
    exit 1
fi
if [[ -n "${SLURM_ARRAY_TASK_ID}" ]]; then
    LINE_NUM=$SLURM_ARRAY_TASK_ID
elif [[ -n "${FLAPY_INPUT_CSV_LINE_NUM}" ]]; then
    LINE_NUM=$PYNGUIN_INPUT_CSV_LINE_NUM
else
    echo "ERROR: either SLURM_ARRAY_TASK_ID or FLAPY_INPUT_CSV_LINE_NUM must be defined"
    exit 1
fi

echo "-- $0"
echo "    input csv file:      $PYNGUIN_CSV_FILE"
echo "    meta file:           $PYNGUIN_META_FILE"
echo "    slurm array task id: $SLURM_ARRAY_TASK_ID"
echo "    input csv line num:  $LINE_NUM"

function sighdl {
  kill -INT "${srunPid}" || true
}

# -- READ CSV LINE
csv_line=$(sed "${LINE_NUM}q;d" "${PYNGUIN_CSV_FILE}")
echo "csv_line:   ${csv_line}" >> "${PYNGUIN_META_FILE}"

# -- PARSE CSV LINE
IFS=, read -r INPUT_DIR_PHYSICAL OUTPUT_DIR_PHYSICAL PACKAGE_DIR_PHYSICAL BASE_PATH PROJ_NAME PROJ_SOURCES \
    PROJ_HASH PYPI_TAG PROJ_MODULES CONFIG_NAME CONFIGURATION_OPTIONS TESTS_TO_BE_RUN SEED <<< "${csv_line}"

# -- REPLACE ; WITH , IN CONFIGURATION OPTIONS
CONFIGURATION_OPTIONS=${CONFIGURATION_OPTIONS//";"/","}

# -- DEBUG OUTPUT
echo "    ----"
echo "    input directory:        ${INPUT_DIR_PHYSICAL}"
echo "    output directory:       ${OUTPUT_DIR_PHYSICAL}"
echo "    package directory:      ${PACKAGE_DIR_PHYSICAL}"
echo "    base path:              ${BASE_PATH}"
echo "    configuration name:     ${CONFIG_NAME}"
echo "    configuration options:  ${CONFIGURATION_OPTIONS}"
echo "    project name:           ${PROJ_NAME}"
echo "    project url:            ${PROJ_SOURCES}"
echo "    project git hash:       ${PROJ_HASH}"
echo "    project pypi tag:       ${PYPI_TAG}"
echo "    project modules:        ${PROJ_MODULES}"
echo "    project seed:           ${SEED}"

# -- LOG
{
    echo "slurm_array_task_id:    ${SLURM_ARRAY_TASK_ID}"
    echo "slurm_array_job_id:     ${SLURM_ARRAY_JOB_ID}"
    echo "slurm_job_id:           ${SLURM_JOB_ID}"
    echo "input_csv_line_num:     ${LINE_NUM}"
    echo "hostname_run_line:      $(cat /etc/hostname)"
} >> "${PYNGUIN_META_FILE}"

function clone_project {
 echo "Adding project into destination folder"
 git clone "${PROJ_SOURCES}" "${INPUT_DIR_PHYSICAL}"
 cd "${INPUT_DIR_PHYSICAL}"
 mkdir -p "${OUTPUT_DIR_PHYSICAL}"
 if [ -n "${PROJ_HASH}" ]
     then git reset --hard "${PROJ_HASH}"
     echo "Resetting to hash: ${PROJ_HASH}"
 fi
 cd "${BASE_PATH}"
}

# -- CLONE THE PROJECT
clone_project

PROJECT_SLURM_OUTPUT_DIR="${PYNGUIN_SLURM_OUTPUT_DIR}/logs/${PROJ_NAME}_${LINE_NUM}"
mkdir -p -m 777 $PROJECT_SLURM_OUTPUT_DIR

# -- RUN CONTAINER
IFS=' ' read -ra ELEMENTS <<< "${PROJ_MODULES}"
for MODULE in "${ELEMENTS[@]}"; do
    if [[ ${PYNGUIN_RUN_ON} = "cluster" ]]; then

        # -- CREATE MODULE SUBDIRECTORY FOR LOGGING
        MODULE_SLURM_OUTPUT_DIR="${PROJECT_SLURM_OUTPUT_DIR}/${MODULE}"
        mkdir -p -m 777 ${MODULE_SLURM_OUTPUT_DIR}

        # -- RUN PYNGUIN CONTAINER
        srun \
        --output="$MODULE_SLURM_OUTPUT_DIR/${MODULE}.out" \
        --error="$MODULE_SLURM_OUTPUT_DIR/${MODULE}.err" \
        -- \
        ./run_pynguin_container.sh \
            "${PYNGUIN_RUN_ON}" \
	    "${BASE_PATH}" \
	    "${INPUT_DIR_PHYSICAL}" \
	    "${OUTPUT_DIR_PHYSICAL}" \
	    "${PACKAGE_DIR_PHYSICAL}" \
	    "${PROJ_NAME}" \
	    "${PROJ_SOURCES}" \
	    "${MODULE}" \
	    "${PROJ_HASH}" \
	    "${PYPI_TAG}" \
	    "${CONFIG_NAME}" \
	    "${CONFIGURATION_OPTIONS}" \
	    "${SEED}" \
            "${MODULE_SLURM_OUTPUT_DIR}" \
            & srunPid=$!
    elif [[ ${PYNGUIN_RUN_ON} = "local" ]]; then
            ./run_pynguin_container.sh \
            "TODO" \
            & srunPid=$!
    else
            echo "Unknown value '$PYNGUIN_RUN_ON' for RUN_ON. Please use 'cluster' or 'local'."
            exit
    fi
done

trap sighdl INT TERM HUP QUIT

while ! wait; do true; done
