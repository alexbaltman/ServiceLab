"""
Utility functions for pulp
"""
import sys
import logging
import requests
from requests.auth import HTTPBasicAuth

import click

# create logger
PULP_UTILS_LOGGER = logging.getLogger('click_application')
logging.basicConfig()


def validate_pulp_ip_cb(ctx, param, value):
    """
    If ip is none then this provides the default production ip for pulp
    """
    if not value:
        value = ctx.obj.get_pulp_info()['url']
    return value


def put(url, ip_address, ctx, username, password,
        payload):
    """
    Wrapper around requests.put
    """
    requests.packages.urllib3.disable_warnings()
    headers = {"Accept": "application/json",
               "Content-Type": "multipart/form-data"}
    try:
        res = requests.put(ip_address + url, verify=False,
                           auth=HTTPBasicAuth(username, password),
                           data=payload,
                           headers=headers)
        click.echo(".", nl=False)
        process_response(res)
    except requests.exceptions.RequestException as ex:
        ctx.logger.error("Could not connect to pulp server. Please,"
                         " check url {0}".format(ip_address))
        ctx.logger.error(str(ex))
        sys.exit(1)
    return res.text


def post(url, ip_address, ctx, username, password, payload):
    """
    Wrapper around requests.post
    """
    requests.packages.urllib3.disable_warnings()
    headers = {"Accept": "application/json"}
    try:
        res = requests.post(ip_address + url, verify=False,
                            auth=HTTPBasicAuth(username, password),
                            headers=headers,
                            data=payload)
        process_response(res)
    except requests.exceptions.RequestException as ex:
        ctx.logger.error("Could not connect to pulp server. Please,"
                         " check url {0}".format(ip_address))
        ctx.logger.error(str(ex))
        sys.exit(1)
    return res.text


def process_response(res):
    """
    This method will process the HTTP response code
    """
    if res.status_code == 404:
        ctx.logger.error("Incorrect repo id supplied... exiting")
        sys.exit(1)
    if res.status_code == 401:
        ctx.logger.error("Authentication failed... exiting")
        sys.exit(1)
    if res.status_code == 400:
        ctx.logger.error("Incorrect information supplied... exiting")
        sys.exit(1)
