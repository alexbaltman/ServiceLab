"""
TestClass to test various Jenkins functions, namely
    1. Pipeline status command.
    2. Build list command.
    3. Build find command.
    4. Log command.
"""
import unittest

from click.testing import CliRunner

from servicelab.utils import jenkins_utils

from servicelab.commands import cmd_list
from servicelab.commands import cmd_find
from servicelab.commands import cmd_build
from servicelab.stack import Context


class TestJenkinsUtils(unittest.TestCase):
    """
    TestJenkinsUtils class is a unittest class for testing jenkins commands.
    Attributes:
        ctx:  Context object of servicelab module.
    """
    JENKINS_SERVER = "https://ccs-jenkins.cisco.com"
    JENKINS_USER = "ragkatti"
    JENKINS_PASS = "NEWjob2015"
    JOB_NAME = "check-servicelab"
    BUILD_STATUS = "check-servicelab"
    RUN_STATUS = "Retriggering last build"

    def setUp(self):
        """
        Setup variables required to test the os_provider functions
        """
        self.ctx = Context()

    def test_cmd_build_status(self):
        """
        Tests pipeline status command.
        """
        status = jenkins_utils.get_build_status(TestJenkinsUtils.JOB_NAME,
                                                TestJenkinsUtils.JENKINS_USER,
                                                TestJenkinsUtils.JENKINS_PASS,
                                                TestJenkinsUtils.JENKINS_SERVER)
        self.assertTrue(TestJenkinsUtils.BUILD_STATUS in status)

    def test_cmd_build_list(self):
        """
        Tests build list command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_list.cli,
                               ['builds',
                                '-u',
                                TestJenkinsUtils.JENKINS_USER,
                                '-p',
                                TestJenkinsUtils.JENKINS_PASS,
                                '-ip',
                                TestJenkinsUtils.JENKINS_SERVER])
        print(result.output)
        self.assertTrue(TestJenkinsUtils.JOB_NAME in result.output.strip())

    def test_build_find(self):
        """
        Tests build find command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_find.cli,
                               ['build',
                                TestJenkinsUtils.JOB_NAME,
                                '-u',
                                TestJenkinsUtils.JENKINS_USER,
                                '-p',
                                TestJenkinsUtils.JENKINS_PASS,
                                '-ip',
                                TestJenkinsUtils.JENKINS_SERVER])
        self.assertTrue(TestJenkinsUtils.JOB_NAME in result.output.strip())

    def test_build_log(self):
        """
        Tests log command.
        """
        log = jenkins_utils.get_build_log(TestJenkinsUtils.JOB_NAME,
                                          TestJenkinsUtils.JENKINS_USER,
                                          TestJenkinsUtils.JENKINS_PASS,
                                          TestJenkinsUtils.JENKINS_SERVER)
        self.assertTrue(jenkins_utils.END_LOG in log)

    def test_cmd_build_run(self):
        """
        Tests pipeline status command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_build.cli,
                               ['run',
                                TestJenkinsUtils.JOB_NAME,
                                '-u',
                                TestJenkinsUtils.JENKINS_USER,
                                '-p',
                                TestJenkinsUtils.JENKINS_PASS,
                                '-ip',
                                TestJenkinsUtils.JENKINS_SERVER])
        self.assertTrue(TestJenkinsUtils.RUN_STATUS in result.output.strip())

if __name__ == '__main__':
    unittest.main()
