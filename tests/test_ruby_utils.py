import os
import unittest
from servicelab.stack import Context
from servicelab.utils import ruby_utils
from servicelab.utils import service_utils


class TestRubyUtils(unittest.TestCase):
    RUBY_VERSION_FILE = ".ruby_version"
    CCS_GEMFILE = "servicelab/.stack/services/ccs-data/Gemfile"
    ROOT_GEMFILE = "Gemfile"

    def _list_of_gems(self, f):
        """ internal  function for servicelab giveing a complete list of gem's
            installed for ruby it reads the incoming file. Each file is a ruby
            install file where line can be of the form:
            ...
            gem 'gem-name'
            ...


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

    def test_ruby_installed(self):
        """ Test for ruby version check.

        """
        self.assertEqual(self.ruby_version, ruby_utils.get_ruby_version())

    def test_list_of_gems(self):
        """ Test if installed gems match which are required by CCS_GEMFILE AND
             ROOT_GEMFILE.

        """
        for item in self.gems:
            self.assertEqual(0, ruby_utils.check_for_gems(item))

if __name__ == '__main__':
    unittest.main()
