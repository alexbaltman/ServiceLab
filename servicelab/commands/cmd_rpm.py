"""
Stack rpm commands to
1.  Download the rpm.
2.  Displays a rpm stats.
3.  Upload the rpm.
"""
import sys
import json
import time

import click
import requests

from servicelab.stack import pass_context
from servicelab.utils import pulp_utils
from servicelab.utils import logger_utils
from servicelab import settings

slab_logger = logger_utils.setup_logger(settings.verbosity, 'stack.rpm')


@click.group('rpm', short_help='RPM to work with.',
             add_help_option=True)
@click.pass_context
def cli(_):
    """
    stack rpm command
    """
    pass


@cli.command('stats', short_help='Display rpm stats from pulp repository')
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
    '--pulp-repo',
    help='Provide the pulp repo id ',
    required=True,
    default=None)
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def display_rpm_status(ctx,
                       rpm,
                       pulp_repo,
                       ip_address,
                       username,
                       password,
                       interactive):
    """
    Displays rpm stats.
    """
    slab_logger.info('Displaying rpm status')
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    if not password or not username:
        slab_logger.error("Username is %s and password is %s. "
                          "Please, set the correct value for both and retry." %
                          (username, password))
        sys.exit(1)
    url = "/pulp/api/v2/repositories/%s/search/units/" % (pulp_repo)
    payload = '{ "criteria": { "filters" : { "unit" : { "name" : "%s"}},'\
              ' "fields": { "unit": [ "name", "version" ] }, "type_ids":'\
              ' [ "rpm" ] } }' % (rpm)
    val = pulp_utils.post(url, ip_address, ctx, username, password, payload)
    slab_logger.log(25, 'Listing rpm stats for rpm : %s' % (rpm))
    slab_logger.log(25, json.dumps(json.loads(val), indent=4, sort_keys=True))


@cli.command('download', short_help='Download the rpm from pulp repository')
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
    '--pulp-repo',
    help='Provide the pulp repo id ',
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
                 pulp_repo,
                 rpm,
                 interactive):
    """
    Download the artifact.
    """
    slab_logger.info('Downloading rpm from pulp repo')
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    if not password or not username:
        slab_logger.error("Username is %s and password is %s. "
                          "Please, set the correct value for both and retry." %
                          (username, password))
        sys.exit(1)
    url = "/pulp/api/v2/distributors/search/"
    payload = '{"criteria":{"filters":{"repo_id":{"$eq": "%s"}}}}' % (pulp_repo)
    val = pulp_utils.post(url, ip_address, ctx, username, password, payload)
    res_json = json.loads(val)
    repo_json = filter(lambda x: x['repo_id'] == pulp_repo, res_json)

    if len(repo_json) > 0:
        url = "/pulp/api/v2/repositories/%s/search/units/" % (pulp_repo)
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
            slab_logger.log(25, "Starting download from {0}".format(download_url))
            req = requests.get(download_url, verify=False)
            with open(rpm_json[0]['metadata']['filename'], 'wb') as rpm_file:
                for chunk in req.iter_content(chunk_size=1024):
                    if chunk:
                        rpm_file.write(chunk)
                        slab_logger.log(25, ".", nl=False)
            slab_logger.log(25, "\nDownload complete.")
            return
        else:
            slab_logger.error(
                "Rpm %s could not be download since it was"
                " not found in repo : %s" % (rpm, pulp_repo))
    else:
        slab_logger.error(
            "Repo with id %s does not exist. Unable to download the rpm." %
            (pulp_repo))


@cli.command('upload', short_help='Upload the rpm to pulp repository')
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
    '--pulp-repo',
    help='Provide the pulp repo id ',
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
               pulp_repo,
               filepath,
               username,
               password,
               interactive):
    """
    Upload the rpm.
    """
    slab_logger.info('Uploading rpm to pulp repo')
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    if not password or not username:
        slab_logger.error("Username is %s and password is %s. "
                          "Please, set the correct value for both and retry." %
                          (username, password))
        sys.exit(1)
    slab_logger.log(25, "Starting upload of {0}".format(filepath))
    url = "/pulp/api/v2/content/uploads/"
    val = pulp_utils.post(url, ip_address, ctx, username, password, "")
    res_json = json.loads(val)
    slab_logger.log(25, "Got upload id : %s " % (res_json['upload_id']))
    rpm_file = open(filepath, 'rb')
    offset = 0
    while True:
        chunk = rpm_file.read(100000)
        if chunk:
            put_url = "%s%s/%s/" % (url, res_json['upload_id'], offset)
            offset = offset + 100000
            slab_logger.log(25, ".", nl=False)
            val = pulp_utils.put(put_url, ip_address,
                                 ctx, username, password, chunk)
            slab_logger.log(25, ".", nl=False)
        else:
            break
    rpm_file.close()
    payload = '{"override_config": {}, "unit_type_id": "rpm", "upload_id": '\
              '"%s", "unit_key": {}, "unit_metadata": '\
              '{"checksum_type": null}}' % (res_json['upload_id'])
    post_url = '/pulp/api/v2/repositories/%s/actions'\
               '/import_upload/' % (pulp_repo)
    slab_logger.log(25, "\nImporting rpm to server for upload id: %s "
                    % (res_json['upload_id']))
    time.sleep(2)
    val = pulp_utils.post(post_url, ip_address, ctx, username,
                          password, payload)
    payload = '{"override_config": {},  "id" : "yum_distributor"}'
    post_url = "/pulp/api/v2/repositories/%s/actions/publish/" % (pulp_repo)
    slab_logger.log(25, "Publishing rpm to server for upload id: %s "
                    % (res_json['upload_id']))
    val = pulp_utils.post(post_url, ip_address, ctx, username,
                          password, payload)
    slab_logger.log(25, "Upload process completed for rpm {0}."
                    "\nGot response from server : ".format(filepath))
    slab_logger.log(25, val)
