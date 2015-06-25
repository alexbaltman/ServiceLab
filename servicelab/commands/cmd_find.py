import click
from servicelab.stack import pass_context


@click.group('find', short_help='Helps you search \
             pipeline resources.', invoke_without_command=True,
             add_help_option=True)
@pass_context
def cli(ctx):
    """
    Helps you search for resources in the SDLC pipeline.
    """
    pass


@cli.command('repo', short_help='Find a repo in Gerrit.')
@click.argument('search_term')
@pass_context
# RFI: how do we take fancy input like grep? aka grep -ie "this|that"
#      see pipe in search term.
def find_repo(ctx, search_term):
    """
    Searches through Gerrit's API for a repo using your search term.
    """
    pass


# RFI: What would we use as search_term here. It's not clear if we
#      need this or not - it's being add for completeness and reducing
#      user confusion.
@cli.command('review', short_help='Find a repo in Gerrit.')
@click.argument('search_term')
@pass_context
# RFI: How do we take fancy input like grep? aka grep -ie "this|that"
#      see pipe in search term.
def find_repo(ctx, search_term):
    """
    Searches through Gerrit's API for a repo using your search term.
    """
    pass

@cli.command('build', short_help='Find a Jenkins build.')
@click.argument('search_term')
@pass_context
# RFI: how do we take fancy input like grep? aka grep -ie "this|that"
#      see pipe in search term.
def find_build(ctx, search_term):
    """
    Searches through Jenkins API for pipelines using your search term.
    """
    pass


@cli.command('artifact', short_help='Find an artifact in artifactory')
@click.argument('search_term')
@pass_context
# RFI: how do we take fancy input like grep? aka grep -ie "this|that"
#      see pipe in search term.
def find_artifact(ctx, search_term):
    """
    Searches through Artifactory's API for artifacts using your search term.
    """
    pass


@cli.command('pipe', short_help='Find a Go deploy pipeline')
@click.argument('search_term')
@pass_context
# RFI: how do we take fancy input like grep? aka grep -ie "this|that"
#      see pipe in search term.
def find_pipe(ctx, search_term):
    """
    Searches through GO's API for pipelines using your search term.
    """
    pass
