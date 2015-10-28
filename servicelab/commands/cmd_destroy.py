""" We're not trying to replace the openstack CLI tool/s so we have to be careful
here on what we want to acheive w/o overlapping. For instance, destroying all of
soemthing is useful and non-overlapping b/c of the order requirements imposed on
the operator as well as the quantity, but deleting one thing would be complete
overlap w/ openstack cli tools.
"""
import os

import click
import shutil

from servicelab.stack import pass_context
from servicelab.utils import vagrant_utils


@click.group('destroy', short_help='Destroys VMs.')
@pass_context
def cli(ctx):
    """
    Destroy things.
    """
    pass


@click.option('-f', '--force', is_flag=True, help='Do not prompt me to destroy'
              'my vm')
@cli.command('vm', short_help='Destroy a vm that your servicelab vagrant environment'
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
@cli.command('min', short_help='Destroy the least necessary in the local environment.')
@pass_context
def destroy_min(ctx, force):
    """ Destroy the minimum required to put us into a usable, but still mostly
    brownfield environment.

    Delete:
    1. .stack/vagrant.yaml
    2. .stack/Vagrantfile
    3. .stack/.vagrant/machines/
    4. .stack/services/service-redhouse-tenant/.vagrant
    5. .stack/services/service-redhouse-tenant/settings.yaml
    """
    ctx.logger.debug("Destroying {0}".format(os.path.join(ctx.path,
                                                          "vagrant.yaml")))
    os.remove(os.path.join(ctx.path, "vagrant.yaml"))
    ctx.logger.debug("Destroying {0}".format(os.path.join(ctx.path,
                                                          "Vagrantfile")))
    os.remove(os.path.join(ctx.path, "Vagrantfile"))
    ctx.logger.debug("Destroying {0}".format(os.path.join(ctx.path,
                                                          ".vagrant",
                                                          "machines")))
    shutil.rmtree(os.path.join(ctx.path,
                               ".vagrant",
                               "machines"))
    red_path = os.path.join(ctx.path,
                            "services",
                            "service-redhouse-tenant")
    if os.path.exists(os.path.join(red_path, ".vagrant")):
        ctx.logger.debug("Destroying {0}".format(os.path.join(red_path, ".vagrant")))
        shutil.rmtree(os.path.join(red_path,
                                   ".vagrant"))
        ctx.logger.debug("Destroying {0}".format(os.path.join(red_path, "settings.yaml")))
        os.remove(os.path.join(red_path, "settings.yaml"))


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
@cli.command('os-networks', short_help='Destroy all networking components in a project')
@pass_context
def destroy_os_networks(ctx, force):
    """Destroy all the networking components in an openstack project including, routers,
    interfaces. networks, subnets. This requires having the openstack credentials sourced,
    as well as no VMs to be existing presently.
    """
    # Can abstract to servicelab/utils/openstack_utils and leverage that code.
    pass


@click.option('-f', '--force', is_flag=True, help='Do not prompt me to destroy'
              'all of the vms in an openstack project')
@cli.command('os-vms', short_help='Destroy all the VMs in a project')
@pass_context
def destroy_os_vms(ctx, force):
    """Destroy all the vms in an openstack project. You must have your openstack env
    vars sourced to your local shell environment.
    """
    # Can abstract to servicelab/utils/openstack_utils and leverage that code.
    pass


@click.option('-f', '--force', is_flag=True, help='Do not prompt me to destroy'
              'a pipeline in GO-CD')
@cli.command('pipe', short_help='Destroy a pipeline in GO-CD')
@pass_context
def destroy_os_vms(ctx, force):
    """Destroy a pipeline in GO-CD. You must be an admin to do so successfully
    """
    # Can abstract to servicelab/utils/gocd_utils and leverage that code.
    ctx.logger.warning("You must be an SDLC admin to successfully delete a pipeline")
