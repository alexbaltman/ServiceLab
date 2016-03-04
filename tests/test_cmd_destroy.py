"""
Tests status utils
"""
import unittest
import sys

from click.testing import CliRunner

from servicelab.utils import service_utils
from servicelab.stack import Context
from servicelab.commands import cmd_destroy


class TestCmdDestroy(unittest.TestCase):

    """
    TestCmdDestroy class is a unittest class for testing stack destroy commands.
    This sets up with a test pipeline.
    Attributes:
        ctx:  Context object of servicelab module.
    """

    def setUp(self):
        """ Setup variables required to test the os_provider functions
        """
        self.ctx = Context()

    @classmethod
    @unittest.skipUnless(sys.platform == "darwin",
                         "Mac only stack up -s is not working in jenkins")
    def setUpClass(cls):
        set_git_cmd = "git config --global user.email"\
                      " \"ragkatti@cisco.com\"; "\
            "git config --global user.name \"Raghu Katti\";"
        check_git_cmd = "git config user.email"
        retcode, check_val = service_utils.run_this(check_git_cmd)

        if "@cisco.com" not in check_val:
            ret_code, _ = service_utils.run_this(set_git_cmd)
            assert ret_code == 0, "Unable to run : git config user.email"

        workon_cmd = "stack workon service-horizon"
        ret_code, _ = service_utils.run_this(workon_cmd)
        assert ret_code == 0, "Unable to run stack workon service-horizon"

        up_cmd = "stack up -s service-horizon"
        retcode, _ = service_utils.run_this(up_cmd)
        assert ret_code == 0, "Unable to run stack up -s service-horizon"

    @unittest.skipUnless(sys.platform == "darwin",
                         "Mac only stack up -s is not working in jenkins")
    def test_cmd_destroy(self):
        """ Tests stack destroy vm.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_destroy.cli,
                               ['vm',
                                'service-horizon-001'])
        self.assertTrue(cmd_destroy.VAGRANTFILE_DELETE_MESSAGE in result.output.strip())
        self.assertTrue(cmd_destroy.INVENTORY_DELETE_MESSAGE in result.output.strip())
        self.assertTrue(cmd_destroy.REBUILDING_CCSDATA_MESSAGE in result.output.strip())
        self.assertTrue(cmd_destroy.INFRA_PORT_DETECT_MESSAGE in result.output.strip())
        self.assertTrue(cmd_destroy.UPDATING_HOSTS_YAML_MESSAGE in result.output.strip())


if __name__ == '__main__':
    unittest.main()
