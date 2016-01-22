"""
    TestClass to test various go cd functions.
"""
import time

import unittest
import requests
from requests.auth import HTTPBasicAuth
from click.testing import CliRunner

from servicelab.commands import cmd_pipe
from servicelab.commands import cmd_list
from servicelab.commands import cmd_find
from servicelab.stack import Context
from servicelab.utils import context_utils
from servicelab.utils import gocd_utils


class TestGoCdUtils(unittest.TestCase):
    """
    TestGoCdUtils class is a unittest class for testing go cd commands.
    This sets up with a test pipeline.
    Attributes:
        ctx:  Context object of servicelab module.
    """

    GOCD_SERVER = "localhost:8153"
    GOCD_USER = "slab"
    GOCD_PASS = "badger"
    GOCD_ENV_GOCD = "{\"ENV_VAR_1\":\"Override_value\"}"
    GOCD_ENV_GOCD_OVERRIDE = "Override_value"
    GOCD_ENV_GOCD_INVALID = "{\"ENV_VAR_INVALID\":\"Value\"}"
    GOCD_ENV_INVALID_ERROR = "Variable 'ENV_VAR_INVALID' "\
                             "has not been configured for pipeline"
    GOCD_REMOTE_USER = "ragkatti"
    GOCD_REMOTE_PASS = "NEWjob2015"
    PIPELINE_NAME = "servicelab-test-only-pipeline"
    SHOW_PIPELINE_NAME = "deploy-sdu-test-tempest"
    T_SCHED = "{\"locked\":false,\"paused\":false,\"schedulable\":true}"
    F_SCHED = "{\"locked\":false,\"paused\":false,\"schedulable\":false}"
    REMOTE_STATUS = "{\"paused\":false,\"schedulable\":true,\"locked\":false}"
    ENDING_LOG = "End of job log for pipeline"
    ALL_STAGES_OUT = "Stage : secondStage  has Passed"

    def setUp(self):
        """ Setup variables required to test the os_provider functions
        """
        self.ctx = Context()
        url = "http://{}/go/tab/admin/" \
              "pipelines/{}.json".format(TestGoCdUtils.GOCD_SERVER,
                                         TestGoCdUtils.PIPELINE_NAME)
        payload = {
            'url': 'https://github.com/Silverpop/sample-helloworld-ant.git',
            'scm': 'git',
            'builder': 'ant',
            'buildfile': 'build.xml',
            'target': 'main'}
        res = requests.post(url,
                            auth=HTTPBasicAuth(TestGoCdUtils.GOCD_USER,
                                               TestGoCdUtils.GOCD_PASS),
                            data=payload)
        if res.status_code not in [200, 400]:
            self.fail("Unable to connect to the go server. "
                      "HTTP return code {}: {}".format(res.status_code,
                                                       res.text))

    def test_cmd_pipeline_status(self):
        """ Tests pipeline status command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_pipe.cli,
                               ['status',
                                TestGoCdUtils.PIPELINE_NAME,
                                '-u',
                                TestGoCdUtils.GOCD_USER,
                                '-p',
                                TestGoCdUtils.GOCD_PASS,
                                '-ip',
                                TestGoCdUtils.GOCD_SERVER])
        self.assertEqual(result.output.strip(), TestGoCdUtils.T_SCHED)

    def test_cmd_run(self):
        """ Tests run command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_pipe.cli,
                               ['run',
                                TestGoCdUtils.PIPELINE_NAME,
                                '-u',
                                TestGoCdUtils.GOCD_USER,
                                '-p',
                                TestGoCdUtils.GOCD_PASS,
                                '-ip',
                                TestGoCdUtils.GOCD_SERVER])
        time.sleep(2)
        result = runner.invoke(cmd_pipe.cli,
                               ['status',
                                TestGoCdUtils.PIPELINE_NAME,
                                '-u',
                                TestGoCdUtils.GOCD_USER,
                                '-p',
                                TestGoCdUtils.GOCD_PASS,
                                '-ip',
                                TestGoCdUtils.GOCD_SERVER])
        self.assertEqual(result.output.strip(), TestGoCdUtils.F_SCHED)
        time.sleep(25)
        result = runner.invoke(cmd_pipe.cli,
                               ['run',
                                TestGoCdUtils.PIPELINE_NAME,
                                '-u',
                                TestGoCdUtils.GOCD_USER,
                                '-p',
                                TestGoCdUtils.GOCD_PASS,
                                '-ip',
                                TestGoCdUtils.GOCD_SERVER,
                                '-e',
                                TestGoCdUtils.GOCD_ENV_GOCD])
        time.sleep(45)
        result = runner.invoke(cmd_pipe.cli,
                               ['log',
                                TestGoCdUtils.PIPELINE_NAME,
                                '-u',
                                TestGoCdUtils.GOCD_USER,
                                '-p',
                                TestGoCdUtils.GOCD_PASS,
                                '-ip',
                                TestGoCdUtils.GOCD_SERVER])
        self.assertTrue(TestGoCdUtils.GOCD_ENV_GOCD_OVERRIDE in
                        result.output.strip())
        time.sleep(45)
        result = runner.invoke(cmd_pipe.cli,
                               ['run',
                                TestGoCdUtils.PIPELINE_NAME,
                                '-u',
                                TestGoCdUtils.GOCD_USER,
                                '-p',
                                TestGoCdUtils.GOCD_PASS,
                                '-ip',
                                TestGoCdUtils.GOCD_SERVER,
                                '-e',
                                TestGoCdUtils.GOCD_ENV_GOCD_INVALID])
        self.assertTrue(TestGoCdUtils.GOCD_ENV_INVALID_ERROR in
                        result.output.strip())
        time.sleep(45)
        result = runner.invoke(cmd_pipe.cli,
                               ['run',
                                TestGoCdUtils.PIPELINE_NAME,
                                '-u',
                                TestGoCdUtils.GOCD_USER,
                                '-p',
                                TestGoCdUtils.GOCD_PASS,
                                '-ip',
                                TestGoCdUtils.GOCD_SERVER,
                                '--all-stages'])
        self.assertTrue(TestGoCdUtils.ALL_STAGES_OUT in
                        result.output.strip())

    def test_cmd_list(self):
        """ Tests pipeline list command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_list.cli,
                               ['pipes',
                                '-u',
                                TestGoCdUtils.GOCD_USER,
                                '-p',
                                TestGoCdUtils.GOCD_PASS,
                                '-ip',
                                TestGoCdUtils.GOCD_SERVER])
        self.assertTrue(TestGoCdUtils.PIPELINE_NAME in result.output.strip())

    def test_cmd_find(self):
        """ Tests find command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_find.cli,
                               ['pipe',
                                TestGoCdUtils.PIPELINE_NAME,
                                '-u',
                                TestGoCdUtils.GOCD_USER,
                                '-p',
                                TestGoCdUtils.GOCD_PASS,
                                '-ip',
                                TestGoCdUtils.GOCD_SERVER])
        self.assertTrue(TestGoCdUtils.PIPELINE_NAME in result.output.strip())

    def test_cmd_log(self):
        """ Tests log command.
        """
        runner = CliRunner()
        time.sleep(25)
        result = runner.invoke(cmd_pipe.cli,
                               ['log',
                                TestGoCdUtils.PIPELINE_NAME,
                                '-u',
                                TestGoCdUtils.GOCD_USER,
                                '-p',
                                TestGoCdUtils.GOCD_PASS,
                                '-ip',
                                TestGoCdUtils.GOCD_SERVER])
        time.sleep(25)
        self.assertTrue(TestGoCdUtils.ENDING_LOG in result.output.strip())

    def test_cmd_show(self):
        """ Tests show command.
        """

        result = gocd_utils.get_pipe_info(TestGoCdUtils.SHOW_PIPELINE_NAME,
                                          TestGoCdUtils.GOCD_REMOTE_USER,
                                          TestGoCdUtils.GOCD_REMOTE_PASS,
                                          context_utils.get_gocd_ip())
        self.assertTrue(TestGoCdUtils.REMOTE_STATUS in result)


if __name__ == '__main__':
    unittest.main()
