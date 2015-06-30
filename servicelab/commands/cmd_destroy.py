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
@click.argument('vm_name')
@pass_context
def destroy_vm(ctx, vm_name):
    """

    """
    click.echo('Destroying vm %s in ccs-data only' % vm_name)


@cli.command('repo', short_help='Destroy a repo in Gerrit.')
@click.argument('repo_name')
@pass_context
def destory_repo(ctx, repo_name):
    """
    Destroys a repo in Gerrit.
    """
    click.echo('Destroying repo %s in Artifactory' % repo_name)


@cli.command('artifact', short_help='Destroy an artifact in artifactory.')
@click.argument('artifact_name')
@pass_context
def destory_artifact(ctx, artifact_name):
    """
    Destroys an artifact in Artifactory.
    """
    click.echo('Destroying artifact %s in Artifactory' % artifact_name)
