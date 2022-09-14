#!/usr/bin/env bash
#SBATCH --job-name=pynguin
#SBATCH --time=24:00:00
#SBATCH --mem=4GB

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
    PROJ_HASH PYPI_TAG PROJ_MODULES CONFIG_NAME CONFIGURATION_OPTIONS TESTS_TO_BE_RUN FUNCS_TO_TRACE \
    THIRD_PARTY_COVERAGE NUM_FLAPY_RUNS SEED <<< "${csv_line}"

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

echo "    tests to be run:        ${TESTS_TO_BE_RUN}"
echo "    funcs to trace:         ${FUNCS_TO_TRACE}"
echo "    number flapy runs:      ${NUM_FLAPY_RUNS}"

# -- LOG
{
    echo "slurm_array_task_id:    ${SLURM_ARRAY_TASK_ID}"
    echo "slurm_array_job_id:     ${SLURM_ARRAY_JOB_ID}"
    echo "slurm_job_id:           ${SLURM_JOB_ID}"
    echo "input_csv_line_num:     ${LINE_NUM}"
    echo "hostname_run_line:      $(cat /etc/hostname)"
} >> "${PYNGUIN_META_FILE}"

# -- RUN CONTAINER
if [[ ${PYNGUIN_RUN_ON} = "cluster" ]]; then
    srun \
        --output="$PYNGUIN_SLURM_OUTPUT_DIR/log.out" \
        --error="$PYNGUIN_SLURM_OUTPUT_DIR/log.out" \
        -- \
        ./run_pynguin_container.sh \
            "${PYNGUIN_RUN_ON}" \
	    "${BASE_PATH}" \
	    "${INPUT_DIR_PHYSICAL}" \
	    "${OUTPUT_DIR_PHYSICAL}" \
	    "${PACKAGE_DIR_PHYSICAL}" \
	    "${PROJ_NAME}" \
	    "${PROJ_SOURCES}" \
	    "${PROJ_MODULES}" \
	    "${PROJ_HASH}" \
	    "${PYPI_TAG}" \
	    "${CONFIG_NAME}" \
	    "${CONFIGURATION_OPTIONS}" \
	    "${SEED}" \
	    "${TESTS_TO_BE_RUN}" \
	    "${NUM_FLAPY_RUNS}" \
	    "${FUNCS_TO_TRACE}" \
        & srunPid=$!
elif [[ ${PYNGUIN_RUN_ON} = "local" ]]; then
    ./run_pynguin_container.sh \
        "TODO" \
    & srunPid=$!
else
    echo "Unknown value '$PYNGUIN_RUN_ON' for RUN_ON. Please use 'cluster' or 'local'."
    exit
fi

trap sighdl INT TERM HUP QUIT

while ! wait; do true; done
