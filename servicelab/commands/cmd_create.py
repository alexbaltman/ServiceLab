"""
The repo module provides a set of repo subcommands to
1. Creates a repository in gerrit production and locally.
2. Creates a host.yaml file in an environment.
3. Compiles data for a new site in the ccs-data repo.
4. Compiles data for a new environment to be built on top of an existing site
   in the ccs-data repo.
5. Create a new VIP in all the sites having a partical environment env_name in
   ccs-data.
"""
import os
import re
import click

import servicelab.utils.ccsdata_haproxy_utils as haproxy

from servicelab.stack import pass_context
from servicelab.utils import create_repo
from servicelab.utils import service_utils
from servicelab.utils import ccsbuildtools_utils
from servicelab.utils import ccsdata_utils
from servicelab.utils import tc_vm_yaml_create
from servicelab.utils import yaml_utils
from servicelab.utils import helper_utils


@click.group('create', short_help='Creates pipeline resources to work with.',
             add_help_option=True)
@click.pass_context
def cli(_):
    """Stack Create command line client"""
    pass


@cli.command('repo',
             short_help='Create a git repository in Gerrit.')
@click.argument('repo_name',
                required=True)
@click.option('--repo-type',
              default='ansible',
              type=click.Choice(['project', 'ansible', 'puppet', "empty"]),
              help="The type of repo (empty, project, ansible, puppet)\n"
                   "A project repo type will create a project of normal type.\n"
                   "Ansible will create a service repo of ansible type.\n"
                   "Puppet will create a service repo of ansible type.\n")
@click.option('-u',
              '--username',
              help='Username used for cloning repos from gerrit')
@click.option('-i',
              '--interactive',
              flag_value=True,
              help="interactive editor")
@pass_context
def repo_new(ctx, repo_name, repo_type, username, interactive):
    """Creates a repository in gerrit production, does 1st commit,
    sets up directory structure, and creates nimbus.yml.

    Sets up service automation dir structure when init a gerrit repo.

    For instance if it's puppet, setup that directory structure

    Add .nimbus.yml file to repo

    Add an interactive mode so they can choose options.
    """
    ctx.logger.info('Creating new repo %s' % repo_name)
    if not username:
        username = ctx.get_username()
    kinds = dict(project="Project", ansible="Ansible",
                 puppet="Puppet", empty="EmptyProject")
    repo = create_repo.Repo.builder(kinds[repo_type], ctx.get_gerrit_server(), ctx.path,
                                    repo_name, username, interactive)
    repo.construct()
    return


@cli.command('host', short_help='Create a host in the local ccs-data repository.')
@click.argument('host_name')
@click.argument('env_name')
@click.option('--ip-address',
              '-ip',
              default=None,
              help='Specify the IP address to use.  ' +
                   '--vlan will be ignored if this option is used'
              )
@click.option('--vlan',
              '-v',
              default="66",
              help='Choose the vlan to add your vm to or default is set to 66'
              )
@click.option('--flavor',
              '-f',
              default="2cpu.4ram.20-96sas",
              help='Choose the flavor for the vm.  Default is set to 2cpu.4ram.20-96sas')
@click.option('--role',
              '-r',
              default='none',
              help='Choose the role of the vm if needed, or the default is "none"')
@click.option('--group',
              '-g',
              help='Choose the group, default is virtual'
              )
@click.option('--sec-groups',
              '-s',
              help='Choose the security groups, comma delimited'
              )
@click.option('--template',
              '-t',
              default=None,
              help='Source file to extract data from.  ' +
                   'Needs to be in the same environment as the new vm to be created'
              )
@pass_context
def host_new(ctx, host_name, env_name, ip_address, vlan, flavor, role, group, sec_groups,
             template):
    """
    Creates a host.yaml file in an environment so that a vm can then be booted.

    HOST_NAME can be the service name and number - my-service-001

    ENV_NAME is the name of the tenant cloud.  Use 'stack list envs' to show all tenants
    """
    ctx.logger.info('Creating file for %s' % host_name)
    groups = ''
    ccs_datapath = os.path.join(ctx.path, 'services', 'ccs-data')
    ret_code, site = ccsdata_utils.get_site_from_env(env_name)
    if ret_code > 0:
        return 1
    if template:
        ctx.logger.log(15, 'Building template data')
        env_path = os.path.join(ccs_datapath, 'sites', site, 'environments', env_name)
        ret_code, yaml_data = yaml_utils.read_host_yaml(template, env_path)
        if ret_code > 0:
            return 1
        if 'groups' in yaml_data:
            groups = yaml_data['groups']
        if 'role' in yaml_data:
            role = yaml_data['role']
        if 'deploy_args' in yaml_data:
            if 'flavor' in yaml_data['deploy_args']:
                flavor = yaml_data['deploy_args']['flavor']
            if 'security_groups' in yaml_data['deploy_args']:
                sec_groups = yaml_data['deploy_args']['security_groups']
            if 'network_name' in yaml_data['deploy_args']:
                net_name = yaml_data['deploy_args']['network_name']
                match = re.search('\D+(\d+)$', net_name)
                if match:
                    vlan = match.group(1)
    if not groups:
        if not group:
            groups = ['virtual']
        else:
            groups = ['virtual', str(group)]
    if sec_groups:
        sec_groups = 'default,' + sec_groups
    else:
        sec_groups = 'default'
    if ip_address:
        ip_address = str(ip_address)
    ret_code = tc_vm_yaml_create.create_vm(ccs_datapath, host_name, str(site),
                                           str(env_name), str(flavor),
                                           str(vlan), str(role), groups,
                                           str(sec_groups), ip_address)
    if ret_code > 0:
        click.echo("File for %s was not created.  Exiting." % host_name)


@cli.command('site', short_help='Create a new site in the local ccs-data repository.')
@click.option('--continue', 'cont', flag_value='continue',
              help="If you did not finish creating your site and paused midway;"
                   " you can continue or abort it.")
@click.option('-u', '--username', help='Username used for cloning repos from gerrit')
@pass_context
def site_new(ctx, username, cont):
    """Compiles data for a new site in the ccs-data repo.

    \b
    1) Syncs the ccs-data and ccs-build-tools repo into the .stack/services directory.
    2) Allows the user to dynamically input data pertaining to the new site which
       is comprised of a single tenant cloud built on top of a service cloud.
       *The data compilation can be quit and resumed for a later time (the temporary
        data is stored in .stack/cache/temp_site.yaml
    3) The data is compiled into a single yaml file (answer-sample.yaml) located in the
       ccs-build-tools/ignition_rb directory and includes:
           *bom version
           *CIMC password
           *vlan numbers and their corresponding ip ranges
           *service cloud information:
               *site name
               *availability zone
               *domain
               *number of virtualized nova cloud nodes
           *tenant cloud information:
               *site name
               *availability zone
               *domain
               *number of virtualized nova, ceph, net and proxy nodes
    4) Within ccs-build-tool, a vagrant environment and virtualbox is used to compile all
       of the data into a single site directory, which is copied into ccs-data.
    """
    ctx.logger.info("Creating a new site in ccs-data")
    if not username:
        username = ctx.get_username()

    ctx.logger.log(15, "Retrieving latest ccs-data branch")
    service_utils.sync_service(ctx.path, "master", username, "ccs-data")

    ctx.logger.log(15, "Retrieving latest ccs-build-tools branch")
    service_utils.sync_service(ctx.path, "master", username, "ccs-build-tools")

    ctx.logger.log(15, "Retreiving user input for new site's data fields...")
    returncode, site_dictionary = ccsbuildtools_utils.gather_site_info(ctx.path, cont)
    if returncode != 1:
        ctx.logger.error("unable to retrieve site data")
        return

    svc_site_name = site_dictionary['service_cloud']['site_name']
    ctx.logger.log(15, "Building and Exporting %s to ccs-data---" % (svc_site_name))
    passed, log = service_utils.run_this('vagrant up; vagrant destroy -f;',
                                         os.path.join(ctx.path, "services",
                                                      "ccs-build-tools"))
    if passed > 0:
        ctx.logger.error("Failed to establish vagrant environment in ccs-build-tools")
        ctx.logger.error("Printing log of vagrant up command in ccs-build-tools")
        ctx.logger.error(log)
        return

    # Copying over contents of files generated by ccsbuildtools into ccs-data
    cmds = "cp -r ccs-build-tools/sites/%(svc)s ccs-data/sites; " \
           "rm -rf ccs-build-tools/sites; " % {'svc': svc_site_name}
    passed, log = service_utils.run_this(cmds, os.path.join(ctx.path, "services"))
    if passed > 0:
        ctx.logger.error("Failed to copy site into ccs-data")
        ctx.logger.error("Printing log of directory exports")
        ctx.logger.error(log)
        return

    ctx.logger.info("Site Data Gathered for %s. Check .stack/services/ccs-data "
                    "for its contents---" % (svc_site_name))


@cli.command('env', short_help='Create a new environment in the local ccs-data repository.')
@click.option('-u', '--username', help='Enter the username')
@pass_context
def env_new(ctx, username):
    """Compiles data for a new environment to be built on top of an existing
    site in the ccs-data repo.

    \b
    1) Syncs the ccs-data and ccs-build-tools repo into the .stack/services directory.
    2) Allows the user to dynamically input data pertaining to the new environment, which
       will be built on top of an existing, specified service cloud.
    3) The data is compiled into a single yaml file (answer-sample.yaml) located in the
       ccs-build-tools/ignition_rb directory and includes:
           *bom version
           *CIMC password
           *vlan numbers and their corresponding ip ranges
           *service cloud information:
               *site name
               *availability zone
               *domain
               *number of virtualized nova cloud nodes
           *tenant cloud information:
               *site name
               *availability zone
               *domain
               *number of virtualized nova, ceph, net and proxy nodes
    4) Within ccs-build-tool, a vagrant environment and virtualbox is used to compile all
       of the data into a single site directory, with which the appropriate environment
       is extracted and copied to the appropriate folder in ccs-data.

      Args:
        ctx: context
        username: credential used for cloning repos from gerrit
    """
    click.echo('Creating a new environment')

    # Get username
    if not username:
        username = ctx.get_username()

    ctx.logger.info("Retrieving latest ccs-data branch")
    service_utils.sync_service(ctx.path, "master", username, "ccs-data")
    ctx.logger.info("Retrieving latest ccs-build-tools branch")
    service_utils.sync_service(ctx.path, "master", username, "ccs-build-tools")

    # Ensure you have latest ccs-data branch
    returncode, site_dictionary = ccsbuildtools_utils.gather_env_info(ctx.path)
    if returncode > 0:
        ctx.logger.error("unable to get the sites information")
        return

    svc_site_name = site_dictionary['service_cloud']['site_name']
    tc_site_name = site_dictionary['tenant_cloud']['site_name']
    ctx.logger.log(15, "Building and Exporting %s to ccs-data---" % (svc_site_name))
    passed, log = service_utils.run_this('vagrant up; vagrant destroy -f; ',
                                         os.path.join(ctx.path, "services",
                                                      "ccs-build-tools"))
    if passed > 0:
        ctx.logger.error("Failed to establish vagrant environment in ccs-build-tools")
        ctx.logger.error("Printing log of vagrant up command in ccs-build-tools")
        ctx.logger.error(log)
        return

    # Copying over contents of files generated by ccsbuildtools into ccs-data
    cmds = "cp -r ccs-build-tools/sites/%(svc)s/environments/%(tc)s "\
           "ccs-data/sites/%(svc)s/environments; "\
           "rm -rf ccs-build-tools/sites; " % {'svc': svc_site_name,
                                               'tc': tc_site_name}
    passed, log = service_utils.run_this(cmds, os.path.join(ctx.path, "services"))
    if passed > 0:
        ctx.logger.error("Failed to copy environment into ccs-data")
        ctx.logger.error("Printing log of directory exports")
        ctx.logger.error(log)
        return

    ctx.logger.info("Env Data Gathered for %s in site %s. Check .stack/services/ccs-data "
                    "for its contents" % (tc_site_name, svc_site_name))


def cb_validate_location(ctx, param, value):
    """
    Validate the location. It can be internal, external or just empty.

    Raises:
        click.BadParameter: If the value supplied is other than internal, external or
                            an empty string.
    """
    if value is None or value == "internal" or value == "external":
        return value
    else:
        raise click.BadParameter("location can only be internal or external")


def cb_validate_ip(ctx, param, value):
    """
    Validate if value supplied is as IPv4 address

    Raises:
        click.BadParameter: If the value supplied is not confirmting to IPv4
    """
    if not value:
        return value

    reg_ipv4 = "^([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\." + \
               "([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\." + \
               "([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\." + \
               "([01]?\\d\\d?|2[0-4]\\d|25[0-5])$"
    ipv4pat = re.compile(reg_ipv4)

    if not ipv4pat.match(value):
        raise click.BadParameter("invalid ip address ")

    return value


@cli.command('vip', short_help='Add a vip for your service to a site in the local'
             ' ccs-data repository.')
@click.argument('vip_name')
@click.argument('env_name')
@click.argument('service_entry')
@click.option('location', '--loc', default="internal", callback=cb_validate_location,
              help="if the entry has to be put in internal or external haproxy")
@click.option('ip_address', '--ip', callback=cb_validate_ip, prompt=True,
              help="ip associated with the vip")
@click.option('server_ips', '--server_ips', multiple=True,
              help="server ips associated with the vip")
@click.option('server_hostnames', '--server_hostnames', multiple=True,
              help="servers hostnames associated with the vip")
@click.option('interactive', '--i', flag_value=True,
              help="interactive editor")
@pass_context
def vip_new(ctx, vip_name, env_name, service_entry, location, ip_address, server_ips,
            server_hostnames, interactive):
    """
    Create a new VIP in all the sites having a partical environment env_name in
    ccs-data. Add this service_entry as  haproxy service.

    The haproxy instance can be internal or external. If the supplied haproxy
    instance is missing from the environemt yaml file then service is not
    added.

    \b
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
    for sites in haproxy.generate_env_for_site(ctx.path, env_name):
        flag = False
        for key in haproxy.search(sites['env'], "%s::haproxy" % (location)):
            sites['env'][vip_name] = ip_address
            lst_ips = list(server_ips)
            lst_hostnames = list(server_hostnames)
            try:
                subkey = next(haproxy.search(sites['env'][key], service_entry))
                sites['env'][key][subkey] = haproxy.generate_tag_value(sites['env'],
                                                                       service_entry,
                                                                       vip_name,
                                                                       lst_ips,
                                                                       lst_hostnames,
                                                                       interactive)
            except StopIteration:
                sites['env'][key][service_entry] = haproxy.generate_tag_value(sites['env'],
                                                                              service_entry,
                                                                              vip_name,
                                                                              lst_ips,
                                                                              lst_hostnames,
                                                                              interactive)
            haproxy.save_ccsdata(ctx.path, sites['site'], env_name, sites['env'])
            flag = True
        if not flag:
            ctx.logger.error("missing %s::haproxy in environment.yaml file for site %s"
                             % (location, sites['site']))
