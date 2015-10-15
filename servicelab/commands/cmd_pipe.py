"""
Pipe stack command submodule implements
    1. Displays a pipeline log.
    2. Displays a pipeline status.
    3. Runs a pipeline.
"""
import copy
import requests

import click
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET

from servicelab.utils import gocd_utils
from servicelab.stack import pass_context


@click.group('pipe', short_help='Pipeline to work with.',
             add_help_option=True)
@click.pass_context
def cli(_):
    """
    Helps you gopipe for resources in the SDLC pipeline.
    """
    pass


@cli.command('log', short_help='Display pipeline log')
@click.argument('pipeline_name', required=True)
@click.option('-u',
              '--user',
              help='Provide go server username',
              required=True)
@click.option('-p',
              '--password',
              help='Provide go server password',
              required=True)
@click.option('-ip',
              '--ip_address',
              default=None,
              callback=gocd_utils.validate_pipe_ip_cb,
              help='Provide the go server ip address.')
@pass_context
def display_pipeline_log(_, pipeline_name, user, password, ip_address):
    """
    Displays a pipeline log.
    """
    stages_url = "http://{0}/go/api/pipelines/{1}/stages.xml"
    # Find latest run info
    res = requests.get(stages_url.format(ip_address, pipeline_name),
                       auth=HTTPBasicAuth(user, password))
    soup = BeautifulSoup(res.content)
    latest_job_info_url = soup.findAll('entry')[0].findAll('link')[0]['href']

    # Find all the job info for that run
    latest_job_info_url = latest_job_info_url.replace("gocd_java_server",
                                                      ip_address)
    job_info_res = requests.get(latest_job_info_url,
                                auth=HTTPBasicAuth(user, password))
    soup = BeautifulSoup(job_info_res.content)
    job_urls = soup.findAll('job')

    # for each of the job, pull the log and display the log
    for job_url in job_urls:
        job_url['href'] = job_url['href'].replace("gocd_java_server",
                                                  ip_address)
        job_url_res = requests.get(job_url['href'],
                                   auth=HTTPBasicAuth(user, password))
        soup = BeautifulSoup(job_url_res.content)
        log_url = soup.find('artifacts')['baseuri']
        log_url = log_url.replace("gocd_java_server", ip_address)
        log_url_res = requests.get(log_url + "/cruise-output/console.log",
                                   auth=HTTPBasicAuth(user, password))
        soup = BeautifulSoup(log_url_res.content)
        print "\n\n-------------------Printing job log for pipeline : ", \
              log_url, "-------------------------"
        print soup
        print "\n\n-------------------End of job log for pipeline : ", \
              log_url, "-------------------------"


@cli.command('status', short_help='Display pipeline status')
@click.argument('pipeline_name', required=True)
@click.option('-u',
              '--user',
              help='Provide go server username',
              required=True)
@click.option('-p',
              '--password',
              help='Provide go server password',
              required=True)
@click.option('-ip',
              '--ip_address',
              default=None,
              callback=gocd_utils.validate_pipe_ip_cb,
              help='Provide the go server ip address and port no <ip:port>.',
              required=True)
@pass_context
def display_pipeline_status(_, pipeline_name, user, password, ip_address):
    """
    Displays a pipeline status.
    """
    server_url = "http://{0}/go/api/pipelines/{1}/status"
    res = requests.get(server_url.format(ip_address, pipeline_name),
                       auth=HTTPBasicAuth(user, password))
    soup = BeautifulSoup(res.content, "html.parser")
    print str(soup)


@cli.command('run', short_help='Trigger a pipeline')
@click.argument('pipeline_name', required=True)
@click.option('-u',
              '--user',
              help='Provide go server username',
              required=True)
@click.option('-p',
              '--password',
              help='Provide go server password',
              required=True)
@click.option('-ip',
              '--ip_address',
              default=None,
              callback=gocd_utils.validate_pipe_ip_cb,
              help='Provide the go server ip address and port <ip:port>.',
              required=True)
@pass_context
def trigger_pipeline(_, pipeline_name, user, password, ip_address):
    """
    Runs a pipeline.
    """
    server_url = "http://{0}/go/api/pipelines/{1}/schedule"
    res = requests.post(server_url.format(ip_address, pipeline_name),
                        auth=HTTPBasicAuth(user, password))
    soup = BeautifulSoup(res.content)
    print soup


@cli.command('clone', short_help='Clone a pipeline')
@click.argument('pipeline_name', required=True)
@click.argument('new_pipeline_name', required=True)
@click.option('-u',
              '--user',
              help='Provide go server username',
              required=True)
@click.option('-p',
              '--password',
              help='Provide go server password',
              required=True)
@click.option('-ip',
              '--ip_address',
              default=None,
              callback=gocd_utils.validate_pipe_ip_cb,
              help='Provide the go server ip address and port <ip:port>.',
              required=True)
@pass_context
def clone_pipeline(_,
                   pipeline_name,
                   new_pipeline_name,
                   user,
                   password,
                   ip_address):
    """
    Clones a pipeline and assigns it the new name.
    """
    config_xmlurl = "http://{0}/go/api/admin/config/current.xml".format(
        ip_address)
    post_config_xmlurl = "http://{0}/go/api/admin/config.xml".format(
        ip_address)
    requests.post(config_xmlurl,
                  auth=HTTPBasicAuth(user, password))

    # Retrieve xml config from server
    (md5, root) = gocd_utils.get_config(config_xmlurl, (user, password))
    new_xml = copy.deepcopy(root)

    new_xml = gocd_utils.create_pipeline(new_xml,
                                         pipeline_name,
                                         new_pipeline_name)

    # Upload results
    new_xmls = ET.tostring(new_xml, encoding='utf-8', method='xml')
    gocd_utils.push_config(post_config_xmlurl, md5, new_xmls, (user, password))
