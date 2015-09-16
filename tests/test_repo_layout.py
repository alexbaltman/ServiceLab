"""
Test Classes for checking Ansible and Puppet Layouts.
"""
import os
import os.path
import shutil
import yaml
import unittest
from servicelab.stack import Context
from servicelab.utils import create_repo
from servicelab.utils import service_utils

@unittest.skip("Tests are to be performed on local machine as they use  staging server")
class TestAnsibleBuilder(unittest.TestCase):
    """
    TestAnsibleBuilder class is a unittest class for repo_new command set, testing
    Ansible Layout on staging server.

    Setup of the test create a project of type Ansible on the staging server and then
    download the template, instantiate the template, create a repo create a nimbus,
    create set up ansible directory and the roles.

    Test will run and test each of the attributes of the created projects

    Attributes:
        ctx                 -- Context object of servicelab module.
        name                -- name of the repo.
        reponame            -- The directory name is always of type
                               service-<name>-ansible.
        roles               -- Preset to [role1, role2, role3].
        user                -- the user running the test.

    """

    def setUp(self):
        """setUp function for context attribute <> clone latest ccsbuildtools
        """
        self.sortTestMethodsUsing = None
        self.name = "ansibletest"
        self.roles = ["role1", "role2"]
        self.chk_script = "ansibletest.chk"
        self.ctx = Context()

        self.ctx.debug = True
        blder = create_repo.Repo.builder("Ansible", self.ctx, self.name)
        blder.chk_script = self.chk_script
        blder.play_roles = self.roles

        self.reponame = blder.get_reponame()
        self.user = blder.get_usr()

        # make sure nothing exist
        if os.path.exists(self.reponame):
            shutil.rmtree(self.reponame)

        blder.construct()

    def tearDown(self):
        shutil.rmtree(self.reponame)

    def test_project(self):
        """
        Check if the project service-ansibletest-ansible exist in the gerrit
        repository as the project.
        """
        hostname = self.ctx.get_gerrit_server()['hostname']
        port = self.ctx.get_gerrit_server()['port']
        cmd = "ssh -p {} {} gerrit ls-projects | grep {}".format(port,
                                                                 hostname,
                                                                 self.reponame)
        retcode, _ = service_utils.run_this(cmd)
        self.assertEqual(0, retcode,
                         "project was not created in the staging area")

    def test_repo(self):
        """
        Check if the project service-ansibletest-ansible exist in the gerrit repository
        has been downloaded or not."
        """
        self.assertTrue(os.path.isdir(self.reponame),
                        "No {} repo downloaded".format(self.reponame))

    def test_nimbus(self):
        """
        Check if the nimbus file for service-ansibletest-ansible has been created.
        """
        nbus = os.path.join(".", self.reponame, ".nimbus.yaml")
        with open(nbus, "r") as nimbus:
            ndict = yaml.load(nimbus)
        self.assertEqual(ndict['service'], self.name + "-ansible", "corrupt file")
        self.assertEqual(ndict['deploy']["type"], "ansible", "corrupt file")
        self.assertEqual(ndict['deploy']['playbook'], self.name + ".yaml",
                         "corrupt file")
        self.assertEqual(ndict['verify']['type'], "serverspec", "corrupt file")
        self.assertEqual(ndict['check']['script'], self.chk_script, "corrupt file")

    def test_ansible(self):
        """
        Check if the ansible directory, ansible check files and roles have been created
        or not for service-ansibletest-ansible.
        """
        ansibledir = os.path.join(self.reponame, "ansible")
        self.assertTrue(os.path.isdir(ansibledir),
                        "missing ansible directory {}".format(self.reponame))

        with open(os.path.join(self.reponame,
                               "ansible",
                               self.name + ".yaml"), "r") as ystrm:
            ydict = yaml.load(ystrm)

        self.assertEqual(ydict['hosts'],
                         "{}-ansible".format(self.name),
                         "corrupt ansible file.")
        self.assertEqual(ydict['remote_user'], self.user, "corrupt ansible file.")
        self.assertEqual(ydict['roles'], self.roles, "corrupt ansible file")

    def test_roles(self):
        """
        Check the overall layout of service-ansibletest-ansible directory.
        """
        path = os.path.join(self.reponame, "ansible", "roles")
        self.assertTrue(os.path.isdir(path), " missing ansibles roles files")
        for role in self.roles:
            self.assertTrue(os.path.isdir(os.path.join(path,
                                                       role,
                                                       "defaults")),
                            "missing roles files")
            self.assertTrue(os.path.isdir(os.path.join(path,
                                                       role,
                                                       "tasks")),
                            "missing roles files")
            self.assertTrue(os.path.isdir(os.path.join(path,
                                                       role,
                                                       "templates")),
                            "missing roles files")


@unittest.skip("Tests are to be performed on local machine as they use  staging server")
class TestPuppetBuilder(unittest.TestCase):
    """
    TestPuppetBuilder class is a unittest class for repo_new command set, testing
    Puppet Layout on Puppet server.

    Setup of the test create a project of type Puppet on the staging server and then
    download the template, instantiate the template, create a repo, create a nimbus,
    create  & set up puppet directory and the roles.

    Test will run and test each of the attributes of the created projects

    Attributes:
        ctx                 -- Context object of servicelab module.
        name                -- name of the repo
        reponame            -- The directory name is always of type
                               service-<name>-puppet
        roles               -- Preset to [ansiblerole1, ansiblerole2, ansiblerole3]
        user                -- the person doing the tests
    """
    def setUp(self):
        """
        setUp function for context attribute <> clone latest ccsbuildtools
        """
        self.sortTestMethodsUsing = None
        self.name = "puppettest"
        self.roles = ["role1", "role2"]
        self.chk_script = "ansible.chk"
        self.ctx = Context()

        self.ctx.debug = True
        blder = create_repo.Repo.builder("Puppet", self.ctx, self.name)
        blder.chk_script = self.chk_script
        blder.play_roles = self.roles
        self.user = blder.get_usr()
        self.reponame = blder.get_reponame()

        # make sure nothing exist
        if os.path.exists(self.reponame):
            shutil.rmtree(self.reponame)
        blder.construct()

    def tearDown(self):
        shutil.rmtree(self.reponame)

    def test_project(self):
        """
        Check if the project service-puppettest-puppet exist in the gerrit repository
        as the project.
        """
        hostname = self.ctx.get_gerrit_server()['hostname']
        port = self.ctx.get_gerrit_server()['port']
        cmd = "ssh -p {} {} gerrit ls-projects | grep {}".format(port,
                                                                 hostname,
                                                                 self.reponame)
        retcode, _ = service_utils.run_this(cmd)
        self.assertEqual(0, retcode,
                         "project was not created in the staging area")

    def test_repo(self):
        """
        Check if the project service-puppettest-puppet exist in the gerrit repository
        has been downloaded or not."
        """
        self.assertTrue(os.path.isdir(self.reponame),
                        "No {} repo downloaded".format(self.reponame))

        path = os.path.join(self.reponame, "data", "service.yaml")
        self.assertTrue(os.path.exists(path), "missing service.yaml file")

        path = os.path.join(self.reponame, "puppet", "manifests", "site.pp")
        self.assertTrue(os.path.exists(path), "missing site.pp file")

        path = os.path.join(self.reponame, "puppet", "modules", self.name,
                            "manifests", "init.pp")
        self.assertTrue(os.path.exists(path),
                        "missing {} module  init.pp file".format(self.name))

        path = os.path.join(self.reponame, "puppet", "modules", self.name,
                            "templates", "index.html.erb")
        self.assertTrue(os.path.exists(path),
                        "missing {} module  index.html.erb file".format(self.name))

        path = os.path.join(self.reponame, "Vagrantfile")
        self.assertTrue(os.path.exists(path),
                        "missing {} module  Vargrant file".format(self.name))

    def test_nimbus(self):
        """
        Check if the nimbus file for service-puppettest-puppet has been created.
        """
        nbus = os.path.join(".", self.reponame, ".nimbus.yaml")
        with open(nbus, "r") as nimbus:
            ndict = yaml.load(nimbus)
        self.assertEqual(ndict['service'], self.name + "-puppet", "corrupt file")
        self.assertEqual(ndict['deploy']["type"], "puppet", "corrupt file")
        self.assertEqual(ndict['deploy']['manifest'],
                         "manifests/site.pp",
                         "corrupt file")
        self.assertEqual(ndict['verify']['type'], "serverspec", "corrupt file")
        self.assertEqual(ndict['check']['script'], self.chk_script, "corrupt file")

if __name__ == '__main__':
    unittest.main()
