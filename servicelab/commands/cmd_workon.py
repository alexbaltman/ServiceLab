"""
Stack subcommand implementation to work on a particular service

"""
import os
import sys

import click

from servicelab.stack import pass_context
from servicelab.utils import service_utils


@click.group('workon',
             invoke_without_command=True,
             short_help="Call a service that you would like to work on.")
@click.argument('service_name', default="current")
@click.option('-b', '--branch', default="master",
              help='Choose a branch to run against for your service.')
@click.option('-db', '--data-branch', default="master",
              help='Choose a ccs-data branch to run against your service.')
@click.option('-u', '--user',
              help='Enter the username')
@pass_context
def cli(ctx, branch, data_branch, user, service_name):
    """
    Creates a service user wants to work on.

    Attributes
        ctx
        interactive
        branch
        data_branch
        user
        service_name
    """
    current = ""
    if not user:
        user = ctx.get_username()
    if os.path.isfile(os.path.join(ctx.path, "current")):
        current_file = os.path.join(ctx.path, "current")
        with open(current_file, 'r') as cfile:
            current = cfile.readline()
            # todo: verify that current is set to something sane.

        if current == any([None, ""]) and (service_name == "current"):
            ctx.logger.error("No service set on command line nor the "
                             "current(literally) file.")
            sys.exit(1)
        elif current == any([None, ""]) and (service_name != "current"):
            returncode = service_utils.check_service(ctx.path, service_name)
            if returncode > 0:
                ctx.logger.debug("Service repo does not exist")
                sys.exit(1)

            service_utils.sync_service(ctx.path, branch, user,
                                       service_name)
            service_utils.link(ctx.path, service_name, branch, user)
            service_utils.setup_vagrant_sshkeys(ctx.path)
            service_utils.sync_service(ctx.path, data_branch, user,
                                       "ccs-data")
        # Note: variable current and string current
        elif service_name != current and service_name != "current":
            returncode = service_utils.check_service(ctx.path, service_name)
            if returncode > 0:
                ctx.logger.debug("Service repo does not exist")
                sys.exit(1)

            service_utils.clean(ctx.path)
            service_utils.sync_service(ctx.path, branch, user,
                                       service_name)
            service_utils.link(ctx.path, service_name, branch, user)
            service_utils.setup_vagrant_sshkeys(ctx.path)
            service_utils.sync_service(ctx.path, data_branch, user,
                                       "ccs-data")
        else:
            # Note: notice we're passing the variable current not service_name.
            returncode = service_utils.check_service(ctx.path, service_name)
            if returncode > 0:
                ctx.logger.debug("Service repo does not exist")
                sys.exit(1)

            service_utils.sync_service(ctx.path, branch, user, current)
            service_utils.link(ctx.path, service_name, branch, user)
            service_utils.setup_vagrant_sshkeys(ctx.path)
            service_utils.sync_service(ctx.path, data_branch, user,
                                       "ccs-data")
    else:
        returncode = service_utils.check_service(ctx.path, service_name)
        if returncode > 0:
            ctx.logger.debug("Service repo does not exist")
            sys.exit(1)
        service_utils.sync_service(ctx.path, branch, user, service_name)
        service_utils.sync_service(ctx.path, data_branch, user,
                                   "ccs-data")
        service_utils.link(ctx.path, service_name, branch, user)
        service_utils.setup_vagrant_sshkeys(ctx.path)
