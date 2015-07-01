import click
from servicelab.stack import pass_context
from pprint import pprint


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
# @click.password_option(help='Enter the gerrit username or \
# CEC you want to use.')
@click.group('up', invoke_without_command=True, short_help="Boots VM(s).")
@pass_context
# RFI: Do we want a explicit prep stage like they do in redhouse-svc
# RFI: Also we need to think about if we're running latest data
#      or not as well as git status.
def cli(ctx, ha, full, osp_aio, interactive, branch, rhel7, username):
    # #Dev testing Block for aaltman
    ctx.log('Reg. Log bro')
    print "username: " + str(username)
    # ctx.vlog('verbose info', 2)
    # ctx.vlog('vverbose info', 3)
    # ctx.vlog('vvverbose info', 4)
    attrs = vars(ctx)
    print ', '.join("%s: %s" % item for item in attrs.items())
    pprint(dir(ctx))


# vagrant status --> stack up status --> is that confusing
# should prob use the stack status cmd
