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
              '--user',
              help='Provide artifactory username',
              required=True)
@click.option('-p',
              '--password',
              help='Provide artifactory password',
              required=True)
@pass_context
def display_artifact_status(_,
                            url,
                            user,
                            password):
    """
    Displays a artifact stats.
    """
    requests.packages.urllib3.disable_warnings()
    res = requests.get(url, auth=HTTPBasicAuth(user, password))
    click.echo(res.content)


@cli.command('download', short_help='Download the artifact')
@click.argument('url', required=True)
@click.option('-u',
              '--user',
              help='Provide artifactory username',
              required=True)
@click.option('-p',
              '--password',
              help='Provide artifactory password',
              required=True)
@click.option('-d',
              '--destintaion',
              help='Provide destination folder',
              required=True)
@pass_context
def download_artifact(_,
                      destination,
                      url,
                      user,
                      password):
    """
    Download the artifact.
    """
    requests.packages.urllib3.disable_warnings()
    res = requests.get(url, auth=HTTPBasicAuth(user, password))
    download_uri = json.loads(res.content)["downloadUri"]

    file_name = download_uri.split('/')[-1]
    click.echo("Starting download of {0} to {1}".format(download_uri, destination))
    with open(os.path.join(destination, file_name), 'wb') as handle:
        response = requests.get(download_uri,
                                stream=True,
                                auth=HTTPBasicAuth(user, password))

        if not response.ok:
            click.echo("Error occured during downloading")
            return

        handle.write(response.text)

    click.echo("Download Complete" % response.text)


@cli.command('upload', short_help='Upload the artifact')
@click.argument('url', required=True)
@click.option('-u',
              '--user',
              help='Provide artifactory username',
              required=True)
@click.option('-p',
              '--password',
              help='Provide artifactory password',
              required=True)
@click.option('-q',
              '--filepath',
              help='Provide file path',
              required=True)
@pass_context
def upload_artifact(_,
                    filepath,
                    url,
                    user,
                    password):
    """
    Upload the artifact.
    """
    click.echo("Starting upload of {0} to {1}".format(filepath, url))
    subprocess.call(['curl',
                     '-X',
                     'PUT',
                     '--upload-file',
                     filepath,
                     url,
                     '-u',
                     "{0}:{1}".format(user, password)])
