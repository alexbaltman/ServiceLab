"""
Set of utility functions for Jenkins server
"""
import sys
import time
import requests

from bs4 import BeautifulSoup
from jenkinsapi.jenkins import Jenkins
from requests.auth import HTTPBasicAuth

import logger_utils
from servicelab import settings

slab_logger = logger_utils.setup_logger(settings.verbosity, 'stack.utils.jenkins')


START_LOG = "-------- Printing job log for build %s--------\n"
END_LOG = "-------- End of job log for build --------"


def get_server_instance(jenkins_server, jenkinsuser, jenkinspass):
    """
    For the given Jenkins servre, User Name and Password get the
    Jenkins instance.
    """
    requests.packages.urllib3.disable_warnings()
    server = ''
    try:
        server = Jenkins(jenkins_server, username=jenkinsuser,
                         password=jenkinspass)
    except Exception as ex:
        slab_logger.log(25, "Unable to connect to Jenkins server : %s " %
                        str(ex))
        return(1, server)

    return(0,  server)


def get_build_status(job_name, user, password, ip_address):
    """
    get the build status
    """
    returncode, server = get_server_instance(ip_address, user, password)
    if not returncode == 0:
        # this should be an exception
        print "unable to get server instance"
        return(returncode, server)

    status = server[job_name].get_last_build().name
    if server[job_name].get_last_build().get_status():
        status = status + "," + server[job_name].get_last_build().get_status()
    return(returncode, status)


def get_build_log(job_name, user, password, ip_address):
    """
    Creates a build log string
    """
    server = get_server_instance(ip_address, user, password)
    if not server:
        # this should be an exception
        print "unable to get server instance"
        return False

    log = server[job_name].get_last_build().name
    if server[job_name].get_last_build().get_status():
        log = log + "," + server[job_name].get_last_build().get_status()

    job_number = server[job_name].get_last_build().get_number()
    log_url = "{0}/job/{1}/{2}/consoleText".format(ip_address, job_name,
                                                   job_number)

    # Find latest run info
    res = requests.post(log_url, auth=HTTPBasicAuth(user, password))
    soup = BeautifulSoup(res.content, "html.parser")
    log = log + START_LOG.format(log_url)
    log = log + str(soup) + "\n"
    log = log + END_LOG + "\n"

    return log


def run_build(job_name, user, password, ip_address, ctx):
    """
    run a build
    """
    server = get_server_instance(ip_address, user, password)
    if not server:
        # this should be an exception
        slab_logger.log(25, "unable to get server instance")
        return False

    if server[job_name].get_last_build():
        build_number = server[job_name].get_last_build().get_number()
        url = "%s/job/%s/%s/gerrit-trigger-retrigger-this/" % (ip_address,
                                                               job_name,
                                                               build_number)
        try:
            slab_logger.log(25, "Retriggering last build # : %s " % (build_number))
            res = requests.post(url, auth=HTTPBasicAuth(user, password))
            process_response(res, ctx)
        except requests.exceptions.RequestException as ex:
            slab_logger.error("Could not connect to jenkins server. Please,"
                              " check url {0}".format(ip_address))
            slab_logger.error(str(ex))
            return False
    else:
        slab_logger.log(25, "Starting Build : %s " % (job_name))
        server.build_job(job_name)

    job_instance = server.get_job(job_name)
    time.sleep(2)
    slab_logger.log(25, '%s run status is : %s' % (job_name, job_instance.is_running()))


def validate_build_ip_cb(ctx, param, value):
    """
    If ip is none then provide the default ip for jenkins.
    """
    if not value:
        value = ctx.obj.get_jenkins_info()['url']
    return value


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
        slab_logger.error("Incorrect jenkins url supplied... exiting")
        return False
    if res.status_code == 401:
        slab_logger.error("Authentication failed... exiting")
        return False
    if res.status_code == 400:
        slab_logger.error("Incorrect information supplied... exiting")
        return False
