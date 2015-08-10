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
@click.option('-e', '--env', help='Choose an environment to put your host \
               into - use the list command to see what environments are \
               available.')
@pass_context
def host_new(ctx, host_name, env):
    """
    Creates a host.yaml file in an environment so that a vm can then be
    booted.
    """
    click.echo('creating new host yaml for %s ...' % host_name)


@cli.command('site')
@click.argument('site_name')
@click.option('cont', '--continue', help='If you did not finish \
               creating your site and paused midway you can continue it.')
@click.option('cont', '--abort', help='If you did not finish \
               creating your site and paused midway you can abort it.')
@click.option('-u', '--username', help='Enter the password for the username')
@pass_context
def site_new(ctx, site_name, username, cont):
    """
    Create a whole new site in ccs-data.
    """
    click.echo('creating new site directory')
    # Get username
    if username is None or "":
        returncode, username = helper_utils.set_user(ctx.path)
    print "Retrieving latest ccs-data branch"
    service_utils.sync_data(ctx.path, username, "master")
    print "Retrieving latest ccs-build-tools branch"
    service_utils.sync_service(ctx.path, "master", username, "ccs-build-tools")
    # TODO: Make sure I have installed required packages for ccs-build-tools -> add to reqs
    print "Writing site specs to answer-sample.yaml"
    ccsbuildtools_utils.overwrite_ansyaml(ctx.path)
    # print "Building and exporting site to ccs-data"
    # passed, log = service_utils.run_this('vagrant up', \
    #                         os.path.join(ctx.path, "services", \
    #                       "ccs-build-tools", "ignition_rb")
    #                    )
    # if log == 1:
    #  return False
    # service_utils.run_this('cp ccs-build-tools/ignition_rb/sites/%s ccs-data/sites' \
    #                        % (site_name) , os.path.join(ctx.path, "services")
    #                      )


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
