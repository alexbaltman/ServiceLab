"""
Build command submodule displays
    1. Build status of a Jenkins job
    2. Build log of a Jenkins Job.

"""
import click

from servicelab.stack import pass_context
from servicelab.utils import jenkins_utils
from servicelab.utils import context_utils


@click.group('build', short_help='Work with builds in Jenkins with this command subset.',
             add_help_option=True)
@click.pass_context
def cli(_):
    """
    Convinence functions for Jenkin job status
    """
    pass


@cli.command('status', short_help='Display the status of a build in Jenkins.')
@click.argument('job_name', required=True)
@click.option('-u',
              '--username',
              help='Provide jenkins username')
@click.option('-p',
              '--password',
              help='Provide jenkins server password')
@click.option('-ip',
              '--ip_address',
              default=context_utils.get_jenkins_url(),
              help="Provide the jenkinsserv url ip address and port "
                   "no in format <ip:portno>.")
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def display_build_status(ctx,
                         job_name,
                         username,
                         password,
                         ip_address,
                         interactive):
    """
    Displays a build status.
    """
    ctx.logger.info('Displaying build status')
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    status = jenkins_utils.get_build_status(job_name,
                                            username,
                                            password,
                                            ip_address)
    click.echo(status)


@cli.command('log', short_help='Display the status log of a build in Jenkins.')
@click.argument('job_name', required=True)
@click.option('-u',
              '--username',
              help='Provide jenkins username')
@click.option('-p',
              '--password',
              help='Provide jenkins server password')
@click.option('-ip',
              '--ip_address',
              default=context_utils.get_jenkins_url(),
              help="Provide the jenkinsserv url ip address and port "
                   "no in format <ip:portno>.")
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def display_build_log(ctx, job_name, username, password, ip_address, interactive):
    """
    Displays a build log.
    """
    ctx.logger.info('Displaying build log')
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    log = jenkins_utils.get_build_log(job_name, username, password, ip_address)
    click.echo(log)


@cli.command('run', short_help='Trigger a build in Jenkins.')
@click.argument('job_name', required=True)
@click.option('-u',
              '--username',
              help='Provide jenkins username')
@click.option('-p',
              '--password',
              help='Provide jenkins server password')
@click.option('-ip',
              '--ip_address',
              default=context_utils.get_jenkins_url(),
              help="Provide the jenkinsserv url ip address and port "
                   "no in format <ip:portno>.")
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def run_build(ctx, job_name, username, password, ip_address, interactive):
    """
    Displays a build status.
    """
    ctx.logger.info('Displaying build status')
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    jenkins_utils.run_build(job_name,
                            username,
                            password,
                            ip_address,
                            ctx)
