import os
import unittest
import getpass
from tests.helpers import temporary_dir
from servicelab.utils import gocd_utils
from servicelab.commands import cmd_pipe
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


class TestGoCdUtils(unittest.TestCase):

    GOCD_SERVER = "localhost:8153"
    GOCD_USER = "raju"
    GOCD_PASS = "badger"
    PIPELINE_NAME = "servicelab-test-only-pipeline"
    T_SCHED = "{\"locked\":false,\"paused\":false,\"schedulable\":true}"
    F_SCHED = "{\"locked\":false,\"paused\":false,\"schedulable\":false}"
    ENDING_LOG = "-------------------End of job log for pipeline"

    """
    TestGoCdUtils class is a unittest class for testing go cd commands.
    This sets up with a test pipeline.
    Attributes:
        ctx:  Context object of servicelab module.
    """

    def setUp(self):
        """ Setup variables required to test the os_provider functions
        """
        self.ctx = Context()
        url = "http://{0}/go/tab/admin/pipelines/{1}.json".format(
            TestGoCdUtils.GOCD_SERVER, TestGoCdUtils.PIPELINE_NAME)
        payload = {
            'url': 'https://github.com/Silverpop/sample-helloworld-ant.git',
            'scm': 'git',
            'builder': 'ant',
            'buildfile': 'build.xml',
            'target': 'main'}
        res = requests.post(
            url,
            auth=HTTPBasicAuth(
                TestGoCdUtils.GOCD_USER,
                TestGoCdUtils.GOCD_PASS),
            data=payload)

    def test_cmd_pipeline_status(self):
        """ Tests pipeline status command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_pipe.cli,
                               ['status',
                                TestGoCdUtils.PIPELINE_NAME,
                                '-g',
                                TestGoCdUtils.GOCD_USER,
                                '-h',
                                TestGoCdUtils.GOCD_PASS,
                                '-s',
                                TestGoCdUtils.GOCD_SERVER])
        self.assertItemsEqual(
            result.output.strip(),
            TestGoCdUtils.T_SCHED)

    def test_cmd_run(self):
        """ Tests run command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_pipe.cli,
                               ['run',
                                TestGoCdUtils.PIPELINE_NAME,
                                '-g',
                                TestGoCdUtils.GOCD_USER,
                                '-h',
                                TestGoCdUtils.GOCD_PASS,
                                '-s',
                                TestGoCdUtils.GOCD_SERVER])
        result = runner.invoke(cmd_pipe.cli,
                               ['status',
                                TestGoCdUtils.PIPELINE_NAME,
                                '-g',
                                TestGoCdUtils.GOCD_USER,
                                '-h',
                                TestGoCdUtils.GOCD_PASS,
                                '-s',
                                TestGoCdUtils.GOCD_SERVER])
        self.assertItemsEqual(
            result.output.strip(),
            TestGoCdUtils.F_SCHED)

    def test_cmd_list(self):
        """ Tests pipeline list command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_list.cli,
                               ['pipes',
                                '-g',
                                TestGoCdUtils.GOCD_USER,
                                '-h',
                                TestGoCdUtils.GOCD_PASS,
                                '-s',
                                TestGoCdUtils.GOCD_SERVER])
        self.assertTrue(TestGoCdUtils.PIPELINE_NAME in result.output.strip())

    def test_cmd_find(self):
        """ Tests find command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_find.cli,
                               ['pipe',
                                TestGoCdUtils.PIPELINE_NAME,
                                '-g',
                                TestGoCdUtils.GOCD_USER,
                                '-h',
                                TestGoCdUtils.GOCD_PASS,
                                '-s',
                                TestGoCdUtils.GOCD_SERVER])
        self.assertItemsEqual(
            result.output.strip(),
            TestGoCdUtils.PIPELINE_NAME)

    def test_cmd_log(self):
        """ Tests log command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_pipe.cli,
                               ['log',
                                TestGoCdUtils.PIPELINE_NAME,
                                '-g',
                                TestGoCdUtils.GOCD_USER,
                                '-h',
                                TestGoCdUtils.GOCD_PASS,
                                '-s',
                                TestGoCdUtils.GOCD_SERVER])
        self.assertTrue(TestGoCdUtils.ENDING_LOG in result.output.strip())


if __name__ == '__main__':
    unittest.main()
