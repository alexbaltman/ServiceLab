from servicelab.utils import service_utils
from servicelab.utils import yaml_utils
from servicelab.utils import vagrant_utils
from servicelab.utils import Vagrantfile_utils
from servicelab.utils import openstack_utils
from servicelab.utils import helper_utils
from servicelab.stack import pass_context
import click
import sys
import os


@click.option('--full', is_flag=True, default=False, help='Boot complete openstack stack without ha, \
              unless --ha flag is set. You can not use the min flag with the full flag')
@click.option('--min', is_flag=True, default=False, help='Boot min openstack stack without ha, \
              unless --ha flag is set. You can not use min flag with the full flag')
@click.option('--rhel7', help='Boot a rhel7 vm.')
@click.option('--target', '-t', help='pick an OSP target vm to boot.')
@click.option('service_name', default="current")
@click.option('-r', '--remote', is_flag=True, default=False,
              help='Boot into an OS environment')
@click.option('--ha', is_flag=True, default=False, help='Enables HA for core OpenStack components \
              by booting the necessary extra VMs.')
@click.option('-b', '--branch', help='Choose a branch to run against \
              for ccs-data.')
@click.option('-u', '--username', help='Enter the password for the username')
@click.option('-i', '--interactive', help='Walk through booting VMs')
# @click.option('--osp-aio', help='Boot a full CCS implementation of the \
#              OpenStack Platform on one VM. Note: This is not the same as \
#              the AIO node deployed in the service cloud.')
@click.group('up', invoke_without_command=True, short_help="Boots VM(s).")
@pass_context
def cli(ctx, ha, full, min, osp_aio, r, interactive, branch, rhel7, username,
        # service_name, target):
        target):
    if min is True and full is True:
        ctx.logger.error("You can not use the min flag with the full flag.")
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

    returncode, current_service = helper_utils.get_current_service(ctx.path)
    # RFI: may not matter if returns 1 if we aren't using current_service
    if returncode > 0:
        ctx.error("Failed to get the current service")
        sys.exit(1)

    # #Dev testing Block for aaltman
    # attrs = vars(ctx)
    # print ', '.join("%s: %s" % item for item in attrs.items())

    if target:
        click.echo("vagrant up %s" % (target))
        a = vagrant_utils.Connect_to_vagrant(vmname=target,
                                             path=ctx.path)
        # TODO: up the provided vm --> check vagrant_utils
        a.v.up()
        service_utils.run_this('vagrant hostmanager')
        sys.exit(0)
        # ======================================================

    if not os.path.isfile(os.path.join(ctx.path, "vagrant.yaml")):
        with open(os.path.join(ctx.path, "vagrant.yaml"), 'w') as f:
            # Note: we could pass here or just close it, either way
            #       we'll get an empty file
            f.write("")

    path_to_utils = os.path.split(ctx.path)
    path_to_utils = os.path.join(path_to_utils[0], "utils")
    pathto_vagrantyaml_templ = os.path.join(path_to_utils, "vagrant.yaml")

    if min:
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

        if r:
            # TODO: Write out remote provider Vagrantfile
            # TODO: set env vars.
            Vagrantfile_utils.overwrite_vagrantfile(ctx.path)
            # TODO: test returncodes
            a = openstack_utils.SLab_OS(path=ctx.path, password='XXXX', username=username,
                                        base_url='XXXX')
            a.login_or_gettoken()
            a.login_or_gettoken(tenant_id='xxxx')
            a.connect_to_neutron()
            returncode, router = a.create_router()
            router_id = router['id']
            returncode, network = a.create_network()
            returncode, subnet = a.create_subnet()
            a.add_int_to_router(router_id, subnet['id'])

            name = a.create_name_for("network", append="mgmt")
            returncode, mgmt_network = a.create_network(name=name)
            name = a.create_name_for("subnet", append="mgmt")
            returncode, mgmt_subnet = a.create_subnet(name=name,
                                                      cidr='192.168.1.0/24')
            a.add_int_to_router(router_id, mgmt_subnet['id'])
        else:
            # Write out local provider Vagrantfile
            Vagrantfile_utils.overwrite_vagrantfile(ctx.path)

        # Boot VMs --> vagrant up in the .stack folder should get all vms

        # Provision VMs separatly if possible.

    # RHEL7 WORKFLOW ===============================
    # add new rhel7 vm to ccs-dev-1
    # add to vagrant.yaml
    # boot it alone

    # SERVICE VM WORKFLOW ==========================
    # service_utils.run_this('vagrant ssh infra-001 -c cp "/etc/ansible"; \
    # cd "/opt/ccs/services/%s; sudo heighliner \
    # --dev --debug deploy"' % (os.path.join(ctx.path, "hosts"),
    # service_name))
