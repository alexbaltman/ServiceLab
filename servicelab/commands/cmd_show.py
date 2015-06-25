import click
from servicelab.stack import pass_context


@click.group('show', short_help='Helps you show the details of a
             pipeline resource.')
@pass_context
def show(ctx):
    """
    Helps you show the details of resources in the SDLC pipeline.
    """
    pass


@show.command('repo', short_help='Show the details of a repo in Gerrit.')
# item is generic right now until we can figure out exactly what that\'s
# going to look like.
@show.argument('item')
@pass_context
def show_repo(ctx, item):
    """
    Shows the details of git repos using Gerrit's API.
    """
    pass


@show.command('review', short_help='Show the details of a review in Gerrit.')
@show.argument('item')
@pass_context
def show_review(ctx, item):
    """
    Shows the details ofa review using Gerrit's API.
    """
    pass


@show.command('build', short_help='Show the details of a build in Jenkins.')
@show.argument('item')
@pass_context
def show_build(ctx, item):
    """
    Shows the details of a build in Jekins.
    """
    pass


@show.command('artifact', short_help='Show the details of an artifact
              in artifactory')
@show.argument('item')
@pass_context
def show_artifact(ctx, item):
    """
    Show the details of an artifact using Artifactory's API.
    """
    pass


@show.command('pipe', short_help='Show the details of a GO deploy pipeline')
@show.argument('item')
@pass_context
def show_pipe(ctx, item):
    """
    Show the details of a deployment pipline using GO's API.
    """
    pass
