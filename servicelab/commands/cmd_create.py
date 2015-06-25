import click
from servicelab.stack import pass_context


@click.group('create', short_help='Creates a pipeline resources to work with.',
             invoke_without_command=True, add_help_option=True)
@click.pass_context
def create(ctx):
    pass


@create.command('repo', short_help='Create a repository in Gerrit')
@create.argument('name')
@create.option('-i', '--interactive', help='Create repo interactively
               with extra details')
# Other option is "source" repository
@create.option('-t', '--type', default="service", help='Choose a repo
               type - either service(config management) or project(source)')
@pass_context
def repo_new(ctx, name):
    """
    Creates a repository in gerrit
    production, does 1st commit, sets up
    directory structure, and creates .nimbus.yml
    """
    click.echo('creating git repository %s ...' % name)


@create.command('host')
@create.argument('name')
@create.option('-e', '--env', help='Choose an environment to put your host
               into - use the list command to see what environments are
               available')
def host_new(ctx, name):
    """
    Creates a host.yaml file in an environment so that a vm can then be
    booted.
    """
    pass


@create.command('site')
@create.argument('name')
def site_new(ctx, name):
    """
    Create a whole site in ccs-data.
    """
    pass


@create.command('env')
@create.argument('name')
def env_new(ctx, name):
    """
    Create a new environment in a site in ccs-data.
    """
    pass

# RFI: is this the right place for this integration w/ haproxy?
@create.command('vip')
# It probably won't take in name
@create.argument('name')
# Should be able to create a template for your service and use that too.
def vip_new(ctx, name):
    """
    Create a new VIP in a site in ccs-data in order to integrate your
    service with haproxy at that particular site.
    """
    pass
