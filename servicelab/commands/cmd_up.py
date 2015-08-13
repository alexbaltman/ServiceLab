from servicelab.utils import service_utils
from servicelab.utils import yaml_utils
from servicelab.utils import vagrant_utils
from servicelab.utils import helper_utils
from servicelab.stack import pass_context
import click
import sys
import os


@click.option('--ha', is_flag=True, default=False, help='Enables HA for core OpenStack components \
              by booting the necessary extra VMs.')
@click.option('--full', help='Boot complete openstack stack without ha, \
              unless --ha flag is set.')
# @click.option('--osp-aio', help='Boot a full CCS implementation of the \
#              OpenStack Platform on one VM. Note: This is not the same as \
#              the AIO node deployed in the service cloud.')
@click.option('-i', '--interactive', help='Walk through booting VMs')
@click.option('-r', '--remote', is_flag=True, default=False,
              help='Boot into an OS environment')
@click.option('-b', '--branch', help='Choose a branch to run against \
              for ccs-data.')
@click.option('--rhel7', help='Boot a rhel7 vm.')
@click.option('--target', '-t', help='pick an osp target to boot.')
@click.option('-u', '--username', help='Enter the password for the username')
# @click.argument('service_name', default="current")
@click.group('up', invoke_without_command=True, short_help="Boots VM(s).")
@pass_context
def cli(ctx, ha, full, osp_aio, interactive, branch, rhel7, username,
        # service_name, target):
        target):
    if not username:
        returncode, username = helper_utils.set_user(ctx.path)

    returncode, current_service = helper_utils.get_current_service(ctx.path)
    # RFI: may not matter if returns 1 if we aren't using current_service
    if returncode > 0:
        ctx.error("Failed to get the current service")
        sys.exit(1)

    # ======================================================
    # #Dev testing Block for aaltman
    # attrs = vars(ctx)
    # print ', '.join("%s: %s" % item for item in attrs.items())

    # CL/JP stack method
    if target:
        click.echo("vagrant up %s" % (target))
        a = vagrant_utils.Connect_to_vagrant(vmname=target,
                                             path=ctx.path)
        a.v.up()
        service_utils.run_this('vagrant hostmanager')
    # service_utils.run_this('vagrant ssh infra-001 -c cp "/etc/ansible"; \
    # cd "/opt/ccs/services/%s; sudo heighliner \
    # --dev --debug deploy"' % (os.path.join(ctx.path, "hosts"),
    # service_name))
    # ======================================================

    # writeout vagrant.yaml w/ current vms
    # read the profiles to see what you need to boot
        # or a prep for a service --> where to store profiles
        # the whole one is defined it's the small one.
    # if not in profile
    # #check if host exists
    # # if not
    # ## read host from templ
    # ## write host
    # ## if it's not in

    # ALL ===============================================
    if not os.path.isfile(os.path.join(ctx.path, "vagrant.yaml")):
        with open(os.path.join(ctx.path, "vagrant.yaml"), 'w') as f:
            f.write("")

    path_to_utils = os.path.split(path)
    path_to_utils = os.path.join(path_to_utils[0], "utils")
    pathto_vagrantyaml_templ = os.path.join(path_to_utils, "vagrant.yaml")

    # MIN WORKFLOW ======================================
    returncode, allmin_vms = yaml_utils.getmin_OS_vms(pathto_vagrantyaml_templ)
    if returcode > 0:
        ctx.logger.error("Couldn't get the vms for the min OS env")
        sys.exit(1)
    try:
        ha_vms = []
        for k in allmin_vms:
            if ha:
                ha_vm = k.replace("001", "002")
                returncode, ha_vm_dict = yaml_utils.gethost_byname(ha_vm,
                                                                   pathto_vagrantyaml_templ)
                if returncode > 0:
                    ctx.logger.error("Couldn't get the vm {0} for HA".format(ha_vm))
                    sys.exit(1)
                else:
                    allmin_vms.append(ha_vm_dict)
            yaml_utils.host_add_vagrantyaml(ctx.path,
                                            "vagrant.yaml",
                                            k,
                                            "ccs-dev-1",
                                            memory=allmin_vms[k]['memory']
                                            box=allmin_vms[k]['box']
                                            role=allmin_vms[k]['role']
                                            profile=allmin_vms[k]['profile']
                                            domain=allmin_vms[k]['domain']
                                            storage=allmin_vms[k]['storage']
                                            )

    except IOError as e:
        ctx.logger.error("{0} for vagrant.yaml in {1}".format(e, ctx.path))
        sys.exit(1)

    # FULL WORKFLOW ================================
    returncode, all_OS_vms = yaml_utils.getfull_OS_vms(pathto_vagrantyaml_templ, "001")
    if returcode > 0:
        ctx.logger.error("Couldn't get the vms for the full OS env")

    # Added FULL HA =============================
    returncode, all_OS_havms = yaml_utils.getfull_OS_vms(pathto_vagrantyaml_templ, "002")
    if returcode > 0:
        ctx.logger.error("Couldn't get the vms for the full OS env")

    # RHEL7 WORKFLOW ===============================
