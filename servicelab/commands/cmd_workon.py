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
    Clones a service repo that the user wants to work on.
    """
    slab_logger.info('Cloning service %s' % service_name)
    current = ""
    if not username:
        username = ctx.get_username()
    repo_name = service_name
    if os.path.isfile(os.path.join(ctx.path, "current")):
        current_file = os.path.join(ctx.path, "current")
        with open(current_file, 'r') as cfile:
            current = cfile.readline()
            # todo: verify that current is set to something sane.

        returncode = service_utils.check_service(ctx.path, service_name)
        if returncode > 0:
            slab_logger.error("Gerrit repo %s does not exist" % service_name)
            sys.exit(1)

        if current == any([None, ""]) and (service_name == "current"):
            slab_logger.error("No service set on command line nor the "
                              "current(literally) file.")
            sys.exit(1)
        # Keeps the repo_name set to service_name
        elif current == any([None, ""]) and (service_name != "current"):
            pass
        # Note: variable current and string current
        elif service_name != current and service_name != "current":
            service_utils.clean(ctx.path)
        else:
            # Note: notice we're passing the variable current not service_name.
            repo_name = current

    returncode = service_utils.sync_service(ctx.path, branch, username, repo_name)
    if not returncode:
        slab_logger.error('Unable to sync %s repo' % service_name)
        sys.exit(1)

    returncode = service_utils.link(ctx.path, service_name, branch, username)
    if not returncode == 0:
        slab_logger.error('Unable to link %s repo' % service_name)
        sys.exit(1)

    returncode, output = service_utils.setup_vagrant_sshkeys(ctx.path)
    if not returncode == 0:
        slab_logger.error('Failed to generate ssh keys:\n%s' % output)
        sys.exit(1)

    if not service_name == 'ccs-data':
        returncode = service_utils.sync_service(ctx.path, data_branch, username, 'ccs-data')
        if not returncode:
            slab_logger.error('Unable to sync ccs-data repo')
            sys.exit(1)
