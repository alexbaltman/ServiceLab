import os
import re
import click
import logging
import json
from servicelab.stack import pass_context
from servicelab.utils import ccsdata_utils
from servicelab.utils import jenkins_utils
import requests
from requests.auth import HTTPBasicAuth
from BeautifulSoup import BeautifulSoup
from jenkinsapi.jenkins import Jenkins
from servicelab.utils import context_utils


@click.group('list', short_help='You can list available pipeline objects',
             add_help_option=True)
@pass_context
def cli(ctx):
    """
    Listing sites and services of ccs-data
    """
    pass


# TODO: the command sites, envs, and hosts should be able to take
#       an option to display the env item belongs to and/or site,
#       as well as print a lot prettier.
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
    d = ccsdata_utils.list_envs_or_sites(ctx.path)
    for keys, values in d.iteritems():
        for k2 in values:
            click.echo(k2)


@cli.command('hosts', short_help="List hosts")
@pass_context
def list_hosts(ctx):
    '''
    Here we list all the hosts using the git submodule ccs-data.
    '''
    ctx.logger.debug("Gathered hosts from ccs-data submodule.")
    d = ccsdata_utils.list_envs_or_sites(ctx.path)
    for keys, values in d.iteritems():
        for k2, v2 in values.iteritems():
            click.echo(v2)


@cli.command('reviews', short_help='List reviews in Gerrit.')
# RFI: Is using an option here 100% the right way to go or nest
#      the command set again (?)
@click.option('ino', '--out', help='List the outgoing reviews I have.')
@click.option('ino', '--inc', help='List the incoming reviews I have.')
@pass_context
def list_repo(ctx, ino):
    """
    Lists repos using Gerrit's API.
    """
    click.echo('Listing reviews in Gerrit.')


# RFI: should there be more intelligence here than a blankey list?
@cli.command('repos', short_help='List repos in Gerrit.')
@pass_context
def list_repos(ctx):
    """
    Lists repos using Gerrit's API.
    """
    click.echo('Listing repos in Gerrit.')


# RFI: should there be more intelligence here than a blankey list?
@cli.command('builds', short_help='List a Jenkins\' builds.')
@click.option(
    '-x',
    '--jenkinsuser',
    help='Provide jenkins username',
    required=True)
@click.option(
    '-y',
    '--jenkinspass',
    help='Provide jenkins server password',
    required=True)
@click.option(
    '-z',
    '--jenkinsservurl',
    help='Provide the jenkinsserv url ip address and port \
        no in format <ip:portno>.',
    required=True)
@pass_context
def list_build(ctx, jenkinsservurl, jenkinsuser, jenkinspass):
    """
    Searches through Jenkins API for pipelines using your search term.
    """
    click.echo('Listing builds in Jenkins.')
    server = jenkins_utils.get_server_instance(jenkinsservurl,
                                               jenkinsuser, jenkinspass)
    for j in server.keys():
        print j


# RFI: should there be more intelligence here than a blankey list?
@cli.command('artifacts', short_help='List artifacts in artifactory')
@click.option(
    '-m',
    '--artuser',
    help='Provide artifactory username',
    required=True)
@click.option(
    '-n',
    '--artpass',
    help='Provide artifactory password',
    required=True)
@click.option(
    '-o',
    '--artservurl',
    default=context_utils.getArtifactoryURL(),
    help='Provide the artifactory url ip address and port \
        no in format http://<ip:portno>.',
    required=True)
@pass_context
def list_artifact(ctx, artservurl, artuser, artpass):
    """
    Lists artifacts using Artifactory's API.
    """
    click.echo('Listing artifacts in Artifactory.')
    listURL = artservurl + "/api/search/creation?from=968987355"
    requests.packages.urllib3.disable_warnings()
    res = requests.get(listURL, auth=HTTPBasicAuth(artuser, artpass))
    print res.content
    for val in json.loads(res.content)["results"]:
        print val["uri"]


@cli.command('pipes', short_help='List Go deployment pipelines')
@click.option(
    '-l',
    '--localrepo',
    help='If provided stack will filter pipelines by services \
          listed in local .stack directory.',
    is_flag=True,
    required=False)
@click.option(
    '-g',
    '--gouser',
    help='Provide go server username',
    required=True)
@click.option(
    '-h',
    '--gopass',
    help='Provide go server password',
    required=True)
@click.option(
    '-s',
    '--goserver',
    help='Provide the go server ip address and port no in format <ip:portno>.',
    required=True)
@pass_context
def list_pipe(ctx, localrepo, gouser, gopass, goserver):
    """
    Lists piplines using GO's API.
    """
    serverURL = "http://{0}/go/api/pipelines.xml".format(goserver)
    serverStringPrefix = "http://{0}/go/api/pipelines/".format(goserver)
    serverStringSuffix = "/stages.xml"
    servicesdirs = []
    if os.path.isdir(os.path.join(ctx.path, "services")):
        servicesdirs = os.listdir(os.path.join(ctx.path, "services"))

    # Find latest run info
    res = requests.get(serverURL, auth=HTTPBasicAuth(gouser, gopass))
    soup = BeautifulSoup(res.content)
    pipelines = soup.findAll('pipeline')
    for pipeline in pipelines:
        r = re.compile(serverStringPrefix + '(.*?)' + serverStringSuffix)
        m = r.search(pipeline['href'])
        if m:
            pipelineName = m.group(1)
            if localrepo:
                for sdir in servicesdirs:
                    if sdir.startswith("service-"):
                        service = sdir.split("service-", 1)[1]
                        if service == pipelineName:
                            print pipelineName
            else:
                print pipelineName
