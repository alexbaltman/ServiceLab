#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
import os
import unittest
from servicelab.utils import helper_utils
from servicelab.utils import service_utils
from tests.helpers import temporary_dir
from servicelab.stack import Context


class TestServiceUtils(unittest.TestCase):
    cleanup_paths = []

    def setUp(self):
        self.ctx = Context()
        pass

    def test_sync_service(self):
        returncode, username = helper_utils.get_gitusername(self.ctx.path)
        if returncode > 0:
            helper_utils.get_loginusername()
        if returncode > 0:
            helper_utils.get_loginusername()
        with temporary_dir() as temp_dir:
            out = service_utils.sync_service(path=temp_dir,
                                             branch='master',
                                             username=username,
                                             service_name='service-heighliner')

            self.assertEqual(out, True)
            out = service_utils.sync_service(path=temp_dir,
                                             branch='master',
                                             username=username,
                                             service_name='service-heighliner')
            self.assertEqual(out, True)

    def test_build_data(self):
        pass

    def test_git_clone(self):
        pass

    def test_git_pull_ff(self):
        pass

    def test_submodule_pull_ff(self):
        pass

    def test_check_for_git(self):
        pass

    def test_setup_vagrant_sshkeys(self):
        with temporary_dir() as temp_dir:
            service_utils.setup_vagrant_sshkeys(temp_dir)
            key_path = os.path.join(temp_dir, 'id_rsa')
            self.assertEqual(os.path.isfile(key_path), True)
            self.assertEqual(os.path.isfile(key_path + '.pub'), True)
            first_key_hash = hashlib.md5(open(key_path,
                                              'rb').read()).hexdigest()
            service_utils.setup_vagrant_sshkeys(temp_dir)
            second_key_hash = hashlib.md5(open(key_path,
                                               'rb').read()).hexdigest()
            self.assertEqual(first_key_hash, second_key_hash)

    def test_link(self):
        pass

    def test_clean(self):
        pass

    def test_check_service(self):
        pass

    def test_run_this(self):
        pass

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
