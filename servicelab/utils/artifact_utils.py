"""
Set of utility functions for Jenkins server
"""

import logging
import requests

from requests.auth import HTTPBasicAuth
from servicelab.stack import Context

ctx = Context()


def get_artifact_info(url, user, password):
    """
    Get artifact info string
    """
    ctx.logger.debug('Extracting artifact information')
    requests.packages.urllib3.disable_warnings()
    try:
        res = requests.get(url, auth=HTTPBasicAuth(user, password))
    except requests.ConnectionError as ex:
        ctx.logger.error(ex)
        raise Exception("Cannot connect to artifactory : %s " % ex)

    return res.content


def validate_artifact_ip_cb(ctx, param, value):
    """
    If ip is none then provide the default ip for artifactory.
    """
    ctx.logger.debug('Setting artifactory IP address')
    if not value:
        value = ctx.obj.get_artifactory_info()['url']
    return value
