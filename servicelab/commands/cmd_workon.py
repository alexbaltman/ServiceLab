import click
from servicelab.stack import pass_context
import os


@click.option('-i', '--interactive', help='Walk through booting VMs')
@click.option('-b', '--branch', default="master", help='Choose a branch to run\
              against for your service.')
@click.option('-u', '--username', help='Enter the password for the username')
# @click.password_option(help='Enter the gerrit username or \
# CEC you want to use.')
@click.argument('service_name')
@click.group('workon', invoke_without_command=True, short_help="Call a service that you would like to \
             work on.")
@pass_context
def cli(ctx, interactive, branch, username, service_name):
    if not os.path.exists(os.path.join(ctx.path, "services")):
        ctx.vlog("Making services directory: %s" % (ctx.path), 2)
        os.makedirs(os.path.join(ctx.path, "services"))
    if branch is not None:
        ctx.vlog("Setting branch to %s" % (branch), 3)
        ctx.branch = branch

    local_services = []
    local_services = os.listdir(os.path.join(ctx.path, "services"))
    if service_name in local_services:
        # Execute Git pull branch into .stack,
        # git checkout branch, or git checkout -b branch
        # --> got to be on the right branch
        ctx.vlog('Running: git pull --ff-only origin %s in %s/services/%s' %
                 ctx.branch, ctx.path, service_name, "2")
    else:
        # Git clone service
        ctx.vlog("Running: git clone -b %s ssh://%s@cis-gerrit.cisco.com:29418/service-%s\
 %s/services/%s" % (ctx.branch,
                    username, service_name, ctx.path, service_name), "2")
