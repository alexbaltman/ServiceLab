"""
The module contains the status subcommand implemenation.
"""
import os

import click

from servicelab.stack import pass_context
from servicelab.utils import status_utils


@click.group('status', short_help='Shows the status of '
             'your servicelab environment.')
def cli():
    """
    Helps you show the details of resources in the SDLC pipeline.
    """
    pass


@cli.command('repo', short_help='Show the status of local service repositories in '
             'your Servicelab environment.')
@pass_context
def cmd_repo_status(ctx):
    """
    Shows the details of git repos.
    """
    status_utils.show_repo_status(ctx.path)


@cli.command('vm', short_help='Show the status of VMs in your Servicelab environment.')
@pass_context
def cmd_vm_status(ctx):
    """
    Shows the vm status
    """
    display_vm_status(ctx)


def display_vm_status(ctx):
    """
    Shows the vm status.
    """
    vagrant_file_path = os.path.join(ctx.path, "Vagrantfile")
    error_message = "\nCannot show VM status since internal error "\
        "has occurred. Most probably this file does not "\
        "exist : %s . Please, run : stack workon <project name>"\
        " to fix the issue." % (vagrant_file_path)
    if os.path.isfile(vagrant_file_path) == False:
        click.echo(error_message)
        sys.exit(1)
    else:
        returncode, _ = status_utils.show_vm_status(ctx.path)
        if returncode == 2:
            click.echo(error_message)
            sys.exit(1)


@cli.command('all', short_help='Shows the complete status of your Servicelab environment.')
@pass_context
def show_all_status(ctx):
    """
    Shows the Vm status.
    """
    status_utils.show_repo_status(ctx.path)
    display_vm_status(ctx)
