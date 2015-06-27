import click
from servicelab.stack import pass_context


@click.group('show', short_help='Helps you show the details of a \
             pipeline resource.')
@pass_context
def cli(ctx):
    """
    Helps you show the details of resources in the SDLC pipeline.
    """
    pass

@cli.command('repo', short_help='Show the details of a repo in Gerrit.')
# item is generic right now until we can figure out exactly what that\'s
# going to look like.
@click.argument('item')
@pass_context
def show_repo(ctx, item):
    """
    Shows the details of git repos using Gerrit's API.
    """
    click.echo('Showing details of repo %s' % item)


@cli.command('review', short_help='Show the details of a review in Gerrit.')
@click.argument('item')
@pass_context
def show_review(ctx, item):
    """
    Shows the details ofa review using Gerrit's API.
    """
    click.echo('Showing diff of review %s' % item)


@cli.command('build', short_help='Show the details of a build in Jenkins.')
@click.argument('item')
@pass_context
def show_build(ctx, item):
    """
    Shows the details of a build in Jekins.
    """
    click.echo('Showing details of build %s' % item)


@cli.command('artifact', short_help='Show the details of an artifact \
              in artifactory.')
@click.argument('item')
@pass_context
def show_artifact(ctx, item):
    """
    Show the details of an artifact using Artifactory's API.
    """
    click.echo('Showing details of artifact %s' % item)


@cli.command('pipe', short_help='Show the details of a GO deploy pipeline')
@click.argument('item')
@pass_context
def show_pipe(ctx, item):
    """
    Show the details of a deployment pipline using GO's API.
    """
    click.echo('Showing details of pipeline %s' % item)
