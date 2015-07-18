from servicelab.stack import pass_context
from servicelab.utils import service_utils
import getpass
import click
import sys
import os


@click.option('-i', '--interactive', help='Walk through booting VMs')
@click.option('-b', '--branch', default="master", help='Choose a branch to run\
              against for your service.')
@click.option('-u', '--username', help='Enter the password for the username')
# @click.password_option(help='Enter the gerrit username or \
# CEC you want to use.')
# RFI: This is required right now, but what if I just want to work on current.
#      Should be able to handle no service argument.
@click.argument('service_name', default="current")
@click.group('workon', invoke_without_command=True, short_help="Call a service that you would like to \
             work on.")
@pass_context
def cli(ctx, interactive, branch, username, service_name):
    current = ""
    if username is None or "":
        username = getpass.getuser()
    print "##ALMOST"
    if os.path.isfile(os.path.join(ctx.path, "current")):
        print "##ONE"
        current_file = os.path.join(ctx.path, "current")
        f = open(current_file, 'r')
        # TODO: verify that current is set to something sane.
        current = f.readline()
        if current == any([None, ""]) and (service_name == "current"):
            ctx.logger.error("No service set on command line nor the\
                             current(literally) file.")
            print "##TWO"
            sys.exit(1)
        elif current == any([None, ""]) and (service_name != "current"):
            print "##THREE"
            returncode = service_utils.check_service(ctx.path, service_name)
            if returncode > 0:
                ctx.logger.debug("Service repo does not exist")
                sys.exit(1)
            service_utils.sync_service(ctx.path, branch, username,
                                       service_name)
            service_utils.link(ctx.path, service_name, branch, username)
            service_utils.setup_vagrant_sshkeys(ctx.path)
            service_utils.sync_data(ctx.path, username, branch)
        # Note: variable current and string current
        elif service_name != current and service_name != "current":
            print "##FOUR"
            returncode = service_utils.check_service(ctx.path, service_name)
            if returncode > 0:
                ctx.logger.debug("Service repo does not exist")
                sys.exit(1)
            service_utils.clean(ctx.path)
            service_utils.sync_service(ctx.path, branch, username,
                                       service_name)
            service_utils.link(ctx.path, service_name, branch, username)
            service_utils.setup_vagrant_sshkeys(ctx.path)
            service_utils.sync_data(ctx.path, username, branch)
        else:
            print "##FIVE"
            # Note: notice we're passing the variable current not service_name.
            returncode = service_utils.check_service(ctx.path, service_name)
            if returncode > 0:
                ctx.logger.debug("Service repo does not exist")
                sys.exit(1)
            service_utils.sync_service(ctx.path, branch, username, current)
            service_utils.link(ctx.path, service_name, branch, username)
            service_utils.setup_vagrant_sshkeys(ctx.path)
            service_utils.sync_data(ctx.path, username, branch)
    else:
        print "##TOO FAR"
        returncode = service_utils.check_service(ctx.path, service_name)
        if returncode > 0:
            ctx.logger.debug("Service repo does not exist")
            sys.exit(1)
        service_utils.sync_service(ctx.path, branch, username, service_name)
        service_utils.sync_data(ctx.path, username, branch)
        service_utils.link(ctx.path, service_name, branch, username)
        service_utils.setup_vagrant_sshkeys(ctx.path)
