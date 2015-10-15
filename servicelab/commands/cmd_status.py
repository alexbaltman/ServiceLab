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
@pass_context
def cmd_repo_status(ctx):
    """
    Shows the details of git repos.
    """
    status_utils.show_repo_status(ctx.path)


@cli.command('vm', short_help='Show the status of servicelab project VMs.')
@pass_context
def cmd_vm_status(ctx):
    """
    Shows the details of git repos.
    """
    error_message = "Error occurred while connecting to Vagrant."
    returncode, _ = status_utils.show_vm_status(ctx.path)
    if returncode == 2:
        ctx.logger.error(error_message)
        click.echo(error_message)


@cli.command('all', short_help='Shows all status of servicelab project repos.')
@pass_context
def show_all_status(ctx):
    """
    Shows the Vm status.
    """
    error_message = "Error occurred while connecting to Vagrant."
    status_utils.show_repo_status(ctx.path)
    returncode, _ = status_utils.show_vm_status(ctx.path)
    if returncode == 2:
        ctx.logger.error(error_message)
        click.echo(error_message)
