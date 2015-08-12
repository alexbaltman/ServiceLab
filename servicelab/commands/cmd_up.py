from servicelab.utils import service_utils
from servicelab.utils import vagrant_utils
from servicelab.utils import helper_utils
from servicelab.stack import pass_context
import click
import sys


@click.option('--ha', is_flag=True, default=False, help='Enables HA for core OpenStack components \
              by booting the necessary extra VMs.')
@click.option('--full', help='Boot complete openstack stack without ha, \
              unless --ha flag is set.')
# @click.option('--osp-aio', help='Boot a full CCS implementation of the \
#              OpenStack Platform on one VM. Note: This is not the same as \
#              the AIO node deployed in the service cloud.')
@click.option('-i', '--interactive', help='Walk through booting VMs')
@click.option('-r', '--remote', is_flag=True, default=False,
              help='Boot into an OS environment')
@click.option('-b', '--branch', help='Choose a branch to run against \
              for ccs-data.')
@click.option('--rhel7', help='Boot a rhel7 vm.')
@click.option('--target', '-t', help='pick an osp target to boot.')
@click.option('-u', '--username', help='Enter the password for the username')
# @click.argument('service_name', default="current")
@click.group('up', invoke_without_command=True, short_help="Boots VM(s).")
@pass_context
def cli(ctx, ha, full, osp_aio, interactive, branch, rhel7, username,
        # service_name, target):
        target):
    if not username:
        returncode, username = helper_utils.set_user(ctx.path)

    returncode, current_service = helper_utils.get_current_service(ctx.path)
    if returncode > 0:
        ctx.error("Failed to get the current service")
        sys.exit(1)

    # ======================================================
    # #Dev testing Block for aaltman
    # attrs = vars(ctx)
    # print ', '.join("%s: %s" % item for item in attrs.items())

    # CL/JP stack method
    if target:
        click.echo("vagrant up %s" % (target))
        a = vagrant_utils.Connect_to_vagrant(vmname=target,
                                             path=ctx.path)
        a.v.up()
        service_utils.run_this('vagrant hostmanager')
    # service_utils.run_this('vagrant ssh infra-001 -c cp "/etc/ansible"; \
    # cd "/opt/ccs/services/%s; sudo heighliner \
    # --dev --debug deploy"' % (os.path.join(ctx.path, "hosts"),
    # service_name))
    # ======================================================

    # writeout vagrant.yaml w/ current vms
    # read the profiles to see what you need to boot
        # or a prep for a service --> where to store profiles
        # the whole one is defined it's the small one.
    # if not in profile
    # #check if host exists
    # # if not
    # ## read host from template
    # ## write host
    # ## if it's not in

    if os.path.isfile(os.path.join(path, xxx)):

        yaml_utils.host_add_vagrantyaml(path, file_name, hostname, site, memory=2,
                                        box='http://cis-kickstart.cisco.com/ccs-rhel-7.box',
                                        role=None, profile=None, domain=1, storage=0)
