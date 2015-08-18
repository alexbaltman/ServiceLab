import os
import re
import unittest
from servicelab.stack import Context
from servicelab.utils import tc_vm_yaml_create


class TestVMYamlCreate(unittest.TestCase):
    """
    TestVMYamlCreate class is a unittest for tc_vm_yaml_create
    """

    def setUp(self):
        """
        Construct the data needed to create a new host yaml file
        """
        self.ctx = Context()
        match = re.search('(.*)\.stack', self.ctx.path)
        if match:
            self.ccsdatapath = os.path.join(match.group(1), 'testsite')
        self.hostname = 'my-test-002'
        self.site = 'test-site-1'
        self.env = 'test-env-1'
        self.flavor = 'fake.flavor.dne'
        self.vlanid = '67'
        self.role = 'none'
        self.groups = 'default'
        self.secgroups = ['default']
        self.filename = os.path.join(self.ccsdatapath, 'sites', self.site,
                                     'environments', self.env, 'hosts.d',
                                     str('csl-a-' + self.hostname + '.yaml')
                                     )

    def test_tc_vm_yaml_create(self):
        """
        Tests the create of the host yaml file within the supplied site / env
        """
        tc_vm_yaml_create.create_vm(self.ccsdatapath, self.hostname, self.site, self.env,
                                    self.flavor, self.vlanid, self.role, self.groups,
                                    self.secgroups)
        self.assertTrue(os.path.isfile(self.filename))
        os.remove(self.filename)


if __name__ == '__main__':
    unittest.main()
