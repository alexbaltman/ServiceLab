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
    matches = []
    username = ""

    path_to_reporoot = os.path.split(path)
    path_to_reporoot = os.path.split(path_to_reporoot[0])
    path_to_reporoot = path_to_reporoot[0]

    regex = re.compile(r'://([a-z]*)@?(ccs|cis)-gerrit.cisco.com')
    with open(os.path.join(path_to_reporoot, ".git", "config"), 'r') as f:
        for line in f.readlines():
            matches = re.search(regex, line)
    username = matches.group(1)
    if not username:
        return 1, username
    else:
        return 0, username
