from servicelab.utils import service_utils
from servicelab.utils import yaml_utils
from servicelab.utils import vagrant_utils
from servicelab.utils import Vagrantfile_utils
from servicelab.utils import openstack_utils
from servicelab.utils import helper_utils
from servicelab.stack import pass_context
import multiprocessing
import click
import sys
import os


@click.option('--full', is_flag=True, default=False, help='Boot complete openstack stack without ha, \
              unless --ha flag is set. You can not use the min flag with the full flag')
@click.option('--mini', is_flag=True, default=False, help='Boot min openstack stack without ha, \
              unless --ha flag is set. You can not use min flag with the full flag')
@click.option('--rhel7', help='Boot a rhel7 vm.')
@click.option('--target', '-t', help='pick an OSP target vm to boot.')
@click.option('--service', '-s', default="", help='This is a service you would like to boot\
              a vm for. e.g. service-sonarqube')
@click.option('-r', '--remote', is_flag=True, default=False,
              help='Boot into an OS environment')
@click.option('--ha', is_flag=True, default=False, help='Enables HA for core OpenStack components \
              by booting the necessary extra VMs.')
@click.option('-b', '--branch', default="master", help='Choose a branch to run against \
              for ccs-data.')
@click.option('-u', '--username', help='Enter the password for the username')
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

    service_utils.sync_service(ctx.path, branch, username, "service-redhouse-tenant")
    service_utils.sync_service(ctx.path, branch, username, "service-redhouse-svc")

    if not any([full, mini, rhel7, target, service]):
        returncode, service = helper_utils.get_current_service(ctx.path)
    # RFI: may not matter if returns 1 if we aren't using current_service
        if returncode > 0:
            ctx.logger.debug("Failed to get the current service")
            sys.exit(0)

    # #Dev testing Block for aaltman
    # attrs = vars(ctx)
    # print ', '.join("%s: %s" % item for item in attrs.items())

    # RHEL7 WORKFLOW ===============================
    if rhel7:
        for i in xrange(1, 100):
            if len(str(i)) == 1:
                i = "00" + str(i)
            elif len(str(i)) == 2:
                i = "0" + str(i)
            hostname = "rhel7-" + i
            returncode = yaml_utils.host_exists_vagrantyaml(os.path.join(ctx.path,
                                                                         "vagrant.yaml"),
                                                            hostname)
            if returncode == 1:
                with open(os.path.join(ctx.path, "vagrant.yaml"), 'w') as f:
                    yaml_utils.write_dev_hostyaml_out(ctx.path, hostname)

                a = vagrant_utils.Connect_to_vagrant(vmname=hostname,
                                                     path=ctx.path)
                a.v.up(vmname=hostname)
                returncode, myinfo = service_utils.run_this('vagrant hostmanager')
                if returncode > 0:
                    ctx.logger.error("Could not run vagrant hostmanager because\
                                    {0}".format(myinfo))
                    sys.exit(1)
                else:
                    sys.exit(0)
    # SERVICE VM WORKFLOW ==========================
    elif service:
        # TODO: Make sure infra001 is up and running or else make it so.
        #       This is for the vagrant ssh heighliner deploy stage at the end.
        for i in xrange(1, 100):
            if len(str(i)) == 1:
                i = "00" + str(i)
            elif len(str(i)) == 2:
                i = "0" + str(i)

            hostname = service + "-" + i
            returncode = yaml_utils.host_exists_vagrantyaml(os.path.join(ctx.path,
                                                                         "vagrant.yaml"),
                                                            hostname)
            if returncode == 1:
                with open(os.path.join(ctx.path, "vagrant.yaml"), 'w') as f:
                    yaml_utils.write_dev_hostyaml_out(ctx.path, hostname)
                    yaml_utils.host_add_vagrantyaml(ctx.path, "vagrant.yaml", hostname,
                                                    "ccs-dev-1")
                Vagrantfile_utils.overwrite_vagrantfile(ctx.path)
                a = vagrant_utils.Connect_to_vagrant(vmname=hostname,
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
        # TODO: Got to ensure service-redhouse-tenant/svc are here to be
        # addressed. No need for an infra node here.
        # RFI: if the infra node is up should we add to authorized_keys?
        click.echo("vagrant up %s" % (target))
        a = vagrant_utils.Connect_to_vagrant(vmname=target,
                                             path=ctx.path)
        # Note: from python-vagrant up function (self, no_provision=False,
        #                                        provider=None, vm_name=None,
        #                                        provision=None, provision_with=None)
        a.v.up(vmname=target)
        returncode, myinfo = service_utils.run_this('vagrant hostmanager')
        if returncode > 0:
            ctx.logger.error("Could not run vagrant hostmanager because\
                             {0}".format(myinfo))
            sys.exit(1)
        else:
            sys.exit(0)

    path_to_utils = os.path.split(ctx.path)
    path_to_utils = os.path.join(path_to_utils[0], "utils")
    pathto_vagrantyaml_templ = os.path.join(path_to_utils, "vagrant.yaml")

    if mini:
        returncode, allmy_vms = yaml_utils.getmin_OS_vms(pathto_vagrantyaml_templ)
    elif full:
        returncode, allmy_vms = yaml_utils.getfull_OS_vms(pathto_vagrantyaml_templ)
    if returncode > 0:
        ctx.logger.error("Couldn't get the vms from the vagrant.yaml.")
        sys.exit(1)
    try:
        for k in allmy_vms:
            if ha:
                ha_vm = k.replace("001", "002")
                returncode, ha_vm_dict = yaml_utils.gethost_byname(ha_vm,
                                                                   pathto_vagrantyaml_templ)
                if returncode > 0:
                    ctx.logger.error("Couldn't get the vm {0} for HA".format(ha_vm))
                    sys.exit(1)
                else:
                    allmy_vms.append(ha_vm_dict)
            yaml_utils.host_add_vagrantyaml(ctx.path,
                                            "vagrant.yaml",
                                            k,
                                            "ccs-dev-1",
                                            memory=allmy_vms[k]['memory'],
                                            box=allmy_vms[k]['box'],
                                            role=allmy_vms[k]['role'],
                                            profile=allmy_vms[k]['profile'],
                                            domain=allmy_vms[k]['domain'],
                                            storage=allmy_vms[k]['storage'],
                                            )
    except IOError as e:
        ctx.logger.error("{0} for vagrant.yaml in {1}".format(e, ctx.path))
        sys.exit(1)

    if remote:
        # TODO: Write out remote provider Vagrantfile not local
        # TODO: get env vars.
        Vagrantfile_utils.overwrite_vagrantfile(ctx.path)
        a = openstack_utils.SLab_OS(path=ctx.path, password='XXXX', username=username,
                                    base_url='XXXX')
        returncode, tenant_id, temp_token = a.login_or_gettoken()
        if returncode > 0:
            ctx.logger.error("Could not create router in project.")
            sys.exit(1)
        returncode, tenant_id, token = a.login_or_gettoken(tenant_id=tenant_id)
        if returncode > 0:
            ctx.logger.error("Could not create router in project.")
            sys.exit(1)
        a.connect_to_neutron()
        returncode, router = a.create_router()
        if returncode > 0:
            ctx.logger.error("Could not create router in project.")
            sys.exit(1)
        router_id = router['id']
        returncode, network = a.create_network()
        if returncode > 0:
            ctx.logger.error("Could not create network in project.")
            sys.exit(1)
        returncode, subnet = a.create_subnet()
        if returncode > 0:
            ctx.logger.error("Could not create subnet in project.")
            sys.exit(1)
        a.add_int_to_router(router_id, subnet['id'])

        name = a.create_name_for("network", append="mgmt")
        returncode, mgmt_network = a.create_network(name=name)
        if returncode > 0:
            ctx.logger.error("Could not create network in project.")
            sys.exit(1)
        name = a.create_name_for("subnet", append="mgmt")
        returncode, mgmt_subnet = a.create_subnet(name=name,
                                                  cidr='192.168.1.0/24')
        if returncode > 0:
            ctx.logger.error("Could not create subnet in project.")
            sys.exit(1)
        a.add_int_to_router(router_id, mgmt_subnet['id'])
    else:
        # Write out local provider Vagrantfile
        Vagrantfile_utils.overwrite_vagrantfile(ctx.path)

    a = vagrant_utils.Connect_to_vagrant(vmname=target, path=ctx.path)
    if os.name == "posix":
        for k in allmy_vms:
            a.v.up(vmname=k, no_provision=True)
    # Provision VMS using 4 CPUs from a pool
        pool = multiprocessing.Pool(4)
        for k in allmy_vms:
            pool.map(a.v.provision(vmname=k))
        pool.close()
        returncode, myinfo = service_utils.run_this('vagrant hostmanager')
        if returncode > 0:
            ctx.logger.error("Could not run vagrant hostmanager because\
                             {0}".format(myinfo))
            sys.exit(1)
        sys.exit(0)
    elif os.name == "nt":
        for k in allmy_vms:
            a.v.up(vmname=k)
        if returncode > 0:
            ctx.logger.error("Could not run vagrant hostmanager because\
                             {0}".format(myinfo))
            sys.exit(1)
        sys.exit(0)
