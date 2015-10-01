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

import click
import json
import requests

from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth

from servicelab.stack import pass_context

from servicelab.utils import context_utils
from servicelab.utils import helper_utils
from servicelab.utils import ccsdata_utils
from servicelab.utils import jenkins_utils
from servicelab.utils import gerrit_functions


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
    ctx.logger.debug("Gathered sites from ccs-data submodule.")

    for keys in ccsdata_utils.list_envs_or_sites(ctx.path):
        click.echo(keys)


@cli.command('envs', short_help="List environments")
@pass_context
def list_envs(ctx):
    '''
    Here we list all the environments using the git submodule ccs-data.
    '''
    ctx.logger.debug("Gathered environments from ccs-data submodule.")
    data = ccsdata_utils.list_envs_or_sites(ctx.path)
    for _, values in data.iteritems():
        for val in values:
            click.echo(val)


@cli.command('hosts', short_help="List hosts")
@pass_context
def list_hosts(ctx):
    '''
    Here we list all the hosts using the git submodule ccs-data.
    '''
    ctx.logger.debug("Gathered hosts from ccs-data submodule.")
    data = ccsdata_utils.list_envs_or_sites(ctx.path)
    for _, values in data.iteritems():
        for _, l2_values in values.iteritems():
            click.echo(l2_values)


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
    username = helper_utils.get_username(ctx.path)
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
    username = helper_utils.get_username(ctx.path)
    gfn = gerrit_functions.GerritFns(username, "", ctx)
    gfn.print_list()


@cli.command('builds', short_help='List a Jenkins\' builds.')
@click.option(
    '-u',
    '--user',
    help='Provide jenkins username',
    required=True)
@click.option(
    '-p',
    '--password',
    help='Provide jenkins server password',
    required=True)
@click.option(
    '-ip',
    '--ip_address',
    default=context_utils.get_jenkins_url(),
    help='Provide the jenkinsserv url ip address and port \
        no in format <ip:portno>.',
    required=True)
@pass_context
def list_build(_, ip_address, user, password):
    """
    Searches through Jenkins API for pipelines using your search term.
    """
    click.echo('Listing builds in Jenkins.')
    server = jenkins_utils.get_server_instance(ip_address,
                                               user,
                                               password)
    for key in server.keys():
        click.echo(key)


@cli.command('artifacts', short_help='List artifacts in artifactory')
@click.option(
    '-u',
    '--user',
    help='Provide artifactory username',
    required=True)
@click.option(
    '-p',
    '--password',
    help='Provide artifactory password',
    required=True)
@click.option(
    '-ip',
    '--ip_address',
    default=context_utils.get_artifactory_url(),
    help='Provide the artifactory url ip address and port \
        no in format http://<ip:portno>.',
    required=True)
@pass_context
def list_artifact(_, ip_address, user, password):
    """
    Lists artifacts using Artifactory's API.
    """
    click.echo('Listing artifacts in Artifactory.')
    list_url = ip_address + "/api/search/creation?from=968987355"
    requests.packages.urllib3.disable_warnings()
    res = requests.get(list_url, auth=HTTPBasicAuth(user, password))
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
              '--user',
              help='Provide go server username',
              required=True)
@click.option('-p',
              '--password',
              help='Provide go server password',
              required=True)
@click.option('-ip',
              '--ip_address',
              default=context_utils.get_gocd_ip(),
              help="Provide the go server ip address and port no in "
                   "format <ip:portno>.",
              required=True)
@pass_context
def list_pipe(ctx, localrepo, user, password, ip_address):
    """
    Lists piplines using GO's API.
    """
    server_url = "http://{0}/go/api/pipelines.xml".format(ip_address)
    server_string_prefix = "http://(.*?)/go/api/pipelines/"
    server_string_suffix = "/stages.xml"
    servicesdirs = []
    if os.path.isdir(os.path.join(ctx.path, "services")):
        servicesdirs = os.listdir(os.path.join(ctx.path, "services"))

    # Find latest run info
    res = requests.get(server_url, auth=HTTPBasicAuth(user, password))
    soup = BeautifulSoup(res.content)
    pipelines = soup.findAll('pipeline')
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
