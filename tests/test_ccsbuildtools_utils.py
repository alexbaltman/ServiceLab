import os
import yaml
import shutil
import getpass
import unittest
from servicelab.stack import Context
from servicelab.utils import ccsbuildtools_utils
from servicelab.utils import service_utils
from servicelab.utils import helper_utils


def _compare_dicts(dict1, dict2):
    """Compares two dictionaries to see if all keys of all
    dictionaries (nested or not) match. Recursive fxn.
    Returns:
         returncode -- 0 (success) or 1 (failure)
    """
    if set(dict1.keys()) != set(dict2.keys()):
        return 1
    for i in dict1:
        if isinstance(dict1[i], dict) and isinstance(dict2[i], dict):
            return _compare_dicts(dict1[i], dict2[i])
    return 0


class TestCCsBuildToolsUtils(unittest.TestCase):
    """
    TestCCsBuildToolsUtils class is a unittest class for ccsbuildtools_utils.
    Attributes:
        ctx: Context object of servicelab module.
    """

    def setUp(self):
        """setUp function for context attribute <> clone latest ccsbuildtools
        """
        self.ctx = Context()
        username = helper_utils.get_username(self.ctx.path)
        service_utils.sync_service(self.ctx.path, "master", username,
                                   "ccs-build-tools"
                                   )

    def TearDown(self):
        """tear down <> remove cloned repo
        """
        shutil.rmtree(os.path.join(self.ctx.path, "services",
                                   "ccs-build-tools"))

    def test_buildargs_match_userinputs(self):
        """test that the data required from the user match the inputs used by the
        data values used by ccsbuildtools.

           -> accessor function is called to assign site_by_user all the inputs
              needed by the current iteration of slab ccsbuildtools_utils
           -> the answer-sample.yaml file contains all the inputs needed by
              the current iteration of ccsbuild-tools to properly build a site
           -> ensure that all keys of both dictionary inputs match
        """
        site_by_user = \
            ccsbuildtools_utils.get_input_requirements_for_ccsbuildtools()
        path_to_repo = os.path.join(self.ctx.path, "services",
                                    "ccs-build-tools")
        with open(os.path.join(path_to_repo, "answer-sample.yaml"), 'r') as f:
            site_by_repo = yaml.load(f)
        self.assertEqual(_compare_dicts(site_by_user, site_by_repo), 0)

    def test_needed_directories_and_files_exist(self):
        """test that all directories references by the ccsbuildtools_utils exist in
        the latest version of the repo
             -> host generation (where hosts are generated - need out of band
                vpn access)
             -> ignition (where site directory is made)
             -> Vagrantfile needed because site is generated using vagrant
                environment
        """
        path_to_repo = \
            os.path.join(self.ctx.path, "services", "ccs-build-tools")
        self.assertEqual(os.path.isdir(os.path.join(path_to_repo,
                                                    "host_generation")), True)
        self.assertEqual(os.path.isdir(os.path.join(path_to_repo,
                                                    "ignition_rb")), True)
        self.assertEqual(os.path.isfile(os.path.join(path_to_repo,
                                                     "Vagrantfile")), True)

    def test_exit_input(self):
        """test that the yaml dictionaries are properly dumped into file.
            -> test that the file exists
            -> tests that the file can be loaded into a dictionary, which
               is equivalent to the dictionary used to dump the file
        """
        site_by_user = \
            ccsbuildtools_utils.get_input_requirements_for_ccsbuildtools()
        path_to_dump = \
            os.path.join(self.ctx.path, "services", "ccs-build-tools",
                         "a.yaml")
        ccsbuildtools_utils.exit_input(site_by_user, path_to_dump, False)
        self.assertEqual(os.path.isfile(path_to_dump), True)
        with open(path_to_dump, 'r') as f:
            self.assertEqual(yaml.load(f), site_by_user)


if __name__ == '__main__':
    unittest.main()
