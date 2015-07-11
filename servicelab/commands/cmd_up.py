from servicelab.utils import service_utils
from servicelab.stack import pass_context
import getpass
import click
import sys
import os


@click.option('--ha', is_flag=True, default=False, help='Enables HA for core OpenStack components \
              by booting the necessary extra VMs.')
@click.option('--full', help='Boot complete openstack stack without ha, \
              unless --ha flag is set.')
@click.option('--osp-aio', help='Boot a full CCS implementation of the \
              OpenStack Platform on one VM. Note: This is not the same as \
              the AIO node deployed in the service cloud.')
@click.option('-i', '--interactive', help='Walk through booting VMs')
@click.option('-b', '--branch', help='Choose a branch to run against \
              for ccs-data.')
@click.option('--rhel7', help='Boot a rhel7 vm.')
@click.option('-u', '--username', help='Enter the password for the username')
@click.argument('service_name', default="current")
# @click.password_option(help='Enter the gerrit username or \
# CEC you want to use.')
@click.group('up', invoke_without_command=True, short_help="Boots VM(s).")
@pass_context
# RFI: Do we want a explicit prep stage like they do in redhouse-svc
# RFI: Also we need to think about if we're running latest data
#      or not as well as git status.
def cli(ctx, ha, full, osp_aio, interactive, branch, rhel7, username, service_name):
    if username is None or "":
        username = getpass.getuser()
    # TODO: Refactor this b/c duplicated in cmd_workon
    if os.path.isfile(os.path.join(ctx.path, "current")):
        current_file = os.path.join(ctx.path, "current")
        f = open(current_file, 'r')
        # TODO: verify that current is set to something sane.
        current = f.readline()
        if current == "" or None:
            ctx.logger.error("No service set.")
            sys.exit
        else:
            ctx.logger.debug("Working on %s" % (current))

    # #Dev testing Block for aaltman
    # attrs = vars(ctx)
    # print ', '.join("%s: %s" % item for item in attrs.items())
    service_utils._run_this('vagrant up', os.path.join(ctx.path, "services", service_name))
    service_utils._run_this('vagrant hostmanager', os.path.join(ctx.path, "services", service_name))
    service_utils._run_this('vagrant ssh infra-001 -c cp os.path.join(%s, "hosts") "/etc/ansible"; cd "/opt/ccs/services/%s; sudo heighliner --dev --debug deploy"' % (ctx.path, service_name))
