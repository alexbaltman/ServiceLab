import os
import filecmp
import unittest
import getpass
from tests.helpers import temporary_dir
from servicelab.utils import Vagrantfile_utils
from servicelab.utils import service_utils
import yaml
import shutil
import time
from string import Template


class TestVagrantFileUtils(unittest.TestCase):
    """
    TestVagrantFileUtils class is a unittest class for vagrantfile_utils.
    Attributes:

    """

    VAGRANTFILE = "Vagrantfile"
    VAGRANT_YAML_FILE = "tests/vagrant.yaml"
    CURRENT_FILE = "tests/current_test"
    VAGRANTFILE_COMPARISON = "tests/Vagrantfile_Comparison"
    VAGRANTFILE_COMPARISON_FILE = "Vagrantfile_Comparison"
    ENV_YAML_STRING = "$envyaml = YAML::load_file('{}/vagrant.yaml')"
    RUBY_MODULES_YAML = "servicelab/.stack/provision/ruby_modules.yaml"
    VAGRANT_PLUGINS_YAML = "servicelab/utils/vagrant_plugins.yaml"

    def test_load_vagrantyaml(self):
        """ Tests creation of loading code for vagrant yaml.
        """
        with temporary_dir() as temp_dir:
            shutil.copy(TestVagrantFileUtils.VAGRANT_YAML_FILE, temp_dir)
            s = Vagrantfile_utils._load_vagrantyaml(temp_dir)
            self.assertEquals(
                Vagrantfile_utils._load_vagrantyaml(temp_dir),
                TestVagrantFileUtils.ENV_YAML_STRING.format(temp_dir))

    def test_overwrite_vagrantfile(self):
        """ Tests overwriting of vagrant yaml.
        """
        with temporary_dir() as temp_dir:
            os.makedirs(os.path.join(temp_dir, "utils"))
            shutil.copy(
                TestVagrantFileUtils.RUBY_MODULES_YAML,
                os.path.join(
                    temp_dir,
                    "utils"))
            shutil.copy(
                TestVagrantFileUtils.VAGRANT_PLUGINS_YAML,
                os.path.join(
                    temp_dir,
                    "utils"))
            shutil.copy(
                TestVagrantFileUtils.CURRENT_FILE,
                os.path.join(
                    temp_dir,
                    "current"))
            shutil.copy(TestVagrantFileUtils.VAGRANTFILE_COMPARISON, temp_dir)
            filein = open(
                os.path.join(
                    temp_dir,
                    TestVagrantFileUtils.VAGRANTFILE_COMPARISON_FILE))
            src = filein.read()
            replaced_contents = src.replace('temp_dir', temp_dir)
            fileout = open(
                os.path.join(
                    temp_dir,
                    TestVagrantFileUtils.VAGRANTFILE_COMPARISON_FILE),
                'w')
            fileout.write(replaced_contents)
            fileout.close()

            Vagrantfile_utils.overwrite_vagrantfile(temp_dir)
            print temp_dir
            self.assertEquals(
                filecmp.cmp(
                    os.path.join(
                        temp_dir,
                        TestVagrantFileUtils.VAGRANTFILE_COMPARISON_FILE),
                    os.path.join(
                        temp_dir,
                        TestVagrantFileUtils.VAGRANTFILE)),
                True)


if __name__ == '__main__':
    unittest.main()
