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
PROJ_MODULES="${8}"
PROJ_HASH="${9}"
PYPI_TAG="${10}"
FROZEN_REQUIREMENTS="${11}"
CONFIGURATION_NAME="${12}"
CONFIGURATION_OPTIONS="${13}"
SEED="${14}"
WRITE_REQS="${15}"

function download_dependencies {
  mkdir -p "${PACKAGE_DIR_PHYSICAL}"
  if [[ "${PYPI_TAG}" -ne "" ]]; then
    tag=${PYPI_TAG}
    echo_blue "Dependency option: PYPI_TAG"
    echo_blue "Writing dependency into requirements file..."
    if [ -z "${tag}" ]
    then echo "${PROJECT_NAME}" > "${PACKAGE_DIR_PHYSICAL}"/package.txt
    else
    echo "${PROJECT_NAME}==${tag}" > "${PACKAGE_DIR_PHYSICAL}"/package.txt
    fi
    echo_blue "Dependencies written to requirements file..."
  else
    echo_blue "Dependency option: FROZEN_REQUIREMENTS"
    if [ -z "${FROZEN_REQUIREMENTS}" ]
      then echo "Error. FROZEN_REQUIREMENTS was empty."
      exit 1
    else
      echo_blue "Writing dependency into requirements file..."
      IFS=' ' read -ra ELEMENTS <<< "${FROZEN_REQUIREMENTS}"
      for REQ in "${ELEMENTS[@]}"; do
	echo "Printing ${REQ} into ${PACKAGE_DIR_PHYSICAL}"
        printf "%s\n" "${REQ}" >> "${PACKAGE_DIR_PHYSICAL}"/package.txt
      done
    fi
  fi

}

function clone_project {
  echo_blue "Adding project into destination folder"
  git clone "${PROJ_SOURCES}" "${INPUT_DIR_PHYSICAL}"
  cd "${INPUT_DIR_PHYSICAL}"
  mkdir -p "${OUTPUT_DIR_PHYSICAL}"
  if [ -n "${PROJ_HASH}" ]
  then git reset --hard "${PROJ_HASH}"
  echo_blue "Resetting to hash: ${PROJ_HASH}"
  fi
  cd "${BASE_PATH}"
}

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
        debug_echo "    PROJECT MODULES:        $PROJ_MODULES"



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
  META_FILE="$INPUT_DIR_PHYSICAL/!pynguin_log.yaml"
  touch "$META_FILE"

  # -- LOG HOSTNAME
  echo "hostname:               $(cat /etc/hostname)"     >> "$META_FILE"
  echo "-- PYNGUIN RELATED ARGUMENTS --"                  >> "$META_FILE"
  echo "INPUT DIRECTORY:        $INPUT_DIR_PHYSICAL"      >> "$META_FILE"
  echo "OUTPUT DIRECTORY:       $OUTPUT_DIR_PHYSICAL"     >> "$META_FILE"
  echo "PACKAGE DIRECTORY:      $PACKAGE_DIR_PHYSICAL"    >> "$META_FILE"
  echo "BASE PATH:              $BASE_PATH"               >> "$META_FILE"
  echo "CONFIGURATION NAME:     $CONFIGURATION_NAME"      >> "$META_FILE"
  echo "CONFIGURATION OPTIONS:  $CONFIGURATION_OPTIONS"   >> "$META_FILE"
  echo "PROJECT NAME:           $PROJ_NAME"               >> "$META_FILE"
  echo "PROJECT GIT HASH:       $PROJ_HASH"               >> "$META_FILE"
  echo "PROJECT PYPI TAG:       $PYPI_TAG"                >> "$META_FILE"
  echo "PROJECT MODULES:        $PROJ_MODULES"            >> "$META_FILE"
fi


# -- CLONE PROJECT, WRITE DEPENDENCY FILES IF NOT DONE YET AND EXECUTE THE CONTAINER
clone_project

if [[ "${WRITE_REQS}" = "true" ]]; then
  download_dependencies
fi

IFS=' ' read -ra ELEMENTS <<< "${PROJ_MODULES}"
for MODULE in "${ELEMENTS[@]}"; do
  # -- EXECUTE CONTAINER
  if [[ "${RUN_ON}" = "cluster" ]]
    then
      podman run --root="$LOCAL_PODMAN_ROOT"\
      --rm -v "$INPUT_DIR_PHYSICAL":/input:ro \
      -v "$OUTPUT_DIR_PHYSICAL":/output \
      -v "$PACKAGE_DIR_PHYSICAL":/package:ro \
      localhost/pynguin-0.26.0 \
      --project-path /input \
      --output-path /output \
      --configuration-id "${CONFIGURATION_NAME}" \
      ${CONFIGURATION_OPTIONS} \
      --project-name "${PROJECT_NAME}" \
      --module-name "${MODULE}" \
      --seed "${SEED}"
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
      --project-name "${PROJECT_NAME}" \
      --module-name "${MODULE}" \
      --seed "${SEED}"
  else
      echo "Unknown value '$RUN_ON' for RUN_ON. Please use 'cluster' or 'local'."
      exit
  fi
done
