#!/bin/bash

GIT_MODULE_PATH=./.git/modules
PROJECTS_PATH=./src/projects
SETUP_TOOLS_PATH=./setup_tools

# CSV files
REPOSITORY_PATH=./csv/martin_frozen_requirements_2.csv
REPOSITORY_PATH_WITH_FROZEN_REQ=./csv/martin_frozen_requirements.csv


MODE=${1}
MODULE_EXPLORATION=${2}
OUTPUT=${3}

function echo_blue {
  BLUE="\033[1;34m"
  NC="\033[0m"
  echo -e "${BLUE}${1}${NC}\n"
}

function create_submodule {
  echo_blue "Adding submodule ${1} into destination folder ${2}"
  git submodule add --force "$1" "$2"
  echo_blue "Submodules hash is:        ${3}"
  WD=$(pwd)
  cd "${2}"
  echo_blue "Working Directory: $(pwd)"
  echo_blue "Resetting to Version:      ${3}"
  git reset --hard "${3}"
  cd "${WD}"
  echo_blue "Created submodule..."
}

function delete_submodule {
  echo_blue "Deleting submodule from destination folder ${1}"
  git submodule deinit -f "${1}"
  git rm -f "${1}"
  rm -r -f "${GIT_MODULE_PATH}"/"${1}"
  echo_blue "Deleted submodule..."
}

# Read the csv file and extract module path information.
# NOTE: Absolute directory paths, when working with git submodules, did not work reliably.
# Therefore relative paths are used.
if [[ ${MODULE_EXPLORATION} = true ]]; then
{
while IFS=, read -r Project_Name Project_URL Project_Hash
do
  if [[ ${MODE} = "TAG" ]];
  then \
    HASH=$(python3 "$SETUP_TOOLS_PATH"/tag_matcher.py -u "$Project_URL" -p "$Project_Name")
    echo_blue "READING PROJECT, MODE=${MODE}:
    NAME=                     ${Project_Name}
    URL=                      ${Project_URL}
    HASH=                     ${Project_Hash}
    MATCHING_GIT_TAG=         ${HASH}
    PATH=                     ${PROJECTS_PATH}/${name}"
    create_submodule "${Project_URL}" "${PROJECTS_PATH}/${Project_Name}" "${HASH}"
    $SETUP_TOOLS_PATH/create_experiment.py --proj_path "${PROJECTS_PATH}/${Project_Name}" --proj_url "${Project_URL}" --proj_hash "" --proj_name "${Project_Name}" --output "${OUTPUT}"
    delete_submodule "${PROJECTS_PATH}/${Project_Name}"

  elif [[ ${MODE} = "FROZEN_REQ" ]]; then
    echo_blue "READING PROJECT, MODE=${MODE}:
    NAME=                     ${Project_Name}
    URL=                      ${Project_URL}
    HASH=                     ${Project_Hash}
    PATH=                     ${PROJECTS_PATH}/${name}"
    create_submodule "${Project_URL}" "${PROJECTS_PATH}/${Project_Name}" "${Project_Hash}"
    dos2unix "${Project_Hash}"
    $SETUP_TOOLS_PATH/create_experiment.py --proj_path "${PROJECTS_PATH}/${Project_Name}" --proj_url "${Project_URL}" --proj_hash "${Project_Hash}" --proj_name "${Project_Name}" --output "${OUTPUT}"
    delete_submodule "${PROJECTS_PATH}/${Project_Name}"
  else
    echo_blue "Unknown value '${MODE}', value has to be either 'TAG' or 'FROZEN_REQ'."
    exit
  fi
done
} < <(tail -n +2 "${REPOSITORY_PATH}")
fi

PYNGUIN_OUTPUT=./src/pynguin_csv/pynguin.csv
if [[ "${MODE}" = "FROZEN_REQ" ]]; then
  python3 experiment.py -d exp_flakiness.xml -r "${OUTPUT}" -o "${PYNGUIN_OUTPUT}" -e True -g "${REPOSITORY_PATH_WITH_FROZEN_REQ}" -i "${PYNGUIN_OUTPUT}"
elif [[ "${MODE}" = "TAG" ]]; then
  python3 experiment.py -d exp_flakiness.xml -r "${OUTPUT}" -o "${PYNGUIN_OUTPUT}"
fi

