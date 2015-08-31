from servicelab.stack import pass_context
from servicelab.utils import service_utils
from servicelab.utils import helper_utils
import click
import sys
import os
import requests
from requests.auth import HTTPBasicAuth
from BeautifulSoup import BeautifulSoup
import xml.etree.ElementTree as ET
import copy
from servicelab.utils import gocd_utils


@click.group('pipe', short_help='Pipeline to work with.',
             add_help_option=True)
@click.pass_context
def cli(ctx):
    pass


@cli.command('log', short_help='Display pipeline log')
@click.argument('pipeline_name', required=True)
@click.option(
    '-g',
    '--gouser',
    help='Provide go server username',
    required=True)
@click.option(
    '-h',
    '--gopass',
    help='Provide go server password',
    required=True)
@click.option(
    '-s',
    '--goserver',
    help='Provide the go server ip address.',
    required=True)
@pass_context
def display_pipeline_log(ctx, pipeline_name, gouser, gopass, goserver):
    """
    Displays a pipeline log.
    """
    stagesURL = "http://{0}/go/api/pipelines/{1}/stages.xml"
    # Find latest run info
    res = requests.get(stagesURL.format(goserver, pipeline_name),
                       auth=HTTPBasicAuth(
        gouser,
        gopass))
    soup = BeautifulSoup(res.content)
    latestJobInfoURL = soup.findAll('entry')[0].findAll('link')[0]['href']

    # Find all the job info for that run
    jobInfoRes = requests.get(
        latestJobInfoURL,
        auth=HTTPBasicAuth(
            gouser,
            gopass))
    soup = BeautifulSoup(jobInfoRes.content)
    jobURLs = soup.findAll('job')

    # for each of the job, pull the log and display the log
    for jobURL in jobURLs:
        jobURLRes = requests.get(
            jobURL['href'], auth=HTTPBasicAuth(
                gouser, gopass))
        soup = BeautifulSoup(jobURLRes.content)
        logURL = soup.find('artifacts')['baseuri']
        logURLRes = requests.get(
            logURL +
            "/cruise-output/console.log",
            auth=HTTPBasicAuth(
                'raju',
                'badger'))
        soup = BeautifulSoup(logURLRes.content)
        print "\n\n-------------------Printing job log for pipeline : ", \
            logURL, "-------------------------"
        print soup
        print "\n\n-------------------End of job log for pipeline : ",\
            logURL, "-------------------------"


@cli.command('status', short_help='Display pipeline status')
@click.argument('pipeline_name', required=True)
@click.option(
    '-g',
    '--gouser',
    help='Provide go server username',
    required=True)
@click.option(
    '-h',
    '--gopass',
    help='Provide go server password',
    required=True)
@click.option(
    '-s',
    '--goserver',
    help='Provide the go server ip address and port no <ip:port>.',
    required=True)
@pass_context
def display_pipeline_status(ctx, pipeline_name, gouser, gopass, goserver):
    """
    Displays a pipeline status.
    """
    serverURL = "http://{0}/go/api/pipelines/{1}/status"
    res = requests.get(serverURL.format(goserver, pipeline_name),
                       auth=HTTPBasicAuth(
        gouser,
        gopass))
    soup = BeautifulSoup(res.content)
    print soup


@cli.command('run', short_help='Trigger a pipeline')
@click.argument('pipeline_name', required=True)
@click.option(
    '-g',
    '--gouser',
    help='Provide go server username',
    required=True)
@click.option(
    '-h',
    '--gopass',
    help='Provide go server password',
    required=True)
@click.option(
    '-s',
    '--goserver',
    help='Provide the go server ip address and port <ip:port>.',
    required=True)
@pass_context
def trigger_pipeline(ctx, pipeline_name, gouser, gopass, goserver):
    """
    Runs a pipeline.
    """
    serverURL = "http://{0}/go/api/pipelines/{1}/schedule"
    res = requests.post(serverURL.format(goserver, pipeline_name),
                        auth=HTTPBasicAuth(gouser, gopass))
    soup = BeautifulSoup(res.content)
    print soup


@cli.command('clone', short_help='Clone a pipeline')
@click.argument('pipeline_name', required=True)
@click.argument('new_pipeline_name', required=True)
@click.option(
    '-g',
    '--gouser',
    help='Provide go server username',
    required=True)
@click.option(
    '-h',
    '--gopass',
    help='Provide go server password',
    required=True)
@click.option(
    '-s',
    '--goserver',
    help='Provide the go server ip address and port <ip:port>.',
    required=True)
@pass_context
def clone_pipeline(
        ctx,
        pipeline_name,
        new_pipeline_name,
        gouser,
        gopass,
        goserver):
    """
    Clones a pipeline and assigns it the new name.
    """
    configXMLURL = "http://{0}/go/api/admin/config/current.xml".format(
        goserver)
    postConfigXMLURL = "http://{0}/go/api/admin/config.xml".format(
        goserver)
    res = requests.post(configXMLURL,
                        auth=HTTPBasicAuth(gouser, gopass))

    # Retrieve xml config from server
    (md5, root) = gocd_utils._get_config(configXMLURL, (gouser, gopass))
    new_xml = copy.deepcopy(root)

    new_xml = gocd_utils._create_pipeline(new_xml,
                                          pipeline_name,
                                          new_pipeline_name)

    # Upload results
    new_xmls = ET.tostring(new_xml, encoding='utf-8', method='xml')
    gocd_utils._push_config(postConfigXMLURL, md5, new_xmls, (gouser, gopass))
