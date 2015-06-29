import click
from servicelab.stack import pass_context


@click.group('create', short_help='Creates a pipeline resources to work with.',
             add_help_option=True)
@click.pass_context
def cli(ctx):
    pass


@cli.command('repo', short_help='Create a repository in Gerrit')
@click.argument('repo_name')
# Note: If you want a -<single_letter> to appear in your cmd and your help
#       pages then you have to take the full name into your command's
#       functions. The other option is to not put the - and take in
#       just the letter into the function.
@click.option('-i', '--interactive', default=False, help='Create repo interactively \
               with extra details.')
@click.option('-t', '--type', default="service", help='Choose a repo \
               type - either service(config management) or project(source).')
@pass_context
def repo_new(ctx, repo_name, interactive, type):
    """
    Creates a repository in gerrit
    production, does 1st commit, sets up
    directory structure, and creates .nimbus.yml
    """
    click.echo('creating git repository %s ...' % repo_name)


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
#What site to put your named environment under.
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
