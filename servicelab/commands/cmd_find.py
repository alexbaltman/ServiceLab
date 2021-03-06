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
import sys

import json
import click
import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup

from servicelab.stack import pass_context
from servicelab.utils import jenkins_utils
from servicelab.utils import pulp_utils
from servicelab.utils import gerrit_functions
from servicelab.utils import logger_utils
from servicelab import settings

slab_logger = logger_utils.setup_logger(settings.verbosity, 'stack.find')


@click.group('find', short_help='Helps you search pipeline resources.',
             invoke_without_command=True,
             add_help_option=True)
@pass_context
def cli(_):
    """
    Helps you search for resources in the SDLC pipeline.
    """
    pass


@cli.command('repo', short_help='Find a repository in Gerrit by regex.')
@click.argument('search_term')
@pass_context
def find_repo(ctx, search_term):
    """
    Searches through Gerrit's API for a repo using your search term.
    """
    slab_logger.info('Searching Gerrit for repos matching %s' % search_term)
    username = ctx.get_username()
    gfn = gerrit_functions.GerritFns(username, "", ctx)
    repo_list = gfn.repo_list()
    for elem in repo_list:
        match_obj = re.search(search_term, elem, re.I)
        if match_obj:
            slab_logger.log(25, elem)


def validate_artifact_ip_cb(ctx, param, value):
    """
    If ip is none then provide the default ip for artifactory.
    """
    if not value:
        value = ctx.obj.get_artifactory_info()['url']
    return value


@cli.command('artifact', short_help='Find an artifact in Artifactory by regex.')
@click.argument('search_term')
@click.option('-u',
              '--username',
              help='Provide artifactory username')
@click.option('-p',
              '--password',
              help='Provide artifactory password')
@click.option('-ip',
              '--ip_address',
              help='Provide the artifactory url ip address and port '
                   'no in format http://<ip:portno>.',
              default=None,
              callback=validate_artifact_ip_cb)
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def find_artifact(ctx, search_term, ip_address,
                  username, password, interactive):
    """
    Searches through Artifactory's API for artifacts using your search term.
    """
    slab_logger.info('Determining artifactory details')
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    if not password or not username:
        slab_logger.error("Username is %s and password is %s. "
                          "Please, set the correct value for both and retry." %
                          (username, password))
        sys.exit(1)
    if ip_address is None:
        ip_address = ctx.get_artifactory_info()
    slab_logger.info('Searching for %s artifact in Artifactory' % search_term)
    find_url = ip_address + "/api/search/artifact?name=" + search_term
    requests.packages.urllib3.disable_warnings()
    res = requests.get(find_url, auth=HTTPBasicAuth(username, password))
    if json.loads(res.content).get('results'):
        for val in json.loads(res.content)["results"]:
            slab_logger.log(25, val["uri"])
    else:
        slab_logger.error("No results found.")
        sys.exit(1)


def validate_pipe_ip_cb(ctx, param, value):
    """
    If ip is none then provide the default ip for gocd.
    """
    if not value:
        value = ctx.obj.get_gocd_info()['ip']
    return value


@cli.command('pipe', short_help='Find a specific Go pipeline by regex.')
@click.argument('search_term')
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
              default=None,
              help='Provide the go server ip address and port number '
                   'in format <ip_address:portnumber>.',
              callback=validate_pipe_ip_cb)
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def find_pipe(ctx, search_term, localrepo, username,
              password, ip_address, interactive):
    """
    Searches through GO's API for pipelines using your search term.
    """
    def _get_pipeline():
        """
        internal function returns a list of the pipeline
        strings from the go server
        """
        slab_logger.info('Finding pipelines from the go server')
        server_url = "http://{0}/go/api/pipelines.xml".format(ip_address)
        res = requests.get(server_url, auth=HTTPBasicAuth(username, password))
        soup = BeautifulSoup(res.content, "html.parser")
        pipelines = soup.findAll('pipeline')
        return pipelines

    def _get_match(pipeline):
        """
        find the match in the pipeline for services and other projects
        """
        slab_logger.info('Searching for matching pipeline')
        try:
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
                                return split_string[len(split_string) - 2], 0
                else:
                    return split_string[len(split_string) - 2], 0
        except re.error:
            return None, 1
        return None, 0

    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    if not password or not username:
        slab_logger.error("Username is %s and password is %s. "
                          "Please, set the correct value for both and retry." %
                          (username, password))
        sys.exit(1)
    servicesdirs = []
    if os.path.isdir(os.path.join(ctx.path, "services")):
        servicesdirs = os.listdir(os.path.join(ctx.path, "services"))

    pipelines = _get_pipeline()

    for pipeline in pipelines:
        match_str, return_code = _get_match(pipeline)
        if return_code == 1:
            slab_logger.error("Internal error occurred. The regular "
                              "expression supplied seems to be invalid. "
                              "Please, retry with a correct regular expression.")
            sys.exit(1)
        else:
            if match_str:
                slab_logger.log(25, match_str)


def validate_build_ip_cb(ctx, param, value):
    """
    If ip is none then provide the default ip for jenkins.
    """
    if not value:
        value = ctx.obj.get_jenkins_info()['url']
    return value


@cli.command('build', short_help='Find a build in Jenkins by regex.')
@click.argument('search_term')
@click.option('-u',
              '--username',
              help='Provide jenkins username')
@click.option('-p',
              '--password',
              help='Provide jenkins server password')
@click.option('-ip',
              '--ip_address',
              help='Provide the jenkinsserv url ip address and port'
                   'no in format <ip:portno>.',
              default=None,
              callback=validate_build_ip_cb)
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def find_build(ctx, search_term, username, password, ip_address, interactive):
    """
    Searches through the build search term.
    """
    slab_logger.info('Searching Jenkins for the specified build')
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    if not password or not username:
        slab_logger.error("Username is %s and password is %s. "
                          "Please, set the correct value for both and retry." %
                          (username, password))
        sys.exit(1)

    returncode, server = jenkins_utils.get_server_instance(ip_address, username, password)
    if not returncode == 0:
        slab_logger.error('Unable to connect to Jenkins server')
        sys.exit(1)
    for key in server.keys():
        match_obj = re.search(search_term, key, re.M | re.I)
        if match_obj:
            slab_logger.log(25, key)


@cli.command('pulp-repos', short_help='Find all the matching pulp repositories')
@click.argument('repo_name')
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
def find_pulp_repos(ctx, repo_name, ip_address, username, password, interactive):
    """
    Lists rpms using Pulp Server API.
    """
    slab_logger.info('Searching for rps on Pulp server')
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    if not password or not username:
        slab_logger.error("Username is %s and password is %s. "
                          "Please, set the correct value for both and retry." %
                          (username, password))
        sys.exit(1)
    url = "/pulp/api/v2/repositories/search/"
    payload = '{ "criteria": { "filters" : { "display_name" : {"$regex" : "%s"}}\
                             } }' % (repo_name)

    val = pulp_utils.post(url, ip_address, ctx, username, password, payload)
    repos = json.loads(val)

    if repos is not None and len(repos) > 0:
        for repo in repos:
            slab_logger.log(25, "Repo Id      : %s" % repo["id"])
            slab_logger.log(25, "Repo Name    : %s" % repo["display_name"])
            slab_logger.log(25, "Repo path    : %s" % repo["_href"] + "\n")
    else:
        slab_logger.error("No matching repositories found on this pulp server.")
