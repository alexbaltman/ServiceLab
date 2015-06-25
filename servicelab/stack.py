#!/usr/bin/env python

import click
import os
import sys

# TODO: "This is a stub so we can grep out all TODO items in the code
# RFI:  "This is a stub where we need to make a coordinated decision about
# something. Request for input/information.
# --> no stub regular comment. More of the why less of the what or how.


# Load Plugins
CONTEXT_SETTINGS = dict(auto_envvar_prefix='COMPLEX')


class Context(object):

    def __init__(self):
        self.verbose = False
        self.path = os.getcwd()

    def log(self, msg, *args):
        """Logs a message to stderr."""
        if args:
            msg %= args
        click.echo(msg, file=sys.stderr)

    def vlog(self, msg, *args):
        """Logs a message to stderr only if verbose is enabled."""
        if self.verbose:
            self.log(msg, *args)

    def vvlog(self, msg, *args):
        """Logs a message to stderr only if double verbose is enabled."""
        if self.vverbose:
            self.log(msg, *args)

    def debug(self, msg, *args):
        """Logs a message to stderr only if debug is enabled."""
        if self.debug:
            self.log(msg, *args)

pass_context = click.make_pass_decorator(Context, ensure=True)
cmd_folder = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                          'commands'))


class ComplexCLI(click.MultiCommand):

    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(cmd_folder):
            if filename.endswith('.py') and \
               filename.startswith('cmd_'):
                rv.append(filename[4:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        try:
            if sys.version_info[0] == 2:
                name = name.encode('ascii', 'replace')
            mod = __import__('servicelab.commands.cmd_' + name,
                             None, None, ['cli'])
        except ImportError:
            return
        return mod.cli


@click.command(cls=ComplexCLI, context_settings=CONTEXT_SETTINGS)
# RFI: Do we need the below option?
@click.option('--path','-p', type=click.Path(exists=True, file_okay=False,
                                        resolve_path=True),
              help='Changes the folder to operate on.')
@click.option('--verbose', '-v', is_flag=True,
              help='Enables verbose mode.')
@click.option('--vverbose', '-vv', is_flag=True,
              help='Enables verbose mode.')
@click.option('--debug', '-vvv', is_flag=True,
              help='Enables verbose mode.')
@pass_context
def cli(ctx, verbose, vverbose, debug, path):
    """A CLI for Cisco Cloud Services."""
    ctx.verbose = verbose
    ctx.vverbose = vverbose
    ctx.debug = debug
    if path is not None:
        ctx.path = path
