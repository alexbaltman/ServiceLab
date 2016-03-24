"""
Tests vagrant utils
"""
import os
import unittest
import vagrant

from tests.helpers import temporary_dir
from servicelab.utils.vagrant_utils import Connect_to_vagrant


class TestVagrantUtils(unittest.TestCase):
    """
        TestVagrantUtils class is a unittest class for vagrant_utils.
        Tests default initialization values, adding boxes,
        creation of Vagrantfile.
        Attributes:
            VM_NAME : VM name
            DEFAULT_PROVIDER : default provider
            DEFAULT_VBOX : default vbox
            DEFAULT_VBOX_URL : vbox url
            VAGRANT_FILE : Vagrantfile
    """
    VM_NAME = "VagrantTestVM1"
    DEFAULT_PROVIDER = "virtualbox"
    DEFAULT_VBOX = "Cisco/rhel-7"
    DEFAULT_VBOX_URL = "http://cis-kickstart.cisco.com/ccs-rhel-7.box"
    VAGRANT_FILE = "Vagrantfile"

    def setUp(self):
        with temporary_dir() as temp_dir:
            os.mkdir(os.path.join(temp_dir, "services"))
            self.vagrant_dir = temp_dir
            self.connect_to_vagrant = Connect_to_vagrant(
                TestVagrantUtils.VM_NAME, os.path.join(self.vagrant_dir, "services"))
            self.vagrantfile_dir = self.vagrant_dir
            self.vagrantfileservices_dir = os.path.join(
                self.vagrant_dir, "services")
            self.v = vagrant.Vagrant(
                root=self.vagrantfileservices_dir,
                quiet_stdout=False,
                quiet_stderr=False)

    def test_default_init(self):
        """ Tests initialization.
        """
        self.assertEquals(
            self.connect_to_vagrant.vm_name,
            TestVagrantUtils.VM_NAME)
        self.assertEquals(self.connect_to_vagrant.path, self.vagrantfileservices_dir)
        self.assertEquals(
            self.connect_to_vagrant.provider,
            TestVagrantUtils.DEFAULT_PROVIDER)
        self.assertEquals(
            self.connect_to_vagrant.default_vbox,
            TestVagrantUtils.DEFAULT_VBOX)
        self.assertEquals(
            self.connect_to_vagrant.default_vbox_url,
            TestVagrantUtils.DEFAULT_VBOX_URL)

if __name__ == '__main__':
    unittest.main()
