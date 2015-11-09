import os
import sys
from subprocess import CalledProcessError

import click

from servicelab.utils import openstack_utils as os_utils
from servicelab.utils import service_utils
from servicelab.utils import vagrant_utils as v_utils
from servicelab.utils import helper_utils
from servicelab.stack import pass_context
from servicelab.utils import yaml_utils
from servicelab.utils import Vagrantfile_utils as Vf_utils


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
@click.group('up',
             invoke_without_command=True,
             short_help="Boots VM(s).")
@pass_context
def cli(ctx, full, mini, rhel7, target, service, remote, ha, redhouse_branch, data_branch,
        service_branch, username, interactive):

    # Things the user Should not do ==================================
    if mini is True and full is True:
        ctx.logger.error("You can not use the mini flag with the full flag.")
        sys.exit(1)

    # Gather as many requirements as possible for the user ===========
    if not username:
        username = ctx.get_username()

    if not any([full, mini, rhel7, target, service]):
        try:
            returncode, service = helper_utils.get_current_service(ctx.path)
        except TypeError:
            ctx.logger.error("Could not get the current service.")
            ctx.logger.error("Try: stack workon service-myservice")
            sys.exit(1)
        if returncode > 0:
            ctx.logger.debug("Failed to get the current service")
            sys.exit(1)

    hostname = ''
    if rhel7:
        hostname = str(helper_utils.name_vm("rhel7", ctx.path))
    elif service:
        if not service_utils.installed(service, ctx.path):
            ctx.logger.error("{0} is not installed on the stack.\n"
                             "Try: stack workon {0}".format(service))
            sys.exit(1)
        hostname = str(helper_utils.name_vm(service, ctx.path))
    elif target:
        hostname = target

    # Setup data and inventory
    if not target and not mini and not full:
        yaml_utils.host_add_vagrantyaml(ctx.path, "vagrant.yaml", hostname,
                                        "ccs-dev-1")
        yaml_utils.write_dev_hostyaml_out(ctx.path, hostname)
        if service:
            retc, myinfo = service_utils.build_data(ctx.path)
            if retc > 0:
                ctx.logger.error('Error building ccs-data ccs-dev-1: ' + myinfo)

        # Prep class Objects
        myvfile = Vf_utils.SlabVagrantfile(path=ctx.path)
        if not os.path.exists(os.path.join(ctx.path, 'Vagrantfile')):
            myvfile.init_vagrantfile()
        myvag_env = v_utils.Connect_to_vagrant(vm_name=hostname,
                                               path=ctx.path)

        # Setup Vagrantfile w/ vm
        my_sec_grps = ""
        if remote:
            returncode, float_net, mynets, my_sec_grps = os_utils.os_ensure_network(ctx.path)
            if returncode > 0:
                ctx.logger.debug("No OS_ environment variables found")
                sys.exit(1)
            myvfile._vbox_os_provider_env_vars(float_net, mynets, my_sec_grps)
            returncode, host_dict = yaml_utils.gethost_byname(hostname, ctx.path)
            if returncode > 0:
                ctx.logger.error('Failed to get the requested host from your Vagrant.yaml')
                sys.exit(1)
            myvfile.add_openstack_vm(host_dict)
        else:
            returncode, host_dict = yaml_utils.gethost_byname(hostname, ctx.path)
            if returncode > 0:
                ctx.logger.error('Failed to get the requested host from your Vagrant.yaml')
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
                ctx.logger.error("Could not run vagrant hostmanager because\
                                 {0}".format(myinfo))
                ctx.logger.error("Vagrant manager will fail if you "
                                 "have local vms and remote vms.")
                sys.exit(1)
        # You can exit safely now if you're just booting a rhel7 vm
        if rhel7:
            sys.exit(0)

    # SERVICE VM remaining workflow  =================================
    if service:
        if remote:
            returncode, infra_name = v_utils.infra_ensure_up(mynets,
                                                             float_net,
                                                             my_sec_grps,
                                                             path=ctx.path)
            if returncode == 1:
                ctx.logger.error("Could not boot a remote infra node")
                sys.exit(1)
        else:
            returncode, infra_name = v_utils.infra_ensure_up(None, None, None, path=ctx.path)
            if returncode == 1:
                ctx.logger.error("Could not boot a local infra node")
                sys.exit(1)

        returncode, myinfo = service_utils.run_this('vagrant hostmanager', ctx.path)
        if returncode > 0:
            returncode, myinfo = service_utils.run_this('vagrant hostmanager '
                                                        '--provider openstack',
                                                        ctx.path)
            if returncode > 0:
                ctx.logger.error("Could not run vagrant hostmanager because\
                                 {0}".format(myinfo))
                ctx.logger.error("Vagrant manager will fail if you have local vms"
                                 "and remote vms.")
                sys.exit(1)

        command = ('vagrant ssh {0} -c \"cd /opt/ccs/services/{1}/ && sudo heighliner '
                   '--dev --debug deploy\"')

        returncode, myinfo = service_utils.run_this(command.format(infra_name, service))
        if returncode > 0:
            ctx.logger.error("There was a failure during the heighliner deploy phase of "
                             "your service. Please see the following information"
                             "for debugging: ")
            ctx.logger.error(myinfo)
            sys.exit(1)
        else:
            sys.exit(0)
    elif target:
        redhouse_ten_path = os.path.join(ctx.path, 'services', 'service-redhouse-tenant')
        service_utils.sync_service(ctx.path, service_branch,
                                   username, "service-redhouse-tenant")
        puppet_path = os.path.join(redhouse_ten_path, "puppet")
        if not os.path.exists(os.path.join(puppet_path, "glance")):
            ctx.logger.info('Updating sub repo.s under service-redhouse-tenant')
            ctx.logger.info('This may take a few minutes.')
            returncode, myinfo = service_utils.run_this("librarian-puppet install",
                                                        puppet_path)
            if returncode > 0:
                ctx.logger.error('Failed to retrieve the necessary puppet configurations.')
                ctx.logger.error(myinfo)
                sys.exit(1)
        a = v_utils.Connect_to_vagrant(vm_name=target, path=redhouse_ten_path)
        if yaml_utils.addto_inventory(target, ctx.path) > 0:
            ctx.logger.error('Could not add {0} to vagrant.yaml'.format(target))
            sys.exit(1)

        if not os.path.exists(os.path.join(ctx.path, 'services', 'ccs-data')):
            service_utils.sync_service(ctx.path, data_branch, username, 'ccs-data')

        if not os.path.exists(os.path.join(ctx.path, 'services', 'ccs-data', 'out')):
            returncode, myinfo = service_utils.build_data(ctx.path)
            if returncode > 0:
                ctx.logger.error('Failed to build ccs-data data b/c ' + myinfo)
                sys.exit(1)

        if not os.path.islink(os.path.join(redhouse_ten_path,
                                           "dev",
                                           "ccs-data")):
            ctx.logger.debug('WARNING: Linking ' + os.path.join(redhouse_ten_path, 'dev',
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
                ctx.logger.error('Failed to write settings yaml - make sure you have your OS'
                                 'cred.s sourced and have access to'
                                 'ccs-gerrit.cisco.com and have keys setup.')
                sys.exit(1)
            a.v.up(vm_name=target, provider='openstack')
        else:
            settingsyaml = {'openstack_provider': 'false'}
            returncode = yaml_utils.wr_settingsyaml(ctx.path, settingsyaml=settingsyaml)
            if returncode > 0:
                ctx.logger.error('Failed to write settings yaml - make sure you have your OS'
                                 'cred.s sourced and have access to'
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
                    ctx.logger.error("Could not run vagrant hostmanager because\
                                     {0}".format(myinfo))
                    sys.exit(1)
        sys.exit(0)

    service_utils.sync_service(ctx.path,
                               redhouse_branch,
                               username,
                               "service-redhouse-tenant")

    if mini:
        returncode, allmy_vms = yaml_utils.getmin_OS_vms(ctx.path)
    elif full:
        returncode, allmy_vms = yaml_utils.getfull_OS_vms(os.path.join(ctx.path,
                                                                       'provision'),
                                                          '001')
    if returncode > 0:
        ctx.logger.error("Couldn't get the vms from the vagrant.yaml.")
        sys.exit(1)
    try:
        # Note: not sure if this will work w/ vm_name set to infra-001 arbitrarily
        # Note: move path to ctx.path if able to boot OSP pieces via infra/heighliner
        redhouse_ten_path = os.path.join(ctx.path, 'services', 'service-redhouse-tenant')
        a = v_utils.Connect_to_vagrant(vm_name='infra-001',
                                       path=os.path.join(redhouse_ten_path))
        myvfile = Vf_utils.SlabVagrantfile(path=ctx.path)
        returncode, float_net, mynets, my_sec_grps = os_utils.os_ensure_network(ctx.path)
        if returncode > 0:
            ctx.logger.error('Failed to get float net and mynets')
            sys.exit(1)
        myvfile._vbox_os_provider_env_vars(float_net, mynets, my_sec_grps)
        if not os.path.exists(os.path.join(ctx.path, 'Vagrantfile')):
            myvfile.init_vagrantfile()
        puppet_path = os.path.join(redhouse_ten_path, "puppet")
        if not os.path.exists(os.path.join(puppet_path, "glance")):
            ctx.logger.info('Updating sub repo.s under service-redhouse-tenant')
            ctx.logger.info('This may take a few minutes.')
            returncode, myinfo = service_utils.run_this(
                                    "USER={0} librarian-puppet install".format(username),
                                    puppet_path)
            if returncode > 0:
                ctx.logger.error('Failed to retrieve the necessary puppet configurations.')
                ctx.logger.error(myinfo)
            returncode = service_utils.copy_certs(os.path.join(
                                                               ctx.path,
                                                               "provision"),
                                                  puppet_path)
            if returncode > 0:
                ctx.logger.error('Failed to copy haproxy certs to ccs puppet module.')
                sys.exit(1)
        if not os.path.exists(os.path.join(ctx.path, 'services', 'ccs-data')):
            service_utils.sync_service(ctx.path, data_branch, username, 'ccs-data')

        if not os.path.exists(os.path.join(ctx.path, 'services', 'ccs-data', 'out')):
            returncode, myinfo = service_utils.build_data(ctx.path)
            if returncode > 0:
                ctx.logger.error('Failed to build ccs-data data b/c ' + myinfo)
                sys.exit(1)

        if not os.path.islink(os.path.join(redhouse_ten_path,
                                           "dev",
                                           "ccs-data")):
            ctx.logger.debug('WARNING: Linking ' + os.path.join(redhouse_ten_path, 'dev',
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
        for i in allmy_vms:
            if ha:
                ha_vm = i.replace("001", "002")
                returncode, ha_vm_dicts = yaml_utils.gethost_byname(ha_vm,
                                                                    os.path.join(ctx.path,
                                                                                 'provision')
                                                                    )
                if returncode > 0:
                    ctx.logger.error("Couldn't get the vm {0} for HA".format(ha_vm))
                    sys.exit(1)
                else:
                    allmy_vms.append(ha_vm_dicts)
            for host in i:
                retcode = yaml_utils.host_add_vagrantyaml(path=ctx.path,
                                                          file_name="vagrant.yaml",
                                                          hostname=host,
                                                          site='ccs-dev-1',
                                                          memory=(i[host]['memory'] / 512),
                                                          box=i[host]['box'],
                                                          role=i[host]['role'],
                                                          profile=i[host]['profile'],
                                                          domain=i[host]['domain'],
                                                          mac_nocolon=i[host]['mac'],
                                                          ip=i[host]['ip'],
                                                          )
                if retcode > 0:
                    ctx.logger.error("Failed to add host" + host)
                    ctx.logger.error("Continuing despite failure...")
            settingsyaml = {'openstack_provider': True}
            returncode = yaml_utils.wr_settingsyaml(ctx.path, settingsyaml, hostname=host)
            if returncode > 0:
                ctx.logger.error('writing to settings yaml failed on: ' + host)
            if remote:
                myvfile.add_openstack_vm(i)
                a.v.up(vm_name=host, provider='openstack')
            else:
                myvfile.add_virtualbox_vm(i)
                a.v.up(vm_name=host)
    except IOError as e:
        ctx.logger.error("{0} for vagrant.yaml in {1}".format(e, ctx.path))
        sys.exit(1)
