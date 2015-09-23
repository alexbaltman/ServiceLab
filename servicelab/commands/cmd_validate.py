"""
Stack functions to validate the YAML File syntax.
"""
import click

from servicelab.stack import pass_context
from servicelab.utils import yaml_utils


@click.group('validate', short_help='Validate resources.',
             add_help_option=True)
@pass_context
def cli(_):
    """
    Function to group stack validate commands.
    """
    pass


@cli.command('yaml', short_help='Check yaml file syntax ')
@click.argument('file_name')
@pass_context
def validate_yaml(_, file_name):
    """
    This cmd function takes the yaml file and validates its syntax.
    """
    yaml_utils.validate_syntax(file_name)
