"""
Stack artifact commands to
1.  Download an artifact.
2.  Display artifact statistics.
3.  Upload an artifact.
"""
import os
import json
import subprocess

import click
import requests

from requests.auth import HTTPBasicAuth
from servicelab.stack import pass_context
from servicelab.utils import logger_utils
from servicelab import settings

slab_logger = logger_utils.setup_logger(settings.verbosity, 'stack.artifact')


@click.group('artifact', short_help='Work with artifacts from artifactory with this command'
             ' subset.', add_help_option=True)
@click.pass_context
def cli(_):
    """
    stack artifact command
    """
    pass


@cli.command('stats', short_help='Display individual artifact statistics in Artifactory.')
@click.argument('url', required=True)
@click.option('-u',
              '--username',
              help='Provide artifactory username')
@click.option('-p',
              '--password',
              help='Provide artifactory password')
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def display_artifact_status(ctx,
                            url,
                            username,
                            password,
                            interactive):
    """
    Displays a artifact stats.
    """
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    if not password or not username:
        slab_logger.error("Username is %s and password is %s. "
                          "Please, set the correct value for both and retry." %
                          (username, password))
        sys.exit(1)
    requests.packages.urllib3.disable_warnings()
    res = requests.get(url, auth=HTTPBasicAuth(username, password))
    slab_logger.log(25, res.content)


@cli.command('download', short_help='Download an artifact from Artifactory.')
@click.argument('url', required=True)
@click.option('-u',
              '--username',
              help='Provide artifactory username')
@click.option('-p',
              '--password',
              help='Provide artifactory password')
@click.option('-d',
              '--destination',
              help='Provide destination folder',
              default=".")
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def download_artifact(ctx,
                      destination,
                      url,
                      username,
                      password,
                      interactive):
    """
    Download the artifact.
    """
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    requests.packages.urllib3.disable_warnings()
    res = requests.get(url, auth=HTTPBasicAuth(username, password))
    download_uri = json.loads(res.content)["downloadUri"]

    file_name = download_uri.split('/')[-1]
    slab_logger.info("Starting download of {0} to {1}. It might "
                     "take a few minutes.".format(download_uri, destination))
    with open(os.path.join(destination, file_name), 'wb') as handle:
        response = requests.get(download_uri,
                                stream=True,
                                auth=HTTPBasicAuth(username, password))

        if not response.ok:
            slab_logger.error("Error occured during downloading")
            return

        handle.write(response.content)

    slab_logger.info("Download Complete")


@cli.command('upload', short_help='Upload an artifact to Artifactory.')
@click.argument('url', required=True)
@click.option('-u',
              '--username',
              help='Provide artifactory username')
@click.option('-p',
              '--password',
              help='Provide artifactory password')
@click.option('-f',
              '--filepath',
              help='Provide file path',
              required=True)
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def upload_artifact(ctx,
                    filepath,
                    url,
                    username,
                    password,
                    interactive):
    """
    Upload the artifact.
    """
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    if not password or not username:
        slab_logger.error("Username is %s and password is %s. "
                          "Please, set the correct value for both and retry." %
                          (username, password))
    slab_logger.info("Starting upload of {0} to {1}".format(filepath, url))
    subprocess.call(['curl',
                     '-X',
                     'PUT',
                     '--upload-file',
                     filepath,
                     url,
                     '-u',
                     "{0}:{1}".format(username, password)])
    slab_logger.info('Completed upload')
