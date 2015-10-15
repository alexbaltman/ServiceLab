"""
The module contains the status subcommand implemenation.
"""
import click

from servicelab.stack import pass_context
from servicelab.utils import status_utils


@click.group('status', short_help='Helps you show the details of a \
             status of the servicelab environment.')
def cli():
    """
    Helps you show the details of resources in the SDLC pipeline.
    """
    pass


@cli.command('repo', short_help='Show the status of servicelab project repos.')
# item is generic right now until we can figure out exactly what that's
# going to look like.
@pass_context
def cmd_repo_status(ctx):
    """
    Shows the details of git repos.
    """
    status_utils.show_repo_status(ctx.path)


@cli.command('all', short_help='Shows all status of servicelab project repos.')
# item is generic right now until we can figure out exactly what that's
# going to look like.
@pass_context
def show_all_status(ctx):
    """
    Shows the Vm status.
    """
    status_utils.show_repo_status(ctx.path)
