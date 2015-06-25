import click
from servicelab.stack import pass_context


@click.group('review', short_help='Helps you work with Gerrit')
@pass_context
def cli(ctx):
    """
    Helps you work with Gerrit.
    """
    pass


@cli.command('inc', short_help='Find a repo in Gerrit.')
@click.argument('search_term')
@pass_context
def review_(ctx, search_term):
    """
    Searches through Gerrit's API for a repo using your search term.
    """
    pass


@cli.command('build', short_help='Find a Jenkins build.')
@click.argument('search_term')
@pass_context
# RFI: how do we take fancy input like grep? aka grep -ie "this|that"
# see pipe in search term
def find_build(ctx, search_term):
    """
    Searches through Jenkins API for pipelines using your search term.
    """
    pass


@cli.command('artifact', short_help='Find an artifact in artifactory')
@click.argument('search_term')
@pass_context
# RFI: how do we take fancy input like grep? aka grep -ie "this|that"
# see pipe in search term
def find_artifact(ctx, search_term):
    """
    Searches through Artifactory's API for artifacts using your search term.
    """
    pass


@cli.command('pipe', short_help='Find a Go deploy pipeline')
@click.argument('search_term')
@pass_context
# RFI: how do we take fancy input like grep? aka grep -ie "this|that"
# see pipe in search term
def find_pipe(ctx, search_term):
    """
    Searches through GO's API for pipelines using your search term.
    """
    pass
