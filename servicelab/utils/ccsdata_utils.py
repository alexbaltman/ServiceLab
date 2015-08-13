import logging
import sys
import os
import yaml

# create logger
# TODO: For now warning and error print. Got to figure out how
#       to import the one in stack.py properly.
service_utils_logger = logging.getLogger('click_application')
logging.basicConfig()


def get_environment_yaml_file(path, site, env):
    """ Creates the env directory path for given path, site and environemt.
    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
        site (str): Desired site
        env (str): Desired environment

    Returns:
        Returns a single string with the path to the created environment.yaml file.

    Example Usage:
        >>> print get_env_for_site_path("/Users/nan/Git/servicelab/servicelab/.stack"
                                        "ccs-dev-1", "servicelab")
        /Users/kunanda/Git/servicelab/servicelab/.stack/services/ccs-data/sites/
        ccs-dev-1/environments/servicelab
    """
    return os.path.join(path,
                        "services", "ccs-data",
                        "sites", site,
                        "environments", env,
                        "data.d", "environment.yaml")


def get_env_settings_for_site(path, site, env):
    """ Creates the env directory path for given path, site and environemt.
    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
        site (str): Desired site
        env (str): Desired environment

    Returns:
        Returns a loaded yaml dictionary or None.

    Example Usage:
        >>> print get_env_settings_for_site("/Users/nan/Git/servicelab/servicelab/.stack"
                                        "ccs-dev-1", "servicelab")
    """
    fnm = os.path.join(path,
                       "services", "ccs-data",
                       "sites", site,
                       "environments", env,
                       "data.d",
                       "environment.yaml")
    with open(fnm) as yaml_file:
        return yaml.load(yaml_file)
    return None


def get_env_for_site_path(path, site, env):
    """Gets the environment directory path for a given path, site and environment

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
        site (str): Desired site
        env (str): Desired environment

    Returns:
        Returns a single string with the path to the created environment.

    Example Usage:
        >>> print get_env_for_site_path("/Users/aaltman/Git/servicelab/servicelab/.stack",
            "ccs-dev-1", "servicelab" )
        /Users/aaltman/Git/servicelab/servicelab/.stack/services/ccs-data/sites/
        ccs-dev-1/environments/servicelab
    """
    return os.path.join(path, "services", "ccs-data", "sites", site,
                        "environments", env)


def list_envs_or_sites(path):
    """Lists all sites and environments in ccs-data

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.

    Returns:
        Returns a dictionary of dictionaries (site -> dirname -> host) such that
        each sitename maps to all host files within the directories it maps to.

    Example Usage:
        >>> print list_envs_or_sites("/Users/aaltman/Git/servicelab/servicelab/.stack")
    """
    # TODO: JIC we want to list services in the future.
    services = []
    os.listdir(path)
    # TODO: Add error handling and possibly return code
    ccsdata_reporoot = os.path.join(path, "services", "ccs-data")
    ccsdata_sitedir = os.path.join(ccsdata_reporoot, "sites")
    our_sites = {}
    our_sites = {x: None for x in os.listdir(ccsdata_sitedir)}
    for key in our_sites:
        # Note: os.walk provides dirpath, dirnames, and files,
        #       but next()[1] provides us just dirnames for an
        #       absolute path.
        # Note: Expected to print dirs of environments/ directiory
        # Note: Assumption - every site will have dir "environments"
        # Note: Couldn't figure out how else to get the dirs correctly
        #       associated so I do the dict comprehension before the
        #       for loop.
        our_sites[key] = {dirnames: None for dirnames in os.walk(os.path.join(
                                                         ccsdata_sitedir, key,
                                                         "environments")).next()[1]}
        for dirs in os.walk(os.path.join(ccsdata_sitedir, key,
                                         "environments")).next()[1]:

            # Note: Get the hosts for each env in each site and add it to data structure
            #       under the right grouping.
            for _, _, files in os.walk(os.path.join(ccsdata_sitedir, key, "environments",
                                                    dirs, "hosts.d")):
                our_sites[key][dirs] = files

            # TODO: get this working - list operator already used
            for _, _, files in os.walk(os.path.join(ccsdata_sitedir, key, "environment",
                                                    dirs, "data.d")):
                pass

    return our_sites


def get_site_from_env(our_sites, env):
    """Given our_sites data structure find the parent site to the given environment.

    Args:
    our_sites (dict of dict of list):
    env (string):

    Returns:
        blah

    Example Usage:
        >>>
    """
    for k in our_sites:
        for x in our_sites[k]:
            if x == env:
                return k
