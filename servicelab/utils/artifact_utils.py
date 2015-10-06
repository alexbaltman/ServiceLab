"""
Set of utility functions for Jenkins server
"""

import logging
import requests

from requests.auth import HTTPBasicAuth


# create logger
ARTIFACT_UTILS_LOGGER = logging.getLogger('click_application')
logging.basicConfig()


def get_artifact_info(url, user, password):
    """
    Get artifact info string
    """
    requests.packages.urllib3.disable_warnings()
    try:
        res = requests.get(url, auth=HTTPBasicAuth(user, password))
    except requests.ConnectionError as ex:
        ARTIFACT_UTILS_LOGGER.error(ex)
        raise Exception("Cannot connect to artifactory : %s " % ex)

    return res.content
