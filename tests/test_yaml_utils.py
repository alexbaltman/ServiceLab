import os
import unittest
import getpass
from tests.helpers import temporary_dir
from servicelab.utils import yaml_utils
from servicelab.utils import service_utils
import yaml
import shutil
import time


class TestYamlUtils(unittest.TestCase):
    """
    TestYamlUtils class is a unittest class for yaml_utils.
    Attributes:
        ctx:  Context object of servicelab module.
    """

    VALID_FILE = "Valid.yaml"
    VALID_FILE_PATH = "tests/Valid.yaml"
    INVALID_FILE = "Invalid.yaml"
    INVALID_FILE_PATH = "tests/Invalid.yaml"
    VAGRANT_YAML = "tests/vagrant.yaml"
    VAGRANT_YAML_FILE = "vagrant.yaml"
    VAGRANT_YAML_DIR = "./"
    HOSTNAME = "proxyinternal-001"
    NONEXISTING_HOSTNAME = "proxyinternal-000001"
    ADD_HOSTNAME = "new-host222"
    SITE_NAME = "ccs-dev-1"
    SITE_YAML_FILE = "environments/dev/hosts.d/infra-002.yaml"
    site_ips = [
        '10.202.43.138',
        '10.202.44.100',
        '10.202.165.147',
        '10.202.165.148',
        '64.102.6.247',
        '171.70.168.183',
        '173.36.131.10',
        '173.37.87.157',
        '192.168.100.0',
        '192.168.100.2',
        '192.168.100.4',
        '192.168.100.5',
        '192.168.100.6',
        '192.168.100.12',
        '192.168.100.13',
        '192.168.100.14',
        '192.168.100.20',
        '192.168.100.21',
        '192.168.100.22',
        '192.168.100.23',
        '192.168.100.30',
        '192.168.100.71',
        '192.168.100.72',
        '192.168.100.73',
        '192.168.100.111',
        '192.168.100.112',
        '192.168.100.121',
        '192.168.100.122',
        '192.168.100.131',
        '192.168.100.132',
        '192.168.100.141',
        '192.168.100.142',
        '192.168.100.151',
        '192.168.100.152',
        '192.168.100.161',
        '192.168.100.162',
        '192.168.100.171',
        '192.168.100.172',
        '192.168.100.181',
        '192.168.100.182',
        '192.168.200.4',
        '192.168.200.20',
        '255.255.255.0']
    yaml_ips = ['192.168.100.2']

    def test_validate_syntax(self):
        """ Tests syntax validation of yaml. Tests valid and invalid files.
        """
        self.assertEquals(
            yaml_utils.validate_syntax(
                TestYamlUtils.VALID_FILE_PATH), 0)
        self.assertEquals(
            yaml_utils.validate_syntax(
                TestYamlUtils.INVALID_FILE_PATH), 1)

    def test_host_exists_vagrantyaml(self):
        """ Tests syntax validation of yaml.
        """
        self.assertEquals(
            yaml_utils.host_exists_vagrantyaml(
                TestYamlUtils.HOSTNAME,
                os.path.join(TestYamlUtils.VAGRANT_YAML_DIR, "tests")),
            0)
        self.assertEquals(
            yaml_utils.host_exists_vagrantyaml(
                TestYamlUtils.NONEXISTING_HOSTNAME,
                TestYamlUtils.VAGRANT_YAML_DIR),
            1)

    def test_host_add_vagrantyaml(self):
        """ Tests adding host to vagrant yaml. Adds a host to vagrant
            file and checks for its presence.
        """
        with temporary_dir() as temp_dir:
            os.makedirs(os.path.join(temp_dir, "services"))
            service_utils._git_clone(
                os.path.join(temp_dir),
                "master",
                getpass.getuser(),
                "ccs-data")
            shutil.copy(TestYamlUtils.VAGRANT_YAML, temp_dir)
            self.assertEquals(
                yaml_utils.host_add_vagrantyaml(
                    temp_dir,
                    os.path.join(temp_dir, TestYamlUtils.VAGRANT_YAML_FILE),
                    TestYamlUtils.ADD_HOSTNAME,
                    TestYamlUtils.SITE_NAME),
                0)
            self.assertEquals(
                yaml_utils.host_exists_vagrantyaml(
                    TestYamlUtils.ADD_HOSTNAME,
                    temp_dir),
                0)

    def test_host_del_vagrantyaml(self):
        """ Tests deleting host to vagrant yaml.
            Adds a hosts, deletes a hosts, checks for absence of host
            in vagrantfile
        """
        with temporary_dir() as temp_dir:
            os.makedirs(os.path.join(temp_dir, "services"))
            service_utils._git_clone(
                os.path.join(temp_dir),
                "master",
                getpass.getuser(),
                "ccs-data")
            shutil.copy(TestYamlUtils.VAGRANT_YAML, temp_dir)
            self.assertEquals(
                yaml_utils.host_add_vagrantyaml(
                    temp_dir,
                    os.path.join(temp_dir, TestYamlUtils.VAGRANT_YAML_FILE),
                    TestYamlUtils.ADD_HOSTNAME,
                    TestYamlUtils.SITE_NAME),
                0)
            self.assertEquals(
                yaml_utils.host_del_vagrantyaml(
                    temp_dir,
                    TestYamlUtils.VAGRANT_YAML_FILE,
                    TestYamlUtils.ADD_HOSTNAME),
                0)
            self.assertEquals(
                yaml_utils.host_exists_vagrantyaml(
                    TestYamlUtils.ADD_HOSTNAME,
                    temp_dir),
                1)

    @unittest.skip('dictionary above does not match ccs-data\
                   im going to mkae this test more robust on\
                   my other computre.')
    def test_get_allips_forsite(self):
        """ Tests getting all ips for a site.
        """
        with temporary_dir() as temp_dir:
            os.makedirs(os.path.join(temp_dir, "services"))
            service_utils._git_clone(
                os.path.join(temp_dir),
                "master",
                getpass.getuser(),
                "ccs-data")
            print yaml_utils.get_allips_forsite(
                    temp_dir,
                    TestYamlUtils.SITE_NAME)
            print " .......", self.site_ips
            self.assertItemsEqual(
                yaml_utils.get_allips_forsite(
                    temp_dir,
                    TestYamlUtils.SITE_NAME),
                self.site_ips)

    def test_get_allips_foryaml(self):
        """ Tests getting all ips for yamls.
        """
        with temporary_dir() as temp_dir:
            os.makedirs(os.path.join(temp_dir, "services"))
            service_utils._git_clone(
                os.path.join(temp_dir),
                "master",
                getpass.getuser(),
                "ccs-data")
            full_path = os.path.join(temp_dir, "services", "ccs-data",
                                     "sites", TestYamlUtils.SITE_NAME)
            with open(os.path.join(full_path, TestYamlUtils.SITE_YAML_FILE),
                      'r') as f:
                doc = yaml.load(f)
                self.assertItemsEqual(
                    yaml_utils.get_allips_foryaml(doc), self.yaml_ips)


if __name__ == '__main__':
    unittest.main()
