import click
from servicelab.stack import pass_context


@click.command('enc', short_help='Encrypt a value and it will give you back an \
               encrypted value for you to put into your ccs-data file.')
@click.argument('value')
@pass_context
# Note: For some reason the -v -vv -vvv etc. are positional. They have to be
# called right after stack.
# RFI: Are we able to change the above so they can be taken wherever?
def cli(ctx, value):
    """
    Encrypt a value to be put into ccs-data.
    """
    ctx.logging.info('Changed files: none')
    ctx.logging.debug('debug info')
