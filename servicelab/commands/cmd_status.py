import click
from servicelab.stack import pass_context


@click.command('status', short_help='Shows status of your \
               servicelab environment.')
@pass_context
def cli(ctx):
    """
    Shows status of your working servicelab environment.
    """
    ctx.log('Changed files: none')
    ctx.vlog('debug info')
