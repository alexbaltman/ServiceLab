import click
from servicelab.stack import pass_context


@click.group('destroy', short_help='Destroys VMs.')
@pass_context
def cli(ctx):
    """
    Destroys vms
    """
    pass


@cli.command('vm', short_help='')
@click.argument('name')
@pass_context
def destroy_vm(ctx, name):
    """

    """
    pass


@cli.command('repo', short_help='Destroy a repo in Gerrit.')
@click.argument('name')
@pass_context
def destory_repo(ctx, name):
    """
    Destroys a repo in Gerrit.
    """
    pass


@cli.command('artifact', short_help='Destroy an artifact in artifactory.')
@click.argument('name')
@pass_context
def destory_artifact(ctx, name):
    """
    Destroys an artifact in Artifactory.
    """
    pass
