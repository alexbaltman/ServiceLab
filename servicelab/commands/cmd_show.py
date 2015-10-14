"""
Stack command to show details of
    1. repo
    2. review
    3. Jenkins build status
    4. artifact
    5. Pipe
"""
import click

from servicelab.stack import pass_context
from servicelab.utils import helper_utils
from servicelab.utils import gerrit_functions
from servicelab.utils import jenkins_utils
from servicelab.utils import context_utils
from servicelab.utils import artifact_utils
from servicelab.utils import gocd_utils


@click.group('show', short_help='Helps you show the details of a \
             pipeline resource.')
@pass_context
def cli(_):
    """
    Helps you show the details of resources in the SDLC pipeline.
    """
    pass


@cli.command('repo', short_help='Show the details of a repo in Gerrit.')
@click.argument('item')
@pass_context
def show_repo(ctx, repo):
    """
    Shows the details of git repos using Gerrit's API.
    """
    username = ctx.get_username()
    gfx = gerrit_functions.GerritFns(username, repo, ctx)
    gfx.print_gerrit("summary")


@cli.command('review', short_help='Show the details of a review in Gerrit.')
@click.argument('review')
@pass_context
def show_review(ctx, review):
    """
    Shows the details ofa review using Gerrit's API.
    """
    username = ctx.get_username()
    project = helper_utils.get_current_service(ctx.path)[1]
    gfx = gerrit_functions.GerritFns(username, project, ctx)
    gfx.print_gerrit("detail", review)


@cli.command('build', short_help='Show the details of a build in Jenkins.')
@click.argument('build_number')
@pass_context
def show_build(ctx, build_number):
    """
    Shows the details of a build in Jekins.
    """
    username = ctx.get_username()
    servername = context_utils.get_jenkins_url()
    password = click.prompt("password", hide_input=True, type=str)
    click.echo(jenkins_utils.get_build_status(build_number, username,
                                              password, servername))
    click.echo(jenkins_utils.get_build_log(build_number, username,
                                           password, servername))


@cli.command('artifact', short_help='Show the details of an artifact \
              in artifactory.')
@click.argument('url')
@click.option('-u',
              '--username',
              help='Provide artifactory server username',
              default=None,
              required=False)
@click.option('-p',
              '--password',
              default=None,
              help='Provide artifactory server password',
              required=False)
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def show_artifact(ctx, username, password, url, interactive):
    """
    Show the details of an artifact using Artifactory's API.
    """
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    click.echo('Showing details of artifact %s' % url)
    click.echo(artifact_utils.get_artifact_info(url, username, password))


@cli.command('pipe', short_help='Show the details of a GO deploy pipeline')
@click.argument('pipeline_name', required=True)
@click.option('-u',
              '--username',
              default=None,
              help='Provide artifactory server username',
              required=False)
@click.option('-p',
              '--password',
              default=None,
              help='Provide artifactory server password',
              required=False)
@click.option('-ip',
              '--ip_address',
              default=None,
              help='Provide the go server ip address and port number '
                   'in format <ip_address:portnumber>.')
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def show_pipe(ctx, pipeline_name, username, password, ip_address, interactive):
    """
    Show the details of a deployment pipline using GO's API.
    """
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    if ip_address is None:
        ip_address = context_utils.get_gocd_ip()
    click.echo('Showing details of pipeline %s' % pipeline_name)
    click.echo(gocd_utils.get_pipe_info(pipeline_name, username,
                                        password, ip_address))
