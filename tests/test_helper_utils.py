import os
import unittest
import getpass
from servicelab.utils import helper_utils
from tests.helpers import temporary_dir


class TestHelperUtils(unittest.TestCase):
    """
        TestHelperUtils class is a unittest class for helper_utils.
        Tests empty and non-empty directories with hierarchy for
        recursive finding of yaml files.
        Attributes:
            YAML_FILE1_DIR
            YAML_FILE1
            YAML_FILE2_DIR
            YAML_FILE2
            YAML_FILE3_DIR
            YAML_FILE3
            YAML_EMPTY_DIR
            YAML_EMPTY_SUBDIR
            DOTSTACK_PATH
            GIT_EMPTY_DIR
            GIT_CONFIG_FILE
            GIT_USERNAME
    """

    YAML_FILE1_DIR = "dir1/subdir1/"
    YAML_FILE1 = "test1.yaml"
    YAML_FILE2_DIR = "dir1/subdir2"
    YAML_FILE2 = "test2.yaml"
    YAML_FILE3_DIR = "dir2/"
    YAML_FILE3 = "test3.yaml"
    YAML_EMPTY_DIR = "emptydir/"
    YAML_EMPTY_SUBDIR = "emptydir/subdir1"
    DOTSTACK_PATH = "servicelab/servicelab/.stack"
    GIT_EMPTY_DIR = "servicelab/.git/"
    GIT_CONFIG_FILE = "config"
    GIT_USERNAME = "aaltman"

    def test_find_all_yaml_recurs(self):
        """ Tests for empty and non-empty yaml directories.
            checks for return code.
        """
        with temporary_dir() as temp_dir:
            os.makedirs(os.path.join(temp_dir, TestHelperUtils.YAML_FILE1_DIR))
            os.makedirs(os.path.join(temp_dir, TestHelperUtils.YAML_FILE2_DIR))
            os.makedirs(os.path.join(temp_dir, TestHelperUtils.YAML_FILE3_DIR))
            os.makedirs(
                os.path.join(
                    temp_dir,
                    TestHelperUtils.YAML_EMPTY_SUBDIR))
            yaml_file_1 = open(
                os.path.join(
                    temp_dir,
                    TestHelperUtils.YAML_FILE1_DIR,
                    TestHelperUtils.YAML_FILE1),
                "w")
            yaml_file_2 = open(
                os.path.join(
                    temp_dir,
                    TestHelperUtils.YAML_FILE2_DIR,
                    TestHelperUtils.YAML_FILE2),
                "w")
            yaml_file_3 = open(
                os.path.join(
                    temp_dir,
                    TestHelperUtils.YAML_FILE3_DIR,
                    TestHelperUtils.YAML_FILE3),
                "w")

            returncode, yaml_dirs = helper_utils.find_all_yaml_recurs(temp_dir)
            self.assertItemsEqual(
                [yaml_file_1.name, yaml_file_2.name, yaml_file_3.name],
                yaml_dirs)

            returncode, yaml_dirs = helper_utils.find_all_yaml_recurs(
                temp_dir + TestHelperUtils.YAML_EMPTY_DIR)
            self.assertItemsEqual(yaml_dirs, [])

    def test_set_user(self):
        """Test that a user is being grabbed from the .git/config file."""

        with temporary_dir() as temp_dir:
            os.makedirs(os.path.join(temp_dir, TestHelperUtils.DOTSTACK_PATH))
            os.makedirs(os.path.join(temp_dir, TestHelperUtils.GIT_EMPTY_DIR))

            content = ("[remote \"origin\"]\n"
                       "        url = ssh://{0}@ccs-gerrit.cisco.com:"
                       "29418/servicelab\n"
                       "        fetch = +refs/heads/*:refs/remotes/origin/*\n"
                       "[remote \"gerrit\"]\n"
                       "        url = ssh://{0}@cis-gerrit.cisco.com:29418/servicelab\n"
                       "        fetch = +refs/heads/*:refs/remotes/gerrit/*\n"
                       "[submodule \"servicelab/.stack/services/ccs-data\"]\n"
                       "        url = ssh://{0}@ccs-gerrit.cisco.com:29418/ccs-data\n"
                       "".format(TestHelperUtils.GIT_USERNAME))

            with open(os.path.join(temp_dir, TestHelperUtils.GIT_EMPTY_DIR,
                                   TestHelperUtils.GIT_CONFIG_FILE), 'w') as f:
                f.write(content)

            returncode, username = helper_utils.get_gitusername(
                                    os.path.join(temp_dir,
                                                 TestHelperUtils.DOTSTACK_PATH))

        self.assertEqual(returncode, 0)
        self.assertEqual(username, TestHelperUtils.GIT_USERNAME)
        self.assertNotEqual(username, None)

if __name__ == '__main__':
    unittest.main()
