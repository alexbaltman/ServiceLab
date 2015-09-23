"""
Build command submodule displays
    1. Build status of a Jenkins job
    2. Build log of a Jenkins Job.

"""
import click
import requests

from requests.auth import HTTPBasicAuth
from BeautifulSoup import BeautifulSoup

from servicelab.stack import pass_context
from servicelab.utils import jenkins_utils


@click.group('build', short_help='Build to work with.',
             add_help_option=True)
@click.pass_context
def cli(_):
    """
    Convinence functions for Jenkin job status
    """
    pass


@cli.command('status', short_help='Display build status')
@click.argument('job_name', required=True)
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
              help="Provide the jenkinsserv url ip address and port "
                   "no in format <ip:portno>.",
              required=True)
@pass_context
def display_build_status(_,
                         job_name,
                         user,
                         password,
                         ip_address):
    """
    Displays a build status.
    """
    server = jenkins_utils.get_server_instance(ip_address, user, password)
    click.echo(server[job_name].get_last_build().name + ", " +
               server[job_name].get_last_build().get_status())


@cli.command('log', short_help='Display build status log')
@click.argument('job_name', required=True)
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
              help="Provide the jenkinsserv url ip address and port "
                   "no in format <ip:portno>.",
              required=True)
@pass_context
def display_build_log(_, job_name, user, password, ip_address):
    """
    Displays a build log.
    """
    server = jenkins_utils.get_server_instance(ip_address, user, password)
    click.echo(server[job_name].get_last_build().name + ", " +
               server[job_name].get_last_build().get_status())

    job_number = server[job_name].get_last_build().get_number()
    log_url = "{0}/job/{1}/{2}/consoleText".format(ip_address, job_name,
                                                   job_number)

    # Find latest run info
    import pdb
    pdb.set_trace()
    res = requests.post(log_url, auth=HTTPBasicAuth(user, password))
    soup = BeautifulSoup(res.content)
    click.echo("-------- Printing job log for build " + log_url + "--------")
    click.echo(soup)
    click.echo("-------- End of job log for build --------")
    click.echo("\n")
