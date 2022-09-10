#!/usr/bin/env bash

# -- HELPER FUNCTIONS
DEBUG=1
function debug_echo {
  [[ "${DEBUG}" = 1 ]] && echo "$@"
}

# -- PARSE ARGUMENTS
RUN_ON="${1}"
CSV_FILE="${2}"
CONSTRAINT="${3}"

dos2unix "${CSV_FILE}"

# -- CREATE LOG DIR
if [[ $RUN_ON = "cluster" ]]
DATE_TIME=$(date +%Y%m%d_%H%M%S)
then SLURM_OUTPUT_DIR=$(mktemp -d $(pwd)/src/results/pynguin_slurm_log/slurm_log_"$DATE_TIME"_XXXX)
cp "${0}" "${SLURM_OUTPUT_DIR}"
cp "${2}" "${SLURM_OUTPUT_DIR}/input.csv"
PYNGUIN_META_FILE="${SLURM_OUTPUT_DIR}/pynguin_run.yaml"
fi

# -- EXPORT VARIABLES
export PYNGUIN_CSV_FILE="${SLURM_OUTPUT_DIR}/input.csv"
export PYNGUIN_RUN_ON=${RUN_ON}
export PYNGUIN_SLURM_OUTPUT_DIR="${SLURM_OUTPUT_DIR}"
export PYNGUIN_META_FILE="${PYNGUIN_META_FILE}"

# -- SBATCH LOG FILES
SBATCH_LOG_FOLDER="$SLURM_OUTPUT_DIR/sbatch_logs/"
mkdir -p "$SBATCH_LOG_FOLDER"
SBATCH_LOG_FILE_PATTERN="$SBATCH_LOG_FOLDER/log-%a.out"

# -- INPUT PRE-PROCESSING
dos2unix "${CSV_FILE}"
CSV_FILE_LENGTH=$(wc -l < "$CSV_FILE")
debug_echo "    CSV file length:   $CSV_FILE_LENGTH"

# -- RUN
if [[ $RUN_ON = "cluster" ]]
then
    echo "running on cluster"
    export PODMAN_HOME=/local/$USER/podman.home
    export LOCAL_PODMAN_ROOT=/local/$USER/podman
    sbatch_info=$(sbatch --parsable \
        --constraint="${CONSTRAINT}" \
        --output "$SBATCH_LOG_FILE_PATTERN" \
        --error  "$SBATCH_LOG_FILE_PATTERN" \
        --array=2-"$CSV_FILE_LENGTH" \
        -- \
        ./run_pynguin_line.sh
    )
    echo "sbatch_submission_info: $sbatch_info"
    echo "sbatch_submission_info: \"$sbatch_info\"" >> "$PYNGUIN_META_FILE"
elif [[ $RUN_ON = "local" ]]
then
    for i in $(seq 2 "$CSV_FILE_LENGTH"); do
        PYNGUIN_INPUT_CSV_LINE_NUM=$i ./run_pynguin_line.sh
    done
else
    echo "Unknown value '$RUN_ON' for RUN_ON. Please use 'cluster' or 'local'."
    exit
fi
