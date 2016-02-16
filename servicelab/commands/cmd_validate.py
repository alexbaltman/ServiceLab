"""
Stack functions to validate the YAML File syntax.
"""
import click

from servicelab.stack import pass_context
from servicelab.utils import yaml_utils
from servicelab.utils import logger_utils
from servicelab import settings

slab_logger = logger_utils.setup_logger(settings.verbosity, 'stack.validate')


@click.group('validate',
             short_help='Help validate resources being used in the pipeline.',
             add_help_option=True)
@pass_context
def cli(_):
    """
    Function to group stack validate commands.
    """
    pass


@cli.command('yaml', short_help='Verify the yaml syntax for the file is good.')
@click.argument('file_name')
@pass_context
def validate_yaml(_, file_name):
    """
    This cmd function takes the yaml file and validates its syntax.
    """
    slab_logger.info('Validating syntax of %s' % file_name)
    yaml_utils.validate_syntax(file_name)
