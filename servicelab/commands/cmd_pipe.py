"""
Pipe stack command submodule implements
    1. Displays a pipeline log.
    2. Displays a pipeline status.
    3. Runs a pipeline.
"""
import json
import copy
import sys
import xml.etree.ElementTree as ET

import click
from bs4 import BeautifulSoup
import requests
from requests.auth import HTTPBasicAuth

from servicelab.utils import gocd_utils
from servicelab.stack import pass_context


@click.group(
    'pipe',
    short_help='Command subset to help you work with Go pipelines.',
    add_help_option=True)
@click.pass_context
def cli(_):
    """
    Helps you gopipe for resources in the SDLC pipeline.
    """
    pass


@cli.command(
    'log',
    short_help='Display the log output from a specific pipeline.')
@click.argument('pipeline_name', required=True)
@click.option('-u',
              '--username',
              help='Provide go server username')
@click.option('-p',
              '--password',
              help='Provide go server password')
@click.option('-ip',
              '--ip_address',
              default=None,
              callback=gocd_utils.validate_pipe_ip_cb,
              help='Provide the go server ip address.')
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def display_pipeline_log(ctx,
                         pipeline_name,
                         username,
                         password,
                         ip_address,
                         interactive):
    """
    Displays a pipeline log.
    """
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    if not password or not username:
        click.echo("Username is %s and password is %s. "
                   "Please, set the correct value for both and retry." %
                   (username, password))
        sys.exit(1)
    stages_url = "http://{0}/go/api/pipelines/{1}/stages.xml"
    # Find latest run info
    res = requests.get(stages_url.format(ip_address, pipeline_name),
                       auth=HTTPBasicAuth(username, password))
    soup = BeautifulSoup(res.content, "html.parser")
    try:
        latest_job_info_url = soup.findAll(
            'entry')[0].findAll('link')[0]['href']
    except Exception as ex:
        click.echo("Internal error occurred. Please, check arguments supplied.")
        click.echo("Error details : %s " % (ex))
        sys.exit(1)

    # Find all the job info for that run
    latest_job_info_url = latest_job_info_url.replace("gocd_java_server",
                                                      ip_address)
    job_info_res = requests.get(latest_job_info_url,
                                auth=HTTPBasicAuth(username, password))
    soup = BeautifulSoup(job_info_res.content, "html.parser")
    job_urls = soup.findAll('job')

    # for each of the job, pull the log and display the log
    for job_url in job_urls:
        job_url['href'] = job_url['href'].replace("gocd_java_server",
                                                  ip_address)
        job_url_res = requests.get(job_url['href'],
                                   auth=HTTPBasicAuth(username, password))
        soup = BeautifulSoup(job_url_res.content, "html.parser")
        log_url = soup.find('artifacts')['baseuri']
        log_url = log_url.replace("gocd_java_server", ip_address)
        log_url_res = requests.get(log_url + "/cruise-output/console.log",
                                   auth=HTTPBasicAuth(username, password))
        soup = BeautifulSoup(log_url_res.content, "html.parser")
        print "\n\n-------------------Printing job log for pipeline : ", \
              log_url, "-------------------------"
        print soup
        print "\n\n-------------------End of job log for pipeline : ", \
              log_url, "-------------------------"


@cli.command('status', short_help='Display the status of a Go pipeline.')
@click.argument('pipeline_name', required=True)
@click.option('-u',
              '--username',
              help='Provide go server username')
@click.option('-p',
              '--password',
              help='Provide go server password')
@click.option('-ip',
              '--ip_address',
              default=None,
              callback=gocd_utils.validate_pipe_ip_cb,
              help='Provide the go server ip address and port no <ip:port>.',
              required=False)
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def display_pipeline_status(ctx,
                            pipeline_name,
                            username,
                            password,
                            ip_address,
                            interactive):
    """
    Displays a pipeline status.
    """
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    if not password or not username:
        click.echo("Username is %s and password is %s. "
                   "Please, set the correct value for both and retry." %
                   (username, password))
        sys.exit(1)
    server_url = "http://{0}/go/api/pipelines/{1}/status"
    res = requests.get(server_url.format(ip_address, pipeline_name),
                       auth=HTTPBasicAuth(username, password))
    soup = BeautifulSoup(res.content, "html.parser")
    print str(soup)


@cli.command('run', short_help='Trigger a Go pipeline.')
@click.argument('pipeline_name', required=True)
@click.option('-u',
              '--username',
              help='Provide go server username')
@click.option('-p',
              '--password',
              help='Provide go server password')
@click.option('-ip',
              '--ip_address',
              default=None,
              callback=gocd_utils.validate_pipe_ip_cb,
              help='Provide the go server ip address and port <ip:port>.',
              required=False)
@click.option(
    '-e',
    '--env',
    default=None,
    help='Provide environment variables in json format e.x {"var1" : "val1"}',
    required=False)
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@click.option('-a',
              '--all-stages',
              flag_value=True,
              help="Process all stages without needing manual approval.")
@pass_context
def trigger_pipeline(ctx,
                     pipeline_name,
                     username,
                     password,
                     ip_address,
                     env,
                     interactive,
                     all_stages):
    """
    Runs a pipeline.
    """
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    if not password or not username:
        click.echo("Username is %s and password is %s. "
                   "Please, set the correct value for both and retry." %
                   (username, password))
        sys.exit(1)
    server_url = "http://{0}/go/api/pipelines/{1}/schedule"
    env_data = None
    if env is not None:
        env_json = json.loads(env)
        for env_key in env_json:
            env_val = env_json[env_key]
            if env_data is None:
                env_data = "variables[{0}]={1}".format(env_key, env_val)
            else:
                env_data = "{0}&variables[{1}]={2}".format(
                    env_data, env_key, env_val)
    return_code, current_pipeline_counter = gocd_utils.get_current_pipeline_counter(
        pipeline_name, ip_address, auth=HTTPBasicAuth(username, password))
    if return_code == -1:
        click.echo("Error occurred. Exiting.")
        return
    click.echo(
        "Current pipeline_counter : %s" %
        (current_pipeline_counter + 1))
    click.echo("Scheduling pipeline.")
    res = requests.post(server_url.format(ip_address, pipeline_name),
                        auth=HTTPBasicAuth(username, password), data=env_data)
    soup = BeautifulSoup(res.content, "html.parser")
    click.echo(soup)
    if all_stages:
        gocd_utils.process_all_stages(
            pipeline_name,
            current_pipeline_counter + 1,
            ip_address,
            auth=HTTPBasicAuth(
                username,
                password))


@cli.command('clone', short_help='Clone a Go pipeline - Go admins only.')
@click.argument('pipeline_name', required=True)
@click.argument('new_pipeline_name', required=True)
@click.option('-u',
              '--username',
              help='Provide go server username')
@click.option('-p',
              '--password',
              help='Provide go server password')
@click.option('-ip',
              '--ip_address',
              default=None,
              callback=gocd_utils.validate_pipe_ip_cb,
              help='Provide the go server ip address and port <ip:port>.',
              required=False)
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def clone_pipeline(ctx,
                   pipeline_name,
                   new_pipeline_name,
                   username,
                   password,
                   ip_address,
                   interactive):
    """
    Clones a pipeline and assigns it the new name.
    """
    if not username:
        username = ctx.get_username()
    if not password:
        password = ctx.get_password(interactive)
    if not password or not username:
        click.echo("Username is %s and password is %s. "
                   "Please, set the correct value for both and retry." %
                   (username, password))
        sys.exit(1)
    config_xmlurl = "http://{0}/go/api/admin/config/current.xml".format(
        ip_address)
    post_config_xmlurl = "http://{0}/go/api/admin/config.xml".format(
        ip_address)
    requests.post(config_xmlurl,
                  auth=HTTPBasicAuth(username, password))

    # Retrieve xml config from server
    (md5, root) = gocd_utils.get_config(config_xmlurl, (username, password))
    new_xml = copy.deepcopy(root)

    new_xml = gocd_utils.create_pipeline(new_xml,
                                         pipeline_name,
                                         new_pipeline_name)

    # Upload results
    new_xmls = ET.tostring(new_xml, encoding='utf-8', method='xml')
    gocd_utils.push_config(post_config_xmlurl, md5,
                           new_xmls, (username, password))
