import click
from servicelab.stack import pass_context


@click.group('create', short_help='Creates a pipeline resources to work with.',
             add_help_option=True)
@click.pass_context
def cli(ctx):
    pass


@cli.command('repo', short_help='Create a repository in Gerrit')
@click.argument('name')
@click.option('-i', '--interactive', help='Create repo interactively \
               with extra details.')
@click.option('-t', '--type', default="service", help='Choose a repo \
               type - either service(config management) or project(source).')
@pass_context
def repo_new(ctx, name):
    """
    Creates a repository in gerrit
    production, does 1st commit, sets up
    directory structure, and creates .nimbus.yml
    """
    click.echo('creating git repository %s ...' % name)


@cli.command('host')
@click.argument('name')
@click.option('-e', '--env', help='Choose an environment to put your host \
               into - use the list command to see what environments are \
               available.') 
def host_new(ctx, name):
    """
    Creates a host.yaml file in an environment so that a vm can then be
    booted.
    """
    pass


@cli.command('site')
@click.argument('name')
@click.option('--continue', help='If you did not finish \
               creating your site and paused midway you can continue it.')
@click.option('--abort', help='If you did not finish \
               creating your site and paused midway you can abort it.')
def site_new(ctx, name):
    """
    Create a whole site in ccs-data.
    """
    pass


@cli.command('env')
@click.argument('name')
@click.option('--continue', help='If you did not finish \
               creating your site and paused midway you can continue it.')
@click.option('--abort', help='If you did not finish \
               creating your site and paused mid-way you can abort it.')
def env_new(ctx, name):
    """
    Create a new environment in a site in ccs-data.
    """
    pass


# RFI: is this the right place for this integration w/ haproxy?
@cli.command('vip')
# It probably won't take in name
@click.argument('name')
# Should be able to create a template for your service and use that too.
def vip_new(ctx, name):
    """
    Create a new VIP in a site in ccs-data in order to integrate your
    service with haproxy at that particular site.
    """
    pass
