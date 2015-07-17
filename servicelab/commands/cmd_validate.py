import click
from servicelab.stack import pass_context
from servicelab.utils import check_yaml


@click.group('validate', short_help='Validate resources.',
             add_help_option=True)
@pass_context
def cli(ctx):
    pass


@cli.command('yaml', short_help='Check yaml file syntax ')
@click.argument('file_name')
@pass_context
def validate_yaml(ctx, file_name):
    """
    This cmd function takes the yaml file and validates its syntax.
    """
    check_yaml.validate_syntax(file_name)
