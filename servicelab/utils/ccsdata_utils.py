import logging
import sys
import os


# create logger
# TODO: For now warning and error print. Got to figure out how
#       to import the one in stack.py properly.
service_utils_logger = logging.getLogger('click_application')
logging.basicConfig()


def get_env_for_site_path(path, site, env):
    """ creates the env directory path for given path, site and environemt."""
    return os.path.join(path,
                        "services", "ccs-data",
                        "sites", site,
                        "environments", env)


def list_envs_or_sites(path):
    """List either a site or an environment in ccs-data."""

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
