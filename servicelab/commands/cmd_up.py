import click
from servicelab.stack import pass_context


@click.command('status', short_help='Shows status of your environment.')
@pass_context
def cli(ctx):
    """
    Shows status of your working environment.
    """
    ctx.log('Changed files: none')
    ctx.vlog('debug info')
