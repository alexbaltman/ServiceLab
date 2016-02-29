import os
import re
import sys
import click

from subprocess import CalledProcessError

from servicelab.utils import openstack_utils as os_utils
from servicelab.utils import service_utils
from servicelab.utils import vagrant_utils as v_utils
from servicelab.utils import helper_utils
from servicelab.stack import pass_context
from servicelab.utils import yaml_utils
from servicelab.utils import vagrantfile_utils as Vf_utils
from servicelab.utils import ccsdata_utils
from servicelab.utils import logger_utils
from servicelab import settings

slab_logger = logger_utils.setup_logger(settings.verbosity, 'stack.up')


@click.option('--full',
              is_flag=True,
              default=False,
              help="Boot complete openstack stack without ha, unless --ha flag is set. "
                   "You can not use the min flag with the full flag")
@click.option('--mini',
              is_flag=True,
              default=False,
              help="Boot min openstack stack without ha,  unless --ha flag is set. "
                   "You can not use min flag with the full flag")
@click.option('--rhel7',
              is_flag=True,
              default=False,
              help='Boot a rhel7 vm.')
@click.option('--target',
              '-t',
              help='pick an OSP target vm to boot.')
@click.option('--service',
              '-s',
              default="",
              help="This is a service you would like to boot a vm "
                   "for. e.g. service-sonarqube")
@click.option('-r',
              '--remote',
              is_flag=True,
              default=False,
              help='Boot into an OS environment')
@click.option('--ha',
              is_flag=True,
              default=False,
              help="Enables HA for core OpenStack components by booting "
                   "the necessary extra VMs.")
@click.option('--redhouse-branch',
              default="release/2.3.3",
              help='Choose a branch to run against for service redhouse tenant and svc.')
@click.option('--data-branch',
              default="master",
              help='Choose a branch of ccs-data')
@click.option('--service-branch',
              default="master",
              help='Choose a branch of your service')
@click.option('-u',
              '--username',
              help='Enter the desired username')
@click.option('-i',
              '--interactive',
              help='Walk through booting VMs')
@click.option('-v',
              '--existing-vm',
              default=False,
              help='Choose a VM from ccs-data to boot.')
@click.option('-e',
              '--env',
              help='Choose an environment from ccs-data.  For use with --existing-vm option')
@click.option('--flavor',
              default='2cpu.4ram.20sas',
              help='Choose the flavor for the VM to use')
@click.option('--image',
              default='slab-RHEL7.1v9',
              help='Choose the image for the VM to use')
@click.group('up',
             invoke_without_command=True,
             short_help="Boot VM(s).")
@pass_context
def cli(ctx, full, mini, rhel7, target, service, remote, ha, redhouse_branch, data_branch,
        service_branch, username, interactive, existing_vm, env, flavor, image):

    flavor = str(flavor)
    image = str(image)
    service_groups = []
    # Things the user Should not do ==================================
    if mini is True and full is True:
        slab_logger.error('You can not use the mini flag with the full flag.')
        sys.exit(1)

    # Gather as many requirements as possible for the user ===========
    if not username:
        slab_logger.log(15, 'Extracting username')
        username = ctx.get_username()

    if not any([full, mini, rhel7, target, service, existing_vm]):
        slab_logger.info("Booting vm from most recently installed service")
        try:
            returncode, service = helper_utils.get_current_service(ctx.path)
        except TypeError:
            slab_logger.error("Could not get the current service.")
            slab_logger.error("Try: stack workon service-myservice")
            sys.exit(1)
        if returncode > 0:
            slab_logger.error("Failed to get the current service")
            sys.exit(1)

    slab_logger.log(15, 'Determining vm hostname')
    hostname = ''
    if rhel7:
        hostname = str(helper_utils.name_vm("rhel7", ctx.path))
    elif service:
        if not service_utils.installed(service, ctx.path):
            slab_logger.error("{0} is not in the .stack/services/ directory.\n"
                              "Try: stack workon {0}".format(service))
            sys.exit(1)
        hostname = str(helper_utils.name_vm(service, ctx.path))
    elif target:
        hostname = target
    elif existing_vm:
        hostname = existing_vm
        ret_code, site = ccsdata_utils.get_site_from_env(env)
        if ret_code > 0:
            slab_logger.error("Could not find parent site for {}".format(env))
            sys.exit(1)
        env_path = os.path.join(ctx.path, 'services', 'ccs-data', 'sites', site,
                                'environments', env)
        ret_code, yaml_data = yaml_utils.read_host_yaml(existing_vm, env_path)
        if ret_code > 0:
            slab_logger.error("Could not find host in site {0} env {1}".format(site, env))
            sys.exit(1)
        try:
            flavor = yaml_data['deploy_args']['flavor']
        except KeyError:
            slab_logger.warning('Unable to find flavor for %s, using default flavor'
                                % hostname)
        service_groups = []
        groups = []
        try:
            for group in yaml_data['groups']:
                if group != 'virtual':
                    groups.append(group)
                    service_group = 'service-' + group.replace('_', '-')
                    if os.path.isdir(os.path.join(ctx.path, 'services', service_group)):
                        service_groups.append(service_group)
        except KeyError:
            pass  # can pass, vm has no groups
        if groups:
            slab_logger.log(25, '\nThe following groups were found within %s yaml file: '
                            % hostname)
            for group in groups:
                slab_logger.log(25, group)
            if not service_groups:
                slab_logger.log(25, '\nNo service groups were found locally installed')
            else:
                slab_logger.log(25, '\nThe following service groups were found installed '
                                'locally:')
                for service in service_groups:
                    slab_logger.log(25, service)
            input_display = ('\nAre the locally installed service groups the expected '
                             'groups to be installed on %s? y/n: ' % hostname)
            if not re.search('^[Yy][Ee]*[Ss]*', raw_input(input_display)):
                slab_logger.log(25, 'Try "stack workon service-<group>" for each to be '
                                'installed and rerun the "stack up --existing-vm" command')
                sys.exit(0)
        else:
            slab_logger.warning('No groups were found for %s.  Continuing to build the VM.'
                                % hostname)

    # Setup data and inventory
    if not target and not mini and not full:
        slab_logger.info('Building data for %s.' % hostname)
        match = re.search('^(\d+)cpu\.(\d+)ram', flavor)
        if match:
            cpus = int(match.group(1))
            memory = int(match.group(2)) * 2
        yaml_utils.host_add_vagrantyaml(ctx.path, "vagrant.yaml", hostname,
                                        "ccs-dev-1", memory=memory, cpus=cpus)
        if not service_groups:
            yaml_utils.write_dev_hostyaml_out(ctx.path, hostname, flavor=flavor, image=image)
        else:
            yaml_utils.write_dev_hostyaml_out(ctx.path, hostname, flavor=flavor, image=image,
                                              groups=service_groups)

        if service or existing_vm:
            retc, myinfo = service_utils.build_data(ctx.path)
            if retc > 0:
                slab_logger.error('Error building ccs-data ccs-dev-1: ' + myinfo)

        # Prep class Objects
        myvfile = Vf_utils.SlabVagrantfile(path=ctx.path, remote=remote)
        if not os.path.exists(os.path.join(ctx.path, 'Vagrantfile')):
            myvfile.init_vagrantfile()
        myvag_env = v_utils.Connect_to_vagrant(vm_name=hostname,
                                               path=ctx.path)

        # Setup Vagrantfile w/ vm
        my_sec_grps = ""
        if remote:
            returncode, float_net, mynets, my_sec_grps = os_utils.os_ensure_network(ctx.path)
            if returncode > 0:
                slab_logger.error("No OS_ environment variables found")
                sys.exit(1)
            myvfile.set_env_vars(float_net, mynets, my_sec_grps)
            returncode, host_dict = yaml_utils.gethost_byname(hostname, ctx.path)
            if returncode > 0:
                slab_logger.error('Failed to get the requested host from your Vagrant.yaml')
                sys.exit(1)
            myvfile.add_openstack_vm(host_dict)
        else:
            returncode, host_dict = yaml_utils.gethost_byname(hostname, ctx.path)
            if returncode > 0:
                slab_logger.error('Failed to get the requested host from your Vagrant.yaml')
                sys.exit(1)
            myvfile.add_virtualbox_vm(host_dict)

        # Get vm running
        myvag_env.v.up(vm_name=hostname)
        returncode, myinfo = service_utils.run_this('vagrant hostmanager', ctx.path)
        if returncode > 0:
            # Second chance.
            returncode, myinfo = service_utils.run_this('vagrant hostmanager '
                                                        '--provider openstack',
                                                        ctx.path)
            if returncode > 0:
                slab_logger.error("Could not run vagrant hostmanager because\
                                 {0}".format(myinfo))
                slab_logger.error("Vagrant hostmanager will fail if you "
                                  "have local vms and remote vms.")
                sys.exit(1)
        # You can exit safely now if you're just booting a rhel7 vm
        if rhel7:
            sys.exit(0)

    # SERVICE VM remaining workflow  =================================
    if service or existing_vm:
        slab_logger.info('Booting service and infra_node vms')
        if remote:
            returncode, infra_name = v_utils.infra_ensure_up(mynets,
                                                             float_net,
                                                             my_sec_grps,
                                                             path=ctx.path)
            if returncode == 1:
                slab_logger.error("Could not boot a remote infra node")
                sys.exit(1)
        else:
            returncode, infra_name = v_utils.infra_ensure_up(None, None, None, path=ctx.path)
            if returncode == 1:
                slab_logger.error("Could not boot a local infra node")
                sys.exit(1)

        returncode, myinfo = service_utils.run_this('vagrant hostmanager', ctx.path)
        if returncode > 0:
            returncode, myinfo = service_utils.run_this('vagrant hostmanager '
                                                        '--provider openstack',
                                                        ctx.path)
            if returncode > 0:
                slab_logger.error("Could not run vagrant hostmanager because\
                                 {0}".format(myinfo))
                slab_logger.error("Vagrant manager will fail if you have local vms"
                                  "and remote vms.")
                sys.exit(1)

        command = ('vagrant ssh {0} -c \"cd /opt/ccs/services/{1}/ && sudo heighliner '
                   '--dev --debug deploy\"')

        if service:
            returncode, myinfo = service_utils.run_this(command.format(infra_name, service),
                                                        ctx.path)
            if returncode > 0:
                slab_logger.error("There was a failure during the heighliner deploy phase of"
                                  " your service. Please see the following information"
                                  "for debugging: ")
                slab_logger.error(myinfo)
                sys.exit(1)
            else:
                sys.exit(0)
        else:  # will only match if existing_vm
            for service in service_groups:
                returncode, myinfo = service_utils.run_this(command.format(infra_name,
                                                                           service),
                                                            ctx.path)
                if returncode > 0:
                    slab_logger.error("There was a failure during the heighliner deploy "
                                      "phase of your service. Please see the following "
                                      "information for debugging: ")
                    slab_logger.error(myinfo)
                    sys.exit(1)
            sys.exit(0)
    elif target:
        slab_logger.info('Booting target service vm')
        redhouse_ten_path = os.path.join(ctx.path, 'services', 'service-redhouse-tenant')
        service_utils.sync_service(ctx.path, redhouse_branch,
                                   username, "service-redhouse-tenant")
        puppet_path = os.path.join(redhouse_ten_path, "puppet")
        if not os.path.exists(os.path.join(puppet_path, "modules", "glance")):
            slab_logger.info('Updating sub repos under service-redhouse-tenant')
            slab_logger.info('This may take a few minutes.')
            returncode, myinfo = service_utils.run_this(
                    "USER={0} librarian-puppet install".format(username),
                    puppet_path)
            if returncode > 0:
                slab_logger.error('Failed to retrieve the necessary puppet configurations.')
                slab_logger.error(myinfo)
                sys.exit(1)
        a = v_utils.Connect_to_vagrant(vm_name=target, path=redhouse_ten_path)
        if yaml_utils.addto_inventory(target, ctx.path) > 0:
            slab_logger.error('Could not add {0} to vagrant.yaml'.format(target))
            sys.exit(1)

        if not os.path.exists(os.path.join(ctx.path, 'services', 'ccs-data')):
            service_utils.sync_service(ctx.path, data_branch, username, 'ccs-data')

        if not os.path.exists(os.path.join(ctx.path, 'services', 'ccs-data', 'out')):
            returncode, myinfo = service_utils.build_data(ctx.path)
            if returncode > 0:
                slab_logger.error('Failed to build ccs-data data b/c ' + myinfo)
                sys.exit(1)

        if not os.path.islink(os.path.join(redhouse_ten_path,
                                           "dev",
                                           "ccs-data")):
            slab_logger.debug('WARNING: Linking ' + os.path.join(redhouse_ten_path, 'dev',
                                                                 'ccs-data') + "with  " +
                              os.path.join(ctx.path, "services", "ccs-data"))
            # Note: os.symlink(src, dst)
            os.symlink(os.path.join(ctx.path,
                                    "services",
                                    "ccs-data"
                                    ),
                       os.path.join(redhouse_ten_path,
                                    "dev",
                                    "ccs-data"))

        if remote:
            settingsyaml = {'openstack_provider': True}
            returncode = yaml_utils.wr_settingsyaml(ctx.path, settingsyaml, hostname=target)
            if returncode > 0:
                slab_logger.error('Failed to write settings yaml - make sure you have your '
                                  'OS cred.s sourced and have access to'
                                  'ccs-gerrit.cisco.com and have keys setup.')
                sys.exit(1)
            a.v.up(vm_name=target, provider='openstack')
        else:
            settingsyaml = {'openstack_provider': 'false'}
            returncode = yaml_utils.wr_settingsyaml(ctx.path, settingsyaml=settingsyaml)
            if returncode > 0:
                slab_logger.error('Failed to write settings yaml - make sure you have your '
                                  'OS cred.s sourced and have access to'
                                  'ccs-gerrit.cisco.com and have keys setup.')
                sys.exit(1)
            a.v.up(vm_name=target)

        """
        The code for host manager is not implemented in service-redhouse-tenant Vagrant File.
        So this is currently stubbed out, as it causes Vagrant errors.
        """
        __EXECUTE__ = None
        if __EXECUTE__:
            returncode, myinfo = service_utils.run_this('vagrant hostmanager',
                                                        redhouse_ten_path)
            if returncode > 0:
                returncode, myinfo = service_utils.run_this('vagrant hostmanager '
                                                            '--provider openstack',
                                                            redhouse_ten_path)
                if returncode > 0:
                    slab_logger.error("Could not run vagrant hostmanager because\
                                     {0}".format(myinfo))
                    sys.exit(1)
        sys.exit(0)

    service_utils.sync_service(ctx.path,
                               redhouse_branch,
                               username,
                               "service-redhouse-tenant")

    if mini:
        slab_logger.info('Booting vms for mini OSP deployment')
        returncode, allmy_vms = yaml_utils.getmin_OS_vms(ctx.path)
    elif full:
        slab_logger.info('Booting vms for full OSP deployment')
        returncode, allmy_vms = yaml_utils.getfull_OS_vms(os.path.join(ctx.path,
                                                                       'provision'),
                                                          '001')
    else:
        return 0
    if returncode > 0:
        slab_logger.error("Couldn't get the vms from the vagrant.yaml.")
        sys.exit(1)

    returncode, order = yaml_utils.get_host_order(os.path.join(ctx.path, 'provision'))
    if returncode > 0:
        slab_logger.error("Couldn't get order of vms from order.yaml")
        sys.exit(1)
    try:
        # Note: not sure if this will work w/ vm_name set to infra-001 arbitrarily
        # Note: move path to ctx.path if able to boot OSP pieces via infra/heighliner
        redhouse_ten_path = os.path.join(ctx.path, 'services', 'service-redhouse-tenant')
        a = v_utils.Connect_to_vagrant(vm_name='infra-001',
                                       path=os.path.join(redhouse_ten_path))
        myvfile = Vf_utils.SlabVagrantfile(path=ctx.path, remote=remote)
        if remote:
            returncode, float_net, mynets, my_sec_grps = os_utils.os_ensure_network(ctx.path)
            if returncode > 0:
                slab_logger.error('Failed to get float net and mynets')
                sys.exit(1)
            myvfile.set_env_vars(float_net, mynets, my_sec_grps)

        if not os.path.exists(os.path.join(ctx.path, 'Vagrantfile')):
            myvfile.init_vagrantfile()
        puppet_path = os.path.join(redhouse_ten_path, "puppet")
        if not os.path.exists(os.path.join(puppet_path, "modules", "glance")):
            slab_logger.info('Updating sub repos under service-redhouse-tenant')
            slab_logger.info('This may take a few minutes.')
            returncode, myinfo = service_utils.run_this(
                                    "USER={0} librarian-puppet install".format(username),
                                    puppet_path)
            if returncode > 0:
                slab_logger.error('Failed to retrieve the necessary puppet configurations.')
                slab_logger.error(myinfo)
            returncode = service_utils.copy_certs(os.path.join(
                                                               ctx.path,
                                                               "provision"),
                                                  puppet_path)
            if returncode > 0:
                slab_logger.error('Failed to copy haproxy certs to ccs puppet module.')
                sys.exit(1)
        if not os.path.exists(os.path.join(ctx.path, 'services', 'ccs-data')):
            service_utils.sync_service(ctx.path, data_branch, username, 'ccs-data')

        if not os.path.exists(os.path.join(ctx.path, 'services', 'ccs-data', 'out')):
            returncode, myinfo = service_utils.build_data(ctx.path)
            if returncode > 0:
                slab_logger.error('Failed to build ccs-data data b/c ' + myinfo)
                sys.exit(1)

        if not os.path.islink(os.path.join(redhouse_ten_path,
                                           "dev",
                                           "ccs-data")):
            slab_logger.debug('WARNING: Linking ' + os.path.join(redhouse_ten_path, 'dev',
                                                                 'ccs-data') + "with  " +
                              os.path.join(ctx.path, "services", "ccs-data"))
            # Note: os.symlink(src, dst)
            os.symlink(os.path.join(ctx.path,
                                    "services",
                                    "ccs-data"
                                    ),
                       os.path.join(redhouse_ten_path,
                                    "dev",
                                    "ccs-data"))
        for i in order:
            # Need to build nodes in specific order
            # so filter out everything but
            # if result is empty, then don't built this node and skip
            # variables aren't referenced outside of a lambda, so had
            # to pass in current node (i) as variable o
            vhosts = filter(lambda x, o=i: o in x, allmy_vms)
            if len(vhosts) == 0:
                continue
            if ha:
                ha_vm = vhosts.replace("001", "002")
                returncode, ha_vm_dicts = yaml_utils.gethost_byname(ha_vm,
                                                                    os.path.join(ctx.path,
                                                                                 'provision')
                                                                    )
                if returncode > 0:
                    slab_logger.error("Couldn't get the vm {0} for HA".format(ha_vm))
                    sys.exit(1)
                else:
                    allmy_vms.append(ha_vm_dicts)
            for hosts in vhosts:
                for host in hosts:
                    newmem = (hosts[host]['memory']/512)
                    retcode = yaml_utils.host_add_vagrantyaml(path=ctx.path,
                                                              file_name="vagrant.yaml",
                                                              hostname=host,
                                                              site='ccs-dev-1',
                                                              memory=newmem,
                                                              box=hosts[host]['box'],
                                                              role=hosts[host]['role'],
                                                              profile=hosts[host]['profile'],
                                                              domain=hosts[host]['domain'],
                                                              mac_nocolon=hosts[host]['mac'],
                                                              ip=hosts[host]['ip'],
                                                              )
                if retcode > 0:
                    slab_logger.error("Failed to add host" + host)
                    slab_logger.error("Continuing despite failure...")
            curhost = vhosts[0].keys()[0]
            if remote:
                settingsyaml = {'openstack_provider': True}
                returncode = yaml_utils.wr_settingsyaml(ctx.path,
                                                        settingsyaml,
                                                        hostname=curhost)
                if returncode > 0:
                    slab_logger.error('writing to settings yaml failed on: ' + curhost)
                myvfile.add_openstack_vm(vhosts[0])
                a.v.up(vm_name=curhost, provider='openstack')
            else:
                myvfile.add_virtualbox_vm(vhosts[0])
                a.v.up(vm_name=curhost)
    except IOError as e:
        slab_logger.error("{0} for vagrant.yaml in {1}".format(e, ctx.path))
        sys.exit(1)
