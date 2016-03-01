"""
The module contains the redeploy subcommand implemenation.
"""
import sys

import click

from servicelab.utils import service_utils
from servicelab.utils import vagrant_utils
from servicelab.stack import pass_context
from servicelab.utils import logger_utils
from servicelab import settings

slab_logger = logger_utils.setup_logger(settings.verbosity, 'stack.cmd.redeploy')


@click.option('-v',
              '--existing-vm',
              default=False,
              help='Choose a VM from ccs-data to redeploy all services to.')
@click.option('-e',
              '--env',
              help='Choose an environment from ccs-data.  For use with --existing-vm option')
@click.command('redeploy',
               short_help="Redeploy your service to your VMs.")
@click.argument('deploy_svc')
@pass_context
def cli(ctx, deploy_svc, existing_vm, env):
    """
    Re-deploy your service in an environment with an existing infra node. This should help
    facillitate rapid development as you can make changes locally on your laptop and
    continually deploy with this command.
    """
    if not deploy_svc.startswith('service-'):
        deploy_svc = 'service-' + deploy_svc
        slab_logger.log(25, 'Adding "service-" to service: ' + deploy_svc)

    command = ('vagrant ssh {0} -c \"cd /opt/ccs/services/{1}/ && sudo heighliner '
               '--dev --debug deploy\"')

    returncode, myinfo = service_utils.run_this(command.format('infra-001', deploy_svc),
                                                ctx.path)

    slab_logger.log(25, myinfo)
    if returncode > 0:
        slab_logger.error('Failed to deploy service. Trying infra-002')
        returncode, myinfo = service_utils.run_this(command.format('infra-002', deploy_svc),
                                                    ctx.path)
        slab_logger.log(25, myinfo)
        if returncode > 0:
            slab_logger.error('Failed to deploy service.')
            sys.exit(1)
        else:
            slab_logger.log(25, 'Deployed service successfully.')
            sys.exit(0)
    else:
        slab_logger.error('Deployed service successfully.')
        sys.exit(0)
