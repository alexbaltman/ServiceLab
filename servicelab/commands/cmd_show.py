import click
from servicelab.stack import pass_context


@click.group('find', short_help='Helps you search
             pipeline resources.', invoke_without_command=True,
             add_help_option=True)
@pass_context
def find(ctx):
    """
    Helps you search for resources in the SDLC pipeline.
    """
    pass


@create.command('repo', short_help='Find a repo in Gerrit')
@create.argument('search_term')
@pass_context
def find_pipe(ctx, search_term):
    """
    Searches through Gerrit's API for pipelines using your search term.
    """
    pass


@create.command('pipe', short_help='Find a Go deploy pipeline')
@create.argument('search_term')
@create.option('-i', '--interactive', help='Helps you search for go deploy
               pipelines interactively')
@pass_context
def find_pipe(ctx, search_term):
    """
    Searches through GO's API for pipelines using your search term.
    """

@create.command('pipe', short_help='Find a Go deploy pipeline')
@create.argument('search_term')
@create.option('-i', '--interactive', help='Helps you search for go deploy
               pipelines interactively')
@pass_context
def find_pipe(ctx, search_term):
    """
    Searches through GO's API for pipelines using your search term.
    """

@create.command('pipe', short_help='Find a Go deploy pipeline')
@create.argument('search_term')
@create.option('-i', '--interactive', help='Helps you search for go deploy
               pipelines interactively')
@pass_context
def find_pipe(ctx, search_term):
    """
    Searches through GO's API for pipelines using your search term.
    """


