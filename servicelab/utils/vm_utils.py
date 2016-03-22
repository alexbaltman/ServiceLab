"""
Utility functions for status command.
"""
import os
from subprocess import CalledProcessError

import vagrant_utils
import logger_utils
import service_utils
import yaml_utils
import vagrantfile_utils as Vf_utils
from servicelab import settings

slab_logger = logger_utils.setup_logger(settings.verbosity, 'stack.utils.status')

VAGRANTFILE_DELETE_MESSAGE = "Deleting the VM"
INVENTORY_DELETE_MESSAGE = "Deleting the VM from vagrant.yaml inventory"
REBUILDING_CCSDATA_MESSAGE = "Rebuilding ccs-data"
INFRA_PORT_DETECT_MESSAGE = "Port found for infra node"
UPDATING_HOSTS_YAML_MESSAGE = "Updating of hosts.yaml on infra node complete"
VM_DOESNT_EXIST_MESSAGE = "Error occurred destroying VM. "\
                          "Most probably the VM doesnt exist."


def destroy_vm_by_name(ctx, force, vm_name):
    """Destroys a single vm by name
    """
    slab_logger.info("Destroying {0}".format(vm_name))
    try:
        myvag_env = vagrant_utils.Connect_to_vagrant(vm_name=vm_name,
                                                     path=ctx.path)
        myvag_env.v.destroy(vm_name)
    except CalledProcessError:
        slab_logger.info(VM_DOESNT_EXIST_MESSAGE)

    myvfile = Vf_utils.SlabVagrantfile(path=ctx.path)
    slab_logger.info("{0} {1} from Vagrantfile".format(VAGRANTFILE_DELETE_MESSAGE, vm_name))
    if not myvfile.delete_virtualbox_vm(vm_name):
        slab_logger.error("VM {0} not found in Vagrantfile".format(vm_name))
    slab_logger.info("{0} {1}".format(INVENTORY_DELETE_MESSAGE, vm_name))
    yaml_utils.host_del_vagrantyaml(ctx.path, "vagrant.yaml", vm_name)
    vm_yaml_file = "%s/services/ccs-data/sites/ccs-dev-1/environments/"\
                   "dev-tenant/hosts.d/%s.yaml" % (ctx.path, vm_name)
    slab_logger.info("Deleting the VM YAML file : %s" % (vm_yaml_file))
    if os.path.exists(vm_yaml_file):
        os.remove(vm_yaml_file)
    else:
        slab_logger.error("VM YAML file not found. Proceeeding.")
    slab_logger.info(REBUILDING_CCSDATA_MESSAGE)
    service_utils.build_data(ctx.path)
    slab_logger.info("Updating hosts.yaml on infra node.")
    slab_logger.info("Detecting infra node port.")
    return_code, port_no = vagrant_utils.get_ssh_port_for_vm("infra-001", ctx.path)
    if return_code != 0:
        slab_logger.error("Unable to find port no. of infra node, cannot update"
                          "hosts.yaml on infra node")
        return
    else:
        return_code, key_path = vagrant_utils.get_ssh_key_path_for_vm("infra-001", ctx.path)
        if return_code != 0:
            slab_logger.error("Unable to find ssh key of infra node, cannot update"
                              "hosts.yaml on infra node")
            return
        else:
            slab_logger.info("%s %s " % (INFRA_PORT_DETECT_MESSAGE, port_no))
            yaml_file = "./services/ccs-data/out/ccs-dev-1/dev/etc/ccs/data/hosts.yaml"
            vm_yaml_file = "/etc/ccs/data/environments/dev-tenant/hosts.yaml"
            yaml_file_path = os.path.join(ctx.path, yaml_file)
            return_code, _ = vagrant_utils.copy_file_to_vm("hosts.yaml", "infra-001",
                                                           yaml_file_path, port_no,
                                                           vm_yaml_file, ctx.path, key_path)
            if return_code != 0:
                slab_logger.info("Could not succesfully update hosts.yaml on infra node.")
            else:
                slab_logger.info(UPDATING_HOSTS_YAML_MESSAGE)
