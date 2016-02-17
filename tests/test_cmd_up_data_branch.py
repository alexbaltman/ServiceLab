"""
Tests status utils
"""
import os
import unittest
from subprocess import CalledProcessError

import click
from click.testing import CliRunner
from subprocess32 import call

from servicelab.utils import vagrant_utils
from servicelab.utils import service_utils
from servicelab.stack import Context
from servicelab.commands import cmd_status
from servicelab.commands import cmd_up


class TestCmdUpDataBranch(unittest.TestCase):

    """
    TestCmdUpDataBranch is a unittest class for testing ccs-data branch.
    Attributes:
        ctx:  Context object of servicelab module.
    """
    VM_STATUS = "Showing vm status of services"

    def setUp(self):
        """ Setup variables required to test the os_provider functions
        """
        self.ctx = Context()

    def test_cmd_vm_status(self):
        """ Tests VM status command.
        """
        runner = CliRunner()
        workon_cmd = "stack workon service-horizon"
        retcode, _ = service_utils.run_this(workon_cmd)
        if retcode != 0:
            cls.success_flag = False
            cls.message = "Unable to run stack workon service-horizon"
            return
        up_cmd = "stack up -s service-horizon"
        retcode, _ = service_utils.run_this(up_cmd)
        result = runner.invoke(cmd_status.cli, ['vm'])
        click.echo(result.output)
        self.assertTrue(TestCmdUpDataBranch.VM_STATUS in result.output)

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
