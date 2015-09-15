from servicelab.stack import pass_context
from servicelab.utils import jenkins_utils
import click
import requests
import json
import urllib2
import urllib
import os
from requests.auth import HTTPBasicAuth
from BeautifulSoup import BeautifulSoup
import subprocess


@click.group('artifact', short_help='Artifact to work with.',
             add_help_option=True)
@click.pass_context
def cli(ctx):
    pass


@cli.command('stats', short_help='Display artifact stats')
@click.argument('artifact_url', required=True)
@click.option(
    '-m',
    '--artuser',
    help='Provide artifactory username',
    required=True)
@click.option(
    '-n',
    '--artpass',
    help='Provide artifactory password',
    required=True)
@pass_context
def display_artifact_status(
        ctx,
        artifact_url,
        artuser,
        artpass):
    """
    Displays a artifact stats.
    """
    requests.packages.urllib3.disable_warnings()
    res = requests.get(artifact_url, auth=HTTPBasicAuth(artuser, artpass))
    click.echo(res.content)


@cli.command('download', short_help='Download the artifact')
@click.argument('artifact_url', required=True)
@click.option(
    '-m',
    '--artuser',
    help='Provide artifactory username',
    required=True)
@click.option(
    '-n',
    '--artpass',
    help='Provide artifactory password',
    required=True)
@click.option(
    '-p',
    '--dest',
    help='Provide destination folder',
    required=True)
@pass_context
def download_artifact(
        ctx,
        dest,
        artifact_url,
        artuser,
        artpass):
    """
    Download the artifact.
    """
    requests.packages.urllib3.disable_warnings()
    res = requests.get(artifact_url, auth=HTTPBasicAuth(artuser, artpass))
    downloadUri = json.loads(res.content)["downloadUri"]
    fileName = downloadUri.split('/')[-1]
    click.echo("Starting download of {0} to {1}".format(downloadUri, dest))
    with open(os.path.join(dest, fileName), 'wb') as handle:
        response = requests.get(
            downloadUri,
            stream=True,
            auth=HTTPBasicAuth(
                artuser,
                artpass))

        if not response.ok:
            click.echo("Error occured downloading")
            return

        handle.write(response.text)

    click.echo("Download Complete................ %s" % response.text)


@cli.command('upload', short_help='Upload the artifact')
@click.argument('artifact_url', required=True)
@click.option(
    '-m',
    '--artuser',
    help='Provide artifactory username',
    required=True)
@click.option(
    '-n',
    '--artpass',
    help='Provide artifactory password',
    required=True)
@click.option(
    '-q',
    '--filepath',
    help='Provide file path',
    required=True)
@pass_context
def upload_artifact(
        ctx,
        filepath,
        artifact_url,
        artuser,
        artpass):
    """
    Upload the artifact.
    """
    click.echo("Starting upload of {0} to {1}".format(filepath, artifact_url))
    subprocess.call([
        'curl',
        '-X',
        'PUT',
        '--upload-file',
        filepath,
        artifact_url,
        '-u',
        "{0}:{1}".format(artuser, artpass)
    ])
