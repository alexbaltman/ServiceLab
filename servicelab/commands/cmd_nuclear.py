import click
from servicelab.stack import pass_context


@click.group('nuclear', short_help='Cleans Everything.')
@pass_context
def cli(ctx):
    """
    For Development purposes only.
    """
    pass


@cli.command('all', short_help='')
@pass_context
def nuclear(ctx):
    """
    Cleans Everything.
    """
    pass
