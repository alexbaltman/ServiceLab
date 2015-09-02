import click
from servicelab.stack import pass_context
from servicelab.utils import explain_utils


@click.group('explain', short_help='Provide high level explanations of servicelab',
             add_help_option=True)
@pass_context
def cli(ctx):
    pass


@cli.command('init', short_help='Compiles all data specified in slab_man_data.yaml'
                                ' into man page'
             )
@pass_context
def explain_init(ctx):
    """
    Grabs data from confluence pages and servicelab docs and leverages sphinx to
    converts them into a single man page that will be queried for high level info.
    """
    explain_utils.compile_man_page(ctx.path)


@cli.command('all', short_help='Navigate all high level topics '
                               'specified in the slab man page'
             )
@pass_context
def explain_all(ctx):
    """
    List all sections of the man page and allow the user to navigate to one of them
    """
    explain_utils.navigate_all(ctx.path)


@cli.command('list', short_help='Navigate to any high level '
                                'topic specified in the slab man page'
             )
@pass_context
def explain_list(ctx):
    """
    List all sections of the man page and allow the user to navigate to one of them
    """
    explain_utils.list_navigable_sections(ctx.path)


@cli.command('whatis', short_help='Accept a string to query all content, and let user'
                                  'navigate to the appropriate sections that matched'
             )
@click.argument('query')
@pass_context
def explain_whatis(ctx, query):
    """
    This cmd lets the user choose a section to navigate to based on how many times it
    contains the query keyword.
    """
    explain_utils.query(ctx.path, query)
