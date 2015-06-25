import click
from servicelab.stack import pass_context


@click.group('list', short_help='You can list available pipeline objects')
             add_help_option=True)
@pass_context
def list(ctx):
    """
    Helps you list resources in the SDLC pipeline.
    """
    pass


# RFI: should there be more intelligence here than a blankey list?
@list.command('repo', short_help='List repos in Gerrit.')
@pass_context
def list_repo(ctx):
    """
    Lists repos using Gerrit's API.
    """
    pass


# RFI: should there be more intelligence here than a blankey list?
@list.command('reviews', short_help='List reviews in Gerrit.')
# RFI: Is using an option here 100% the right way to go or nest
#      the command set again (?)
@list.option('--out', short_help='List the outgoing reviews I have.')
@list.option('--inc', short_help='List the incoming reviews I have.')
@pass_context
def list_repo(ctx):
    """
    Lists repos using Gerrit's API.
    """
    pass


# RFI: should there be more intelligence here than a blankey list?
@list.command('build', short_help='List a Jenkins\' builds.')
@pass_context
def list_build(ctx):
    """
    Searches through Jenkins API for pipelines using your search term.
    """
    pass


# RFI: should there be more intelligence here than a blankey list?
@list.command('artifact', short_help='List artifacts in artifactory')
@pass_context
def list_artifact(ctx):
    """
    Lists artifacts using Artifactory's API.
    """
    pass


# RFI: should there be more intelligence here than a blankey list?
@list.command('pipe', short_help='List Go deployment pipelines')
@pass_context
def list_pipe(ctx, search_term):
    """
    Lists piplines using GO's API.
    """
    pass
