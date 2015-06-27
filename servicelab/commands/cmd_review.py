import click
from servicelab.stack import pass_context


@click.group('review', short_help='Helps you work with Gerrit')
@pass_context
def cli(ctx):
    """
    Helps you work with Gerrit.
    """
    pass


@cli.command('inc', short_help='Find incoming reviews Gerrit.')
# RFI: Do we need search term? Should it be username or is that coming
#      coming from the config file / env var.s?
# @click.argument('search_term')
@pass_context
def review_inc(ctx):
    """
    Searches through Gerrit's API for incoming reviews for your username.
    """
    pass


@cli.command('out', short_help='Find outgoing reviews in Gerrit.')
@pass_context
def review_out(ctx):
    """
    Searches through Gerrit's API for outgoing reviews for your username.
    """
    pass


# RFI: Can we do +2 w/ the plus?
@cli.command('plustwo', short_help='Plus two gerrit change set.')
@click.argument('item')
@pass_context
def review_plustwo(ctx, item):
    """
    Approves and merges a gerrit change set.
    """
    pass


# RFI: Can we do +1 w/ the plus?
@cli.command('plusone', short_help='Plus one gerrit change set.')
@click.argument('item')
@pass_context
def review_plusone(ctx, item):
    """
    Approves, but does not merge a gerrit change set, which means change set
    requires another approver.
    """
    pass


@cli.command('--abandon', short_help='Abandon gerrit change set.')
@click.argument('item')
@pass_context
def review_ab(ctx, item):
    """
    Abandon a gerrit change set.
    """
    pass
