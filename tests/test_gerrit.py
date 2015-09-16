"""
Test Classes for gerrit.
"""
import re
import shutil
import click
import unittest
from servicelab.stack import Context
from servicelab.utils import gerrit_functions
from servicelab.utils import service_utils


@unittest.skip("Tests are to be performed on local machine as they use  staging server")
class TestGerrtFunctions(unittest.TestCase):
    """
    TestGerritFunctions class is a unittest class testing the various gerrit api's
    including the
        1. Check the incoming queue
        2. Check the outgoing queue
        3. Check if the particualr review exist in the repository
        4. Check if -1 can be given for the changes.
        5. Check if +1 can be given for the changes.
        6. Check if the changes can be merged (+2 +1)

    The staging server is used for testing the changes.
    A sample project testproject has been created on teh staging server. This
    project is cloned on the tmp directory. A line is added to the test.py. After
    the locally committing the file the test is run to check the input, output
    queues and finally various review numbers are performed to finally abandon or
    approve the merge.
    """

    def setUp(self):
        """
        setUp function for gerrit functions
        """
        self.sortTestMethodsUsing = None

        self.ctx = Context()
        self.ctx.debug = True
        self.user = "kunanda"
        self.prjname = "testproject"
        self.prjdir = "/tmp/" + self.prjname
        self.hostname = self.ctx.get_gerrit_server()['hostname']
        self.port = self.ctx.get_gerrit_server()['port']

        self.testrepo = "testproject"
        service_utils.run_this("cd /tmp;"
                               "git clone ssh://{}@{}:{}/{}".format(self.user,
                                                                    self.hostname,
                                                                    self.port,
                                                                    self.prjname))
        service_utils.run_this("cd {};git checkout develop;".format(self.prjdir))
        with open("{}/test.py".format(self.prjdir), "a") as tfile:
            tfile.write("print 'Hello world'")

        cmdrt, cmdrtstr = service_utils.run_this("cd {};".format(self.prjdir) +
                                                 "git add test.py;"
                                                 "git commit -m 'one additional line';")
        cmd = "cd {};git review develop".format(self.prjdir)
        cmdrt, cmdrtstr = service_utils.run_this(cmd)
        if cmdrt:
            click.echo("unable to perform setup for the test")
            click.echo("test failed")
            self.fail(cmdrtstr)

        mtch = re.search("(https://.*/)([0-9]+)", cmdrtstr)
        if not (mtch and mtch.group(2)):
            click.echo("unable to find match in the string\n{}".format(cmdrtstr))
            self.fail("test failed: unable to determine changeset")
        self.review = mtch.group(2)

    def tearDown(self):
        """
        teardown function removes the directory /tmp/prjdir
        """
        if self.review:
            gfn = gerrit_functions.GerritFns(self.user, self.prjname, self.ctx)
            gfn.print_gerrit("", self.review, self.user, "", "abandoned")
        shutil.rmtree(self.prjdir)

    def test_review(self):
        """
        check if we get the review
        """
        gfn = gerrit_functions.GerritFns(self.user, self.prjname, self.ctx)
        gerrit_functions.GerritFns.instrument_code = True
        rev = gfn.print_gerrit("", self.review, self.user, "", "")
        self.assertIsNotNone(rev, "Unable to find the review item {}".format(self.review))

    def test_review_number(self):
        """
        test the review number
        """
        gfn = gerrit_functions.GerritFns(self.user, self.prjname, self.ctx)
        gerrit_functions.GerritFns.instrument_code = True
        gfn.change_review(self.review, 1, 0, "reviewed")
        rev = gfn.print_gerrit("", self.review, self.user, "", "")
        import pdb
        pdb.set_trace()
        self.assertEqual(rev["currentPatchSet"]["approvals"][0]["value"],
                         "1",
                         "unable to change the code review value")

    def test_abandon(self):
        """
        test if able to abandon
        """
        gfn = gerrit_functions.GerritFns(self.user, self.prjname, self.ctx)
        gerrit_functions.GerritFns.instrument_code = True
        gfn.code_state(self.review, "abandon", "abandon by unit test")
        rev = gfn.print_gerrit("", self.review, self.user, "", "abandoned")
        if rev:
            self.review = None
        self.assertIsNotNone(rev, "Unable to find the review item {}".format(self.review))


if __name__ == '__main__':
    unittest.main()
