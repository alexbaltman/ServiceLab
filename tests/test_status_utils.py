"""
Tests status utils
"""
import os
import unittest
from subprocess import CalledProcessError

import click
from click.testing import CliRunner

from servicelab.utils import vagrant_utils
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
    SERVICE_PATH = "services/service-sdlc-pulp"
    NEW_FILE_PATH = "services/service-sdlc-pulp/somefile.txt"
    REPO_NOCHANGE = "servicelab/.stack/services/service-sdlc-pulp/master"
    REPO_COMMIT_CHANGE = "To Commit"
    REPO_INCOMING_CHANGE = "To Pull"
    REPO_OUTGOING_CHANGE = "To Review"
    VM_STATUS = "Showing vm status of services"

    def setUp(self):
        """ Setup variables required to test the os_provider functions
        """
        self.ctx = Context()
        if not self.success_flag:
            self.fail(self.message)

    @classmethod
    def setUpClass(cls):
        cls.success_flag = True
        set_git_cmd = "git config --global user.email"\
                      " \"ragkatti@cisco.com\"; "\
            "git config --global user.name \"Raghu Katti\";"
        check_git_cmd = "git config user.email"
        retcode, check_val = service_utils.run_this(check_git_cmd)

        if "@cisco.com" not in check_val:
            retcode, _ = service_utils.run_this(set_git_cmd)
            if retcode != 0:
                cls.success_flag = False
                cls.message = "Unable to run : git config user.email"
                return

        workon_cmd = "stack workon service-sdlc-pulp"
        retcode, _ = service_utils.run_this(workon_cmd)
        if retcode != 0:
            cls.success_flag = False
            cls.message = "Unable to run stack workon service-sdlc-pulp"
            return
        up_cmd = "stack up -s service-sdlc-pulp"
        retcode, _ = service_utils.run_this(up_cmd)

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
        revert_command = 'cd {}; git fetch origin master; git reset --hard \
                         origin/master'.format(service_path)

        retcode, _ = service_utils.run_this(revert_command)
        self.assertEqual(0, retcode,
                         "Unable to run revert command")

    def test_cmd_repo_status_incoming(self):
        """ Tests pipeline status command.
        """
        service_path = os.path.join(self.ctx.path,
                                    TestStatusUtils.SERVICE_PATH)
        reset_command = "cd {}; git reset `git log --format=\"%H\" -n 3 "\
                        " | tail -n 1`".format(service_path)
        retcode, _ = service_utils.run_this(reset_command)
        self.assertEqual(0, retcode,
                         "Unable to run reset command")

        runner = CliRunner()
        result = runner.invoke(cmd_status.cli,
                               ['repo'])
        self.assertTrue(TestStatusUtils.REPO_INCOMING_CHANGE in result.output)

    def test_cmd_vm_status(self):
        """ Tests VM status command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_status.cli,
                               ['vm'])
        self.assertTrue(TestStatusUtils.VM_STATUS in result.output)

    def test_cmd_all_status(self):
        """ Tests all status command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_status.cli,
                               ['all'])
        self.assertTrue(TestStatusUtils.REPO_NOCHANGE in result.output)
        self.assertTrue(TestStatusUtils.VM_STATUS in result.output)

    @classmethod
    def tearDownClass(cls):
        """
        Perform cleanup
        """
        click.echo('Cleaning up all the VMs :')
        ctx = Context()
        vm_connection = vagrant_utils.Connect_to_vagrant(vm_name="infra-001",
                                                         path=ctx.path)
        try:
            statuses = vm_connection.v.status()
            for status in statuses:
                vm_connection.v.destroy(status[0])
                click.echo("Destroyed VM name : {} ".format(status[0]))
        except CalledProcessError:
            click.echo("Could not perform VM cleanup. Exiting")


if __name__ == '__main__':
    unittest.main()
