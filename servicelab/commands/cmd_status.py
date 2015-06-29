import click
from servicelab.stack import pass_context
from pprint import pprint


@click.command('status', short_help='Shows status of your \
               servicelab environment.')
@pass_context
def cli(ctx):
    """
    Shows status of your working servicelab environment.
    """
    ctx.log('Changed files: none')
    ctx.vlog('###DEBUG###', "4")
