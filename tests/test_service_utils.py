#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import shutil
import socket

import hashlib
import unittest
from tests.helpers import temporary_dir

from servicelab.utils import helper_utils
from servicelab.utils import service_utils
from servicelab.stack import Context


class TestServiceUtils(unittest.TestCase):
    """
    Test all of the functions in servicelab/utils/service_utils.py

    Attributes:
        ctx: Click module context object from servicelab/stack.py
    """
    ctx = Context()
    username = ctx.username
    if re.search('sdlc-\d+', socket.gethostname()):
        username = 'jenkins'

    def setUp(self):
        """
        Setup a separate temporary directory to use for each test
        """
        with temporary_dir() as temp_dir:
            self.temp_dir = temp_dir

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_sync_service(self):
        """
        Test the sync_service function

        Ensure that a git repo is successfully synced
        Ensure that a nonexistant git repo is not successfully synced
        """
        sync_service_out = service_utils.sync_service(
            path=self.temp_dir,
            branch='master',
            username=self.username,
            service_name='service-horizon')
        self.assertEqual(sync_service_out, True)

        sync_service_out = service_utils.sync_service(
            path=self.temp_dir,
            branch='master',
            username=self.username,
            service_name='service-fakeservice')
        self.assertEqual(sync_service_out, False)

    def test_build_data(self):
        """
        Test the build_data function

        Ensure that ccs-data is not installed
        Ensure that lightfuse.rb is able to build the ccs-dev-1 site
        """
        build_data_return, build_data_out = service_utils.build_data(self.temp_dir)
        self.assertEqual(build_data_return, 1)
        self.assertTrue('Could not find ccs-data' in build_data_out)

        shutil.copytree(os.path.join(self.ctx.path, 'provision'),
                        os.path.join(self.temp_dir, 'provision'))
        service_utils._git_clone(path=self.temp_dir,
                                 branch='master',
                                 username=self.username,
                                 service_name='ccs-data')
        build_data_return, build_data_out = service_utils.build_data(self.temp_dir)
        self.assertEqual(build_data_return, 0)
        self.assertFalse(build_data_out)

    def test_copy_certs(self):
        """
        Test the copy_certs function

        Ensure that trying to copy to an invalid directory fails
        Ensure that the cert files copy to the specified directory
        """
        src_path = os.path.join(self.ctx.path, 'provision')
        dst_path = os.path.join(self.temp_dir, 'fake_dir')
        copy_certs_return = service_utils.copy_certs(src_path, dst_path)
        self.assertEqual(copy_certs_return, 1)

        check_path = os.path.join(self.temp_dir,
                                  'modules',
                                  'ccs',
                                  'files',
                                  'certs',
                                  'dev-csi-a')
        os.makedirs(check_path)
        copy_certs_return = service_utils.copy_certs(src_path, self.temp_dir)
        self.assertEqual(copy_certs_return, 0)
        for pem_file in ['ccsapi.dev-csi-a.cis.local.pem',
                         'meter.dev-csi-a.cis.local.pem',
                         'ha_dev-csi-a.cis.local.pem',
                         'ha_storage.dev-csi-a.cis.local.pem']:
            self.assertTrue(os.path.isfile(os.path.join(check_path, pem_file)))

    def test_git_clone(self):
        """
        Test the _git_clone function

        Ensure failure with bad repo/branch names
        Ensure success with valide repo/branch names
        """
        git_clone_return, git_clone_data = service_utils._git_clone(
            path=self.temp_dir,
            branch='fake-branch',
            username=self.username,
            service_name='fake-repo')
        self.assertEqual(git_clone_return, 1)
        repo_dir = os.path.join(self.temp_dir, 'services', 'fake-repo')
        self.assertFalse(os.path.isdir(repo_dir))

        git_clone_return, git_clone_data = service_utils._git_clone(
            path=self.temp_dir,
            branch='master',
            username=self.username,
            service_name='service-horizon')
        self.assertEqual(git_clone_return, 0)
        repo_dir = os.path.join(self.temp_dir, 'services', 'service-horizon')
        self.assertTrue(os.path.isdir(repo_dir))

    def test_git_pull_ff(self):
        """
        Test the _git_pull_ff function

        Clone a repo
        Ensure failure of fast forward pull with bad branch name
        Ensure success of fast forward pull with valid repo/branch names
        """
        git_clone_return, git_clone_data = service_utils._git_clone(
            path=self.temp_dir,
            branch='master',
            username=self.username,
            service_name='service-horizon')

        git_pull_return, git_pull_output = service_utils._git_pull_ff(
            path=self.temp_dir,
            branch='service-horizon',
            service_name='fake-repo')
        self.assertEqual(git_pull_return, 1)

        git_pull_return, git_pull_output = service_utils._git_pull_ff(
            path=self.temp_dir,
            branch='master',
            service_name='service-horizon')
        self.assertEqual(git_pull_return, 0)

    def test_check_for_cmd(self):
        """
        Test the _check_for_cmd function, which checks if the specified command is installed

        Ensure fake-command is not installed
        Ensure git is installed
        """
        check_cmd_return, check_cmd_output = service_utils._check_for_cmd('fake-command')
        self.assertEqual(check_cmd_return, 1)

        check_cmd_return, check_cmd_output = service_utils._check_for_cmd('git')
        self.assertEqual(check_cmd_return, 0)

    def test_setup_vagrant_sshkeys(self):
        """
        Test the setup_vagrant_sshkeys function, which gens vagrant keys if they are not
        already installed
        """
        service_utils.setup_vagrant_sshkeys(self.temp_dir)
        key_path = os.path.join(self.temp_dir, 'id_rsa')
        self.assertEqual(os.path.isfile(key_path), True)
        self.assertEqual(os.path.isfile(key_path + '.pub'), True)
        first_key_hash = hashlib.md5(open(key_path, 'rb').read()).hexdigest()
        service_utils.setup_vagrant_sshkeys(self.temp_dir)
        second_key_hash = hashlib.md5(open(key_path, 'rb').read()).hexdigest()
        self.assertEqual(first_key_hash, second_key_hash)

    def test_link(self):
        """
        Test the link function, which links the current-service dir to services/repo_name

        Ensure failure of invalid data
        Ensure successful symlink of valid data
        """
        link_return = service_utils.link(
            path=self.temp_dir,
            service_name='fake-repo',
            branch='fake-branch',
            username=self.username)
        self.assertEqual(link_return, 1)

        link_return = service_utils.link(
            path=self.temp_dir,
            service_name='service-horizon',
            branch='master',
            username=self.username)
        self.assertEqual(link_return, 0)

    def test_clean(self):
        """
        Test the clean function, which deletes the current file and unlinks current_service

        Clone and symlink a repo to current-service, and set as current
        Ensure current file and current-service symlink exist
        Ensure current file and current-service symlink are removed
        """
        sync_service_return = service_utils.sync_service(
            path=self.temp_dir,
            branch='master',
            username=self.username,
            service_name='service-horizon')
        link_return = service_utils.link(
            path=self.temp_dir,
            service_name='service-horizon',
            branch='master',
            username=self.username)
        self.assertEqual(link_return, 0)
        self.assertTrue(os.path.islink(os.path.join(self.temp_dir, 'current_service')))
        self.assertTrue(os.path.isfile(os.path.join(self.temp_dir, 'current')))

        service_utils.clean(self.temp_dir)
        self.assertFalse(os.path.islink(os.path.join(self.temp_dir, 'current_service')))
        self.assertFalse(os.path.isfile(os.path.join(self.temp_dir, 'current')))

    def test_check_service(self):
        """
        Test the check_service function, which checks gerrit for the specified repo

        Ensure failure of invalid repo
        Emsure success of valid repo
        """
        check_service_return = service_utils.check_service(
            path=self.temp_dir,
            service_name='fake_repo')
        self.assertEqual(check_service_return, 1)

        check_service_return = service_utils.check_service(
            path=self.temp_dir,
            service_name='service-horizon')
        self.assertEqual(check_service_return, 0)

    def test_run_this(self):
        """
        Test the run_this function, which runs a shell command

        Ensure failure of invalid command
        Ensure success of valid command
        """
        run_this_return, run_this_output = service_utils.run_this('fake-command')
        self.assertTrue(run_this_return != 0)

        run_this_return, run_this_output = service_utils.run_this('type bash')
        self.assertEqual(run_this_return, 0)

    def test_installed(self):
        """
        Test the installed function, which checks if the specified repo is cloned locally

        Ensure failure with fake repo
        Ensure success with valid repo
        """
        sync_service_return = service_utils.sync_service(
            path=self.temp_dir,
            branch='master',
            username=self.username,
            service_name='service-horizon')
        sync_service_return = service_utils.link(
            path=self.temp_dir,
            service_name='service-horizon',
            branch='master',
            username=self.username)
        installed_return = service_utils.installed('fake-service', self.temp_dir)
        self.assertFalse(installed_return)

        installed_return = service_utils.installed('service-horizon', self.temp_dir)
        self.assertTrue(installed_return)


if __name__ == '__main__':
    unittest.main()
