""" We're not trying to replace the openstack CLI tool/s so we have to be careful
here on what we want to acheive w/o overlapping. For instance, destroying all of
soemthing is useful and non-overlapping b/c of the order requirements imposed on
the operator as well as the quantity, but deleting one thing would be complete
overlap w/ openstack cli tools.
"""
import os
import sys

import click

from servicelab.stack import pass_context
from servicelab.utils import vagrant_utils
from servicelab.utils import helper_utils
from servicelab.utils import openstack_utils


@click.group('destroy', short_help='Destroys VMs.')
@pass_context
def cli(ctx):
    """
    Destroy things.
    """
    pass


@click.option('-f', '--force', is_flag=True, help='Do not prompt me to destroy'
              'my vm')
@cli.command(
    'vm',
    short_help='Destroy a vm that your servicelab vagrant environment'
    'knows about')
@click.argument('vm_name')
@pass_context
def destroy_vm(ctx, force, vm_name):
    """Destroy non OSP VMs in either virtualbox or Openstack. This function
    will do some basic cleanup as well.

    1. Remove from inventory. (?)
    2. Delete from Vagrantfile (?)
    3. Remove from dev-tenant in ccs-data (?)
    """
    ctx.logger.debug("Destroying {0}".format(vm_name))
    # What if it's an ospvm from stack list ospvms --> redhouse vms.
    # TODO: IN that case need to attach to different path.
    myvag_env = vagrant_utils.Connect_to_vagrant(vm_name=vm_name,
                                                 path=ctx.path)
    myvag_env.v.destroy(vm_name)


@click.option('-f', '--force', is_flag=True, help='Do not prompt me to destroy'
              'local environment')
@cli.command(
    'min',
    short_help='Destroy the minimum required in the local environment.')
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
    directories = ['services/service-redhouse-tenant/.vagrant/machines',
                   'services/service-redhouse-tenant/settings.yaml',
                   '.vagrant/machines']
    files = ['Vagrantfile', 'vagrant.yaml']

    directories = [os.path.join(ctx.path, di) for di in directories]
    files = [os.path.join(ctx.path, fi) for fi in files]

    returncode = helper_utils.destroy_files(files)
    if returncode > 0:
        ctx.logger.error('Failed to delete all the required files: ')
        ctx.logger.error(files)
        sys.exit(1)

    returncode = helper_utils.destroy_dirs(directories)
    if returncode > 0:
        ctx.logger.error('Failed to delete all the required files: ')
        ctx.logger.error(files)
        sys.exit(1)


@click.option('-f', '--force', is_flag=True, help='Do not prompt me to destroy'
              'more of local environment')
@cli.command(
    'more',
    short_help='Destroy my ccs-data and service-redhouse-tenant'
    'as well as the minimum necessary to refresh env.')
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
    directories = ['services/service-redhouse-tenant',
                   'services/ccs-data',
                   '.vagrant/machines']
    files = ['Vagrantfile', 'vagrant.yaml']

    directories = [os.path.join(ctx.path, di) for di in directories]
    files = [os.path.join(ctx.path, fi) for fi in files]

    returncode = helper_utils.destroy_files(files)
    if returncode > 0:
        ctx.logger.error('Failed to delete all the required files: ')
        ctx.logger.error(files)
        sys.exit(1)
    returncode = helper_utils.destroy_dirs(directories)
    if returncode > 0:
        ctx.logger.error('Failed to delete all the required directories: ')
        ctx.logger.error(directories)
        sys.exit(1)


@click.option('-f', '--force', is_flag=True, help='Do not prompt me to destroy'
              'an artifact')
@cli.command('artifact', short_help='Destroy an artifact in artifactory.')
@click.argument('artifact_name')
@pass_context
def destory_artifact(ctx, force, artifact_name):
    """
    Destroys an artifact in Artifactory.
    """
    pass


@cli.command('repo', short_help='Destroy an repo in Gerrit.')
@click.argument('repo_name')
@pass_context
def destory_gerritrepo(ctx, repo_name):
    """
    Destroys an artifact in Artifactory.
    """
    ctx.logger.warning('This command requires admin privledges')
    click.echo('Destroying repo %s in Gerrit' % repo_name)


@click.option('-f', '--force', is_flag=True, help='Do not prompt me to destroy'
              'the networking in an openstack project')
@cli.command(
    'os-networks',
    short_help='Destroy all networking components in a project')
@pass_context
def destroy_os_networks(ctx, force):
    """Destroy all the networking components in an openstack project including, routers,
    interfaces. networks, subnets. This requires having the openstack credentials sourced,
    as well as no VMs to be existing presently.
    """
    # Can abstract to servicelab/utils/openstack_utils and leverage that code.
    returncode, running_vm = openstack_utils.os_check_vms(ctx.path)
    if returncode == 0:
        if not running_vm:
            openstack_utils.os_delete_networks(ctx.path, force)
        else:
            click.echo(
                "The above VMs need to be deleted before you can run this command.")
    else:
        click.echo("Error occurred connecting to Vagrant. To debug try running : vagrant up"
                   " in %s " % (ctx.path))


@click.option('-f', '--force', is_flag=True, help='Do not prompt me to destroy'
              'all of the vms in an openstack project')
@cli.command('os-vms', short_help='Destroy all the VMs in a project')
@pass_context
def destroy_os_vms(ctx, force):
    """Destroy all the vms in an openstack project. You must have your openstack env
    vars sourced to your local shell environment.
    """
    openstack_utils.os_delete_vms(ctx.path, force)
