""" We're not trying to replace the openstack CLI tool/s so we have to be careful
here on what we want to acheive w/o overlapping. For instance, destroying all of
soemthing is useful and non-overlapping b/c of the order requirements imposed on
the operator as well as the quantity, but deleting one thing would be complete
overlap w/ openstack cli tools.
"""
import os
import sys
import click
from subprocess import CalledProcessError

from servicelab.utils import logger_utils
from servicelab.stack import pass_context
from servicelab.utils import vagrant_utils
from servicelab.utils import helper_utils
from servicelab.utils import openstack_utils
from servicelab.utils import service_utils
from servicelab.utils import yaml_utils
from servicelab.utils import vagrantfile_utils as Vf_utils
from servicelab import settings

slab_logger = logger_utils.setup_logger(settings.verbosity, 'stack.destroy')

VAGRANTFILE_DELETE_MESSAGE = "Deleting the VM"
INVENTORY_DELETE_MESSAGE = "Deleting the VM from vagrant.yaml inventory"
REBUILDING_CCSDATA_MESSAGE = "Rebuilding ccs-data"
INFRA_PORT_DETECT_MESSAGE = "Port found for infra node"
UPDATING_HOSTS_YAML_MESSAGE = "Updating of hosts.yaml on infra node complete"
VM_DOESNT_EXIST_MESSAGE = "Error occurred destroying VM. "\
                          "Most probably the VM doesnt exist."


@click.group('destroy',
             short_help='Remove local and remote pipeline resources.',
             add_help_option=True)
@pass_context
def cli(_):
    """
    Destroy things.
    """
    pass


@click.option('-f', '--force', is_flag=True, help='Do not prompt me to destroy'
              'my vm')
@cli.command(
    'vm',
    short_help='Destroy a servicelab vm.'
    ' knows about.')
@click.argument('vm_name')
@pass_context
def destroy_vm(ctx, force, vm_name):
    """Destroy non OSP VMs in either virtualbox or Openstack. This function
    will do some basic cleanup as well.

    1. Remove from inventory. (?)
    2. Delete from Vagrantfile (?)
    3. Remove from dev-tenant in ccs-data (?)
    """
    # What if it's an ospvm from stack list ospvms --> redhouse vms.
    # TODO: IN that case need to attach to different path.
    print("Destroying {0}".format(vm_name))
    try:
        myvag_env = vagrant_utils.Connect_to_vagrant(vm_name=vm_name,
                                                     path=ctx.path)
        myvag_env.v.destroy(vm_name)
    except CalledProcessError:
        slab_logger.info(VM_DOESNT_EXIST_MESSAGE)

    myvfile = Vf_utils.SlabVagrantfile(path=ctx.path)
    print("{0} {1} from Vagrantfile".format(VAGRANTFILE_DELETE_MESSAGE, vm_name))
    if not myvfile.delete_virtualbox_vm(vm_name):
        print("VM {0} not found in Vagrantfile".format(vm_name))
    print("{0} {1}".format(INVENTORY_DELETE_MESSAGE, vm_name))
    yaml_utils.host_del_vagrantyaml(ctx.path, "vagrant.yaml", vm_name)
    vm_yaml_file = "%s/services/ccs-data/sites/ccs-dev-1/environments/"\
                   "dev-tenant/hosts.d/%s.yaml" % (ctx.path, vm_name)
    print("Deleting the VM YAML file : %s" % (vm_yaml_file))
    if os.path.exists(vm_yaml_file):
        os.remove(vm_yaml_file)
    else:
        print("VM YAML file not found. Proceeeding.")
    print(REBUILDING_CCSDATA_MESSAGE)
    service_utils.build_data(ctx.path)
    print("Updating hosts.yaml on infra node.")
    print("Detecting infra node port.")
    return_code, port_no = vagrant_utils.get_ssh_port_for_vm("infra-001", ctx.path)
    if return_code != 0:
        print("Unable to find port no. of infra node, cannot update"
              "hosts.yaml on infra node")
        return
    else:
        print("%s %s " % (INFRA_PORT_DETECT_MESSAGE, port_no))
        yaml_file = "./services/ccs-data/out/ccs-dev-1/dev/etc/ccs/data/hosts.yaml"
        vm_yaml_file = "/etc/ccs/data/environments/dev-tenant/hosts.yaml"
        yaml_file_path = os.path.join(ctx.path, yaml_file)
        return_code, ret_info = vagrant_utils.copy_file_to_vm(yaml_file_path, port_no,
                                                              vm_yaml_file, ctx.path)
        if return_code != 0:
            print("Could not succesfully update hosts.yaml on infra node.")
        else:
            print(UPDATING_HOSTS_YAML_MESSAGE)


@click.option('-f', '--force', is_flag=True, help='Do not prompt me to destroy'
              'local environment')
@cli.command(
    'min',
    short_help='Destroy the least required to put the local environment'
               ' back into a usable state.')
@pass_context
def destroy_min(ctx, force):
    """ Destroy the minimum required to put us into a usable, but still mostly
    brownfield environment.

    Delete:
    1. .stack/vagrant.yaml
    2. .stack/Vagrantfile
    3. .stack/.vagrant/machines/
    4. .stack/services/service-redhouse-tenant/.vagrant/machines
    5. .stack/services/service-redhouse-tenant/settings.yaml
    """
    slab_logger.info('Destroying all vagrant files')
    directories = ['services/service-redhouse-tenant/.vagrant/machines',
                   'services/service-redhouse-tenant/settings.yaml',
                   '.vagrant/machines']
    files = ['Vagrantfile', 'vagrant.yaml']

    # before we destroy lets check if we have any machine not destroyed still
    slab_logger.log(25, "Checking for active VMs.")
    if vagrant_utils.check_vm_is_available(ctx.path):
        slab_logger.log(25, "There are active VMs in the stack environment. "
                        "Please destroy these using stack destroy vm command\n")
        sys.exit(-1)
    slab_logger.log(25, "No active VMs found. Proceeding with destroy.")

    directories = [os.path.join(ctx.path, di) for di in directories]
    files = [os.path.join(ctx.path, fi) for fi in files]

    returncode = helper_utils.destroy_files(files)
    if returncode > 0:
        slab_logger.error('Failed to delete all the required files: ')
        slab_logger.error(files)
        sys.exit(1)

    returncode = helper_utils.destroy_dirs(directories)
    if returncode > 0:
        slab_logger.error('Failed to delete all the required files: ')
        slab_logger.error(files)
        sys.exit(1)


@click.option('-f', '--force', is_flag=True, help='Do not prompt me to destroy'
              'more of local environment')
@cli.command(
    'more',
    short_help='Destroy my ccs-data and service-redhouse-tenant'
    ' as well as the minimum necessary to refresh the environment')
@pass_context
def destroy_more(ctx, force):
    """ Destroy my copy of ccs-data and service-redhouse-tenant in addition to the
    minimum need to get us into a usable, but still mostly brownfield environment.

    Delete:
    1. .stack/vagrant.yaml
    2. .stack/Vagrantfile
    3. .stack/.vagrant/machines/
    4. .stack/services/service-redhouse-tenant/
    5. .stack/services/ccs-data/
    """
    slab_logger.info('Destroying vagrant files, ccs-data and service-redhouse-tenant repos')
    directories = ['services/service-redhouse-tenant',
                   'services/ccs-data',
                   '.vagrant/machines']
    files = ['Vagrantfile', 'vagrant.yaml']

    directories = [os.path.join(ctx.path, di) for di in directories]
    files = [os.path.join(ctx.path, fi) for fi in files]

    returncode = helper_utils.destroy_files(files)
    if returncode > 0:
        slab_logger.error('Failed to delete all the required files: ')
        slab_logger.error(files)
        sys.exit(1)
    returncode = helper_utils.destroy_dirs(directories)
    if returncode > 0:
        slab_logger.error('Failed to delete all the required directories: ')
        slab_logger.error(directories)
        sys.exit(1)


@click.option('-f', '--force', is_flag=True, help='Do not prompt me to destroy'
              'an artifact')
@cli.command('artifact', short_help='Destroy an artifact in Artifactory.')
@click.argument('artifact_name')
@pass_context
def destory_artifact(ctx, force, artifact_name):
    """
    Destroys an artifact in Artifactory.
    """
    pass


@cli.command('repo', short_help='Destroy a repo in Gerrit.')
@click.argument('repo_name')
@pass_context
def destory_gerritrepo(ctx, repo_name):
    """
    Destroys an artifact in Artifactory.
    """
    slab_logger.warning('This command requires admin privledges')
    slab_logger.info('Destroying repo %s in Gerrit' % repo_name)


@click.option('-f', '--force', is_flag=True, help='Do not prompt me to destroy'
              'the networking in an openstack project')
@cli.command(
    'os-networks',
    short_help='Destroy all networking components in an Openstack project.')
@pass_context
def destroy_os_networks(ctx, force):
    """Destroy all the networking components in an openstack project including, routers,
    interfaces. networks, subnets. This requires having the openstack credentials sourced,
    as well as no VMs to be existing presently.
    """
    slab_logger.info('Destroying all Openstack networking components')
    # Can abstract to servicelab/utils/openstack_utils and leverage that code.
    returncode, running_vm = openstack_utils.os_check_vms(ctx.path)
    if returncode == 0:
        if not running_vm:
            openstack_utils.os_delete_networks(ctx.path, force)
        else:
            slab_logger.error(
                "The above VMs need to be deleted before you can run this command.")
    else:
        slab_logger.error("Error occurred connecting to Vagrant. To debug try running : "
                          "vagrant up in %s " % (ctx.path))


@click.option('-f', '--force', is_flag=True, help='Do not prompt me to destroy'
              'all of the vms in an openstack project')
@cli.command('os-vms', short_help='Destroy all the VMs in an Openstack project.')
@pass_context
def destroy_os_vms(ctx, force):
    """Destroy all the vms in an openstack project. You must have your openstack env
    vars sourced to your local shell environment.
    """
    openstack_utils.os_delete_vms(ctx.path, force)
