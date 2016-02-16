"""
Utility functions for go
"""
import sys
import time
import copy
import json
import xml.etree.ElementTree as ET
import click
import requests

import logger_utils

from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
from servicelab import settings

slab_logger = logger_utils.setup_logger(settings.verbosity, 'stack.utils.gocd')


def get_config(config_xmlurl, auth=None):
    """
    Retrieves the go config

    Attributes
        config_xmlurl
        auth
    """
    slab_logger.log(15, "Retrieving go config")
    if auth:
        req = requests.get(config_xmlurl, auth=auth)
    else:
        req = requests.get(config_xmlurl)
    if req.status_code == 200:
        try:
            root = ET.fromstring(req.text)
        except requests.ConnectionError as ex:
            slab_logger.error("Failure parsing xml from request" + ex)
            sys.exit(1)
    else:
        slab_logger.error("Request failed")
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
    slab_logger.log(15, "Uploading go config")
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
        slab_logger.error(req.status_code, req.text)
        sys.exit(1)
    time.sleep(1)


def get_current_pipeline_counter(pipeline_name, ip_address, auth=None):
    """
    Get current pipeline counter

    Attributes:
        pipeline_name
    """
    slab_logger.log(15, 'Determining current pipeline counter')
    url = "http://%s/go/api/pipelines/%s/history/0" % (
        ip_address, pipeline_name)

    if auth:
        req = requests.get(url, auth=auth)
    else:
        req = requests.get(url)
    if req.status_code != 200:
        slab_logger.error(req.status_code, req.text)
        return -1, None
    pipeline_history = json.loads(req.text)
    if pipeline_history['pipelines'] and len(
            pipeline_history['pipelines']) > 0:
        pipeline_counter = pipeline_history['pipelines'][0]['counter']
    else:
        pipeline_counter = None
    return 0, pipeline_counter


def process_all_stages(pipeline_name, pipeline_counter, ip_address, auth=None):
    """
    Process all stages with needing manual intervention

    Attributes:
        pipeline_name
    """
    slab_logger.log(15, 'Processing pipeline stages')
    wait_for_pipeline(pipeline_name, ip_address, auth)
    return_code, pipeline_instance = get_pipeline_instance(
        pipeline_name, pipeline_counter, ip_address, auth)
    if return_code != 0:
        slab_logger.error("Error occurred. Exiting")
        return

    i = 0
    if pipeline_instance['stages']:
        for stage in pipeline_instance['stages']:
            return_code, current_pipeline_instance = get_pipeline_instance(
                pipeline_name, pipeline_counter, ip_address, auth)
            matching_stage = current_pipeline_instance['stages'][i]
            if return_code != 0:
                slab_logger.error("Error occurred. Exiting")
                return

            if 'result' in matching_stage:
                click.echo(
                    "Stage : %s  has %s " %
                    (matching_stage['name'],
                     matching_stage['result']))
                if matching_stage['result'] == "Failed":
                    slab_logger.error("Exiting.")
                    return
            else:
                click.echo("Scheduling Stage : %s " % (stage['name']))
                url = "http://%s/go/run/%s/%s/%s" % (
                    ip_address, pipeline_name, pipeline_counter, stage['name'])
                req = requests.post(url, auth=auth, data="")
                if req.status_code != 200:
                    slab_logger.error(req.status_code, req.text)
                    return -1, None
                time.sleep(10)
                wait_for_stage(
                    pipeline_name,
                    ip_address,
                    stage['name'],
                    pipeline_counter,
                    auth=auth)
                return_code, current_pipeline_instance = get_pipeline_instance(
                    pipeline_name, pipeline_counter, ip_address, auth)
                matching_stage = current_pipeline_instance['stages'][i]
                click.echo(
                    "Stage : %s  has %s " %
                    (matching_stage['name'],
                     matching_stage['result']))

            i += 1


def get_pipeline_instance(
        pipeline_name,
        pipeline_counter,
        ip_address,
        auth=None):
    """
    Gets a pipeline instance
    """
    slab_logger.log(15, 'Determining pipeline instance')
    url = "http://%s/go/api/pipelines/%s/instance/%s" % (
        ip_address, pipeline_name, pipeline_counter)
    if auth:
        req = requests.get(url, auth=auth)
    else:
        req = requests.get(url)
    if req.status_code != 200:
        slab_logger.error(req.status_code, req.text)
        return -1, None
    pipeline_instance = json.loads(req.text)
    return 0, pipeline_instance


def wait_for_pipeline(pipeline_name, ip_address, auth=None):
    """
    Wait for pipeline.
    """
    slab_logger.log(15, 'Waiting for pipeline %s' % pipeline_name)
    server_url = "http://{0}/go/api/pipelines/{1}/status".format(
        ip_address, pipeline_name)
    schedulable = False

    while not schedulable:
        res = requests.get(server_url, auth=auth)
        status = json.loads(res.content)
        if status:
            schedulable = status['schedulable']
        else:
            return
        if not status['schedulable']:
            slab_logger.warning("Pipeline is running. Waiting for it to finish.")
            time.sleep(10)


def wait_for_stage(
        pipeline_name,
        ip_address,
        stage_name,
        pipeline_counter,
        auth=None):
    """
    Wait for stage.
    """
    slab_logger.log(15, 'Waiting for stage %s' % stage_name)
    server_url = "http://{0}/go/api/stages/{1}/{2}/instance/{3}/1".format(
        ip_address, pipeline_name, stage_name, pipeline_counter)
    stopped = False

    while not stopped:
        res = requests.get(server_url, auth=auth)
        stage = json.loads(res.content)
        if stage['result'] != "Unknown":
            stopped = True
        else:
            slab_logger.warning(
                "Stage %s is running. Waiting for it to finish." %
                (stage['name']))
            time.sleep(10)


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
    slab_logger.log(15, 'Creating new pipeline %s' % new_name)
    pipeline = root.find('.//pipeline[@name="%s"]' % name)
    pipeline_parent = root.find('.//pipeline[@name="%s"]/..' % name)

    new_pipeline = root.find('.//pipeline[@name="%s"]' % new_name)
    if new_pipeline is not None:
        slab_logger.error("The pipeline name : %s provided already exists. Please "
                         "provide a different pipeline name. " % new_name)
        sys.exit(1)

    if pipeline is None:
        slab_logger.error("The original pipeline does not exist: %s" % name)
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
    slab_logger.log(15, 'Determining IP address for gocd server')
    if not value:
        value = ctx.obj.get_gocd_info()['ip']
    return value


def get_pipe_info(pipeline_name, username, password, ip_address):
    """
    Get pipe info string
    """
    slab_logger.log(15, 'Determining pipeline information string')
    requests.packages.urllib3.disable_warnings()
    try:
        url = "http://{0}/go/api/pipelines/{1}/status".format(ip_address,
                                                              pipeline_name)
        res = requests.get(url, auth=HTTPBasicAuth(username, password))
        soup = BeautifulSoup(res.content, "html.parser")
    except requests.ConnectionError as ex:
        slab_logger.error(ex)
        raise Exception("Cannot connect to Go CD Server : %s " % ex)

    return soup
