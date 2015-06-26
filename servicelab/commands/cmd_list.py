import click
from servicelab.stack import pass_context


@click.group('list', short_help='You can list available pipeline objects',
             add_help_option=True)
@pass_context
def cli(ctx):
    """
    Helps you list resources in the SDLC pipeline.
    """
    pass


# RFI: should there be more intelligence here than a blankey list?
@cli.command('repos', short_help='List repos in Gerrit.')
@pass_context
def list_repo(ctx):
    """
    Lists repos using Gerrit's API.
    """
    pass


# RFI: should there be more intelligence here than a blankey list?
@cli.command('reviews', short_help='List reviews in Gerrit.')
# RFI: Is using an option here 100% the right way to go or nest
#      the command set again (?)
@click.option('--out', help='List the outgoing reviews I have.')
@click.option('--inc', help='List the incoming reviews I have.')
@pass_context
def list_repo(ctx):
    """
    Lists repos using Gerrit's API.
    """
    pass


# RFI: should there be more intelligence here than a blankey list?
@cli.command('builds', short_help='List a Jenkins\' builds.')
@pass_context
def list_build(ctx):
    """
    Searches through Jenkins API for pipelines using your search term.
    """
    pass


# RFI: should there be more intelligence here than a blankey list?
@cli.command('artifacts', short_help='List artifacts in artifactory')
@pass_context
def list_artifact(ctx):
    """
    Lists artifacts using Artifactory's API.
    """
    pass


# RFI: should there be more intelligence here than a blankey list?
@cli.command('pipes', short_help='List Go deployment pipelines')
@pass_context
def list_pipe(ctx, search_term):
    """
    Lists piplines using GO's API.
    """
    pass
