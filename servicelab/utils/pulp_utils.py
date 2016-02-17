"""
Utility functions for pulp
"""
import sys
import logging
import requests
from requests.auth import HTTPBasicAuth

import logger_utils
from servicelab import settings

slab_logger = logger_utils.setup_logger(settings.verbosity, 'stack.utils.pulp')


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
    slab_logger.log(15, 'Validating pulp server IP address')
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
    slab_logger.log(15, 'Sending put request to %s' % ip_address)
    requests.packages.urllib3.disable_warnings()
    headers = {"Accept": "application/json",
               "Content-Type": "multipart/form-data"}
    try:
        res = requests.put(ip_address + url, verify=False,
                           auth=HTTPBasicAuth(username, password),
                           data=payload,
                           headers=headers)
        slab_logger.log(25, ".", nl=False)
        process_response(res, ctx)
    except requests.exceptions.RequestException as ex:
        slab_logger.error("Could not connect to pulp server. Please,"
                          " check url {0}".format(ip_address))
        slab_logger.error(str(ex))
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
    slab_logger.log(15, 'Sending post request to %s' % ip_address)
    requests.packages.urllib3.disable_warnings()
    headers = {"Accept": "application/json"}
    try:
        slab_logger.log(25, ip_address + url)
        res = requests.post(ip_address + url, verify=False,
                            auth=HTTPBasicAuth(username, password),
                            headers=headers,
                            data=payload)
        process_response(res, ctx)
    except requests.exceptions.RequestException as ex:
        slab_logger.error("Could not connect to pulp server. Please,"
                          " check url {0}".format(ip_address))
        slab_logger.error(str(ex))
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
    slab_logger.log(15, 'Sending get request to %s' % ip_address)
    requests.packages.urllib3.disable_warnings()
    headers = {"Accept": "application/json"}
    try:
        res = requests.get(ip_address + url, verify=False,
                           auth=HTTPBasicAuth(username, password),
                           headers=headers)
        process_response(res, ctx)
    except requests.exceptions.RequestException as ex:
        slab_logger.error("Could not connect to pulp server. Please,"
                          " check url {0}".format(ip_address))
        slab_logger.error(str(ex))
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
    slab_logger.log(15, 'Processing REST API response')
    if res.status_code == 404:
        slab_logger.error("Incorrect pulp repo id supplied... exiting")
        sys.exit(1)
    if res.status_code == 401:
        slab_logger.error("Authentication failed... exiting")
        sys.exit(1)
    if res.status_code == 400:
        slab_logger.error("Incorrect information supplied... exiting")
        sys.exit(1)
