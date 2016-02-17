import os
import re
import click
import shutil
import fnmatch
import getpass

import logger_utils

import yaml_utils
from servicelab import settings

slab_logger = logger_utils.setup_logger(settings.verbosity, 'stack.utils.helper')


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
    slab_logger.log(15, 'Finding all yaml files within %s' % full_path)
    matches = []
    if os.path.exists(full_path):
        for dirpath, dirnames, filenames in os.walk(full_path):
            # Note: Don't have to look for yml b/c lightfuse
            #       doesn't compile to "yml"s only "yaml"s
            for filename in fnmatch.filter(filenames, '*.yaml'):
                matches.append(os.path.join(dirpath, filename))
        return 0, matches
    else:
        slab_logger.error("Could not find files in %s" % (full_path))
        return 1, matches


def get_gitusername(path):
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
        >>> print path
        /Users/aaltman/Git/servicelab/servicelab/.stack
        >>> print get_gitusername(path)
        (0, aaltman)
    """
    slab_logger.log(15, 'Extracting username from gerrit clone command')
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
                if not username:
                    return 1, username
                slab_logger.debug('Gerrit username is %s' % username)
                return 0, username
    slab_logger.debug('Unable to determine username')
    return 1, username


def get_loginusername():
    """Gets the login  user name.

    Returns:
        username(str): login name

    Example Usage:
    >>> print get_loginusername()
    aaltman
    """
    return getpass.getuser()


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
        >>> print path
        /Users/aaltman/Git/servicelab/servicelab/.stack
        >>> print get_current_service(path)
        (0, service-redhouse-tenant)
    """
    slab_logger.log(15, 'Determining current service from last "stack workon" command')
    if os.path.isfile(os.path.join(path, "current")):
            current_file = os.path.join(path, "current")
            f = open(current_file, 'r')
            # TODO: verify that current is set to something sane.
            current = f.readline()
            if current != "":
                slab_logger.debug('Current service is %s' % current)
                return 0, current
    slab_logger.debug('Unable to determine current service')
    return 1, ""


def get_path_to_utils(path):
    """Given the path to servicelab/servicelab/.stack return where the utils
       folder is expected.

    Args:
        path (str): Absolute path to .stack in servicelab repo.
                    '/Users/aaltman/Git/servicelab/servicelab/.stack'

    Returns:
        path (str): Absolute path to utils folder within servicelab.

    Example Usage:
        >>> print path
            '/Users/aaltman/Git/servicelab/servicelab/.stack'
        >>> print path_to_utils(path)
            '/Users/aaltman/Git/servicelab/servicelab/utils'
    """
    slab_logger.log(15, 'Determining path to servicelab/servicelab/utils')
    split_path = os.path.split(path)
    path_to_utils = os.path.join(split_path[0], "utils")
    slab_logger.debug('Utils path is %s' % path_to_utils)
    return path_to_utils


def name_vm(name, path):
    """This is how we're currently generating a name for arbitrary vms.

    Args:
        name (str): The suffix to attach to the name.
        path (str): The path to the yaml file that's holding your inventory. Typically,
                    the vagrant.yaml in path --> .stack/vagrant.yaml

    Returns:
        hsotname (str): The name of the next vm inline that's not in the
        vagrant.yaml for the given path.

    Example Usage:
        >>> helper_utils.name_vm('rhel7', path)
        rhel7-001
    """
    slab_logger.log(15, 'Determining next available hostname for %s' % name)
    for i in xrange(1, 100):
        hostname = name + "-" + "%03d" % (i)
        returncode = yaml_utils.host_exists_vagrantyaml(hostname, path)
        if returncode == 1:
            slab_logger.debug('Hostname set to %s' % hostname)
            return hostname


def destroy_files(paths_to_files):
    """For cmd_destroy mostly - allows you to delete a batch of files.

    Args:
        paths_to_files (list): Take a list of paths to files as strings so
                               that they can be removed.

    Returns:
        0 - Successfully deleted
        1 - Didn't delete successfully

    Example Usage:
        >>> destroy_files(['/root/.bashrc', '/root/.config', '/home/aaltman/myfile'])
        0
    """
    for mypath in paths_to_files:
        slab_logger.log(15, "Destroying {0}".format(mypath))
        if os.path.exists(mypath):
            try:
                os.remove(mypath)
                slab_logger.debug("File destroyed successfully: {0}".format(mypath))
            except OSError as ex:
                slab_logger.debug("File was not destroyed: {0}".format(mypath))
                slab_logger.error('Caught error: ')
                slab_logger.error(ex)
                return 1
        else:
            slab_logger.debug("File does not exist : {0}".format(mypath))
    return 0


def destroy_dirs(paths):
    """For cmd_destroy mostly - allows you to delete a batch of directories.

    Args:
        paths (list): Take a list of paths to directories as strings so
                      that they can be removed.

    Returns:
        0 - Successfully deleted
        1 - Didn't delete successfully

    Example Usage:
        >>> destroy_dirs(['/home/aaltman', '/etc', '/'])
        0
    """
    for path in paths:
        if os.path.exists(path):
            slab_logger.log(15, "Destroying {0}".format(path))
            try:
                shutil.rmtree(path)
                slab_logger.debug("Directory destroyed successfully : {0}".format(path))
            except OSError as ex:
                slab_logger.debug("Directory was not destroyed : {0}".format(path))
                slab_logger.error('Caught error: ')
                slab_logger.error(ex)
                return 1
        else:
            slab_logger.debug("Directory does not exist : {0}".format(path))
    return 0
