""" We're not trying to replace the openstack CLI tool/s so we have to be careful
here on what we want to acheive w/o overlapping. For instance, destroying all of
soemthing is useful and non-overlapping b/c of the order requirements imposed on
the operator as well as the quantity, but deleting one thing would be complete
overlap w/ openstack cli tools.
"""
import os
import sys
from subprocess import CalledProcessError

import click

from servicelab.utils import logger_utils
from servicelab.stack import pass_context
from servicelab.utils import vagrant_utils
from servicelab.utils import helper_utils
from servicelab.utils import openstack_utils
from servicelab.utils import vm_utils
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
@click.option('-a', '--all-vms', is_flag=True, help='Destroy all vms')
@cli.command(
    'vm',
    short_help='Destroy a servicelab vm.'
    ' knows about.')
@click.argument('vm_name', default="")
@pass_context
def destroy_vm(ctx, force, vm_name, all_vms):
    """Destroy non OSP VMs in either virtualbox or Openstack. This function
    will do some basic cleanup as well.
    1. Destroys the VM
    2. Deletes from Vagrantfile
    3. Removes the service-<service-name>.yaml from environments
    3. Reruns heighliner
    4. Updates the hosts.yaml on infra node
    """
    # What if it's an ospvm from stack list ospvms --> redhouse vms.
    # TODO: IN that case need to attach to different path.
    if all_vms:
        if vm_name:
            slab_logger.error("VM Name cannot be specified with --all-vms option.")
        else:
            vm_connection = vagrant_utils.Connect_to_vagrant(vm_name="infra-001",
                                                             path=ctx.path)
            try:
                statuses = vm_connection.v.status()
                for status in statuses:
                    if "infra-001" not in status[0]:
                        vm_utils.destroy_vm_by_name(ctx, force, status[0])
            except CalledProcessError:
                error_message = "\nCannot show VM status since internal error "\
                    "has occurred. Most probably this file does not "\
                    "exist : %s . Please, run : stack workon <project name>"\
                    " to fix the issue." % (ctx.path)
                slab_logger.error(error_message)
                sys.exit(1)
    else:
        if not vm_name:
            slab_logger.error("Please, specify the VM name to be deleted.")
        else:
            vm_utils.destroy_vm_by_name(ctx, force, vm_name)


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
