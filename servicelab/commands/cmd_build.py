from servicelab.stack import pass_context
from servicelab.utils import jenkins_utils
import click
import requests
from requests.auth import HTTPBasicAuth
from BeautifulSoup import BeautifulSoup


@click.group('build', short_help='Build to work with.',
             add_help_option=True)
@click.pass_context
def cli(ctx):
    pass


@cli.command('status', short_help='Display build status')
@click.argument('job_name', required=True)
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
def display_build_status(
        ctx,
        job_name,
        jenkinsuser,
        jenkinspass,
        jenkinsservurl):
    """
    Displays a build status.
    """
    server = jenkins_utils.get_server_instance(
        jenkinsservurl, jenkinsuser, jenkinspass)
    print server[job_name].get_last_build().name, ", ",
    print server[job_name].get_last_build().get_status()


@cli.command('log', short_help='Display build status log')
@click.argument('job_name', required=True)
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
def display_build_log(ctx, job_name, jenkinsuser, jenkinspass, jenkinsservurl):
    """
    Displays a build log.
    """
    server = jenkins_utils.get_server_instance(
        jenkinsservurl, jenkinsuser, jenkinspass)
    print server[job_name].get_last_build().name, ", ",
    server[job_name].get_last_build().get_status()
    jobNumber = server[job_name].get_last_build().get_number()
    logURL = "{0}/job/{1}/{2}/consoleText".format(jenkinsservurl, job_name,
                                                  jobNumber)
    # Find latest run info
    res = requests.post(logURL, auth=HTTPBasicAuth(jenkinsuser, jenkinspass))
    soup = BeautifulSoup(res.content)
    print "\n\n-------------------Printing job log for build : ", \
        logURL, "-------------------------"
    print soup
    print "\n\n-------------------End of job log for build : ",\
        logURL, "-------------------------"
