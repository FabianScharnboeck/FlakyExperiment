#!/usr/bin/env bash

# -- HELPER FUNCTIONS
DEBUG=1
function debug_echo {
  [[ "${DEBUG}" = 1 ]] && echo "$@"
}

# -- PARSE ARGUMENTS
RUN_ON="${1}"
CSV_FILE="${2}"

dos2unix "${CSV_FILE}"

# -- CREATE LOG DIR
if [[ $RUN_ON = "cluster" ]]
DATE_TIME=$(date +%Y%m%d_%H%M%S)
then SLURM_OUTPUT_DIR=$(mktemp -d $(pwd)/src/results/pynguin_slurm_log/slurm_log_"$DATE_TIME"_XXXX)
cp "${0}" "${SLURM_OUTPUT_DIR}"
cp "${2}" "${SLURM_OUTPUT_DIR}"
fi

# -- MAIN
{
    read # ignore header
    while IFS=, read -r INPUT_DIR_PHYSICAL OUTPUT_DIR_PHYSICAL PACKAGE_DIR_PHYSICAL BASE_PATH PROJ_NAME PROJ_SOURCES \
    PROJ_HASH PYPI_TAG PROJ_MODULES CONFIG_NAME CONFIGURATION_OPTIONS TESTS_TO_BE_RUN FUNCS_TO_TRACE \
    THIRD_PARTY_COVERAGE NUM_FLAPY_RUNS SEED; do

        debug_echo "-- $0"
        debug_echo "    input directory:        $INPUT_DIR_PHYSICAL"
        debug_echo "    output directory:       $OUTPUT_DIR_PHYSICAL"
        debug_echo "    package directory:      $PACKAGE_DIR_PHYSICAL"
        debug_echo "    base path:              $BASE_PATH"
        debug_echo "    configuration name:     $CONFIG_NAME"
        debug_echo "    configuration options:  $CONFIGURATION_OPTIONS"
        debug_echo "    project name:           $PROJ_NAME"
        debug_echo "    project url:            $PROJ_SOURCES"
        debug_echo "    project git hash:       $PROJ_HASH"
        debug_echo "    project pypi tag:       $PYPI_TAG"
        debug_echo "    project modules:        $PROJ_MODULES"
        debug_echo "    project seed:           $SEED"

        debug_echo "    tests to be run:        $TESTS_TO_BE_RUN"
        debug_echo "    funcs to trace:         $FUNCS_TO_TRACE"
        debug_echo "    number flapy runs:      $NUM_FLAPY_RUNS"

        if [[ $RUN_ON = "cluster" ]]
        then
            export PODMAN_HOME=/local/$USER/podman.home
            export LOCAL_PODMAN_ROOT=/local/$USER/podman
            # -- RUN ON CLUSTER
            sbatch \
                --constraint "pontipine" \
                -o "$SLURM_OUTPUT_DIR/${PROJ_NAME}_${SEED}.out" \
                -e "$SLURM_OUTPUT_DIR/${PROJ_NAME}_${SEED}.out" \
                -- \
                ./run_pynguin_container.sh \
                "${RUN_ON}" \
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
                "${FUNCS_TO_TRACE}"
        elif [[ $RUN_ON = "local" ]]
        then
          ./run_pynguin_container.sh \
          "${RUN_ON}" \
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
          "${FUNCS_TO_TRACE}"
        else
            echo "Unknown value '$RUN_ON' for RUN_ON. Please use 'cluster' or 'local'."
            exit
        fi

    done
} <"${CSV_FILE}"
