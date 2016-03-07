"""
Stack subcommand implementation to work on a particular service

"""
import os
import sys
import click

from servicelab.stack import pass_context
from servicelab.utils import service_utils
from servicelab.utils import logger_utils
from servicelab import settings

slab_logger = logger_utils.setup_logger(settings.verbosity, 'stack.workon')


@click.group('workon',
             invoke_without_command=True,
             short_help="Clone a service locally that you would like to work on.")
@click.argument('service_name', default="current")
@click.option('-b', '--branch', default="master",
              help='Choose a branch to run against for your service.')
@click.option('-db', '--data-branch', default="master",
              help='Choose a ccs-data branch to run against your service.')
@click.option('-u', '--username',
              help='Enter the username')
@pass_context
def cli(ctx, branch, data_branch, username, service_name):
    """
    Clones the service user wants to work on.
    """
    slab_logger.info('Cloning service %s' % service_name)
    current = ""
    if not username:
        username = ctx.get_username()
    if os.path.isfile(os.path.join(ctx.path, "current")):
        current_file = os.path.join(ctx.path, "current")
        with open(current_file, 'r') as cfile:
            current = cfile.readline()
            # todo: verify that current is set to something sane.

        if current == any([None, ""]) and (service_name == "current"):
            slab_logger.error("No service set on command line nor the "
                              "current(literally) file.")
            sys.exit(1)

        returncode = service_utils.check_service(ctx.path, service_name)
        if returncode > 0:
            slab_logger.error("Service repo does not exist")
            sys.exit(1)
        elif current == any([None, ""]) and (service_name != "current"):
            service_utils.sync_service(ctx.path, branch, username, service_name)
            service_utils.link(ctx.path, service_name, branch, username)
            service_utils.setup_vagrant_sshkeys(ctx.path)
            service_utils.sync_service(ctx.path, data_branch, username,
                                       "ccs-data")
        # Note: variable current and string current
        elif service_name != current and service_name != "current":
            service_utils.clean(ctx.path)
            service_utils.sync_service(ctx.path, branch, username, service_name)
            service_utils.link(ctx.path, service_name, branch, username)
            service_utils.setup_vagrant_sshkeys(ctx.path)
            service_utils.sync_service(ctx.path, data_branch, username,
                                       "ccs-data")
        else:
            # Note: notice we're passing the variable current not service_name.
            service_utils.sync_service(ctx.path, branch, username, current)
            service_utils.link(ctx.path, service_name, branch, username)
            service_utils.setup_vagrant_sshkeys(ctx.path)
            service_utils.sync_service(ctx.path, data_branch, username,
                                       "ccs-data")
    else:
        returncode = service_utils.check_service(ctx.path, service_name)
        if returncode > 0:
            slab_logger.error("Service repo does not exist")
            sys.exit(1)
        service_utils.sync_service(ctx.path, branch, username, service_name)
        service_utils.sync_service(ctx.path, data_branch, username, "ccs-data")
        service_utils.link(ctx.path, service_name, branch, username)
        service_utils.setup_vagrant_sshkeys(ctx.path)
