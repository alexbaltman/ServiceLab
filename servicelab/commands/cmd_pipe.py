from servicelab.stack import pass_context
from servicelab.utils import service_utils
from servicelab.utils import helper_utils
import click
import sys
import os
import requests
from requests.auth import HTTPBasicAuth
from BeautifulSoup import BeautifulSoup


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

    # Find latest run info
    res = requests.get(
        "http://{0}:8153/go/api/pipelines/test/stages.xml".format(goserver),
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
