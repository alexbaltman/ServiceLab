"""
Utility functions for go
"""
import sys
import time
import copy

import logging
import click
import requests
import xml.etree.ElementTree as ET
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup


# create logger
GOCD_UTILS_LOGGER = logging.getLogger('click_application')
logging.basicConfig()


def get_config(config_xmlurl, auth=None):
    """
    Retrieves the go config

    Attributes
        config_xmlurl
        auth
    """
    click.echo("Retrieving go config")
    if auth:
        req = requests.get(config_xmlurl, auth=auth)
    else:
        req = requests.get(config_xmlurl)
    if req.status_code == 200:
        try:
            root = ET.fromstring(req.text)
        except requests.ConnectionError as ex:
            click.echo("Failure parsing xml from request" + ex)
            sys.exit(1)
    else:
        click.echo("Request failed")
        sys.exit(1)

    return (req.headers['x-cruise-config-md5'], root)


def push_config(config_xmlurl, md5, xmlfile, auth=None):
    """
    Uploading go config

    Attributes:
        config_xmlurl
        md5
        xmlfile
        auth
    """
    click.echo("Uploading go config")
    payload = {
        'md5': md5,
        'xmlFile': xmlfile
    }

    if auth:
        req = requests.post(config_xmlurl,
                            auth=auth, data=payload)
    else:
        req = requests.post(config_xmlurl, data=payload)
    if req.status_code != 200:
        click.echo(req.status_code, req.text)
        sys.exit(1)
    time.sleep(1)


def create_pipeline(root, name, new_name):
    """Creates a pipeline.

    Args:
        name (str): Name of existing name
        new_name(str): Name of the new pipeline

    Returns:
    Example Usage:
        >>> print create_pipeline(root,
        name, new_name)
    """
    pipeline = root.find('.//pipeline[@name="%s"]' % name)
    pipeline_parent = root.find('.//pipeline[@name="%s"]/..' % name)

    new_pipeline = root.find('.//pipeline[@name="%s"]' % new_name)
    if new_pipeline is not None:
        click.echo("The pipeline name : %s provided already exists. Please "
                   "provide a different pipeline name. " % new_name)
        sys.exit(1)

    if pipeline is None:
        click.echo("The original pipeline does not exist: %s" % name)
        sys.exit(1)

    new_pipeline = copy.deepcopy(pipeline)
    click.echo("Setting pipeline name: %s" % new_name)
    new_pipeline.set('name', new_name)
    pipeline_parent.append(new_pipeline)

    return root


def validate_pipe_ip_cb(ctx, param, value):
    """
    If ip is none then provide the default ip for gocd.
    """
    if not value:
        value = ctx.obj.get_gocd_info()['ip']
    return value


def get_pipe_info(pipeline_name, username, password, ip_address):
    """
    Get pipe info string
    """
    requests.packages.urllib3.disable_warnings()
    try:
        url = "http://{0}/go/api/pipelines/{1}/status".format(ip_address,
                                                              pipeline_name)
        res = requests.get(url, auth=HTTPBasicAuth(username, password))
        soup = BeautifulSoup(res.content, "html.parser")
    except requests.ConnectionError as ex:
        GOCD_UTILS_LOGGER.error(ex)
        raise Exception("Cannot connect to Go CD Server : %s " % ex)

    return soup
