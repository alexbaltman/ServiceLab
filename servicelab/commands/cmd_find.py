"""
Find command submodule implements listing all the searches through
    1. Gerrit's server for a repo
    2. Artifactory server for artifacts
    3. GO server for pipelines
    4. The build search term.
matching the given search string regular expression.
"""
import os
import re

import json
import click
import requests

from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth

from servicelab.stack import pass_context
from servicelab.utils import jenkins_utils
from servicelab.utils import gerrit_functions
from servicelab.utils import helper_utils


@click.group('find', short_help='Helps you search \
             pipeline resources.', invoke_without_command=True,
             add_help_option=True)
@pass_context
def cli(_):
    """
    Helps you search for resources in the SDLC pipeline.
    """
    pass


@cli.command('repo', short_help='Find a repo in Gerrit.')
@click.argument('search_term')
@pass_context
def find_repo(ctx, search_term):
    """
    Searches through Gerrit's API for a repo using your search term.
    """
    username = helper_utils.get_username(ctx.path)
    gfn = gerrit_functions.GerritFns(username, "", ctx)
    repo_list = gfn.repo_list()
    for elem in repo_list:
        match_obj = re.search(search_term, elem, re.I)
        if match_obj:
            click.echo(elem)


def validate_artifact_ip_cb(ctx, param, value):
    """
    If ip is none then provide the default ip for artifactory.
    """
    if not value:
        value = ctx.obj.get_artifactory_info()
    return value


@cli.command('artifact', short_help='Find an artifact in artifactory')
@click.argument('search_term')
@click.option('-u',
              '--user',
              help='Provide artifactory username',
              required=True)
@click.option('-p',
              '--password',
              help='Provide artifactory password',
              required=True)
@click.option('-ip',
              '--ip_address',
              help='Provide the artifactory url ip address and port '
                   'no in format http://<ip:portno>.',
              default=None,
              callback=validate_artifact_ip_cb)
@pass_context
def find_artifact(ctx, search_term, ip_address, user, password):
    """
    Searches through Artifactory's API for artifacts using your search term.
    """
    if ip_address is None:
        ip_address = ctx.get_artifactory_info()
    click.echo('Searching for %s artifact in Artifactory' % search_term)
    find_url = ip_address + "/api/search/artifact?name=" + search_term
    requests.packages.urllib3.disable_warnings()
    res = requests.get(find_url, auth=HTTPBasicAuth(user, password))
    for val in json.loads(res.content)["results"]:
        click.echo(val["uri"])


def validate_pipe_ip_cb(ctx, param, value):
    """
    If ip is none then provide the default ip for gocd.
    """
    if not value:
        value = ctx.obj.get_gocd_info()
    return value


@cli.command('pipe', short_help='Find a Go deploy pipeline')
@click.argument('search_term')
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
              default=None,
              help='Provide the go server ip address and port number '
                   'in format <ip_address:portnumber>.',
              callback=validate_pipe_ip_cb)
@pass_context
def find_pipe(ctx, search_term, localrepo, user, password, ip_address):
    """
    Searches through GO's API for pipelines using your search term.
    """
    def _get_pipeline():
        """
        internal function returns a list of the pipeline
        strings from the go server
        """
        server_url = "http://{0}/go/api/pipelines.xml".format(ip_address)
        res = requests.get(server_url, auth=HTTPBasicAuth(user, password))
        soup = BeautifulSoup(res.content)
        pipelines = soup.findAll('pipeline')
        return pipelines

    def _get_match(pipeline):
        """
        find the match in the pipeline for services and other projects
        """
        search_string = pipeline['href']
        split_string = search_string.split('/')
        search_string = search_term
        match_obj = re.search(search_string,
                              split_string[len(split_string) - 2],
                              re.M | re.I)
        if match_obj:
            if localrepo:
                for sdir in servicesdirs:
                    if sdir.startswith("service-"):
                        service = sdir.split("service-", 1)[1]
                        if service == match_obj.group():
                            return split_string[len(split_string) - 2]
            else:
                return split_string[len(split_string) - 2]
        return None

    servicesdirs = []
    if os.path.isdir(os.path.join(ctx.path, "services")):
        servicesdirs = os.listdir(os.path.join(ctx.path, "services"))

    pipelines = _get_pipeline()

    for pipeline in pipelines:
        match_str = _get_match(pipeline)
        if match_str:
            click.echo(match_str)


def validate_build_ip_cb(ctx, param, value):
    """
    If ip is none then provide the default ip for jenkins.
    """
    if not value:
        value = ctx.obj.get_jenkins_info()
    return value


@cli.command('build', short_help='Find a build')
@click.argument('search_term')
@click.option('-u',
              '--user',
              help='Provide jenkins username',
              required=True)
@click.option('-p',
              '--password',
              help='Provide jenkins server password',
              required=True)
@click.option('-ip',
              '--ip_address',
              help='Provide the jenkinsserv url ip address and port'
                   'no in format <ip:portno>.',
              default=None,
              callback=validate_build_ip_cb)
@pass_context
def find_build(_, search_term, user, password, ip_address):
    """
    Searches through the build search term.
    """
    server = jenkins_utils.get_server_instance(ip_address, user, password)
    for key in server.keys():
        match_obj = re.search(search_term, key, re.M | re.I)
        if match_obj:
            click.echo(key)
