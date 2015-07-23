import os
import unittest
from servicelab.stack import Context
from servicelab.utils import ccsdata_utils


class TestCCsDataUtils(unittest.TestCase):
    """
    TestCCsDataUtils class is a unittest class for ccsdata_utils.
    It gets all the data avialable in the .stack directory. It
    uses ccsdata_utils to gets all the sites information in the
    data structure and verifies if the data associated with the
    given site svl-pod-1 is available or not. Also checks if the
    environment associated with the site exist or not.

    Attributes:
        ctx:  Context object of servicelab module.
        site_to_check: site against which the test is run

    """

    def setUp(self):
        """ setUp function of the TestCCsDataUtils class, it sets
        up the context attribute amd site_to_check.

        The setUp function has hardcoded the value of site_to_check
        to "svl-pod-1".

        """
        self.ctx = Context()
        self.site_to_check = "svl-pod-1"

    def test_ccs_site_exist(self):
        """ The test_ccs_site_exist is a test case to check if
        site_to_check is available amongs the sites which we get
        by using ccsdata_utilsr:.list_envs_or_sites function.

        If the assertion fails then test fails.
        """
        sites = ccsdata_utils.list_envs_or_sites(self.ctx.path)
        self.assertIn(self.site_to_check, sites)

    def test_ccs_site_env_exist(self):
        """ The test_ccs_site_env_exist is a test case to check if
        environment for site_to_check is available amongs the sites
        which we get by using ccsdata_utilsr:list_envs_or_sites
        function.

        If the assertion fails then test fails. The assertion can
        fail for number of reasons :
        1. The site_to_check site is not in the list returned by
           ccsdata_utilsr:list_envs_or_sites.
        2. If we do not have an environment for the the given
           site_to_check site.
        3. If the data exist but is not in the directory as
           supplied by (path, site, environemt).
        """
        sites = ccsdata_utils.list_envs_or_sites(self.ctx.path)
        self.assertIn(self.site_to_check, sites)

        envs = sites[self.site_to_check]
        self.assertIsNotNone(envs)

        # we expect atleast one environment to exist in svl-pod-1
        env = envs.keys()[0]
        self.assertIsNotNone(env)
        print env

        path = ccsdata_utils.get_env_for_site_path(self.ctx.path,
                                                   self.site_to_check,
                                                   env)
        self.assertTrue(os.path.isdir(path))


if __name__ == '__main__':
    unittest.main()
