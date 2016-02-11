"""
stack
"""
import os
import sys
import click
import logging

from servicelab import settings

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

        __gerrit_test_info - Gerrit staging server
        __gerrit_info      - Gerrit server


    """
    from servicelab.utils import helper_utils

    def __init__(self):
        self.branch = "master"
        self.path = os.path.join(os.path.dirname(__file__), '.stack')
        self.config = os.path.join(os.path.dirname(__file__), '.stack/stack.conf')

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

def write_settings_file():
    settings_file = os.path.join(os.path.dirname(__file__), 'settings.py')
    myfile = open(settings_file, 'w')
    file_data = '# Global variables file\n\nverbosity = %i' % settings.verbosity
    myfile.write(file_data)
    myfile.close()


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
            settings.verbosity = 20
            message = 'verbose (INFO)'
        elif verbose == 2:
            settings.verbosity = 15
            message = 'very verbose (DETAIL)'
        elif verbose >= 3:
            settings.verbosity = 10
            message = 'debug (DEBUG)'
        click.echo('Verbosity set to %s\n' % message)
    else:
        settings.verbosity = 30
    write_settings_file()
    reload(settings)
