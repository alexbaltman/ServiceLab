import os
import re
import click
import logging
from servicelab.stack import pass_context
from servicelab.utils import ccsdata_utils


@click.group('list', short_help='You can list available pipeline objects',
             add_help_option=True)
@pass_context
def cli(ctx):
    """
    Listing sites and services of ccs-data
    """
    pass


@cli.command('sites', short_help="List sites")
@pass_context
def list_sites(ctx):
    '''
    Here we list all the sites using the git submodule ccs-data.
    '''
    ctx.logger.debug("Gathered sites from ccs-data submodule.")
    for item in ccsdata_utils.list_envs_or_sites(ctx.path, "sites"):
        click.echo(item)


@cli.command('envs', short_help="List environments")
@pass_context
def list_envs(ctx):
    '''
    Here we list all the environments using the git submodule ccs-data.
    '''
    ctx.logger.debug("Gathered environments from ccs-data submodule.")
    for item in ccsdata_utils.list_envs_or_sites(ctx.path, "envs"):
        click.echo(item)


@cli.command('reviews', short_help='List reviews in Gerrit.')
# RFI: Is using an option here 100% the right way to go or nest
#      the command set again (?)
@click.option('ino', '--out', help='List the outgoing reviews I have.')
@click.option('ino', '--inc', help='List the incoming reviews I have.')
@pass_context
def list_repo(ctx, ino):
    """
    Lists repos using Gerrit's API.
    """
    click.echo('Listing reviews in Gerrit.')


# RFI: should there be more intelligence here than a blankey list?
@cli.command('repos', short_help='List repos in Gerrit.')
@pass_context
def list_repos(ctx):
    """
    Lists repos using Gerrit's API.
    """
    click.echo('Listing repos in Gerrit.')


# RFI: should there be more intelligence here than a blankey list?
@cli.command('builds', short_help='List a Jenkins\' builds.')
@pass_context
def list_build(ctx):
    """
    Searches through Jenkins API for pipelines using your search term.
    """
    click.echo('Listing builds in Jenkins.')


# RFI: should there be more intelligence here than a blankey list?
@cli.command('artifacts', short_help='List artifacts in artifactory')
@pass_context
def list_artifact(ctx):
    """
    Lists artifacts using Artifactory's API.
    """
    click.echo('Listing artifacts in Artifactory.')


# RFI: should there be more intelligence here than a blankey list?
@cli.command('pipes', short_help='List Go deployment pipelines')
@pass_context
def list_pipe(ctx):
    """
    Lists piplines using GO's API.
    """
    click.echo('Listing pipeliness in GO.')
