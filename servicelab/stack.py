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


class Logger(object):
    """
    Setup class context object to handle logging for all commands and utils

    Attributes
        verbose (boolean)
        vverbose (boolean)
        debug (boolean)
        logger (logger)

        file_handler       - Create filehandler that logs everything.
        formatter          - Create formatter and add it to the handlers

    """
    def __init__(self):
        self.path = os.path.join(os.path.dirname(__file__), '.stack')
        # Setup Logging
        self.branch = "master"
        self.verbose = False
        self.vverbose = False
        self.debug = False
        self.logger = logging.getLogger('stack')
        logging.addLevelName(15, 'DETAIL')

        # Create filehandler that logs everything.
        self.file_handler = logging.FileHandler(os.path.join(self.path,
                                                             'stack.log'))
        self.file_handler.setLevel(logging.DEBUG)

        # Create formatter and add it to the handlers
        self.formatter = logging.Formatter("%(asctime)s - %(name)s - "
                                           "%(levelname)s - %(message)s")
        self.file_handler.setFormatter(self.formatter)

        # Add handlers to the logger
        self.logger.addHandler(self.file_handler)


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

        __gerrit_test_info - Gerrit staging server
        __gerrit_info      - Gerrit server


    """
    from servicelab.utils import helper_utils

    def __init__(self):
        self.logger = Logger().logger
        self.path = os.path.join(os.path.dirname(__file__), '.stack')
        self.config = os.path.join(os.path.dirname(__file__),
                                   '.stack/stack.conf')

        self.pkey_name = "servicelab/utils/public_key.pkcs7.pem"

        self.__gerrit_test_info = {"hostname": "ccs-gerrit-stg.cisco.com",
                                   "port": 29418}
        self.__gerrit_info = {"hostname": "ccs-gerrit.cisco.com",
                              "port": 29418}
        self.__artifactory_info = \
            {"url": "https://ccs-artifactory.cisco.com/artifactory"}
        self.__gocd_info = \
            {"ip": "sdlc-go.cisco.com"}
        self.__jenkins_info = \
            {"url": "https://ccs-jenkins.cisco.com"}
        self.__pulp_info = \
            {"url": "https://ccs-mirror.cisco.com"}
        self.username = self.helper_utils.get_username(self.path)
        self.password = None

        # set the user name according to this defined hierarchy
        returncode, self.username = helper_utils.get_gitusername(self.path)
        if returncode > 0:
            helper_utils.get_loginusername()

        self.password = None
        if os.getenv("OS_USERNAME"):
            self.username = os.getenv("OS_USERNAME")
            self.password = os.getenv("OS_PASSWORD")

        if os.getenv("STK_USERNAME"):
            self.username = os.getenv("STK_USERNAME")
            self.password = os.getenv("STK_PASSWORD")

        if not self.username:
            self.logger.error('Unable to determine username')
            sys.exit(1)

    def get_gerrit_server(self):
        """
        get_gerrit_server get the gerrit server
        """
        return self.__gerrit_info

    def get_gocd_info(self):
        """
        get_gocd_info get the gocd server
        """
        return self.__gocd_info

    def get_jenkins_info(self):
        """
        get_jenkins_info get the gocd server
        """
        return self.__jenkins_info

    def get_gerrit_staging_server(self):
        """
        get_gerrit_staging_server get the gerrit server
        """
        return self.__gerrit_test_info

    def get_artifactory_info(self):
        """
        returns the artifactory info
        """
        return self.__artifactory_info

    def get_pulp_info(self):
        """
        returns the pulp info
        """
        return self.__pulp_info

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

    def get_username(self):
        """
        username
        """
        if not self.username:
            self.logger.error("servicelab: username is unavailable from git config,"
                              " os, or environments OS_USERNAME, STX_USERNAMRE. "
                              "Please set it through any of the given "
                              "mechanism and run the command again.")
            sys.exit(1)
        return self.username

    def get_password(self, interactive=False):
        """
        user password
        """
        if interactive and not self.password:
            self.password = click.prompt("password", hide_input=True, type=str)
        return self.password

pass_context = click.make_pass_decorator(Context, ensure=True)


class ComplexCLI(click.MultiCommand):
    """
    ComplexCLI
    """
    def list_commands(self, ctx):
        """
        list_commands returns list of all the commands existing
        in the cmd_folder.
        """
        cmd_folder = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                  'commands'))
        cmd = []
        for filename in os.listdir(cmd_folder):
            if filename.endswith('.py') and filename.startswith('cmd_'):
                cmd.append(filename[4:-3])
        cmd.sort()
        return cmd

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
@click.option('--username', '-u', help="user")
@click.option('--password', '-p', help="password")
@click.option('--verbose', '-v', count=True, help='Verbosity level, up to 3 for debug')
@pass_context
def cli(ctx, username, password, verbose):
    """A CLI for Cisco Cloud Services."""

    if username:
        ctx.username = username
    if password:
        ctx.password = password
    if verbose:
        if verbose == 1:
            ctx.verbose = True
            ctx.logger.setLevel(logging.INFO)
            verbosity = 'verbose (INFO)'
        elif verbose == 2:
            ctx.vverbose = True
            ctx.logger.setLevel(15)
            verbosity = 'very verbose (DETAIL)'
        elif verbose >= 3:
            ctx.debug = True
            ctx.logger.setLevel(logging.DEBUG)
            verbosity = 'debug (DEBUG)'
        click.echo('Verbosity set to %s\n' % verbosity)
