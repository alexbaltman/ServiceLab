"""
Stack rpm commands to
1.  Download the rpm.
2.  Displays a rpm stats.
3.  Upload the rpm.
"""
import json
import time

import click
import requests

from servicelab.stack import pass_context
from servicelab.utils import pulp_utils


@click.group('rpm', short_help='RPM to work with.',
             add_help_option=True)
@click.pass_context
def cli(_):
    """
    stack rpm command
    """
    pass


@cli.command('stats', short_help='Display rpm stats')
@click.argument('rpm', required=True)
@click.option('-u',
              '--username',
              help='Provide artifactory username')
@click.option('-p',
              '--password',
              help='Provide artifactory password')
@click.option(
    '-ip',
    '--ip_address',
    help='Provide the pulp server url ip address and port '
         'no in format http://<ip:portno>.',
    default=None,
    callback=pulp_utils.validate_pulp_ip_cb)
@click.option(
    '-s',
    '--site',
    help='Provide the site id ',
    required=True,
    default=None)
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def display_rpm_status(ctx,
                       rpm,
                       site,
                       ip_address,
                       username,
                       password,
                       interactive):
    """
    Displays rpm stats.
    """
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    url = "/pulp/api/v2/repositories/%s/search/units/" % (site)
    payload = '{ "criteria": { "filters" : { "unit" : { "name" : "%s"}},'\
              ' "fields": { "unit": [ "name", "version" ] }, "type_ids":'\
              ' [ "rpm" ] } }' % (rpm)
    val = pulp_utils.post(url, ip_address, ctx, username, password, payload)
    click.echo('Listing rpm stats for rpm : %s' % (rpm))
    click.echo(json.dumps(json.loads(val), indent=4, sort_keys=True))


@cli.command('download', short_help='Download the rpm')
@click.argument('rpm', required='True')
@click.option('-u',
              '--username',
              help='Provide pulp username')
@click.option('-p',
              '--password',
              help='Provide pulp password')
@click.option(
    '-ip',
    '--ip_address',
    help='Provide the pulp server url ip address and port '
         'no in format http://<ip:portno>.',
    default=None,
    callback=pulp_utils.validate_pulp_ip_cb)
@click.option(
    '-s',
    '--site',
    help='Provide the site id ',
    required=True,
    default=None)
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def download_rpm(ctx, username,
                 password,
                 ip_address,
                 site,
                 rpm,
                 interactive):
    """
    Download the artifact.
    """
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    url = "/pulp/api/v2/distributors/search/"
    payload = '{"criteria":{"filters":{"repo_id":{"$eq": "%s"}}}}' % (site)
    val = pulp_utils.post(url, ip_address, ctx, username, password, payload)
    res_json = json.loads(val)
    repo_json = filter(lambda x: x['repo_id'] == site, res_json)

    if len(repo_json) > 0:
        url = "/pulp/api/v2/repositories/%s/search/units/" % (site)
        payload = '{ "criteria": { "filters" : { "unit" : { "name" : "%s"}},'\
                  ' "fields": { "unit": [ "name", "filename" ] },'\
                  ' "type_ids": [ "rpm" ] } }' % (rpm)
        val = pulp_utils.post(url, ip_address, ctx, username,
                              password, payload)
        rpm_json = json.loads(val)
        if len(rpm_json) > 0:
            download_url = '%s/pulp/repos/%s/%s' % (ip_address,
                                                    repo_json[0]
                                                    ['config']
                                                    ['relative_url'],
                                                    rpm_json[0]['metadata']
                                                    ['filename'])
            click.echo("Starting download from {0}".format(download_url))
            req = requests.get(download_url, verify=False)
            with open(rpm_json[0]['metadata']['filename'], 'wb') as rpm_file:
                for chunk in req.iter_content(chunk_size=1024):
                    if chunk:
                        rpm_file.write(chunk)
                        click.echo(".", nl=False)
            click.echo("\nDownload complete.")
            return
        else:
            click.echo(
                "Rpm %s could not be download since it was"
                " not found in repo : %s" % (rpm, site))
    else:
        ctx.logger.error(
            "Repo with id %s does not exist. Unable to download the rpm." %
            (site))


@cli.command('upload', short_help='Upload the rpm')
@click.option('-u',
              '--username',
              help='Provide pulp username')
@click.option('-p',
              '--password',
              help='Provide pulp password')
@click.option(
    '-ip',
    '--ip_address',
    help='Provide the pulp server url ip address and port '
         'no in format http://<ip:portno>.',
    default=None,
    callback=pulp_utils.validate_pulp_ip_cb)
@click.option(
    '-s',
    '--site',
    help='Provide the site id ',
    required=True,
    default=None)
@click.option('-f',
              '--filepath',
              help='Provide file path to rpm',
              required=True)
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def upload_rpm(ctx, ip_address,
               site,
               filepath,
               username,
               password,
               interactive):
    """
    Upload the rpm.
    """
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    click.echo("Starting upload of {0}".format(filepath))
    url = "/pulp/api/v2/content/uploads/"
    val = pulp_utils.post(url, ip_address, ctx, username, password, "")
    res_json = json.loads(val)
    click.echo("Got upload id : %s " % (res_json['upload_id']))
    rpm_file = open(filepath, 'rb')
    offset = 0
    while True:
        chunk = rpm_file.read(100000)
        if chunk:
            put_url = "%s%s/%s/" % (url, res_json['upload_id'], offset)
            offset = offset + 100000
            click.echo(".", nl=False)
            val = pulp_utils.put(put_url, ip_address,
                                 ctx, username, password, chunk)
            click.echo(".", nl=False)
        else:
            break
    rpm_file.close()
    payload = '{"override_config": {}, "unit_type_id": "rpm", "upload_id": '\
              '"%s", "unit_key": {}, "unit_metadata": '\
              '{"checksum_type": null}}' % (res_json['upload_id'])
    post_url = '/pulp/api/v2/repositories/%s/actions'\
               '/import_upload/' % (site)
    click.echo(
        "\nImporting rpm to server for upload id: %s " %
        (res_json['upload_id']))
    time.sleep(2)
    val = pulp_utils.post(post_url, ip_address, ctx, username,
                          password, payload)
    payload = '{"override_config": {},  "id" : "yum_distributor"}'
    post_url = "/pulp/api/v2/repositories/%s/actions/publish/" % (site)
    click.echo(
        "Publishing rpm to server for upload id: %s " %
        (res_json['upload_id']))
    val = pulp_utils.post(post_url, ip_address, ctx, username,
                          password, payload)
    click.echo(
        "Upload process completed for rpm {0}."
        "\nGot response from server : ".format(filepath))
    click.echo(val)
