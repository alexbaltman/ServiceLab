"""
    TestClass to test various go cd functions.
"""
import unittest
import sys

from click.testing import CliRunner

from servicelab.commands import cmd_list
from servicelab.commands import cmd_rpm
from servicelab.commands import cmd_find
from servicelab.stack import Context


class TestPulpUtils(unittest.TestCase):
    """
    TestPulpUtils class is a unittest class for testing pulp rpm commands.
    Attributes:
        ctx:  Context object of servicelab module.
    """

    PULP_USER = "admin"
    PULP_PASS = "admin"
    PULP_IP = "https://localhost:4430"
    PULP_UPLOAD_OUT = "Upload process completed for rpm"
    PULP_DOWNLOAD_OUT = "epel-release-7-5.noarch.rpm"
    PULP_STATS_OUT = '"name": "epel-release"'
    PULP_REPO_OUT = 'Repo Name    : CentOS-7-x86_64'
    PULP_RPM_OUT = 'Name    : epel-release'
    PULP_REPO_REGEX = 'CentOS-7-x86_6*'

    def setUp(self):
        """ Setup variables required to test the os_provider functions
        """
        self.ctx = Context()

    @unittest.skipUnless(sys.platform == "darwin",
                         "test only relevant on MacOSX")
    def test_cmd_upload(self):
        """ Tests pulp rpm upload command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_rpm.cli,
                               ['upload',
                                '-u',
                                TestPulpUtils.PULP_USER,
                                '-p',
                                TestPulpUtils.PULP_PASS,
                                '-ip',
                                TestPulpUtils.PULP_IP,
                                '-f',
                                '/tmp/epel-release-latest-7.noarch.rpm',
                                '-s',
                                'CentOS-7-x86_64'
                                ]
                               )
        self.assertTrue(TestPulpUtils.PULP_UPLOAD_OUT in result.output.strip())

    @unittest.skipUnless(sys.platform == "darwin",
                         "test only relevant on MacOSX")
    def test_cmd_download(self):
        """ Tests pulp rpm download command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_rpm.cli,
                               ['download',
                                '-u',
                                TestPulpUtils.PULP_USER,
                                '-p',
                                TestPulpUtils.PULP_PASS,
                                '-ip',
                                TestPulpUtils.PULP_IP,
                                '-s',
                                'CentOS-7-x86_64',
                                'epel-release'
                                ]
                               )
        self.assertTrue(
            TestPulpUtils.PULP_DOWNLOAD_OUT in result.output.strip())

    @unittest.skipUnless(
        sys.platform == "darwin",
        "test only relevant on MacOSX")
    def test_cmd_stats(self):
        """ Tests pulp rpm stats command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_rpm.cli,
                               ['stats',
                                '-u',
                                TestPulpUtils.PULP_USER,
                                '-p',
                                TestPulpUtils.PULP_PASS,
                                '-ip',
                                TestPulpUtils.PULP_IP,
                                '-s',
                                'CentOS-7-x86_64',
                                'epel-release'
                                ]
                               )
        self.assertTrue(TestPulpUtils.PULP_STATS_OUT in result.output.strip())

    @unittest.skipUnless(
        sys.platform == "darwin",
        "test only relevant on MacOSX")
    def test_cmd_list_rpms(self):
        """ Tests pulp rpm list command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_list.cli,
                               ['rpms',
                                '-u',
                                TestPulpUtils.PULP_USER,
                                '-p',
                                TestPulpUtils.PULP_PASS,
                                '-ip',
                                TestPulpUtils.PULP_IP,
                                '-s',
                                'CentOS-7-x86_64'
                                ]
                               )
        self.assertTrue(TestPulpUtils.PULP_RPM_OUT in result.output.strip())

    @unittest.skipUnless(
        sys.platform == "darwin",
        "test only relevant on MacOSX")
    def test_cmd_list_repos(self):
        """ Tests pulp repos list command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_list.cli,
                               ['pulp-repos',
                                '-u',
                                TestPulpUtils.PULP_USER,
                                '-p',
                                TestPulpUtils.PULP_PASS,
                                '-ip',
                                TestPulpUtils.PULP_IP,
                                ]
                               )
        self.assertTrue(TestPulpUtils.PULP_REPO_OUT in result.output.strip())

    @unittest.skipUnless(
        sys.platform == "darwin",
        "test only relevant on MacOSX")
    def test_cmd_find_repos(self):
        """ Tests pulp repos find command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_find.cli,
                               ['pulp-repos',
                                '-u',
                                TestPulpUtils.PULP_USER,
                                '-p',
                                TestPulpUtils.PULP_PASS,
                                '-ip',
                                TestPulpUtils.PULP_IP,
                                TestPulpUtils.PULP_REPO_REGEX
                                ]
                               )
        self.assertTrue(TestPulpUtils.PULP_REPO_OUT in result.output.strip())

if __name__ == '__main__':
    unittest.main()
