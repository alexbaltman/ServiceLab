import logging
import click
import os
import sys

# TODO: "This is a stub so we can grep out all TODO items in the code
# RFI:  "This is a stub where we need to make a coordinated decision about
# something. Request for input/information.
# --> no stub regular comment. More of the why less of the what or how.


# Global Variables
# auto envvar prefix will take in any env vars that are prefixed with STK
# short for stack.
CONTEXT_SETTINGS = dict(auto_envvar_prefix='STK')


# Setup class context object to pass to all commands that opt in to
# context. You can access through ctx attribute. E.G. ctx.verbose.
class Context(object):

    def __init__(self):
        self.path = os.path.join(os.path.dirname(__file__), '.stack')
        self.config = os.path.join(os.path.dirname(__file__),
                                   '.stack/stack.conf')
        # Setup Logging
        self.branch = "master"
        self.verbose = False
        self.vverbose = False
        self.debug = False
        self.logger = logging.getLogger('click_application')
        self.setLevel(logging.INFO)
        # Create filehandler that logs everything.
        self.file_handler = logging.FileHandler('stack.log')
        self.file_handler.setLevel(logging.DEBUG)
        # Create console handler that logs up to error msg.s.
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(logging.INFO)
        # Create formatter and add it to the handlers
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(Levelname)s - %(message)s')
        self.file_handler.setFormatter(self.formatter)
        self.console_handler.setFormatter(self.formatter)
        # Add handlers to the logger
        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(self.console_handler)


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
@click.option('--path', '-p', type=click.Path(exists=True, file_okay=False,
              resolve_path=True),
              help='Indicates your working servicelab folder.')
@click.option('--verbose', '-v', is_flag=True, default=False,
              help='Enables verbose mode.')
@click.option('--vverbose', '-vv', is_flag=True, default=False,
              help='Enables extra verbose mode.')
@click.option('--debug', '-vvv', is_flag=True, default=False,
              help='Enables debug mode.')
@click.option('--config', '-c', help='You can specify a config file for \
              stack to pull information from.')
@pass_context
def cli(ctx, verbose, vverbose, debug, path, config):
    """A CLI for Cisco Cloud Services."""
    ctx.verbose = verbose
    ctx.vverbose = vverbose
    ctx.debug = debug
    if ctx.verbose:
        ctx.console_handler.setLevel(logging.WARNING)
    if ctx.vverbose:
        ctx.console_handler.setLevel(logging.ERROR)
    if ctx.debug:
        ctx.console_handler.setLevel(logging.DEBUG)
    if path is not None:
        ctx.path = path
    if config is not None:
        ctx.config = config
