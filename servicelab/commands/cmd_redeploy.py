"""
The module contains the redeploy subcommand implemenation.
"""
import sys

import click

from servicelab.utils import service_utils
from servicelab.utils import vagrant_utils
from servicelab.stack import pass_context


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
        click.echo('Adding "service-" to service: ' + deploy_svc)

    command = ('vagrant ssh {0} -c \"cd /opt/ccs/services/{1}/ && sudo heighliner '
               '--dev --debug deploy\"')

    returncode, myinfo = service_utils.run_this(command.format('infra-001', deploy_svc),
                                                ctx.path)

    click.echo(myinfo)
    click.echo('Failed to deploy service. Trying infra-002')
    if returncode > 0:
        returncode, myinfo = service_utils.run_this(command.format('infra-002', deploy_svc),
                                                    ctx.path)
        if returncode > 0:
            click.echo(myinfo)
            click.echo('Failed to deploy service.')
            sys.exit(1)
        else:
            click.echo(myinfo)
            click.echo('Deployed service successfully.')
            sys.exit(0)
    else:
        click.echo(myinfo)
        click.echo('Deployed service successfully.')
        sys.exit(0)
