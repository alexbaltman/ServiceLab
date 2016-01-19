"""
Set of utility functions for Jenkins server
"""
import sys
import time

import requests
import click

from bs4 import BeautifulSoup
from jenkinsapi.jenkins import Jenkins
from requests.auth import HTTPBasicAuth


START_LOG = "-------- Printing job log for build %s--------\n"
END_LOG = "-------- End of job log for build --------"


def get_server_instance(jenkins_server, jenkinsuser, jenkinspass):
    """
    For the given Jenkins servre, User Name and Password get the
    Jenkins instance.
    """
    requests.packages.urllib3.disable_warnings()
    try:
        server = Jenkins(jenkins_server, username=jenkinsuser,
                         password=jenkinspass)
    except Exception as ex:
        click.echo("Unable to connect to Jenkins server : %s " %
                   str(ex))
        sys.exit(1)

    return server


def get_build_status(job_name, user, password, ip_address):
    """
    get the build status
    """
    server = get_server_instance(ip_address, user, password)
    if not server:
        # this should be an exception
        print "unable to get server instance"
        return False

    status = server[job_name].get_last_build().name
    if server[job_name].get_last_build().get_status():
        status = status + "," + server[job_name].get_last_build().get_status()
    return status


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
        click.echo("unable to get server instance")
        return False

    if server[job_name].get_last_build():
        build_number = server[job_name].get_last_build().get_number()
        url = "%s/job/%s/%s/gerrit-trigger-retrigger-this/" % (ip_address,
                                                               job_name,
                                                               build_number)
        try:
            click.echo("Retriggering last build # : %s " % (build_number))
            res = requests.post(url, auth=HTTPBasicAuth(user, password))
            process_response(res, ctx)
        except requests.exceptions.RequestException as ex:
            ctx.logger.error("Could not connect to jenkins server. Please,"
                             " check url {0}".format(ip_address))
            ctx.logger.error(str(ex))
            return False
    else:
        click.echo("Starting Build : %s " % (job_name))
        server.build_job(job_name)

    job_instance = server.get_job(job_name)
    time.sleep(2)
    click.echo('%s run status is : %s' % (job_name, job_instance.is_running()))


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
        ctx.logger.error("Incorrect jenkins url supplied... exiting")
        return False
    if res.status_code == 401:
        ctx.logger.error("Authentication failed... exiting")
        return False
    if res.status_code == 400:
        ctx.logger.error("Incorrect information supplied... exiting")
        return False
