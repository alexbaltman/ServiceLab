import logging
import fnmatch
import sys
import os
import re

# create logger
# TODO: For now warning and error print. Got to figure out how
#       to import the one in stack.py properly.
helper_utils_logger = logging.getLogger('click_application')
logging.basicConfig()


def find_all_yaml_recurs(full_path):
    """Find all yaml files in given directory structure recursively.

    Args:
        full_path (str): Ths is the full path that you want
                         recursively explore for yaml files.
    Returns:
        Returncode (int):
            0 -- Success
            1 -- Failure
        matches (list): A list of files ending in yaml
                        with their absolute paths.

    Example Usage:
        >>> print full_path
        /Users/aaltman/Git/servicelab/servicelab/.stack/services/ccs-data
        >>> print find_all_yaml_recurs(full_path)
        0, [('/Users/aaltman/Git/servicelab/servicelab/.stack/services/ccs-data/utils/\
             ignition-utils/data-environment.yaml',
             '/Users/aaltman/Git/servicelab/servicelab/.stack/services/ccs-data/utils/\
             ignition-utils/rtp10-data-environment.yaml',
             '/Users/aaltman/Git/servicelab/servicelab/.stack/services/ccs-data/utils/\
             ignition-utils/rtp10-RH-data-environment.yaml',
             ...

        A very large list is typically expected when dealing with ccs-data.
    """
    matches = []
    if os.path.exists(full_path):
        for dirpath, dirnames, filenames in os.walk(full_path):
            # Note: Don't have to look for yml b/c lightfuse
            #       doesn't compile to "yml"s only "yaml"s
            for filename in fnmatch.filter(filenames, '*.yaml'):
                matches.append(os.path.join(dirpath, filename))
        return 0, matches
    else:
        helper_utils_logger.error("Could not find files in %s"
                                  % (full_path))
        return 1, matches


def set_user(path):
    """Sets user to whoever clone the git repo from gerrit.

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
    Returns:
        Returncode (int):
            0 -- Success
            1 -- Failure

    Example Usage:
        >>> print ctx.path
        /Users/aaltman/Git/servicelab/servicelab/.stack
        >>> print set_user(ctx.path)
        (0, aaltman)
    """
    matches = None
    username = ""

    path_to_reporoot = os.path.split(path)
    path_to_reporoot = os.path.split(path_to_reporoot[0])
    path_to_reporoot = path_to_reporoot[0]

    regex = re.compile(r'://([a-z]*)@?(ccs|cis)-gerrit.cisco.com')
    with open(os.path.join(path_to_reporoot, ".git", "config"), 'r') as f:
        for line in f.readlines():
            matches = re.search(regex, line)
            if matches:
                username = matches.group(1)
                return 0, username
    return 1, username


def get_current_service(path):
    """Get the service last set by the user if it exists.

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
    Returns:
        Returncode (int):
            0 -- Success
            1 -- Failure
        current_service (str): Return the current service as a string that
                               represents the last service set by the user.
                               It's found through the working directory file
                               called current, which should have a single
                               one word string.

    Example Usage:
        >>> print ctx.path
        /Users/aaltman/Git/servicelab/servicelab/.stack
        >>> print get_current_service(ctx.path)
        (0, service-redhouse-tenant)
    """
    if os.path.isfile(os.path.join(path, "current")):
            current_file = os.path.join(path, "current")
            f = open(current_file, 'r')
            # TODO: verify that current is set to something sane.
            current = f.readline()
            if current == "":
                helper_utils_logger.error("No service set.")
                return 1, current
            else:
                helper_utils_logger.debug("Working on %s" % (current))
                return 0, current


def get_path_to_utils(path):
    """Given the path to servicelab/servicelab/.stack return where the utils
       folder is expected.

    Args:
        path (str): Absolute path to .stack in servicelab repo.
                    '/Users/aaltman/Git/servicelab/servicelab/.stack'

    Returns:
        path (str): Absolute path to utils folder within servicelab.

    Example Usage:
        >>> print ctx.path
            '/Users/aaltman/Git/servicelab/servicelab/.stack'
        >>> print path_to_utils(ctx.path)
            '/Users/aaltman/Git/servicelab/servicelab/utils'
    """
    split_path = os.path.split(path)
    path_to_utils = os.path.join(split_path[0], "utils")
    return path_to_utils
