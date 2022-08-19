#!/bin/bash

GIT_MODULE_PATH=./.git/modules
PROJECTS_PATH=./src/projects
REPOSITORY_PATH=./csv/python_top_200.csv
SETUP_TOOLS_PATH=./setup_tools

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
{
while IFS=, read -r Project_Name Project_URL Project_Hash
do
  HASH=$(python3 "$SETUP_TOOLS_PATH"/tag_matcher.py -u "$Project_URL" -p "$Project_Name")
  echo_blue "READING PROJECT:
  NAME=                     ${Project_Name}
  URL=                      ${Project_URL}
  HASH=                     ${Project_Hash}
  MATCHING_GIT_TAG=         ${HASH}
  PATH=                     ${PROJECTS_PATH}/${name}"
  create_submodule "${Project_URL}" "${PROJECTS_PATH}/${Project_Name}" "${HASH}"
  $SETUP_TOOLS_PATH/create_experiment.py "${PROJECTS_PATH}/${Project_Name}" "${Project_URL}" "${Project_Hash}" "${Project_Name}"
  delete_submodule "${PROJECTS_PATH}/${Project_Name}"
done
} < <(tail -n +2 "${REPOSITORY_PATH}")

