import argparse
import subprocess
import sys
import re

from typing import List, Tuple, Match, Set

import requests
from requests import Response


def pypi_versions(package_name: str) -> str:
    """
    Searches for the latest PyPi version of a given package name.
    :param package_name: String representing the package for which the latest version should be found.
    :return: the latest version on PyPi
    """
    url: str = "https://pypi.org/pypi/%s/json" % (package_name,)
    r: Response = requests.get(url=url)
    data = r.json()
    versions: List[str] = sorted(list(data["releases"].keys()))
    latest_version: str = versions[-1]
    return latest_version


def get_latest_commit(package_url: str) -> str:
    """
    Return the latest commit hash of a given GitHub URL
    """
    data: str = str(
        subprocess.check_output(["git", "ls-remote", package_url, "HEAD"])
    )
    commit_hash: str = data.split("\\")[0].split("\'")[1]
    return commit_hash


def match_git_tag_versions(package_url: str, pypi_version: str) -> Tuple[str, str, str]:
    """
    Searches for all available Github versions of a given URL and matches it with the given pypi version.
    :param package_url: GitHub URL of the project.
    :param pypi_version: Pypi_version of the project.
    :return: Either the matching versions or the Pypi_version and the latest github commit are returned with a status
    flag indicating the versions are matching or not.
    """
    tags: Set[str] = find_git_tag_versions_by_url(package_url=package_url)
    latest_commit: str = get_latest_commit(package_url=package_url)

    # Falls es keine Tags gibt, benutze den latest commit
    if not tags:
        print(latest_commit)
        return pypi_version, latest_commit, "FALLBACK"

    # matching_git_tag (beinhaltet möglicherweise ein 'v' davor) auf dazugehörige pypi version setzen
    for git_tag in tags:
        regex = "v*"+pypi_version
        if re.match(regex, git_tag):
            matching_git_tag: str = git_tag
            print(matching_git_tag)
            return pypi_version, matching_git_tag, "MATCH"

    # Falls es keine matching tags gibt, benutze spätesten commit.
    print(latest_commit)
    return pypi_version, latest_commit, "FALLBACK"


def find_git_tag_versions_by_url(package_url: str) -> Set[str]:
    """
    :param package_url: GitHub URL
    :return: Set of all GitTag versions
    """
    data: str = str(
        subprocess.check_output(["git", "ls-remote", "--tags", package_url])
    )
    new_data: List[str] = data.split("\\n")
    tags: Set[str] = set()
    for d in new_data:
        git_tag: Match = re.search("tags/.*[0-9]+", d)
        if git_tag is not None:
            git_tag: str = str(git_tag.group(0))
            git_tag = git_tag.split("/")[1]
            tags.add(git_tag)
    return tags


def get_tags(package, package_url) -> Tuple[str, str, str]:
    latest_pypi_version: str = pypi_versions(package)
    return match_git_tag_versions(package_url, latest_pypi_version)


def main(argv: List[str]) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--package",
        dest="package",
        required=True,
        help="Package to get the latest pypi version from and to match with corresponding git tag.",
    )
    parser.add_argument(
        "-u",
        "--url",
        dest="url",
        required=True,
        help="Package url to get the matching git-tag version from and to match with corresponding pypi tag.",
    )
    args = parser.parse_args()
    package = args.package
    package_url = args.url

    """
    At the moment this module does not provide any meaningful output.
    """
    latest_pypi_version: str = pypi_versions(package)
    match_git_tag_versions(package_url, latest_pypi_version)


if __name__ == "__main__":
    main(sys.argv)
