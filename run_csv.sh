#!/usr/bin/env bash

# -- DOC
# This scripts require LOCAL_PODMAN_ROOT to be set

# -- HELPER FUNCTIONS
DEBUG=1
function debug_echo {
  [[ "${DEBUG}" = 1 ]] && echo "$@"
}

# -- PARSE ARGUMENTS
RUN_ON=$1
CSV_FILE=$2
PLUS_RANDOM_RUNS=$3
FLAPY_ARGS=$4
RESULTS_PARENT_FOLDER=$5

# -- DEBUG OUTPUT
debug_echo "-- $0"
debug_echo "    Run on:            $RUN_ON"
debug_echo "    CSV file:          $CSV_FILE"
debug_echo "    Plus random runs:  $PLUS_RANDOM_RUNS"
debug_echo "    Flapy args:        $FLAPY_ARGS"
debug_echo "    ----"


# -- INPUT PRE-PROCESSING
dos2unix "${CSV_FILE}"
CSV_FILE_LENGTH=$(wc -l < "$CSV_FILE")
debug_echo "    CSV file length:   $CSV_FILE_LENGTH"

# -- CREATE RESULTS_DIR
if [ -z "${RESULTS_PARENT_FOLDER}" ]; then
    RESULTS_PARENT_FOLDER=$(pwd)
fi
DATE_TIME=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="${RESULTS_PARENT_FOLDER}/flapy-results_${DATE_TIME}"
mkdir -p "${RESULTS_DIR}"

# -- SAVE INPUT FILE
FLAPY_META_FOLDER="$RESULTS_DIR/!flapy.run/"
mkdir "${FLAPY_META_FOLDER}"
cp "${CSV_FILE}" "${FLAPY_META_FOLDER}/input.csv"

# -- LOG META INFOS
FLAPY_META_FILE="$FLAPY_META_FOLDER/flapy_run.yaml"
{
    echo "run_on:                 \"$RUN_ON\""
    echo "csv_file:               \"$CSV_FILE\""
    echo "plus_random_runs:       \"$PLUS_RANDOM_RUNS\""
    echo "flapy_args:             \"$FLAPY_ARGS\""
    echo "csv_file_length:        $CSV_FILE_LENGTH"
} >> "$FLAPY_META_FILE"


# -- EXPORT VARIALBE
#     these variables will be picked up by run_line.sh
export FLAPY_INPUT_CSV_FILE="${FLAPY_META_FOLDER}/input.csv"
export FLAPY_INPUT_PLUS_RANDOM_RUNS=$PLUS_RANDOM_RUNS
export FLAPY_INPUT_OTHER_ARGS=$FLAPY_ARGS
export FLAPY_INPUT_RUN_ON=$RUN_ON
export FLAPY_DATE_TIME=$DATE_TIME
export FLAPY_RESULTS_DIR=$RESULTS_DIR

# -- SBATCH LOG FILES
SBATCH_LOG_FOLDER="$FLAPY_META_FOLDER/sbatch_logs/"
mkdir -p "$SBATCH_LOG_FOLDER"
SBATCH_LOG_FILE_PATTERN="$SBATCH_LOG_FOLDER/log-%a.out"

# -- RUN
if [[ $RUN_ON = "cluster" ]]
then
    echo "running on cluster"
    export PODMAN_HOME=/local/$USER/podman.home
    export LOCAL_PODMAN_ROOT=/local/$USER/podman
    sbatch_info=$(sbatch --parsable \
        --constraint="" \
        --output "$SBATCH_LOG_FILE_PATTERN" \
        --error  "$SBATCH_LOG_FILE_PATTERN" \
        --array=2-"$CSV_FILE_LENGTH" \
        -- \
        run_line.sh
    )
    echo "sbatch_submission_info: $sbatch_info"
    echo "sbatch_submission_info: \"$sbatch_info\"" >> "$FLAPY_META_FILE"
elif [[ $RUN_ON = "local" ]]
then
    for i in $(seq 2 "$CSV_FILE_LENGTH"); do
        FLAPY_INPUT_CSV_LINE_NUM=$i ./run_line.sh
    done
else
    echo "Unknown value '$RUN_ON' for RUN_ON. Please use 'cluster' or 'local'."
    exit
fi