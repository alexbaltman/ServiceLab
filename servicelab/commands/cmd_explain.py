"""
Stack explain command provides
    1. grab
       Grabs data from confluence pages and servicelab docs and leverages sphinx to
       converts them into a single man page that will be queried for high level info.
    2. all
       To list all sections of the man page and allow the user to navigate to one of them
    3. list
       To list all sections of the man page and allow the user to navigate to one of them
    4. whatis
       This cmd lets the user choose a section to navigate to based on how many times it
       contains the query keyword.
"""
import click
from servicelab.stack import pass_context
from servicelab.utils import explain_utils


@click.group('explain', short_help='Provide high level explanations of servicelab.',
             add_help_option=True)
@pass_context
def cli(_):
    """
    Stack decorator for explain command.
    """
    pass


@cli.command('init',
             short_help='Compiles all wiki documentation in slab_man_data.yaml'
                        ' into a man page.')
@click.option('-u',
              '--username',
              help='Provide artifactory server username',
              default=None,
              required=False)
@click.option('-p',
              '--password',
              default=None,
              help='Provide artifactory server password',
              required=False)
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def explain_init(ctx, username, password, interactive):
    """
    Grabs data from confluence pages and servicelab docs and leverages sphinx to
    converts them into a single man page that will be queried for high level info.
    """
    ctx.logger.info('Building man page from servicelab docs')
    try:
        if not username:
            username = ctx.get_username()
        if not password:
            password = ctx.get_password(interactive)
        explain_utils.compile_man_page(ctx.path, username, password)
    except Exception as ex:
        ctx.logger.error(str(ex))
        ctx.logger.error("Please check username/password and try again")


@cli.command('all', short_help='Navigate all high level topics '
                               'specified in the slab man page.')
@pass_context
def explain_all(ctx):
    """
    List all sections of the man page and allow the user to navigate to one of them
    """
    ctx.logger.info('Listing man page sections for user selection')
    try:
        explain_utils.navigate_all(ctx.path)
    except Exception as ex:
        ctx.logger.error(str(ex))
        ctx.logger.error("Try 'stack explain init' to run all explain subcommands")


@cli.command('list', short_help='Navigate to any high level '
                                'topic specified in the slab man page')
@pass_context
def explain_list(ctx):
    """
    List all sections of the man page and allow the user to navigate to one of them
    """
    ctx.logger.info('Listing man page sections for user selection')
    try:
        explain_utils.list_navigable_sections(ctx.path)
    except Exception as ex:
        ctx.logger.error(str(ex))
        ctx.logger.error("Try 'stack explain init' to run all explain subcommands")


@cli.command('whatis', short_help='Accept a string to query all documents and create'
                                  ' a navigation menu by expected relevancy.')
@click.argument('query')
@pass_context
def explain_whatis(ctx, query):
    """
    This cmd lets the user choose a section to navigate to based on how many times it
    contains the query keyword.
    """
    ctx.logger.info('Selecting section based on query matches')
    try:
        explain_utils.query(ctx.path, query)
    except Exception as ex:
        ctx.logger.error(str(ex))
        ctx.logger.error("Try 'stack explain init' to run all explain subcommands")
