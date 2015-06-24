import click
from servicelab.stack import pass_context

@click.command('status', short_help='Shows file changes.')
@pass_context
def cli(ctx):
    """Shows file changes in the current working directory."""
    cxt.log('Changed files: none')
    cxt.vlog('debug info')
