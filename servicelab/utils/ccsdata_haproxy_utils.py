import re
import yaml
import click

import ccsdata_utils
import yaml_utils
import logger_utils

from random import randint
from fabric.api import run
from servicelab import settings

lab_logger = logger_utils.setup_logger(settings.verbosity, 'stack.utils.ccsdata_haproxy')


def _search_env(path, env):
    slab_logger.debug('Searching for %s in ccs-data sites' % env)
    lst = []
    ret_code, sites = ccsdata_utils.list_envs_or_sites(path)
    if ret_code > 0:
        return lst
    for site, envs in sites.iteritems():
        if env in envs.keys():
            lst.append((site, env))
    return lst


def generate_env_for_site(path, env):
    """ The generate_env_for_site is a generator iterating over all the
    environment in the path. It generates a tuple containing the
    {site, env} dictionary. It it does not find anything it raises
    StopIteration exception.

    Arguments:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
        env (str): Desired environment

    Returns:
        This returns {'site':site, 'env': env_settings}  dictionary.

    """
    slab_logger.debug('Generating site and env dictionary')
    site_env_lst = _search_env(path, 'dev')

    for site, env in site_env_lst:
        env_settings = ccsdata_utils.get_env_settings_for_site(path,
                                                               site, env)
        yield {'site': site, 'env': env_settings}


def search(search_dict, pattern_str):
    """ Search is a generator iterating over the search_dictionary for the
    key having pattern string. If it does not find anything it raises
    StopIteration exception.

    Arguments:
        search_dict (dict): Dictionary
        pattern_str: The desired substring.

   Returns:
        The key containing the pattern will be return or it may generate
        a StopIteration exceptipon.

    """
    for key in search_dict.keys():
        if pattern_str in key:
            yield key


def save_ccsdata(path, site, env, data):
    """ This saves the data as a yaml file specified by the path, site and
    environment.

    Arguments:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
        site (str): Desired site
        env (str): Desired environment
        data (dict): The data dictionary to be saved as yaml file.

    Returns:
        The data dictionary saved as yaml file.
    """
    yaml_file = ccsdata_utils.get_environment_yaml_file(path, site, env)
    ccsdata_utils.ordered_yaml.dump(data, yaml_file, Dumper=yaml.SafeDumper)


def console_print(data):
    """ This is a pretty print for the dictionary.

    Arguments:
        data (dict): The data dictionary.
    """
    for key, value in data.iteritems():
        slab_logger.log(25, key + " : " + str(value))


def generate_tag_value(complete_dict, entry, ip, server_ips=None,
                       server_hostnames=None, interactive=False):
    """ This generates the various dictionary elements of the haproxy instance
    defined by entry which can be internal or external. The various
    (element, value) tuples are then merged in the complete-dict. The default
    dictionary entries under haproxy created by generate_tag_value are
    server_ip, server_hostnames, port, ssl. If interactive is true the
    following set of the dictionary entries  can be added by the user through
    console.
        --has_backup
        --backendport
        --backend_options
        --frontend_options
    Args:
        complete_dict (dict):
        entry (str) : this can be internal or extrenal.
        ip (ip) : The virtual ip address.
        server_ips: Server ips
        server_hostname: Server hostnames.
        interactive: True or False. If true user can input data through
                     console.

    Returns:
        Returns a completed haproxy entry
        Below is an example of ceilometer entry dictionary created by this api.

        {ceilometer:
            {
                port: 59083
                server_names: u'*ceilometer_hostnames'
                server_ips: u'*ceilometer_ips'
                ssl: False
                vip: u'%%{}{hiera(''my_vip_name'')}'
            }
        }
    """
    slab_logger.debug('Generating data for proxy node')

    def _get_server_ip_name(complete_dict, ipslst, interactive):
        data = {}
        if not interactive:
            data["server_ips"] = ipslst
            return data

        # as interactive is enabled so prompt and get the results
        if ipslst != []:
            slab_logger.log(25, "Supplied ip's are : " + str(ipslst))
        else:
            ipslst = []
        while True:
            server_ipname = click.prompt("server_ips", default="")
            if server_ipname[0:1] == '?':
                possible_iplst = {}
                for ip_name in search(complete_dict, "ip"):
                    possible_iplst[ip_name] = complete_dict[ip_name]
                slab_logger.log(25, "all available ips are :")
                console_print(possible_iplst)
                continue

            if server_ipname == "":
                break
            ipslst.append(server_ipname)

        if ipslst:
            data["server_ips"] = ipslst
        return data

    def _get_server_hostnames(complete_dict, hostlst, interactive):
        data = {}
        nlst = []
        if not interactive:
            for name in hostlst:
                if name in complete_dict.keys():
                    nlst.append(complete_dict[name])
                else:
                    nlst.append(name)

            data["server_hostnames"] = nlst
            return data

        # as interactive is enabled so prompt and get the results
        if hostlst != []:
            slab_logger.log(25, "Supplied hostnames are : " + str(hostlst))
        else:
            hostlst = []
        while True:
            server_hostname = click.prompt("server_hostnames", default="")
            if server_hostname[0:1] == "?":
                hostname_lst = {}
                for hostname in search(complete_dict, "hostname"):
                    hostname_lst[hostname] = complete_dict[hostname]
                slab_logger.log(25, "all available host names are :")
                console_print(hostname_lst)
                continue

            if server_hostname == "":
                break
            if server_hostname in complete_dict.keys():
                server_hostname = complete_dict[server_hostname]
            hostlst.append(server_hostname)

        if hostlst:
            data["server_hostnames"] = hostlst
        return data

    def _get_port(complete_dict, interactive):
        data = {}
        if not interactive:
            data['port'] = randint(1024, 65535)
        else:
            data['port'] = click.prompt("port",
                                        type=click.INT,
                                        default=randint(1024, 65535))
        return data

    def _get_backendport(complete_dict, interactive):
        data = {}
        if not interactive:
            return data

        data['backend_port'] = click.prompt("backend_port",
                                            type=click.INT,
                                            default=randint(1024, 65535))
        return data

    def _get_ssl(complete_dict, interactive):
        data = {}
        if not interactive:
            data['ssl'] = False
        else:
            data['ssl'] = click.prompt("ssl", type=click.BOOL, default=False)
        return data

    def _get_has_backup(complete_dict, interactive):
        data = {}
        if not interactive:
            return data
        if click.confirm('do you want to set has_backup option'):
            data['has_backup'] = click.prompt("has_backup",
                                              type=click.BOOL,
                                              default=True)
        return data

    def _get_frontend_options(complete_dict, interactive):
        data = {}
        if not interactive:
            return data

        if click.confirm('do you want to set frontend_options'):
            option = {}
            sublst = []
            if click.confirm("option: tcpka available", default=True):
                sublst.append('tcpka')
            if click.confirm("option: httpchk available", default=True):
                sublst.append('httpchk')
            if click.confirm("option: tcplog available", default=True):
                sublst.append('tcplog')
            if sublst:
                option['options'] = sublst
            option['balance'] = click.prompt("balance", default='source')
            data['frontend_options'] = option
        return data

    def _get_backend_options(complete_dict, interactive):
        data = {}
        if not interactive:
            return data

        backend_options = ""
        if click.confirm("do you want to set backend_options"):
            data['backend_options_present'] = True
            data['backend_options'] = click.prompt("backend_options")
        return data

    def _merge(x, y):
        z = x.copy()
        z.update(y)
        return z

    data = {}
    data["vip"] = "%%{}{hiera('" + ip + "')}"
    data = _merge(data,
                  _get_server_ip_name(complete_dict,
                                      server_ips or entry,
                                      interactive))
    data = _merge(data,
                  _get_server_hostnames(complete_dict,
                                        server_hostnames or entry,
                                        interactive))
    data = _merge(data,
                  _get_port(complete_dict, interactive))
    data = _merge(data,
                  _get_backendport(complete_dict, interactive))
    data = _merge(data,
                  _get_ssl(complete_dict, interactive))
    data = _merge(data,
                  _get_has_backup(complete_dict, interactive))
    data = _merge(data,
                  _get_frontend_options(complete_dict, interactive))
    data = _merge(data,
                  _get_backend_options(complete_dict, interactive))

    return data
