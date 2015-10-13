"""
Tests status utils
"""
import os
import unittest

from click.testing import CliRunner

from servicelab.utils import service_utils
from servicelab.stack import Context
from servicelab.commands import cmd_status


class TestStatusUtils(unittest.TestCase):

    """
    TestStatusUtils class is a unittest class for testing go cd commands.
    This sets up with a test pipeline.
    Attributes:
        ctx:  Context object of servicelab module.
    """
    REPO_STATUS = "Showing repo status of services"
    SERVICE_PATH = "services/service-sdlc-pulp"
    NEW_FILE_PATH = "services/service-sdlc-pulp/somefile.txt"
    REPO_NOCHANGE = "servicelab/.stack/services/service-sdlc-pulp/master"
    REPO_COMMIT_CHANGE = "To Commit"
    REPO_INCOMING_CHANGE = "To Pull"
    REPO_OUTGOING_CHANGE = "To Review"
    VM_STATUS = "Showing VM status of services"
    SHA_COMMIT = "2e957178ab4176b5d55c1edfbda3ae20503d1eae"

    def setUp(self):
        """ Setup variables required to test the os_provider functions
        """
        self.ctx = Context()
        cmd = "git config --global user.email \"ragkatti@cisco.com\"; "\
              "git config --global user.name \"Raghu Katti\";stack "\
              "workon service-sdlc-pulp"
        retcode, _ = service_utils.run_this(cmd)
        self.assertEqual(0, retcode,
                         "Unable to run stack workon service-sdlc-pulp")

    def test_cmd_repo_status_nochange(self):
        """ Tests pipeline status command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_status.cli,
                               ['repo'])
        self.assertTrue(TestStatusUtils.REPO_NOCHANGE in result.output)

    def test_cmd_repo_status_change(self):
        """ Tests pipeline status command.
        """
        file_path = os.path.join(self.ctx.path, TestStatusUtils.NEW_FILE_PATH)
        with open(file_path, 'w') as test_file:
            test_file.write('Hello\n')
        runner = CliRunner()
        result = runner.invoke(cmd_status.cli,
                               ['repo'])
        self.assertTrue(TestStatusUtils.REPO_COMMIT_CHANGE in result.output)

        service_path = os.path.join(self.ctx.path,
                                    TestStatusUtils.SERVICE_PATH)
        commit_command = 'cd {}; git add somefile.txt; \
                         git commit -m "testing" \
                         somefile.txt'.format(service_path)
        retcode, _ = service_utils.run_this(commit_command)
        self.assertEqual(0, retcode,
                         "Unable to run commit command")

        result = runner.invoke(cmd_status.cli,
                               ['repo'])
        self.assertTrue(TestStatusUtils.REPO_OUTGOING_CHANGE in result.output)

    def test_cmd_repo_status_incoming(self):
        """ Tests pipeline status command.
        """
        service_path = os.path.join(self.ctx.path,
                                    TestStatusUtils.SERVICE_PATH)
        reset_command = 'cd {}; git reset {}'.\
            format(service_path, TestStatusUtils.SHA_COMMIT)
        retcode, _ = service_utils.run_this(reset_command)
        self.assertEqual(0, retcode,
                         "Unable to run reset command")

        runner = CliRunner()
        result = runner.invoke(cmd_status.cli,
                               ['repo'])
        self.assertTrue(TestStatusUtils.REPO_INCOMING_CHANGE in result.output)
        revert_command = 'cd {}; git fetch origin master; git reset --hard \
                         origin/master'.format(service_path)

        retcode, _ = service_utils.run_this(revert_command)
        self.assertEqual(0, retcode,
                         "Unable to run revert command")


if __name__ == '__main__':
    unittest.main()
