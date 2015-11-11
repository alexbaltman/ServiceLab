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

import click
import json
import requests

from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth

from servicelab.stack import pass_context

from servicelab.utils import ccsdata_utils
from servicelab.utils import jenkins_utils
from servicelab.utils import artifact_utils
from servicelab.utils import gocd_utils
from servicelab.utils import gerrit_functions
from servicelab.utils import yaml_utils


@click.group('list', short_help='You can list available pipeline objects',
             add_help_option=True)
@pass_context
def cli(_):
    """
    Listing sites and services of ccs-data
    """
    pass


@cli.command('sites', short_help="List sites")
@pass_context
def list_sites(ctx):
    '''
    Here we list all the sites using the git submodule ccs-data.
    '''
    try:
        val_lst = []
        for keys in ccsdata_utils.list_envs_or_sites(ctx.path):
            val_lst.append(keys)
        val_lst.sort()
        click.echo(val_lst)
    except Exception as ex:
        ctx.logger.info("unable to get site list. unable to read ccs-data")
        ctx.logger.info(ex)


@cli.command('envs', short_help="List environments")
@pass_context
def list_envs(ctx):
    '''
    Here we list all the environments using the git submodule ccs-data.
    '''
    try:
        val_lst = []
        data = ccsdata_utils.list_envs_or_sites(ctx.path)
        for _, values in data.iteritems():
            for val in values:
                val_lst.append(val)
        val_lst.sort()
        click.echo(val_lst)
    except Exception as ex:
        ctx.logger.info("unable to get environment list. unable to read ccs-data")
        ctx.logger.info(ex)


@cli.command('hosts', short_help="List hosts")
@pass_context
def list_hosts(ctx):
    '''
    Here we list all the hosts using the git submodule ccs-data.
    '''
    try:
        data = ccsdata_utils.list_envs_or_sites(ctx.path)
        for _, values in data.iteritems():
            for _, l2_values in values.iteritems():
                click.echo(l2_values)
    except Exception as ex:
        ctx.logger.info("unable to get environment list. unable to read ccs-data")
        ctx.logger.info(ex)


@cli.command('reviews', short_help='List reviews in Gerrit.')
@click.option('inout',
              '--inc/--out',
              help='List the incoming or outgoing reviews.',
              default=True)
@pass_context
def list_reviews(ctx, inout):
    """
    Lists reviews using Gerrit's API.
    """
    username = ctx.get_username()
    gfn = gerrit_functions.GerritFns(username, "", ctx)
    if inout:
        gfn.print_gerrit(pformat="summary", number=None, owner=username,
                         reviewer="", status="open")
    else:
        gfn.print_gerrit(pformat="summary", number=None, owner="",
                         reviewer=username, status="open")


@cli.command('repos', short_help='List repos in Gerrit.')
@pass_context
def list_repos(ctx):
    """
    Lists repos using Gerrit's API.
    """
    username = ctx.get_username()
    gfn = gerrit_functions.GerritFns(username, "", ctx)
    gfn.print_list()


@cli.command('builds', short_help='List a Jenkins\' builds.')
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
    click.echo('Listing builds in Jenkins.')
    server = jenkins_utils.get_server_instance(ip_address,
                                               username,
                                               password)
    for key in server.keys():
        click.echo(key)


@cli.command('artifacts', short_help='List artifacts in artifactory')
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
    click.echo('Listing artifacts in Artifactory.')
    list_url = ip_address + "/api/search/creation?from=968987355"
    requests.packages.urllib3.disable_warnings()
    res = requests.get(list_url, auth=HTTPBasicAuth(username, password))
    click.echo(res.content)
    for val in json.loads(res.content)["results"]:
        click.echo(val["uri"])


@cli.command('pipes', short_help='List Go deployment pipelines')
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
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    if not password or not username:
        click.echo("Username is %s and password is %s. "
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
                            click.echo(pipeline_name)
            else:
                click.echo(pipeline_name)


@cli.command('ospvms', short_help='List all OpenStack Platform VMs')
@pass_context
def ospvms_list(ctx):
    """
    Lists Openstack Platform VMs
    """
    provision_path = os.path.join(ctx.path, 'provision')
    osp_vms = yaml_utils.getfull_OS_vms(provision_path, '001')
    for host_data in osp_vms[1]:
        for host in host_data:
            click.echo(host)
