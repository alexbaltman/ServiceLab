"""
Build command submodule displays
    1. Build status of a Jenkins job
    2. Build log of a Jenkins Job.

"""
import click

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
    status = jenkins_utils.get_build_status(job_name,
                                            user,
                                            password,
                                            ip_address)
    click.echo(status)


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
    log = jenkins_utils.get_build_log(job_name, user, password, ip_address)
    click.echo(log)
