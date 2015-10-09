import os
import re
import yaml
import shutil
import unittest
import ipaddress
from servicelab.stack import Context
from servicelab.utils import tc_vm_yaml_create


class TestVMYamlCreate(unittest.TestCase):
    """
    TestVMYamlCreate class is a unittest for tc_vm_yaml_create
    """

    def write_file(self, f, data):
        with open(f, 'w') as outfile:
            outfile.write(yaml.dump(data, default_flow_style=False))

    def setUp(self):
        """
        Construct the data needed to create a new host yaml file
        """
        self.ctx = Context()
        self.ccsdatapath = os.path.join(self.ctx.path, 'testsite')
        self.hostname1 = 'my-test-001'
        self.hostname2 = 'my-test-002'
        self.site = 'test-site-1'
        self.env = 'test-env-1'
        self.tcregion = 'csl-a'
        self.flavor = 'fake.flavor.dne'
        self.vlanid = '67'
        self.role = 'none'
        self.groups = 'default'
        self.secgroups = ['default']
        self.ip1 = None
        self.ip2 = '10.11.12.152'
        self.filename1 = os.path.join(self.ccsdatapath, 'sites', self.site,
                                      'environments', self.env, 'hosts.d',
                                      str(self.tcregion + '-' + self.hostname1 + '.yaml')
                                      )
        self.filename2 = os.path.join(self.ccsdatapath, 'sites', self.site,
                                      'environments', self.env, 'hosts.d',
                                      str(self.tcregion + '-' + self.hostname2 + '.yaml')
                                      )
        self.subnet = ipaddress.IPv4Network(unicode('10.12.14.128/25'))
        env_path = os.path.join(self.ccsdatapath, 'sites', self.site, 'environments')

        # Create a fake site to simulate ccs-data repo
        output_path = os.path.join(env_path, self.site, 'data.d')
        os.makedirs(output_path)
        output_file = os.path.join(output_path, 'environment.yaml')
        yaml_data = {'domain_name': 'test.site.com',
                     'region': 'csm',
                     }
        self.write_file(output_file, yaml_data)
        output_path = os.path.join(env_path, self.site, 'hosts.d')
        os.makedirs(output_path)
        output_file = os.path.join(output_path, 'csm-fake-node.yaml')
        yaml_data = {'type': 'physical'}
        self.write_file(output_file, yaml_data)
        output_path = os.path.join(env_path, self.env, 'data.d')
        os.makedirs(output_path)
        output_file = os.path.join(output_path, 'environment.yaml')
        yaml_data = {'tc_region': self.tcregion,
                     'vlan66': '10.11.12.0/24',
                     'vlan67': '10.12.14.128/25',
                     }
        self.write_file(output_file, yaml_data)
        output_path = os.path.join(env_path, self.env, 'hosts.d')
        os.makedirs(output_path)
        for i in range(1, 21):
            hostname = str(self.tcregion + '-fake-vm-' + str(i).zfill(3) + '.yaml')
            output_file = os.path.join(output_path, hostname)
            yaml_data = {
                'interfaces': {
                    'eth0': {
                        'ip_address': str(self.subnet.network_address + 4 + i),
                    },
                },
                'type': 'virtual',
            }
            self.write_file(output_file, yaml_data)

    def test_tc_vm_yaml_create(self):
        """
        Tests the create of the host yaml file within the supplied site / env
        """
        tc_vm_yaml_create.create_vm(self.ccsdatapath, self.hostname1, self.site, self.env,
                                    self.flavor, self.vlanid, self.role, self.groups,
                                    self.secgroups, self.ip1)
        tc_vm_yaml_create.create_vm(self.ccsdatapath, self.hostname2, self.site, self.env,
                                    self.flavor, self.vlanid, self.role, self.groups,
                                    self.secgroups, self.ip2)
        self.assertTrue(os.path.isfile(self.filename1))
        self.assertTrue(os.path.isfile(self.filename2))
        self.ctx.logger.debug('Expected files were found')
        with open(self.filename1, 'r') as yaml_file:
            yaml_data = yaml.load(yaml_file)
            ipaddr = str(self.subnet.network_address + 25)
        self.assertTrue(yaml_data['interfaces']['eth0']['ip_address'] == ipaddr)
        with open(self.filename2, 'r') as yaml_file:
            yaml_data = yaml.load(yaml_file)
        self.assertTrue(yaml_data['interfaces']['eth0']['ip_address'] == self.ip2)
        self.ctx.logger.debug('Expected IPs were found')

    def tearDown(self):
        shutil.rmtree(self.ccsdatapath)


if __name__ == '__main__':
    unittest.main()
