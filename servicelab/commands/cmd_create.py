import os
import re
import yaml
import click
from fabric.api import run
from servicelab.stack import pass_context
from servicelab.utils import helper_utils
from servicelab.utils import service_utils
from servicelab.utils import ccsbuildtools_utils
from servicelab.utils import ccsdata_utils
from servicelab.utils import yaml_utils
from servicelab.utils import tc_vm_yaml_create
from servicelab.utils.ccsdata_haproxy_utils import *


@click.group('create', short_help='Creates pipeline resources to work with.',
             add_help_option=True)
@click.pass_context
def cli(ctx):
    """Stack Create command line client"""
    pass


@cli.command('repo', short_help='Create repo')
@click.argument('repo_name', required=True)
@click.option('--kind', prompt='Which type of repo? '
                               'Standard, Ansible, or Puppet')
@pass_context
def repo_new(ctx, repo_name, kind):
    """Creates a repository in gerrit production, does 1st commit,
    sets up directory structure, and creates nimbus.yml by leveraging
    Fabric's Pythonic remote execution.

    Sets up service automation dir structure when init a gerrit repo.

    For instance if it's puppet, setup that directory structure

    If it's Ansible have user commit it.

    Add .nimbus.yml file to repo

    Add an interactive mode so they can choose options.

    :param repo_name:    The name of the repository
    :param kind:         The type of repo (Standard, Ansible, Puppet)

    .. note::
        Work to be done to keep up with DRY principles and
        folder structure setup. Needs prompt validation if user did not input
        correct type of repo.
    """
    kind_lower = kind.lower()
    click.echo('Creating Project: {}'.format(kind_lower))
    if kind_lower == 'standard':
        run('fab create_standard')
    elif kind_lower == 'ansible':
        run('fab create_ansible')
    elif kind_lower == 'puppet':
        run('fab create_puppet')
    return


@cli.command('host')
@click.argument('host_name')
@click.argument('env_name')
@click.option('--vlan', default="66", help='Choose the vlan to add your vm to or default\
                              is set to 66')
@click.option('--flavor', default="2cpu.4ram.20-96sas", help='Choose the flavor for the vm.\
                          Default is set to 2cpu.4ram.20-96sas')
@click.option('--role', default='none', help='Choose the role of the vm if needed, or the\
                          default is "none"')
@click.option('--group', help='Choose the group, default is virtual')
@click.option('--sec-groups', help='Choose the security groups, comma delimited')
@pass_context
def host_new(ctx, host_name, env_name, vlan, flavor, role, group, sec_groups):
    """
    Creates a host.yaml file in an environment so that a vm can then be
    booted.

    HOST_NAME can be the service name and number - my-service-001

    ENV_NAME is the name of the tenant cloud.  Use 'stack list envs' to show all tenants
    """
    ccs_datapath = os.path.join(ctx.path, "services", "ccs-data")
    our_sites = ccsdata_utils.list_envs_or_sites(ctx.path)
    site = ccsdata_utils.get_site_from_env(our_sites, env_name)
    if site is None:
        print '%s is an invalid env.  Please select one from "stack list envs"' % env_name
        return 1
    groups = ['virtual', str(group)]
    if sec_groups:
        sec_groups = 'default,' + sec_groups
    else:
        sec_groups = 'default'
    tc_vm_yaml_create.create_vm(ccs_datapath, host_name, str(site), str(env_name),
                                str(flavor), str(vlan), str(role), groups,
                                str(sec_groups))


@cli.command('site')
@click.option('cont', '--continue', help='If you did not finish \
               creating your site and paused midway you can continue it.')
@click.option('cont', '--abort', help='If you did not finish \
               creating your site and paused midway you can abort it.')
@click.option('-u', '--username', help='Enter the password for the username')
@pass_context
def site_new(ctx, username, cont):
    """
    Create a whole new site in ccs-data.
    """
    # Get username
    if username is None or "":
        returncode, username = helper_utils.set_user(ctx.path)
    click.echo("Retrieving latest ccs-data branch")
    service_utils.sync_data(ctx.path, username, "master")
    click.echo("Retrieving latest ccs-build-tools branch")
    service_utils.sync_service(ctx.path, "master", username, "ccs-build-tools")
    # TODO: Make sure I have installed required packages for ccs-build-tools -> add to reqs
    click.echo("Retreiving user input for new site's data fields...")
    returncode, site_name = ccsbuildtools_utils.gather_site_info(ctx.path)
    click.echo("---Building and Exporting site to ccs-data---")
    passed, log = service_utils.run_this('vagrant up',
                                         os.path.join(ctx.path, "services",
                                                      "ccs-build-tools", "ignition_rb"
                                                      )
                                         )
    click.echo("Printing log of ccs-build-tools...")
    click.echo(log)
    if passed == 1:
        return False
    service_utils.run_this('cp ccs-build-tools/ignition_rb/sites/%s ccs-data/sites'
                           % (site_name), os.path.join(ctx.path, "services")
                           )
    service_utils.run_this('vagrant destroy -f',
                           os.path.join(ctx.path, "services",
                                        "ccs-build-tools", "ignition_rb")
                           )
    click.echo("---Site Data Gathered. Check .stack/services/ccs-data for its contents---")


@cli.command('env')
@click.argument('env_name')
# What site to put your named environment under.
@click.argument('site')
@click.option('cont', '--continue', help='If you did not finish \
               creating your site and paused midway you can continue it.')
@click.option('cont', '--abort', help='If you did not finish \
               creating your site and paused mid-way you can abort it.')
@click.option('-u', '--username', help='Enter the password for the username')
@pass_context
def env_new(ctx, env_name, site, cont):
    """
    Create a new environment in a site in ccs-data.
    """
    click.echo('Creating new env yamls in %s for %s' % (site, env_name))
    # Get username
    # if username is None or "":
    #    helper_utils.set_user(ctx.path)
    # Ensure you have latest ccs-data branch
    # Might need to replace ".' with path to reporoot... from class context?
    # service_utils.sync_data("./servicelab/servicelab/.stack", username, master)
    # Check for the site in ccs-data
    # site_path = os.path.join("./servicelab/servicelab/.stack", "services", "ccs-data", \
    #                      "sites", site, "environments", env_name)
    #    if not os.path.exists(site_path)
    #       echo "Site does not exist"
    #      return False
    # Manually inject file into the site
    # Build data via BOM Generation Script
    #   service_utils.build_data("./servicelab/servicelab/.stack")
    #    return True


# RFI: is this the right place for this integration w/ haproxy?
def validate_location(ctx, param, value):
    if value is None or value == "internal" or value == "external":
        return value
    else:
        raise click.BadParameter("location can only be internal or extermal")


def validate_ip(ctx, param, value):
    if value is None:
        return value

    reg_ipv4 = "^([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\." + \
               "([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\." + \
               "([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\." + \
               "([01]?\\d\\d?|2[0-4]\\d|25[0-5])$"
    ipv4pat = re.compile(reg_ipv4)

    if not ipv4pat.match(value):
        raise click.BadParameter("invalid ip address ")

    return value


@cli.command('vip')
@click.argument('vip_name')
@click.argument('env_name')
@click.argument('service_entry')
@click.option('location', '--loc', default="internal", callback=validate_location,
              help="if the entry has to be put in internal or external haproxy")
@click.option('ip', '--ip', callback=validate_ip, prompt=True,
              help="ip associated with the vip")
@click.option('server_ips', '--server_ips',
              help="server ips associated with the vip")
@click.option('server_hostnames', '--server_hostnames',
              help="servers hostnames associated with the vip")
@click.option('interactive', '--i', flag_value=True,
              help="interactive editor")
@pass_context
def vip_new(ctx, env_name, vip_name, service_entry, location, ip, server_ips,
            server_hostnames, interactive):
    """
    Create a new VIP in all the sites having a partical environment env_name in
    ccs-data. Add this service_entry as  haproxy service.

    The haproxy instance can be internal or external. If the supplied haproxy
    instance is missing from the environemt yaml file then service is not
    added.

    By default only certain entries will be generated. For instance:
        stack create vip vip123 dev internal celiometer
    will create the following entries in haproxy:

        ccs::proxy_internal::haproxy_instances:
          ceilometer:
            port: 62970
            server_ips: ceilometer
            ssl: false
            vip: '%%{}{hiera(''vip123'')}'

    The port number is randomly generated port number and  ssl is always set to false.
    The ip option specifies the ip associated with the specific vip_name. If supplied
    then service_ips and service_hostnames are added.

    One can also invoke the command in interactive mode where the haproxy instance
    options can be specied and build dynamically.

    """
    for sites in generate_env_for_site(ctx.path, env_name):
        flag = False
        for key in search(sites['env'], "%s::haproxy" % (location)):
            sites['env'][vip_name] = ip
            try:
                subkey = next(search(sites['env'][key], service_entry))
                sites['env'][key][subkey] = generate_tag_value(sites['env'],
                                                               service_entry,
                                                               vip_name,
                                                               server_ips,
                                                               server_hostnames,
                                                               interactive)
            except StopIteration, e:
                sites['env'][key][service_entry] = generate_tag_value(sites['env'],
                                                                      service_entry,
                                                                      vip_name,
                                                                      server_ips,
                                                                      server_hostnames,
                                                                      interactive)
            save_ccsdata(ctx.path, sites['site'], env_name, sites['env'])
            flag = True
        if not flag:
            click.echo("missing %s::haproxy in environment.yaml file for site %s"
                       % (location, sites['site']))
