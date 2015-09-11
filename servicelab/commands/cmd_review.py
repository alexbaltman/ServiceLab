import click
from servicelab.stack import pass_context
from servicelab.utils import helper_utils
from servicelab.utils import gerrit_functions


@click.group('review', short_help='Helps you work with Gerrit')
@pass_context
def cli(ctx):
    """
    Helps you work with Gerrit.
    """
    pass


# RFI: Aren't the inc and out basically the same as list out review
# list inc review? Do we need both?
@cli.command('inc', short_help='Find incoming reviews Gerrit.')
@click.option('-p', '--project', help='Enter the project')
@click.option('-u', '--username', help='Enter the desired username')
@click.option('-d', '--detail', help='Show detailed description',
              flag_value=True, default=False)
@pass_context
def review_inc(ctx, project, username, detail):
    """
    Searches through Gerrit's API for incoming reviews for your username.
    """
    if not username:
        username = click.prompt("User Name",
                                default=helper_utils.get_username(ctx.path))

    if not project:
        project = click.prompt("Project Name",
                               default=helper_utils.get_current_service(ctx.path)[1])
    gfn = gerrit_functions.GerritFns(username, project, ctx)
    if detail:
        gfn.print_gerrit(pformat="detail", number=None, owner="",
                         reviewer=username, status="open")
    else:
        gfn.print_gerrit(pformat="summary", number=None, owner="",
                         reviewer=username, status="open")


@cli.command('out', short_help='Find outgoing reviews in Gerrit.')
@click.option('-p', '--project', help='Enter the project')
@click.option('-u', '--username', help='Enter the desired username')
@click.option('-d', '--detail', help='Show detailed description', default=False)
@pass_context
def review_out(ctx, project, username, detail):
    """
    Searches through Gerrit's API for outgoing reviews for your username.
    """
    click.echo('Grabbing outgoing reviews from Gerrit')
    if not username:
        username = click.prompt("User Name",
                                default=helper_utils.get_username(ctx.path))

    if not project:
        project = click.prompt("Project Name",
                               default=helper_utils.get_current_service(ctx.path)[1])
    gfn = gerrit_functions.GerritFns(username, project, ctx)
    if detail:
        gfn.print_gerrit(pformat="detail", number=None, owner=username,
                         reviewer="", status="open")
    else:
        gfn.print_gerrit(pformat="summary", number=None, owner=username,
                         reviewer="", status="open")


# RFI: Can we do +2 w/ the plus?
@cli.command('plustwo', short_help='Plus two gerrit change set.')
@click.argument('item')
@click.option('-p', '--project', help='Enter the project')
@click.option('-u', '--username', help='Enter the desired username')
@click.option('-m', '--message', help='Enter the desired message', type=str, default="")
@pass_context
def review_plustwo(ctx, review, project, username, message):
    """
    Approves and merges a gerrit change set.
    """
    if not username:
        username = click.prompt("User Name",
                                default=helper_utils.get_username(ctx.path))

    if not project:
        project = click.prompt("Project Name",
                               default=helper_utils.get_current_service(ctx.path)[1])

    if not message:
        message = click.prompt("Message", default=message)

    gfn = gerrit_functions.GerritFns(username, project, ctx)
    gfn.change_review(review, 2, 1, message)


@cli.command('plusone', short_help='Plus one gerrit change set.')
@click.argument('review')
@click.option('-p', '--project', help='Enter the project')
@click.option('-u', '--username', help='Enter the desired username')
@click.option('-m', '--message', help='Enter the desired message', type=str, default="")
@pass_context
def review_plusone(ctx, review, project, username, message):
    """
    Approves, but does not merge a gerrit change set, which means change set
    requires another approver.
    """
    if not username:
        username = click.prompt("User Name",
                                default=helper_utils.get_username(ctx.path))

    if not project:
        project = click.prompt("Project Name",
                               default=helper_utils.get_current_service(ctx.path)[1])

    if not message:
        message = click.prompt("Message", default=message)

    gfn = gerrit_functions.GerritFns(username, project, ctx)
    gfn.change_review(review, 1, 0, message)


@cli.command('minusone', short_help='Minus one gerrit change set.')
@click.argument('review')
@click.option('-p', '--project', help='Enter the project')
@click.option('-u', '--username', help='Enter the desired username')
@click.option('-m', '--message', help='Enter the desired message', type=str, default="")
@pass_context
def review_minusone(ctx, review, project, username, message):
    """
    Prefer the code is not submitted.
    """
    if not username:
        username = click.prompt("User Name",
                                default=helper_utils.get_username(ctx.path))

    if not project:
        project = click.prompt("Project Name",
                               default=helper_utils.get_current_service(ctx.path)[1])

    if not message:
        message = click.prompt("Message", default=message)

    gfn = gerrit_functions.GerritFns(username, project, ctx)
    gfn.change_review(review, -1, 0, message)


@cli.command('minustwo', short_help='Minus two gerrit change set.')
@click.argument('review')
@click.option('-p', '--project', help='Enter the project')
@click.option('-u', '--username', help='Enter the desired username')
@click.option('-m', '--message', help='Enter the desired message', type=str, default="")
@pass_context
def review_minustwo(ctx, review, project, username, message):
    """
    Do not submit the code
    """
    if not username:
        username = click.prompt("User Name",
                                default=helper_utils.get_username(ctx.path))

    if not project:
        project = click.prompt("Project Name",
                               default=helper_utils.get_current_service(ctx.path)[1])

    if not message:
        message = click.prompt("Message", default=message)

    gfn = gerrit_functions.GerritFns(username, project, ctx)
    gfn.change_review(review, -1, 0, message)


@cli.command('abandon', short_help='Abandon gerrit change set.')
@click.argument('review')
@click.option('-p', '--project', help='Enter the project')
@click.option('-u', '--username', help='Enter the desired username')
@click.option('-m', '--message', help='Enter the desired message', type=str, default="")
@pass_context
def review_abandon(ctx, review, project, username, message):
    """
    Abandon a gerrit change set.
    """
    if not username:
        username = click.prompt("User Name",
                                default=helper_utils.get_username(ctx.path))

    if not project:
        project = click.prompt("Project Name",
                               default=helper_utils.get_current_service(ctx.path)[1])

    if not message:
        message = click.prompt("Message", default=message)

    gfn = gerrit_functions.GerritFns(username, project, ctx)
    gfn.code_state(review, "abandon", message)


@cli.command('show', short_help='display  particular review')
@click.argument('review')
@click.option('-p', '--project', help='Enter the project')
@click.option('-u', '--username', help='Enter the desired username')
@pass_context
def review_show(ctx, review, project, username):
    """
    Display the review
    """
    if not username:
        username = click.prompt("User Name",
                                default=helper_utils.get_username(ctx.path))

    if not project:
        project = click.prompt("Project Name",
                               default=helper_utils.get_current_service(ctx.path)[1])

    gfn = gerrit_functions.GerritFns(username, project, ctx)
    gfn.print_gerrit("detail", review)


@cli.command('code', short_help='display  particular review changeset details')
@click.argument('review')
@click.option('-p', '--project', help='Enter the project')
@click.option('-u', '--username', help='Enter the desired username')
@pass_context
def review_code(ctx, review, project, username):
    """
    Display the review
    """
    if not username:
        username = click.prompt("User Name",
                                default=helper_utils.get_username(ctx.path))

    if not project:
        project = click.prompt("Project Name",
                               default=helper_utils.get_current_service(ctx.path)[1])

    gfn = gerrit_functions.GerritFns(username, project, ctx)
    gfn.code_review(review)
