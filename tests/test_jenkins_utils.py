import os
import unittest
import getpass
from tests.helpers import temporary_dir
from servicelab.utils import jenkins_utils
from servicelab.commands import cmd_build
from servicelab.commands import cmd_list
from servicelab.commands import cmd_find
import yaml
import shutil
import time
import requests
from requests.auth import HTTPBasicAuth
from BeautifulSoup import BeautifulSoup
from servicelab.stack import Context
from click.testing import CliRunner


class TestJenkinsUtils(unittest.TestCase):

    JENKINS_SERVER = "https://ccs-jenkins.cisco.com"
    JENKINS_USER = "ragkatti"
    JENKINS_PASS = "NEWjob2015"
    JOB_NAME = "check-servicelab"
    BUILD_STATUS = "check-servicelab"
    ENDING_LOG = "-------------------End of job log for build"

    """
    TestJenkinsUtils class is a unittest class for testing jenkins commands.
    Attributes:
        ctx:  Context object of servicelab module.
    """
    def setUp(self):
        """ Setup variables required to test the os_provider functions
        """
        self.ctx = Context()

    def test_cmd_build_status(self):
        """ Tests pipeline status command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_build.cli,
                               ['status',
                                TestJenkinsUtils.JOB_NAME,
                                '-x',
                                TestJenkinsUtils.JENKINS_USER,
                                '-y',
                                TestJenkinsUtils.JENKINS_PASS,
                                '-z',
                                TestJenkinsUtils.JENKINS_SERVER])
        print result.output
        self.assertTrue(
            TestJenkinsUtils.BUILD_STATUS in result.output.strip())

    def test_cmd_build_list(self):
        """ Tests build list command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_list.cli,
                               ['builds',
                                '-x',
                                TestJenkinsUtils.JENKINS_USER,
                                '-y',
                                TestJenkinsUtils.JENKINS_PASS,
                                '-z',
                                TestJenkinsUtils.JENKINS_SERVER])
        self.assertTrue(TestJenkinsUtils.JOB_NAME in result.output.strip())

    def test_build_find(self):
        """ Tests build find command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_find.cli,
                               ['build',
                                TestJenkinsUtils.JOB_NAME,
                                '-x',
                                TestJenkinsUtils.JENKINS_USER,
                                '-y',
                                TestJenkinsUtils.JENKINS_PASS,
                                '-z',
                                TestJenkinsUtils.JENKINS_SERVER])
        self.assertItemsEqual(
            result.output.strip(),
            TestJenkinsUtils.JOB_NAME)

    def test_build_log(self):
        """ Tests log command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_build.cli,
                               ['log',
                                TestJenkinsUtils.JOB_NAME,
                                '-x',
                                TestJenkinsUtils.JENKINS_USER,
                                '-y',
                                TestJenkinsUtils.JENKINS_PASS,
                                '-z',
                                TestJenkinsUtils.JENKINS_SERVER])
        self.assertTrue(TestJenkinsUtils.ENDING_LOG in result.output.strip())


if __name__ == '__main__':
    unittest.main()
