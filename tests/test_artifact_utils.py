"""
    TestClass to test various go cd functions.
"""
import unittest

from click.testing import CliRunner

from servicelab.commands import cmd_list
from servicelab.commands import cmd_find
from servicelab.stack import Context
from servicelab.utils import artifact_utils


class TestArtifactUtils(unittest.TestCase):
    """
    TestArtifactUtils class is a unittest class for testing artifact commands.
    Attributes:
        ctx:  Context object of servicelab module.
    """

    ARTIFACTORY_USER = "ragkatti"
    ARTIFACTORY_PASS = "NEWjob2015"
    ARTIFACT = "https://ccs-artifactory.cisco.com/artifactory/api/storage"\
               "/bmcweb/repodata/filelists.xml.gz"
    STATUS = "bmcweb"

    def setUp(self):
        """ Setup variables required to test the os_provider functions
        """
        self.ctx = Context()

    def test_cmd_list(self):
        """ Tests artifact list command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_list.cli,
                               ['artifacts',
                                '-u',
                                TestArtifactUtils.ARTIFACTORY_USER,
                                '-p',
                                TestArtifactUtils.ARTIFACTORY_PASS])
        self.assertTrue(TestArtifactUtils.ARTIFACT in result.output.strip())

    def test_cmd_find(self):
        """ Tests artifact list command.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_find.cli,
                               ['artifact',
                                'filelists',
                                '-u',
                                TestArtifactUtils.ARTIFACTORY_USER,
                                '-p',
                                TestArtifactUtils.ARTIFACTORY_PASS])
        self.assertTrue(TestArtifactUtils.ARTIFACT in result.output.strip())

    def test_cmd_show(self):
        """ Tests show command.
        """

        result = artifact_utils.get_artifact_info(
            TestArtifactUtils.ARTIFACT,
            TestArtifactUtils.ARTIFACTORY_USER,
            TestArtifactUtils.ARTIFACTORY_PASS)
        self.assertTrue(TestArtifactUtils.STATUS in result)


if __name__ == '__main__':
    unittest.main()
