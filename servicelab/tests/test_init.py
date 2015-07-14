import unittest
import socket
import sys

gerrit_host = 'cis-gerrit.cisco.com'


class TestInitCmds(unittest.TestCase):

    def setUp(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if not s.connect((gerrit_host, 29418)):
            print "Cannot access %s on port 29418" % (gerrit_host,)
            sys.exit(1)

    def test_init_servicetype_service(self):
        pass

    def test_init_servicetype_service_failure(self):
        pass

    def test_init_servicetype_project(self):
        pass

    def test_init_servicetype_project_failure(self):
        pass

    def test_init_verbose(self):
        pass

    def test_init_debug(self):
        pass

    @classmethod
    def tearDownClass():
        pass

if __name__ == '__main__':
    unittest.main()
