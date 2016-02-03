import logging
import sys
import os
import ordered_yaml
import yaml

from servicelab.utils import tc_vm_yaml_create
from servicelab.stack import Context

ctx = Context()


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
    ctx.logger.debug('Building path for %s environment.yaml file' % env)
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
    ctx.logger.debug('Extracting data from %s environment.yaml file' % env)
    fnm = os.path.join(path,
                       "services", "ccs-data",
                       "sites", site,
                       "environments", env,
                       "data.d",
                       "environment.yaml")
    with open(fnm) as yaml_file:
        return ordered_yaml.load(yaml_file)
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
    ctx.logger.debug('Building path to %s directory' % env)
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
    ctx.logger.log(15, 'Gathering site names from ccs-data')
    # TODO: JIC we want to list services in the future.
    services = []
    our_sites = {}
    os.listdir(path)
    # TODO: Add error handling and possibly return code
    ctx.logger.debug('Checking for ccs-data repo')
    ccsdata_reporoot = os.path.join(path, "services", "ccs-data")
    if not os.path.isdir(ccsdata_reporoot):
        ctx.logger.error('The ccs-data repo could not be found.  '
                         'Please try "stack workon ccs-data"')
        return(1, our_sites)
    ccsdata_sitedir = os.path.join(ccsdata_reporoot, "sites")
    our_sites = {x: None for x in os.listdir(ccsdata_sitedir)}
    ctx.logger.debug('Ensuring found sites are valid sites and not environments')
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
            for _, _, files in os.walk(os.path.join(ccsdata_sitedir,
                                                    key,
                                                    "environments",
                                                    dirs,
                                                    "hosts.d")):
                our_sites[key][dirs] = files

            # TODO: get this working - list operator already used
            for _, _, files in os.walk(os.path.join(ccsdata_sitedir, key, "environment",
                                                    dirs, "data.d")):
                pass

    return(0, our_sites)


def get_site_from_env(env):
    """Given our_sites data structure find the parent site to the given environment.

    Args:
    env (string):

    Returns:
        blah

    Example Usage:
        >>>
    """
    ctx.logger.debug('Determining site from environment %s' % env)
    ret_code, our_sites = (list_envs_or_sites(ctx.path))
    if ret_code > 0:
        return(1, 'invalid')
    for k in our_sites:
        for x in our_sites[k]:
            if x == env:
                return(0, k)
    ctx.logger.error('%s is an invalid env. Please select one from stack list envs'
                     % env_name)
    return(1, 'invalid')


def get_flavors_from_site(site_env_path):
    """Extract all flavors from the specified site.

    Args:
        site_env_path {str}: Path to the ccs-data site environment
            services/ccs-data/sites/service/environments

    Returns:
        flavors {list}: Sorted list of flavors found within the site

    Example Usage:
    >>> pprint.pprint(ccsdata_utils.get_flavors_from_site(
        '/home/paketner/repo/servicelab/servicelab/.stack/services/ccs-data' +
        '/sites/rtp10-svc-1/environments'))
    ['2cpu.4ram.20-96sas',
     '2cpu.4ram.50-96sas',
     '4cpu.16ram.50-0sas',
     '4cpu.8ram.20-512sas',
     etc....]
    """
    ctx.logger.debug('Extracting flavors for site %s' % site)
    flavors = []
    site_data = get_host_data_from_site(site_env_path)
    for env in site_data:
        for host in site_data[env]:
            if 'deploy_args' in site_data[env][host]:
                if 'flavor' in site_data[env][host]['deploy_args']:
                    flavor = site_data[env][host]['deploy_args']['flavor']
                    if flavor not in flavors:
                        flavors.append(flavor)
    flavors.sort()
    return(flavors)


def get_host_data_from_site(site_env_path):
    """Extract all host.yaml data from all environments within the supplied site

    Args:
        site_env_path {str}: Path to the ccs-data site environment
            services/ccs-data/sites/service/environments

    Returns:
        site_data {dict of dicts (4-5 layers)}: Extracted data from all of the host.yaml
            files within the environments.  See example below.

    Example Usage:
        >>> pprint.pprint(ccsdata_utils.get_host_data_from_site(
            '/home/paketner/repo/servicelab/servicelab/.stack/services/ccs-data' +
            '/sites/ccs-dev-1/environments'))
        {'dev': {'aio-001.yaml': {'deploy_args': {'availability_zone': 'csm-a',
                                                  'flavor': '2cpu.4ram.20sas',
                                                  'image': 'slab-RHEL7.1v7',
                                                  'network_name': 'SLAB_aaltman_network',
                                                  'security_groups': 'default',
                                                  'subnet_name': 'SLAB_aaltman_network_subn',
                                                  'tenant': 'dev'},
                                  'groups': ['redhouse-svc', 'virtual'],
                                  'hostname': 'aio-001',
                                  'interfaces': {'eth0': {'gateway': '192.168.100.2',
                                                          'ip_address': '192.168.100.21',
                                                          'netmask': '255.255.255.0'}},
                                  'nameservers': '192.168.100.2',
                                  'role': 'aio',
                                  'server': 'sdlc-mirror.cisco.com',
                                  'type': 'virtual'},
    """
    ctx.logger.debug('Extracting all host yaml file data from %s' % site_env_path)
    site_data = {}
    for env in os.listdir(site_env_path):
        site_data[env] = {}
        hosts_path = os.path.join(site_env_path, env, 'hosts.d')
        if os.path.exists(hosts_path):
            hosts = os.listdir(hosts_path)
            for host in hosts:
                host_file = os.path.join(hosts_path, host)
                site_data[env][host] = tc_vm_yaml_create.open_yaml(host_file)
    return(site_data)
