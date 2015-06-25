import click
from servicelab.stack import pass_context


@click.command('enc', short_help='Encrypt a value and it will give you back an \
               encrypted value for you to put into your ccs-data file.')
@click.argument('value')
@pass_context
def cli(ctx, value):
    """
    Encrypt a value to be put into ccs-data.
    """
    ctx.log('Changed files: none')
    ctx.vlog('debug info')
