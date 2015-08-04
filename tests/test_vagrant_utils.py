import os
import unittest
import getpass
from tests.helpers import temporary_dir
from servicelab.utils.vagrant_utils import Connect_to_vagrant
import vagrant


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
            self.vagrant_dir = temp_dir
            self.connect_to_vagrant = Connect_to_vagrant(
                TestVagrantUtils.VM_NAME, temp_dir)
            self.vagrantfile_dir = os.path.join(
                self.vagrant_dir, "services", "current_service")
            self.v = vagrant.Vagrant(
                root=self.vagrantfile_dir,
                quiet_stdout=False,
                quiet_stderr=False)

    def test_default_init(self):
        """ Tests initialization.
        """
        self.assertEquals(
            self.connect_to_vagrant.vmname,
            TestVagrantUtils.VM_NAME)
        self.assertEquals(self.connect_to_vagrant.path, self.vagrant_dir)
        self.assertEquals(
            self.connect_to_vagrant.provider,
            TestVagrantUtils.DEFAULT_PROVIDER)
        self.assertEquals(
            self.connect_to_vagrant.default_vbox,
            TestVagrantUtils.DEFAULT_VBOX)
        self.assertEquals(
            self.connect_to_vagrant.default_vbox_url,
            TestVagrantUtils.DEFAULT_VBOX_URL)

    def test_add_box(self):
        """ Tests adding box.
        """
        self.connect_to_vagrant.add_box()
        box_list = self.v.box_list()
        self.assertEquals(
            next(
                (image.name for image in box_list
                    if image.name == TestVagrantUtils.DEFAULT_VBOX),
                None),
            TestVagrantUtils.DEFAULT_VBOX)

    def test_create_Vagrantfile(self):
        """ Tests creation of Vagrantfile.
        """
        self.connect_to_vagrant.add_box()
        self.connect_to_vagrant.create_Vagrantfile(self.vagrant_dir)
        self.assertEquals(
            os.path.isfile(
                os.path.join(
                    self.vagrantfile_dir,
                    TestVagrantUtils.VAGRANT_FILE)),
            True)


if __name__ == '__main__':
    unittest.main()
