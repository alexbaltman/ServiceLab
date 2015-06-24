import click
from servicelab.stack import pass_context


@click.group('create', short_help='Creates a pipeline resources to work with.',
             invoke_without_command=True, add_help_option=True)
@click.pass_context
def create(ctx):
    pass


@create.command('repo')
@create.argument('name')
@create.option('-i', '--interactive',)
@create.option('-t', '--type',)
@pass_context
def repo_new(ctx, name):
    """
    Creates a repository in gerrit
    production, does 1st commit, sets up
    directory structure, and creates .nimbus.yml
    """
    click.echo('creating git repository %s ...' % name)

