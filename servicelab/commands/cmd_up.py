import click
from servicelab.stack import pass_context


# RFI: What's the best way to implement a non required
#      argument for <service_name>. --> use group?
@click.command('up', short_help='')
@click.option('--ha', help='')
@click.option('--full', help='comple stack no ha')
@click.option('', '--osp-aio', help='')
@click.option('-i', '--interactive', help='')
@click.option('--username', help='')
@click.option('--password', help='')
@click.option
@pass_context
# RFI: Do we want a explicit prep stage like they do in redhouse-svc
# RFI: Also we need to think about if we're running latest data
#      or not as well as git status.
def up(ctx):
    """

    """
    pass


# vagrant status --> stack up status --> is that confusing
# should prob use the stack status cmd
