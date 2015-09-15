from servicelab.utils import Vagrantfile_utils
from servicelab.utils import openstack_utils
from servicelab.utils import service_utils
from servicelab.utils import vagrant_utils
from servicelab.utils import helper_utils
from servicelab.stack import pass_context
from subprocess import CalledProcessError
from servicelab.utils import yaml_utils
import multiprocessing
import click
import time
import sys
import os


@click.option('--full', is_flag=True, default=False, help='Boot complete openstack stack without ha, \
              unless --ha flag is set. You can not use the min flag with the full flag')
@click.option('--mini', is_flag=True, default=False, help='Boot min openstack stack without ha, \
              unless --ha flag is set. You can not use min flag with the full flag')
@click.option('--rhel7', is_flag=True, default=False, help='Boot a rhel7 vm.')
@click.option('--target', '-t', help='pick an OSP target vm to boot.')
@click.option('--service', '-s', default="", help='This is a service you would like to boot\
              a vm for. e.g. service-sonarqube')
@click.option('-r', '--remote', is_flag=True, default=False,
              help='Boot into an OS environment')
@click.option('--ha', is_flag=True, default=False, help='Enables HA for core OpenStack components \
              by booting the necessary extra VMs.')
@click.option('-b', '--branch', default="master", help='Choose a branch to run against \
              for service redhouse tenant and svc.')
@click.option('-u', '--username', help='Enter the desired username')
@click.option('-i', '--interactive', help='Walk through booting VMs')
# @click.option('--osp-aio', help='Boot a full CCS implementation of the \
#              OpenStack Platform on one VM. Note: This is not the same as \
#              the AIO node deployed in the service cloud.')
@click.group('up', invoke_without_command=True, short_help="Boots VM(s).")
@pass_context
def cli(ctx, full, mini, rhel7, target, service, remote, ha, branch, username,
        interactive):
    if mini is True and full is True:
        ctx.logger.error("You can not use the mini flag with the full flag.")
        sys.exit(1)

    if not username:
        returncode, username = helper_utils.set_user(ctx.path)
        if returncode > 0:
            import getpass
            ctx.logger.debug("Couldn't set user from .git/config will try\
                              to use current running user.")
            username = getpass.getuser()
            if not username:
                ctx.logger.debug("Still couldn't set username. Exiting.")
                sys.exit(1)

    if not any([full, mini, rhel7, target, service]):
        returncode, service = helper_utils.get_current_service(ctx.path)
        if returncode > 0:
            ctx.logger.debug("Failed to get the current service")
            sys.exit(0)

    # RHEL7 WORKFLOW ===============================
    if rhel7:
        hostname = name_vm("rhel7", ctx.path)
        # Note: Reserve the ip jic other vms are booted from this
        #       servicelab env.
        yaml_utils.write_dev_hostyaml_out(ctx.path, hostname)
        yaml_utils.host_add_vagrantyaml(ctx.path, "vagrant.yaml", hostname,
                                        "ccs-dev-1")
        myvfile = Vagrantfile_utils.SlabVagrantfile(path=ctx.path)
        if os.path.exists(os.path.join(ctx.path, 'Vagrantfile')):
            myvfile.init_vagrantfile()

        if remote:
            returncode, float_net, mynets = os_ensure_network()
            if returncode > 0:
                sys.exit(1)
            myvfile._vbox_os_provider_env_vars()
            myvfile.add_openstack_vm(hostname=hostname)
        else:
            returncode, host_dict = yaml_utils.gethost_byname(hostname, ctx.path)
            if returncode > 0:
                ctx.logger.error('Failed to get the requested host from your Vagrant.yaml')
                sys.exit(1)
            myvfile.add_virtualbox_vm(host_dict[hostname])

        a = vagrant_utils.Connect_to_vagrant(vm_name=hostname,
                                             path=ctx.path)
        a.v.up(vm_name=hostname)
        returncode, myinfo = service_utils.run_this('vagrant hostmanager')
        if returncode > 0:
            ctx.logger.error("Could not run vagrant hostmanager because\
                            {0}".format(myinfo))
            sys.exit(1)
        else:
            sys.exit(0)
    # SERVICE VM WORKFLOW ==========================
    elif service:
        returncode = infra_ensure_up(path=ctx.path)
        if returncode == 1:
            ctx.logger.error("Could not boot infra-001")
            sys.exit(1)

        hostname = name_vm(service, ctx.path)
        returncode = yaml_utils.write_dev_hostyaml_out(ctx.path, hostname)
        if returncode == 1:
            ctx.logger.error("Couldn't write vm yaml to ccs-dev-1 for " + hostname)
            sys.exit(1)
        returncode = yaml_utils.host_add_vagrantyaml(ctx.path, "vagrant.yaml",
                                                     hostname, "ccs-dev-1")
        if returncode == 1:
            ctx.logger.error("Couldn't write vm to vagrant.yaml in " + ctx.path)
            sys.exit(1)

        myvfile = Vagrantfile_utils.SlabVagrantfile(path=ctx.path)
        if os.path.exists(os.path.join(ctx.path, 'Vagrantfile')):
            myvfile.init_vagrantfile()
        # TODO: We got to boot to wherever the infra node is or put one there.
        if remote:
            returncode, float_net, mynets = os_ensure_network()
            myvfile._vbox_os_provider_env_vars()
            myvfile.add_openstack_vm(hostname=hostname)
        else:
            returncode, host_dict = yaml_utils.gethost_byname(hostname, ctx.path)
            if returncode > 0:
                ctx.logger.error('Failed to get the requested host from your Vagrant.yaml')
                sys.exit(1)
            myvfile.add_virtualbox_vm(host_dict[hostname])

        a = vagrant_utils.Connect_to_vagrant(vm_name=hostname,
                                             path=ctx.path)
        a.v.up(vm_name=hostname)
        returncode, myinfo = service_utils.run_this('vagrant hostmanager')
        if returncode > 0:
            ctx.logger.error("Could not run vagrant hostmanager because\
                            {0}".format(myinfo))
            sys.exit(1)
        else:
            sys.exit(0)
        # TODO: Figure out a better way to execute this. The ssh can be very
        #       fragile.
        service_utils.run_this('vagrant ssh infra-001 -c cp "/etc/ansible"; \
                                cd "/opt/ccs/services/%s; sudo heighliner \
                                --dev --debug deploy"' % (os.path.join(ctx.path, "hosts"),
                                                          service))
        returncode, myinfo = service_utils.run_this('vagrant hostmanager')
        if returncode > 0:
            ctx.logger.error("Could not run vagrant hostmanager because\
                             {0}".format(myinfo))
    elif target:
        service_utils.sync_service(ctx.path, branch, username, "service-redhouse-tenant")
        service_utils.sync_service(ctx.path, branch, username, "service-redhouse-svc")
        # Note: os.link(src, dst)
        if not os.path.islink(os.path.join(ctx.path,
                                           "services",
                                           "service-redhouse-tenant",
                                           "dev",
                                           "ccs-data")):
            ctx.logger.debug('WARNING: Linking ' + os.path.join(ctx.path, "services",
                             "service-redhouse-tenant") + "with " +
                             os.path.join(ctx.path, "services", "ccs-data"))
            os.link(os.path.join(ctx.path,
                                 "services",
                                 "ccs-data"
                                 ),
                    os.path.join(ctx.path,
                                 "services",
                                 "service-redhouse-tenant",
                                 "dev",
                                 "ccs-data"))
        # TODO: if the infra node is up should we add to authorized_keys?
        click.echo("vagrant up %s" % (target))
        a = vagrant_utils.Connect_to_vagrant(vm_name=target,
                                             path=os.path.join(ctx.path,
                                                               "services",
                                                               "service-redhouse-tenant"))
        # Note: from python-vagrant up function (self, no_provision=False,
        #                                        provider=None, vm_name=None,
        #                                        provision=None, provision_with=None)
        a.v.up(vm_name=target)
        returncode, myinfo = service_utils.run_this('vagrant hostmanager')
        if returncode > 0:
            ctx.logger.error("Could not run vagrant hostmanager because\
                             {0}".format(myinfo))
            sys.exit(1)
        else:
            sys.exit(0)

    service_utils.sync_service(ctx.path, branch, username, "service-redhouse-tenant")
    service_utils.sync_service(ctx.path, branch, username, "service-redhouse-svc")

    if mini:
        returncode, allmy_vms = yaml_utils.getmin_OS_vms(ctx.path)
    elif full:
        returncode, allmy_vms = yaml_utils.getfull_OS_vms(ctx.path)
    if returncode > 0:
        ctx.logger.error("Couldn't get the vms from the vagrant.yaml.")
        sys.exit(1)
    try:
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
    except IOError as e:
        ctx.logger.error("{0} for vagrant.yaml in {1}".format(e, ctx.path))
        sys.exit(1)

    a = vagrant_utils.Connect_to_vagrant(vm_name=target, path=ctx.path)
    if os.name == "posix":
        for k in allmy_vms:
            for i in k:
                a.v.up(vm_name=i, no_provision=True)
        # Note: Provision VMS using 4 CPUs from a pool
        pool = multiprocessing.Pool(4)
        for k in allmy_vms:
            for i in k:
                pool.map(a.v.provision(vm_name=i))
        pool.close()
        returncode, myinfo = service_utils.run_this('vagrant hostmanager')
        if returncode > 0:
            ctx.logger.error("Could not run vagrant hostmanager because\
                             {0}".format(myinfo))
            sys.exit(1)
        sys.exit(0)
    elif os.name == "nt":
        for k in allmy_vms:
            for i in k:
                a.v.up(vm_name=i)
        if returncode > 0:
            ctx.logger.error("Could not run vagrant hostmanager because\
                             {0}".format(myinfo))
            sys.exit(1)
        sys.exit(0)


def name_vm(name, path):
    for i in xrange(1, 100):
        i = str(i)
        if len(i) == 1:
            i = "00" + i
        elif len(i) == 2:
            i = "0" + i
        hostname = name + "-" + i
        returncode = yaml_utils.host_exists_vagrantyaml(hostname, path)
        if returncode == 1:
            return hostname


def infra_ensure_up(hostname="infra-001", path=None):
    '''
    #Out[3]: [Status(name='rhel7-001', state='running', provider='virtualbox')]
    #CalledProcessError
    '''
    infra_connection = vagrant_utils.Connect_to_vagrant(vm_name="infra-001",
                                                        path=path)
    try:
        returncode = vm_isrunning(hostname=hostname, path=path)
        if returncode == 1:
            infra_connection.v.up(vm_name=hostname)
            returncode = vm_isrunning(hostname=hostname, path=path)
            if returncode == 0:
                return 0
            else:
                # no ctx provided
                # ctx.logger.error("Could not boot " + hostname)
                return 1
    except CalledProcessError as e:
        path_to_utils = helper_utils.get_path_to_utils(path)
        returncode, idic = yaml_utils.gethost_byname(hostname, path_to_utils)
        if returncode == 1:
            # ctx.logger.error("Couldn't get the templated host details\
            # in vagrant.yaml.:")
            # ctx.logger.error(e)
            # RFI: Should I exit here??
            print(e)
            sys.exit(1)

        retcode = yaml_utils.host_add_vagrantyaml(path=path,
                                                  file_name="vagrant.yaml",
                                                  hostname=hostname,
                                                  memory=(idic[hostname]['memory'] / 512),
                                                  box=idic[hostname]['box'],
                                                  role=idic[hostname]['role'],
                                                  profile=idic[hostname]['profile'],
                                                  domain=idic[hostname]['domain'],
                                                  mac_nocolon=idic[hostname]['mac'],
                                                  ip=idic[hostname]['ip'],
                                                  site='ccs-dev-1')
        # TODO: Need a better error check here:
        if retcode == 0:
            infra_connection.v.up(vm_name=hostname)
            return 0
        else:
            # Not defined yet b/c not @pass_context to sub function
            # ctx.logger.error("Failed to bring up " + hostname)
            return 1


def vm_isrunning(hostname, path):
    vm_connection = vagrant_utils.Connect_to_vagrant(vm_name=hostname,
                                                     path=path)
    status = vm_connection.v.status()
    if status[0][1] == "running":
        return 0
    else:
        return 1


def os_ensure_network(path):
    password = os.environ.get('OS_PASSWORD')
    username = os.environ.get('OS_USERNAME')
    base_url = os.environ.get('OS_REGION_NAME')
    if not password or not base_url:
        # ctx.logger.error('Can --not-- boot into OS b/c password or base_url is\
        # not set')
        # ctx.logger.error('Exiting now.')
        return 1
    a = openstack_utils.SLab_OS(path=path, password=password, username=username,
                                base_url=base_url)
    returncode, tenant_id, temp_token = a.login_or_gettoken()
    if returncode > 0:
        # ctx.logger.error("Could not create router in project.")
        return 1
    returncode, tenant_id, token = a.login_or_gettoken(tenant_id=tenant_id)
    if returncode > 0:
        # ctx.logger.error("Could not create router in project.")
        return 1
    a.connect_to_neutron()
    returncode, float_net = a.find_floatnet_id(return_name="Yes")
    if returncode > 0:
        # ctx.logger.error('Could not get the name for the floating network.')
        return 1
    returncode, router = a.create_router()
    if returncode > 0:
        # ctx.logger.error("Could not create router in project.")
        return 1
    router_id = router['id']
    returncode, network = a.create_network()
    if returncode > 0:
        # ctx.logger.error("Could not create network in project.")
        return 1
    returncode, subnet = a.create_subnet()
    if returncode > 0:
        # ctx.logger.error("Could not create subnet in project.")
        return 1
    # ctx.logger.debug('Sleeping 5s b/c of slow neutron create times.')
    time.sleep(5)
    a.add_int_to_router(router_id, subnet['id'])

    mgmtname = a.create_name_for("network", append="mgmt")
    returncode, mgmt_network = a.create_network(name=mgmtname)
    if returncode > 0:
        # ctx.logger.error("Could not create network in project.")
        return 1
    name = a.create_name_for("subnet", append="mgmt")
    returncode, mgmt_subnet = a.create_subnet(name=name,
                                              cidr='192.168.1.0/24')
    if returncode > 0:
        # ctx.logger.error("Could not create subnet in project.")
        return 1
    # ctx.logger.debug('Sleeping 5s b/c of slow neutron create times.')
    time.sleep(5)
    a.add_int_to_router(router_id, mgmt_subnet['id'])
    mynets = a.neutron.list_networks()
    mynewnets = []

    for i in mynets['networks']:
        if i.get('name') == name:
            mynewnets.append(i)
        elif i.get('name') == mgmtname:
            mynewnets.append(i)

    return 0, float_net, mynewnets
