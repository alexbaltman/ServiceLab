import click
import re
import os
from servicelab.stack import pass_context
from servicelab.utils import jenkins_utils
import requests
from requests.auth import HTTPBasicAuth
from BeautifulSoup import BeautifulSoup
from jenkinsapi.jenkins import Jenkins


@click.group('find', short_help='Helps you search \
             pipeline resources.', invoke_without_command=True,
             add_help_option=True)
@pass_context
def cli(ctx):
    """
    Helps you search for resources in the SDLC pipeline.
    """
    pass


@cli.command('repo', short_help='Find a repo in Gerrit.')
@click.argument('search_term')
@pass_context
# RFI: how do we take fancy input like grep? aka grep -ie "this|that"
#      see pipe in search term.
def find_repo(ctx, search_term):
    """
    Searches through Gerrit's API for a repo using your search term.
    """
    click.echo('Searching for %s in Gerrit' % search_term)


# RFI: What would we use as search_term here. It's not clear if we
#      need this or not - it's being add for completeness and reducing
#      user confusion.
@cli.command('review', short_help='Find a review in Gerrit.')
@click.argument('search_term')
@pass_context
# RFI: How do we take fancy input like grep? aka grep -ie "this|that"
#      see pipe in search term.
def find_review(ctx, search_term):
    """
    Searches through Gerrit's API for a repo using your search term.
    """
    click.echo('Searching for %s review in Gerrit' % search_term)


@cli.command('build', short_help='Find a Jenkins build.')
@click.argument('search_term')
@pass_context
# RFI: how do we take fancy input like grep? aka grep -ie "this|that"
#      see pipe in search term.
def find_build(ctx, search_term):
    """
    Searches through Jenkins API for pipelines using your search term.
    """
    click.echo('Searching for %s build in Jenkins' % search_term)


@cli.command('artifact', short_help='Find an artifact in artifactory')
@click.argument('search_term')
@pass_context
# RFI: how do we take fancy input like grep? aka grep -ie "this|that"
#      see pipe in search term.
def find_artifact(ctx, search_term):
    """
    Searches through Artifactory's API for artifacts using your search term.
    """
    click.echo('Searching for %s artifact in Artifactory' % search_term)


@cli.command('pipe', short_help='Find a Go deploy pipeline')
@click.argument('search_term')
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
    help='Provide the go server ip address and port number \
          in format <ipaddress:portnumber>.',
    required=True)
@pass_context
def find_pipe(ctx, search_term, localrepo, gouser, gopass, goserver):
    """
    Searches through GO's API for pipelines using your search term.
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
        r = re.compile(serverStringPrefix + search_term + serverStringSuffix)
        searchString = pipeline['href']
        splitString = searchString.split('/')
        searchString = search_term
        searchObj = re.search(
            "^" + searchString + "$",
            splitString[
                len(splitString) - 2],
            re.M | re.I)
        if searchObj:
            if localrepo:
                for sdir in servicesdirs:
                    if sdir.startswith("service-"):
                        service = sdir.split("service-", 1)[1]
                        if service == searchObj.group():
                            print searchObj.group()
            else:
                print searchObj.group()


@cli.command('build', short_help='Find a build')
@click.argument('search_term')
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
    help='Provide the jenkinsserv url ip address and port\
    no in format <ip:portno>.',
    required=True)
@pass_context
def find_build(ctx, search_term, jenkinsuser, jenkinspass, jenkinsservurl):
    """
    Searches through the build search term.
    """
    server = jenkins_utils.get_server_instance(jenkinsservurl,
                                               jenkinsuser, jenkinspass)
    for j in server.keys():
        searchObj = re.search(
            "^" + search_term + "$",
            j,
            re.M | re.I)
        if searchObj:
            print searchObj.group()
