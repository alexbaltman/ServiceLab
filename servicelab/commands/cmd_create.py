import click
from fabric.api import run
from servicelab.stack import pass_context


@click.group('create', short_help='Creates pipeline resources to work with.',
             add_help_option=True)
@click.pass_context
def cli(ctx):
    """Stack Create command line client"""
    pass


@cli.command('repo', short_help='Create repo')
@click.argument('repo_name', required=True)
@click.option('--kind', prompt='Which type of repo? '
                               'Standard, Ansible, or Puppet')
@pass_context
def repo_new(ctx, repo_name, kind):
    """Creates a repository in gerrit production, does 1st commit,
    sets up directory structure, and creates nimbus.yml by leveraging
    Fabric's Pythonic remote execution.

    Sets up service automation dir structure when init a gerrit repo.

    For instance if it's puppet, setup that directory structure

    If it's Ansible have user commit it.

    Add .nimbus.yml file to repo

    Add an interactive mode so they can choose options.

    :param repo_name:    The name of the repository
    :param kind:         The type of repo (Standard, Ansible, Puppet)

    .. note::
        Work to be done to keep up with DRY principles and
        folder structure setup. Needs prompt validation if user did not input
        correct type of repo.
    """

    kind_lower = kind.lower()
    click.echo('Creating Project: {}'.format(kind_lower))
    if kind_lower == 'standard':
        run('fab create_standard')
    elif kind_lower == 'ansible':
        run('fab create_ansible')
    elif kind_lower == 'puppet':
        run('fab create_puppet')
    return


@cli.command('host')
@click.argument('host_name')
@click.option('-e', '--env', help='Choose an environment to put your host \
               into - use the list command to see what environments are \
               available.')
@pass_context
def host_new(ctx, host_name, env):
    """
    Creates a host.yaml file in an environment so that a vm can then be
    booted.
    """
    click.echo('creating new host yaml for %s ...' % host_name)


@cli.command('site')
@click.argument('site_name')
@click.option('cont', '--continue', help='If you did not finish \
               creating your site and paused midway you can continue it.')
@click.option('cont', '--abort', help='If you did not finish \
               creating your site and paused midway you can abort it.')
@pass_context
def site_new(ctx, site_name, cont):
    """
    Create a whole site in ccs-data.
    """
    click.echo('creating new host yaml for %s ...' % site_name)


@cli.command('env')
@click.argument('env_name')
# What site to put your named environment under.
@click.argument('site')
@click.option('cont', '--continue', help='If you did not finish \
               creating your site and paused midway you can continue it.')
@click.option('cont', '--abort', help='If you did not finish \
               creating your site and paused mid-way you can abort it.')
@pass_context
def env_new(ctx, env_name, site, cont):
    """
    Create a new environment in a site in ccs-data.
    """
    click.echo('Creating new env yamls in %s for %s' % (site, env_name))


# RFI: is this the right place for this integration w/ haproxy?
@cli.command('vip')
# It probably won't take in name
@click.argument('vip_name')
@click.argument('env_name')
# Should be able to create a template for your service and use that too.
@pass_context
def vip_new(ctx, vip_name, env_name):
    """
    Create a new VIP in a site in ccs-data in order to integrate your
    service with haproxy at that particular site.
    """
    click.echo('Creating new vip entry in %s for %s' % (env_name, vip_name))
