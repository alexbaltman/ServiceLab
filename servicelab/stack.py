"""
stack
"""
import os
import sys

import logging

import click

# Global Variables
# auto envvar prefix will take in any env vars that are prefixed with STK
# short for stack.
CONTEXT_SETTINGS = dict(auto_envvar_prefix='STK')


class Context(object):
    """
    Setup class context object to pass to all commands that opt in to
    context. You can access through ctx attribute. E.G. ctx.verbose.

    Attributes -
        path = os.path.join(os.path.dirname(__file__), '.stack')
        config = os.path.join(os.path.dirname(__file__),
                                   '.stack/stack.conf')

        pkey_name (str)    - servicelab public key

        branch (str)
        verbose (boolean)
        vverbose (boolean)
        debug (boolean)
        logger (logger)

        file_handler       - Create filehandler that logs everything.
        console_handler    - Create console handler that logs up to error msg.s.
        formatter          - Create formatter and add it to the handlers

        __gerrit_test_info - Gerrit staging server
        __gerrit_info      - Gerrit server


    """
    def __init__(self):
        self.path = os.path.join(os.path.dirname(__file__), '.stack')
        self.config = os.path.join(os.path.dirname(__file__),
                                   '.stack/stack.conf')

        self.pkey_name = "servicelab/utils/public_key.pkcs7.pem"

        # Setup Logging
        self.branch = "master"
        self.verbose = False
        self.vverbose = False
        self.debug = False
        self.logger = logging.getLogger('click_application')
        self.logger.setLevel(logging.DEBUG)

        # Create filehandler that logs everything.
        self.file_handler = logging.FileHandler(os.path.join(self.path,
                                                             'stack.log'))
        self.file_handler.setLevel(logging.DEBUG)

        # Create console handler that logs up to error msg.s.
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(logging.DEBUG)

        # Create formatter and add it to the handlers
        self.formatter = logging.Formatter("%(asctime)s - %(name)s - "
                                           "%(levelname)s - %(message)s")
        self.file_handler.setFormatter(self.formatter)
        self.console_handler.setFormatter(self.formatter)

        # Add handlers to the logger
        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(self.console_handler)
        self.__gerrit_test_info = {"hostname": "ccs-gerrit-stg.cisco.com", "port": 29418}
        self.__gerrit_info = {"hostname": "ccs-gerrit.cisco.com", "port": 29418}

    def get_gerrit_server(self):
        """
        get_gerrit_server get the gerrit server
        """
        return self.__gerrit_info

    def get_gerrit_staging_server(self):
        """
        get_gerrit_staging_server get the gerrit server
        """
        return self.__gerrit_test_info

    def reporoot_path(self):
        """
        reporoot_path gets path of the repo
        """
        path_to_reporoot = os.path.split(self.path)
        path_to_reporoot = os.path.split(path_to_reporoot[0])
        path_to_reporoot = path_to_reporoot[0]
        return path_to_reporoot

    def pkey_fname(self):
        """
        pkey_fname gets file name of the public key.
        """
        return os.path.join(self.reporoot_path(), self.pkey_name)


pass_context = click.make_pass_decorator(Context, ensure=True)


class ComplexCLI(click.MultiCommand):
    """
    ComplexCLI
    """
    def list_commands(self, ctx):
        """
        list_commands returns list of all the commands existing in the cmd_folder.
        """
        cmd_folder = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                  'commands'))
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
@click.option('--path', '-p',
              type=click.Path(exists=True,
                              file_okay=False,
                              resolve_path=True),
              help='Indicates your working servicelab folder.')
@click.option("--verbose", "-v",
              is_flag=True, default=False,
              help="Enables verbose mode.")
@click.option("--vverbose", "-vv",
              is_flag=True, default=False,
              help='Enables extra verbose mode.')
@click.option("--debug", '-vvv',
              is_flag=True, default=False,
              help='Enables debug mode.')
@click.option('--config', '-c',
              help="You can specify a config file for "
              "stack to pull information from.")
@pass_context
def cli(ctx, verbose, vverbose, debug, path, config):
    """A CLI for Cisco Cloud Services."""
    ctx.verbose = verbose
    ctx.vverbose = vverbose
    ctx.debug = debug
    ctx.console_handler.setLevel(logging.CRITICAL)

    if ctx.verbose:
        ctx.console_handler.setLevel(logging.ERROR)
    if ctx.vverbose:
        ctx.console_handler.setLevel(logging.WARNING)
    if ctx.debug:
        ctx.console_handler.setLevel(logging.DEBUG)
    if path is not None:
        ctx.path = path
    if config is not None:
        ctx.config = config
