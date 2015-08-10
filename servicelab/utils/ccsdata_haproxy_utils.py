import click
import re
import yaml
from random import randint
from fabric.api import run
from servicelab.stack import pass_context
from servicelab.utils import ccsdata_utils
from servicelab.utils import yaml_utils


def _search_env(path, env):
    lst = []
    sites = ccsdata_utils.list_envs_or_sites(path)
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
    with open(yaml_file, "w") as yaml_file:
        # note we can't dump arbitary yaml object. need to install a new dumper
        yaml_file.write(yaml.safe_dump(data, default_flow_style=False))


def console_print(data):
    """ This is a pretty print for the dictionary.

    Arguments:
        data (dict): The data dictionary.
    """
    for key, value in data.iteritems():
        click.echo(key + " : " + str(value))


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
        interactive: True or False. If true user can input data through console.

    Returns:
        Returns a completed haproxy entry

    """

    def _get_server_ip_name(complete_dict, entry, interactive):
        data = {}
        if not interactive:
            data["server_ips"] = entry
            return data

        # as interactive is enabled so prompt and get the results
        server_ip_name = "*%s_servr_ips" % (entry)
        server_ip_name = click.prompt("server_ips", default=server_ip_name)
        while server_ip_name[0:1] == '?':
            ip_lst = {}
            for ip_name in search(complete_dict, server_ip_name[1:]):
                ip_lst[ip_name] = complete_dict[ip_name]
            click.echo("all available ips are :")
            console_print(ip_lst)
            server_ip_name = "*%s_serevr_ips" % (entry)
            server_ip_name = click.prompt("server_ips", default=server_ip_name)
        data["server_ips"] = "*" + server_ip_name
        return data

    def _get_server_hostnames(complete_dict, entry, interactive):
        data = {}
        if not interactive:
            data["server_ips"] = entry
            return data

        # as interactive is enabled so prompt and get the results
        server_hostnames = "%s_hostnames" % (entry)
        server_hostnames = click.prompt("server_hostnames",
                                        default=server_hostnames)
        while server_hostnames[0:1] == "?":
            hostname_lst = {}
            for hostname in search(complete_dict, "hostnames"):
                hostname_lst[hostname] = complete_dict[hostname]
            print "all available host names are :"
            console_print(hostname_lst)
            server_hostnames = "*%s_hostnames" % (entry)
            server_hostnames = click.prompt("server_names",
                                            default=server_hostnames)
        data["server_hostnames"] = server_hostnames
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
                                      entry or server_ips,
                                      interactive))
    data = _merge(data,
                  _get_server_hostnames(complete_dict,
                                        entry or server_hostnames,
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
