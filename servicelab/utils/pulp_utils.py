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
    """Validates the supplied pulp ip information.

    If supplied ip is none then provide the default production ip for pulp.

    Args:
        ctx (object): Context object of stack.
        param (str): callback parameter name
        value(str): value to be passed

    Returns:
        value  -- Pulp ip address

    Example Usage:
        >>> print validate_pulp_ip_cb(ctx, param, "localhost")
    """

    if not value:
        value = ctx.obj.get_pulp_info()['url']
    return value


def put(url, ip_address, ctx, username, password,
        payload):
    """Makes a put request to supplied to URL.

    Make a put request using the the url, username, password and payload.

    Args:
        url (str): url path to used.
        ip_address (str): ip_address prefix
        ctx(str): Stack context object
        username(str): Username to be used
        password(str): Password to be used
        payload(object): Json object to submitted

    Returns:
        response  -- Returns server put response

    Example Usage:
        >>> print put("/pulp/api/v2/repositories", "http://localhost/", ctx, "admin",
                      "admin", {"criteria":{"filters":{"repo_id":{"$eq": "test_repo"}}}})
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
        process_response(res, ctx)
    except requests.exceptions.RequestException as ex:
        ctx.logger.error("Could not connect to pulp server. Please,"
                         " check url {0}".format(ip_address))
        ctx.logger.error(str(ex))
        sys.exit(1)
    return res.text


def post(url, ip_address, ctx, username, password, payload):
    """Makes a post request to supplied to URL.

    Make a post request using the the url, username, password and payload.

    Args:
        url (str): url path to used.
        ip_address (str): ip_address prefix
        ctx(str): Stack context object
        username(str): Username to be used
        password(str): Password to be used
        payload(object): Json object to submitted

    Returns:
        response  -- Returns server post response

    Example Usage:
        >>> print post("/pulp/api/v2/repositories", "http://localhost/", ctx, "admin",
                      "admin", {"criteria":{"filters":{"repo_id":{"$eq": "test_repo"}}}})
    """
    requests.packages.urllib3.disable_warnings()
    headers = {"Accept": "application/json"}
    try:
        click.echo(ip_address + url)
        res = requests.post(ip_address + url, verify=False,
                            auth=HTTPBasicAuth(username, password),
                            headers=headers,
                            data=payload)
        process_response(res, ctx)
    except requests.exceptions.RequestException as ex:
        ctx.logger.error("Could not connect to pulp server. Please,"
                         " check url {0}".format(ip_address))
        ctx.logger.error(str(ex))
        sys.exit(1)
    return res.text


def get(url, ip_address, ctx, username, password):
    """Makes a get request to supplied to URL.

    Make a get request using the the url, username, password.

    Args:
        url (str): url path to used.
        ip_address (str): ip_address prefix
        ctx(str): Stack context object
        username(str): Username to be used
        password(str): Password to be used

    Returns:
        response  -- Returns server get response

    Example Usage:
        >>> print get("/pulp/api/v2/repositories", "http://localhost/", ctx, "admin",
                      "admin")
    """
    requests.packages.urllib3.disable_warnings()
    headers = {"Accept": "application/json"}
    try:
        res = requests.get(ip_address + url, verify=False,
                           auth=HTTPBasicAuth(username, password),
                           headers=headers)
        process_response(res, ctx)
    except requests.exceptions.RequestException as ex:
        ctx.logger.error("Could not connect to pulp server. Please,"
                         " check url {0}".format(ip_address))
        ctx.logger.error(str(ex))
        sys.exit(1)
    return res.text


def process_response(res, ctx):
    """Processes a REST API response.

    Checks for different error response status codes and displays message.

    Args:
        res (object): http response object
        ctx(str): Stack context object
        username(str): Username to be used
        password(str): Password to be used

    Returns:
        None

    Example Usage:
        >>> print process_response(res, ctx)
    """
    if res.status_code == 404:
        ctx.logger.error("Incorrect pulp repo id supplied... exiting")
        sys.exit(1)
    if res.status_code == 401:
        ctx.logger.error("Authentication failed... exiting")
        sys.exit(1)
    if res.status_code == 400:
        ctx.logger.error("Incorrect information supplied... exiting")
        sys.exit(1)
