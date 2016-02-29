import logger_utils

from servicelab.stack import Context
from servicelab import settings

slab_logger = logger_utils.setup_logger(settings.verbosity, 'stack.utils.context')

"""
 context_utils : Wrapper utilities for Context
"""


def get_artifactory_url():
    ctx = Context()
    slab_logger.debug('Extracting artifactory url')
    return ctx.get_artifactory_info()["url"]


def get_gocd_ip():
    ctx = Context()
    slab_logger.debug('Extracting gocd server ip address')
    return ctx.get_gocd_info()["ip"]


def get_jenkins_url():
    ctx = Context()
    slab_logger.debug('Extracting jenkins url')
    return ctx.get_jenkins_info()["url"]
