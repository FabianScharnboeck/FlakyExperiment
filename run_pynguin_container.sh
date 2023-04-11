#!/bin/bash

# -- CHECK IF ENVIRONMENT VARIABLES ARE DEFINED
if [ -z ${LOCAL_PODMAN_ROOT+x} ]; then
    echo "LOCAL_PODMAN_ROOT not set, exiting"
    exit
fi
if [ -z ${PODMAN_HOME+x} ]; then
    echo "PODMAN_HOME not set, exiting"
    exit
fi

DEBUG=1
function debug_echo {
  [[ "${DEBUG}" = 1 ]] && echo "$@"
}

function echo_blue {
  BLUE="\033[1;34m"
  NC="\033[0m"
  echo -e "${BLUE}$1${NC}
"
}

# -- PARSE ARGS
RUN_ON="${1}"

# -- PYNGUIN RELATED ARGS
BASE_PATH="${2}"
INPUT_DIR_PHYSICAL="${3}"
OUTPUT_DIR_PHYSICAL="${4}"
PACKAGE_DIR_PHYSICAL="${5}"
PROJECT_NAME="${6}"
PROJ_SOURCES="${7}"
MODULE="${8}"
PROJ_HASH="${9}"
PYPI_TAG="${10}"
CONFIGURATION_NAME="${11}"
CONFIGURATION_OPTIONS="${12}"
SEED="${13}"

# -- LOGGING RELATED ARGUMENTS
MODULE_SLURM_OUTPUT_DIR="${14}"

# -- DEBUG OUTPUT
echo "-- $0 (run_container.sh)"
        debug_echo "    -- RELATED ARGUMENTS --"
        debug_echo "    INPUT DIRECTORY:        $INPUT_DIR_PHYSICAL"
        debug_echo "    OUTPUT DIRECTORY:       $OUTPUT_DIR_PHYSICAL"
        debug_echo "    PACKAGE DIRECTORY:      $PACKAGE_DIR_PHYSICAL"
        debug_echo "    BASE PATH:              $BASE_PATH"
        debug_echo "    CONFIGURATION NAME:     $CONFIGURATION_NAME"
        debug_echo "    CONFIGURATION OPTIONS:  $CONFIGURATION_OPTIONS"
        debug_echo "    PROJECT NAME:           $PROJECT_NAME"
        debug_echo "    PROJECT GIT HASH:       $PROJ_HASH"
        debug_echo "    PROJECT PYPI TAG:       $PYPI_TAG"
        debug_echo "    PROJECT MODULE:         $MODULE"



# -- PREPARE ENVIRONMENT
unset XDG_RUNTIME_DIR
unset XDG_CONFIG_HOME
# create podman folders
mkdir -p "${PODMAN_HOME}"
mkdir -p "${LOCAL_PODMAN_ROOT}"
# change home (your home dir doesn't get mounted on the cluster)
export HOME=$PODMAN_HOME
alias p='podman --root=$LOCAL_PODMAN_ROOT'

# -- INITIALIZE META FILE
if [[ "${RUN_ON=}" = "cluster" ]]
then
  META_FILE="$INPUT_DIR_PHYSICAL/pynguin_log.log"
  

  # -- LOG HOSTNAME
  echo "-- CONTAINER AND NODE RELATED ARGUMENTS --"	  >> "$META_FILE"
  echo "hostname:               $(cat /etc/hostname)"     >> "$META_FILE"
  echo "flapy_container_id:	$(podman --root="${LOCAL_PODMAN_ROOT}" images localhost/pynguin-0.27.0 --format "{{.ID}}")" >> "$META_FILE"
  echo "-- PYNGUIN RELATED ARGUMENTS --"                  >> "$META_FILE"
  echo "INPUT DIRECTORY:        $INPUT_DIR_PHYSICAL"      >> "$META_FILE"
  echo "OUTPUT DIRECTORY:       $OUTPUT_DIR_PHYSICAL"     >> "$META_FILE"
  echo "PACKAGE DIRECTORY:      $PACKAGE_DIR_PHYSICAL"    >> "$META_FILE"
  echo "BASE PATH:              $BASE_PATH"               >> "$META_FILE"
  echo "CONFIGURATION NAME:     $CONFIGURATION_NAME"      >> "$META_FILE"
  echo "CONFIGURATION OPTIONS:  $CONFIGURATION_OPTIONS"   >> "$META_FILE"
  echo "PROJECT NAME:           $PROJECT_NAME"            >> "$META_FILE"
  echo "PROJECT GIT HASH:       $PROJ_HASH"               >> "$META_FILE"
  echo "PROJECT PYPI TAG:       $PYPI_TAG"                >> "$META_FILE"
  echo "PROJECT MODULE:         $MODULE"                  >> "$META_FILE"
  echo "COVERAGE_REPORT_DIR     $MODULE_SLURM_OUTPUT_DIR">> "$META_FILE"
fi

  # -- EXECUTE CONTAINER
  if [[ "${RUN_ON}" = "cluster" ]]
  then
      echo "-- RUNNING PYNGUIN ON MODULE -->$MODULE<-- --"
      podman run --root="$LOCAL_PODMAN_ROOT"\
      --rm -v "$INPUT_DIR_PHYSICAL":/input:ro \
      -v "$OUTPUT_DIR_PHYSICAL":/output \
      -v "$PACKAGE_DIR_PHYSICAL":/package:ro \
      -v "$MODULE_SLURM_OUTPUT_DIR":/log \
      localhost/pynguin-0.27.0 \
      --project-path /input \
      --output-path /output \
      --module-name "${MODULE}" \
      --project-name "${PROJECT_NAME}" \
      --configuration-id "${CONFIGURATION_NAME}" \
      ${CONFIGURATION_OPTIONS} \
      --create-coverage-report True \
      --report-dir /log \
      --format-with-black False \
      --seed "${SEED}"
      echo "EXIT CODE: $?" >> "${MODULE_SLURM_OUTPUT_DIR}/${MODULE}-EXIT_CODE.log"
  elif [[ "${RUN_ON}" = "local" ]]
    then
      podman run \
      --rm -v /mnt"$INPUT_DIR_PHYSICAL":/input:ro \
      -v /mnt"$OUTPUT_DIR_PHYSICAL":/output \
      -v /mnt"$PACKAGE_DIR_PHYSICAL":/package:ro \
      localhost/pynguin-0.19.0 \
      -v \
      --project-path /input \
      --output-path /output \
      --configuration-id "${CONFIGURATION_NAME}" \
      ${CONFIGURATION_OPTIONS} \
      --create-coverage-report "True" \
      --report-dir "${PROJECT_SLURM_OUTPUT_DIR}/" \
      --project-name "${PROJECT_NAME}" \
      --module-name "${MODULE}" \
      --seed "${SEED}"
  else
      echo "Unknown value '$RUN_ON' for RUN_ON. Please use 'cluster' or 'local'."
      exit
  fi
