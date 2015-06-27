import click
from servicelab.stack import pass_context


# Note: Not for GA.
# RFI: How do we leave this code in and disable the help for it?
@click.group('nuclear', short_help='Cleans Everything.')
@pass_context
def cli(ctx):
    """
    For Development purposes only.
    """
    pass


@cli.command('all', short_help='Seriously. It cleans - Everything')
@pass_context
def nuclear(ctx):
    """
    Cleans Everything.
    """
    click.echo('Nuking your development servicelab zone')
