"""
Stack artifact commands to
1.  Download the artifact.
2.  Displays a artifact stats.
3.  Upload the artifact.
"""
import os
import json
import subprocess

import click
import requests

from requests.auth import HTTPBasicAuth
from servicelab.stack import pass_context


@click.group('artifact', short_help='Artifact to work with.',
             add_help_option=True)
@click.pass_context
def cli(_):
    """
    stack artifact command
    """
    pass


@cli.command('stats', short_help='Display artifact stats')
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
    requests.packages.urllib3.disable_warnings()
    res = requests.get(url, auth=HTTPBasicAuth(username, password))
    click.echo(res.content)


@cli.command('download', short_help='Download the artifact')
@click.argument('url', required=True)
@click.option('-u',
              '--username',
              help='Provide artifactory username')
@click.option('-p',
              '--password',
              help='Provide artifactory password')
@click.option('-d',
              '--destintaion',
              help='Provide destination folder',
              required=True)
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
    click.echo("Starting download of {0} to {1}".format(download_uri, destination))
    with open(os.path.join(destination, file_name), 'wb') as handle:
        response = requests.get(download_uri,
                                stream=True,
                                auth=HTTPBasicAuth(username, password))

        if not response.ok:
            click.echo("Error occured during downloading")
            return

        handle.write(response.text)

    click.echo("Download Complete" % response.text)


@cli.command('upload', short_help='Upload the artifact')
@click.argument('url', required=True)
@click.option('-u',
              '--username',
              help='Provide artifactory username')
@click.option('-p',
              '--password',
              help='Provide artifactory password')
@click.option('-q',
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
    click.echo("Starting upload of {0} to {1}".format(filepath, url))
    subprocess.call(['curl',
                     '-X',
                     'PUT',
                     '--upload-file',
                     filepath,
                     url,
                     '-u',
                     "{0}:{1}".format(username, password)])
