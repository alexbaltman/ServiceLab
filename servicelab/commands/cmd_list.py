"""
List command submodule implements listing all the
    1. Sites and services of ccs-data
    2. Environments using the git submodule ccs-data.
    3. Hosts using the git submodule ccs-data.
    4. Repos using Gerrit's API.
    5. Piplines using GO's API.
    and also
    6. Searches through Jenkins API for pipelines using the given search term.
"""
import os
import re
import sys
import json
import yaml

import click
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth
import requests

from servicelab.stack import pass_context
from servicelab.utils import ccsdata_utils
from servicelab.utils import jenkins_utils
from servicelab.utils import artifact_utils
from servicelab.utils import gocd_utils
from servicelab.utils import gerrit_functions
from servicelab.utils import yaml_utils
from servicelab.utils import pulp_utils
from servicelab.utils import logger_utils
from servicelab import settings

slab_logger = logger_utils.setup_logger(settings.verbosity, 'stack.list')


@click.group('list', short_help='You can list objects in pipeline resources.',
             add_help_option=True)
@pass_context
def cli(_):
    """
    Listing sites and services of ccs-data
    """
    pass


@cli.command('sites', short_help="List all sites in ccs-data.")
@pass_context
def list_sites(ctx):
    '''
    Here we list all the sites using the git submodule ccs-data.
    '''
    slab_logger.info('Listing all sites within ccs-data')
    try:
        val_lst = []
        ret_code, sites = ccsdata_utils.list_envs_or_sites(ctx.path)
        if ret_code > 0:
            return 1
        for keys in sites:
            val_lst.append(keys)
        val_lst.sort()
        for site in val_lst:
            slab_logger.log(25, site)
    except Exception as ex:
        slab_logger.error("unable to get site list. unable to read ccs-data")
        slab_logger.error(ex)


@cli.command('envs', short_help="List all environments in ccs-data.")
@pass_context
def list_envs(ctx):
    '''
    Here we list all the environments using the git submodule ccs-data.
    '''
    slab_logger.info('Listing all environmentss (tenant clouds) within ccs-data')
    try:
        val_lst = []
        ret_code, data = ccsdata_utils.list_envs_or_sites(ctx.path)
        if ret_code > 0:
            return 1
        for _, values in data.iteritems():
            for val in values:
                val_lst.append(val)
        val_lst.sort()
        for env in val_lst:
            slab_logger.log(25, env)
    except Exception as ex:
        slab_logger.error(
            "unable to get environment list. unable to read ccs-data")
        slab_logger.error(ex)


@cli.command('hosts', short_help="List all hosts in ccs-data.")
@pass_context
def list_hosts(ctx):
    '''
    Here we list all the hosts using the git submodule ccs-data.
    '''
    slab_logger.info('Listing all hosts within ccs-data')
    try:
        ret_code, data = ccsdata_utils.list_envs_or_sites(ctx.path)
        if ret_code > 0:
            return 1
        for _, values in data.iteritems():
            for _, l2_values in values.iteritems():
                slab_logger.log(25, l2_values)
    except Exception as ex:
        slab_logger.error(
            "unable to get environment list. unable to read ccs-data")
        slab_logger.error(ex)


@cli.command('reviews', short_help='List your outstanding reviews in Gerrit.')
@click.option('inout',
              '--inc/--out',
              help='List the incoming or outgoing reviews.',
              default=True)
@click.option('-u',
              '--username',
              help='Provide gerrit username',
              default="")
@pass_context
def list_reviews(ctx, inout, username):
    """
    Lists reviews using Gerrit's API.
    """
    slab_logger.info('Listing outstanding reviews in Gerrit')
    if not username:
        username = ctx.get_username()
    gfn = gerrit_functions.GerritFns(username, "", ctx)
    if inout:
        gfn.print_gerrit(pformat="summary", number=None, owner=username,
                         reviewer="", status="open")
    else:
        gfn.print_gerrit(pformat="summary", number=None, owner="",
                         reviewer=username, status="open")


@cli.command('repos', short_help='List all repositories in Gerrit.')
@click.option('-u',
              '--username',
              help='Provide gerrit username',
              default="")
@pass_context
def list_repos(ctx, username):
    """
    Lists repos using Gerrit's API.
    """
    slab_logger.info('Listing repos in Gerrit')
    if not username:
        username = ctx.get_username()
    gfn = gerrit_functions.GerritFns(username, "", ctx)
    gfn.print_list()


@cli.command('builds', short_help='List all build jobs in Jenkins.')
@click.option(
    '-u',
    '--username',
    help='Provide jenkins username')
@click.option(
    '-p',
    '--password',
    help='Provide jenkins server password')
@click.option(
    '-ip',
    '--ip_address',
    help='Provide the jenkinsserv url ip address and port'
         'no in format <ip:portno>.',
    default=None,
    callback=jenkins_utils.validate_build_ip_cb)
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def list_build(ctx, ip_address, username, password, interactive):
    """
    Searches through Jenkins API for pipelines using your search term.
    """
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    slab_logger.info('Listing builds in Jenkins.')
    returncode, server = jenkins_utils.get_server_instance(ip_address,
                                                           username,
                                                           password)
    if not returncode == 0:
        slab_logger.error('Unable to connect to Jenkins server')
        sys.exit(1)
    for key in server.keys():
        slab_logger.log(25, key)


@cli.command('artifacts', short_help='List all artifacts in Artifactory.')
@click.option(
    '-u',
    '--username',
    help='Provide artifactory username')
@click.option(
    '-p',
    '--password',
    help='Provide artifactory password')
@click.option(
    '-ip',
    '--ip_address',
    help='Provide the artifactory url ip address and port '
         'no in format http://<ip:portno>.',
    default=None,
    callback=artifact_utils.validate_artifact_ip_cb)
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def list_artifact(ctx, ip_address, username, password, interactive):
    """
    Lists artifacts using Artifactory's API.
    """
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    slab_logger.info('Listing artifacts in Artifactory.')
    list_url = ip_address + "/api/search/creation?from=968987355"
    requests.packages.urllib3.disable_warnings()
    res = requests.get(list_url, auth=HTTPBasicAuth(username, password))
    for val in json.loads(res.content)["results"]:
        logger.log(25, val["uri"])


@cli.command('pipes', short_help='List all pipelines in GO.')
@click.option('-l',
              '--localrepo',
              help='If provided stack will filter pipelines by services '
                   'listed in local .stack directory.',
              is_flag=True,
              required=False)
@click.option('-u',
              '--username',
              help='Provide go server username')
@click.option('-p',
              '--password',
              help='Provide go server password')
@click.option('-ip',
              '--ip_address',
              help='Provide the go server url ip address and port'
                   'no in format <ip:portno>.',
              default=None,
              callback=gocd_utils.validate_pipe_ip_cb)
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def list_pipe(ctx, localrepo, username, password, ip_address, interactive):
    """
    Lists piplines using GO's API.
    """
    slab_logger.info('Listing go pipelines')
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    if not password or not username:
        slab_logger.error("Username is %s and password is %s. "
                          "Please, set the correct value for both and retry." %
                          (username, password))
        sys.exit(1)

    server_url = "http://{0}/go/api/pipelines.xml".format(ip_address)
    servicesdirs = []
    if os.path.isdir(os.path.join(ctx.path, "services")):
        servicesdirs = os.listdir(os.path.join(ctx.path, "services"))

    # Find latest run info
    res = requests.get(server_url, auth=HTTPBasicAuth(username, password))
    soup = BeautifulSoup(res.content, "html.parser")
    pipelines = soup.findAll('pipeline')
    display_pipelines(pipelines, localrepo, servicesdirs)


def display_pipelines(pipelines, localrepo, servicesdirs):
    """
    Displays pipelines
    """
    server_string_prefix = "http://(.*?)/go/api/pipelines/"
    server_string_suffix = "/stages.xml"
    for pipeline in pipelines:
        exp = re.compile(server_string_prefix + '(.*?)' + server_string_suffix)
        match = exp.search(pipeline['href'])
        if match:
            pipeline_name = match.group(0)
            if localrepo:
                for sdir in servicesdirs:
                    if sdir.startswith("service-"):
                        service = sdir.split("service-", 1)[1]
                        if service == pipeline_name:
                            slab_logger.log(25, pipeline_name)
            else:
                tokens = pipeline_name.split('/')
                slab_logger.log(25, tokens[len(tokens) - 2])


@cli.command('ospvms', short_help='List all OpenStack Platform VMs')
@pass_context
def ospvms_list(ctx):
    """
    Lists Openstack Platform VMs
    """
    slab_logger.info('Listing Opesnstack platform VMs')
    provision_path = os.path.join(ctx.path, 'provision')
    osp_vms = yaml_utils.getfull_OS_vms(provision_path, '001')
    osp_vms[1].sort()
    for host_data in osp_vms[1]:
        for host in host_data:
            slab_logger.log(25, host)


@click.option('--site', '-s', default=None,
              help='Name of a ccs-data site to search for flavors')
@cli.command('flavors', short_help='List all of the flavors within a specified site')
@pass_context
def flavors_list(ctx, site):
    """
    Lists all of the flavors within all sites or a specified site
    """
    if not os.path.exists(os.path.join(ctx.path, 'services', 'ccs-data')):
        slab_logger.error('The ccs-data repo does not appear to be installed.  ' +
                          'Try "stack workon ccs-data"')
        return 1
    if site:
        slab_logger.info('Listing flavors for site %s' % site)
        site_path = os.path.join(ctx.path, 'services', 'ccs-data', 'sites', site)
        if not os.path.exists(site_path):
            slab_logger.error('Site %s does not exist' % site)
            return 1
        site_env_path = os.path.join(site_path, 'environments')
        flavor_list = ccsdata_utils.get_flavors_from_site(site_env_path)
    else:
        slab_logger.info('Listing flavors for all sites')
        try:
            source_file = os.path.join(ctx.path, 'cache', 'all_sites_flavors.yaml')
            with open(source_file, 'r') as stream:
                source_data = yaml.load(stream)
        except IOError:
            slab_logger.error('Unable to open %s.  Run the "make_flavors_yaml.py" to ' +
                              'create this file' % source_file)
            return 1
        flavor_list = []
        for site in source_data:
            for flavor in source_data[site]:
                if flavor not in flavor_list:
                    flavor_list.append(flavor)
        flavor_list.sort()

    for flavor in flavor_list:
        slab_logger.log(25, flavor)


@cli.command('rpms', short_help='List rpms in pulp repository')
@click.option(
    '-u',
    '--username',
    help='Provide pulp server username')
@click.option(
    '-p',
    '--password',
    help='Provide pulp server password')
@click.option(
    '-ip',
    '--ip_address',
    help='Provide the pulp server url ip address and port '
         'no in format http://<ip:portno>.',
    default=None,
    callback=pulp_utils.validate_pulp_ip_cb)
@click.option(
    '-s',
    '--pulp-repo',
    help='Provide the pulp repo id ',
    required=True,
    default=None)
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def list_rpms(ctx, ip_address, username, password, pulp_repo, interactive):
    """
    Lists rpms using Pulp Server API.
    """
    slab_logger.info('Listing rpms from pulp server')
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    if not password or not username:
        slab_logger.error("Username is %s and password is %s. "
                          "Please, set the correct value for both and retry." %
                          (username, password))
        sys.exit(1)
    url = "/pulp/api/v2/repositories/%s/search/units/" % (pulp_repo)
    payload = '{ "criteria": { "fields": { "unit": [ "name",'\
              '"version", "filename", "relative_url" ] },'\
              '"type_ids": [ "rpm" ] } }'
    val = pulp_utils.post(url, ip_address, ctx, username, password, payload)
    rpms = json.loads(val)

    if rpms is not None and len(rpms) > 0:
        for rpm in rpms:
            slab_logger.log(25, "Id      : %s" % rpm["id"])
            slab_logger.log(25, "Filename: %s" % rpm["metadata"]["filename"])
            slab_logger.log(25, "Name    : %s" % rpm["metadata"]["name"])
            slab_logger.log(25, "Version : %s" % rpm["metadata"]["version"] + "\n")
    else:
        slab_logger.error("No rpms found in this repository.")


@cli.command('pulp-repos', short_help='List all the pulp repositories')
@click.option(
    '-u',
    '--username',
    help='Provide pulp server username')
@click.option(
    '-p',
    '--password',
    help='Provide pulp server password')
@click.option(
    '-ip',
    '--ip_address',
    help='Provide the pulp server url ip address and port '
         'no in format http://<ip:portno>.',
    default=None,
    callback=pulp_utils.validate_pulp_ip_cb)
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def list_pulp_repos(ctx, ip_address, username, password, interactive):
    """
    Lists rpms using Pulp Server API.
    """
    slab_logger.info('Listing repos from pulp server')
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    if not password or not username:
        slab_logger.error("Username is %s and password is %s. "
                          "Please, set the correct value for both and retry." %
                          (username, password))
        sys.exit(1)
    url = "/pulp/api/v2/repositories/"
    val = pulp_utils.get(url, ip_address, ctx, username, password)
    repos = json.loads(val)

    if repos is not None and len(repos) > 0:
        for repo in repos:
            slab_logger.log(25, "Repo Id      : %s" % repo["id"])
            slab_logger.log(25, "Repo Name    : %s" % repo["display_name"])
            slab_logger.log(25, "Repo path    : %s" % repo["_href"] + "\n")
    else:
        slab_logger.log(25, "No repositories found on this pulp server.")
