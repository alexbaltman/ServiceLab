import os
import unittest
from servicelab.stack import Context
from servicelab.utils import ruby_utils
from servicelab.utils import service_utils


class TestRubyUtils(unittest.TestCase):
    """TestRubyUtils is a unittest.TestCase class for doing unit test
    for the ruby_utils. It has a set up function which coolects all
    the gems to install for servicelab module.

    Attributes:
        RUBY_VERSION_FILE: A const which refers to the ruby version
            file as installed by ervicelab.
        CCS_GEMFILE: A const which referes to the gem file for CCS
            data.
        ROOT_GEMFILE: A const which refers to gem file for whole
            servicelab module.
        gems: List of gems used by servicelab modules.

    """
    RUBY_VERSION_FILE = ".ruby_version"
    CCS_GEMFILE = "servicelab/.stack/services/ccs-data/Gemfile"
    ROOT_GEMFILE = "Gemfile"

    def _list_of_gems(self, f):
        """ Internal  function for servicelab giving a complete list of gem's
            to be installed. It reads the incoming file. Each file is a ruby
            install file where line can be of the form:
            ...
            gem 'gem-name'
            ...

        Args:
            f: file object containing list of gems.

        Returns:
            list of gems to be installed.
        """
        gemlst = []
        for line in f:
            line = line.strip()
            if line.startswith("gem"):
                gem = line.split(" ")[1]
                if(gem.startswith('\'')):
                    gem = gem[1:gem.rfind('\'')]
                elif(gem.startswith('\"')):
                    gem = gem[1:gem.rfind('\"')]
                gemlst.append(gem)
        return gemlst

    def setUp(self):
        """ setUp function for Ruby Utils test, this setsup the ruby version as
        defined in RUBY_VERSION_FILE and GEMS list as defined in Root and
        CCS directories.

        """
        ctx = Context()
        path_to_reporoot = os.path.split(ctx.path)
        path_to_reporoot = os.path.split(path_to_reporoot[0])
        path_to_reporoot = path_to_reporoot[0]

        # setup the gem's
        ruby_utils.setup_gems(ctx.path)
        ruby_utils.setup_gems(ctx.path, 0)

        # setup the gem's
        ruby_utils.setup_gems(ctx.path, 1)
        ruby_utils.setup_gems(ctx.path, 0)

        try:
            self.ruby_version = None
            with open(os.path.join(path_to_reporoot,
                                   TestRubyUtils.RUBY_VERSION_FILE)) as f:
                self.ruby_version = f.readlines()[0].strip()[5:10]

            self.gems = []
            with open(os.path.join(path_to_reporoot,
                                   TestRubyUtils.ROOT_GEMFILE)) as f:
                self.gems = self._list_of_gems(f)

            with open(os.path.join(path_to_reporoot,
                                   TestRubyUtils.CCS_GEMFILE)) as f:
                self.gems = self.gems + self._list_of_gems(f)
        except IOError, e:
            self.Fail(1, 0, "Setup FAILS b/c can't access ruby-version, ccs-data/Gemfile.")

    def tearDown(self):
        for gem in self.gems:
            ruby_utils.uninstall_gem(gem)

    @unittest.skip("Waiting on Jenkins env fix w/ ccs-data.")
    def test_ruby_installed(self):
        """ Test for ruby version check.

        """
        self.assertEqual(self.ruby_version, ruby_utils.get_ruby_version())

    @unittest.skip("Waiting on Jenkins env fix w/ ccs-data.")
    @unittest.skipIf(not ruby_utils.check_devenv(), "ruby dev env is absent")
    def test_list_of_gems(self):
        """ Test installed gems match all gems in servicelab root and ccs.

        """
        for item in self.gems:
            self.assertEqual(0, ruby_utils.check_for_gems(item))

if __name__ == '__main__':
    unittest.main()
