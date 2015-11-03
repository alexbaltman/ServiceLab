import os
import yaml
import shutil
import unittest
import ipaddress

from click.testing import CliRunner
from servicelab.stack import Context
from servicelab.commands import cmd_up
from servicelab.utils import vagrant_utils


class TestStackUp(unittest.TestCase):
    """
    TestStackUp class is a unittest class for testing the 'stack up' commands
    """
    ctx = Context()

    def setUp(self):
        """
        Build site data needed to test both vagrant.yaml and vm host.yaml creation
        """
        self.site = 'ccs-dev-1'
        self.tenant = 'dev-tenant'
        self.hosts_path = os.path.join(self.ctx.path, 'services', 'ccs-data', 'sites',
                                       self.site, 'environments', self.tenant, 'hosts.d')
        self.subnet = '192.168.100.0/24'
        self.addr_subnet = ipaddress.IPv4Network(unicode(self.subnet))
        os.environ['OS_USERNAME'] = 'jenkins-test'
        os.environ['OS_PASSWORD'] = 'Cisco12345'
        os.environ['OS_REGION_NAME'] = 'us-rdu-3'
        os.environ['OS_AUTH_URL'] = 'https://us-rdu-3.cisco.com:5000/v2.0/'
        os.environ['OS_TENANT_NAME'] = 'jenkins-slab'
        os.environ['OS_TENANT_ID'] = 'dc4b64c3ddcc4ce5abbddd43a24b1b0a'
        # Preserve existing data
        self.vagrant_yaml = os.path.join(self.ctx.path, 'vagrant.yaml')
        if os.path.isfile(self.vagrant_yaml):
            self.vagrant_bak = os.path.join(self.ctx.path, 'vagrant.bak')
            os.rename(self.vagrant_yaml, self.vagrant_bak)
        self.Vagrant_file = os.path.join(self.ctx.path, 'Vagrantfile')
        if os.path.isfile(self.Vagrant_file):
            self.Vagrant_bak = os.path.join(self.ctx.path, 'Vagrantfile.bak')
            os.rename(self.Vagrant_file, self.Vagrant_bak)
        self.dotvagrant_dir = os.path.join(self.ctx.path, '.vagrant')
        if os.path.isdir(self.dotvagrant_dir):
            self.dotvagrant_bak = os.path.join(self.ctx.path, '.vagrant_bak')
            os.rename(self.dotvagrant_dir, self.dotvagrant_bak)
        env_path = os.path.join(self.ctx.path, 'services', 'ccs-data', 'sites', self.site,
                                'environments', self.tenant)
        self.hosts_path = os.path.join(env_path, 'hosts.d')
        self.backup_path = os.path.join(env_path, 'hosts.bak')
        os.makedirs(self.backup_path)
        for f in os.listdir(self.hosts_path):
            file_name = os.path.join(self.hosts_path, f)
            file_bak = os.path.join(self.backup_path, f)
            os.rename(file_name, file_bak)
        # Generate files to consume IPs .5 - .14
        for i in range(1, 11):
            hostname = 'service-holder-' + str(i).zfill(3) + '.yaml'
            output_file = os.path.join(self.hosts_path, hostname)
            file_data = {
                'interfaces': {
                    'eth0': {
                        'ip_address': str(self.addr_subnet.network_address + 4 + i),
                    },
                },
            }
            with open(output_file, 'w') as outfile:
                outfile.write(yaml.dump(file_data, default_flow_style=False))

    def tearDown(self):
        """
        Remove the temp directory and files
        """
        my_vm_connection = vagrant_utils.Connect_to_vagrant(vm_name='rhel7-001',
                                                            path=self.ctx.path)
        ispoweron, isremote = vagrant_utils.vm_isrunning('rhel7-001', self.ctx.path)
        if ispoweron == 0:
            my_vm_connection.v.destroy(vm_name='rhel7-001')
        for f in os.listdir(self.hosts_path):
            file_name = os.path.join(self.hosts_path, f)
            os.remove(file_name)
        for f in os.listdir(self.backup_path):
            file_bak = os.path.join(self.backup_path, f)
            file_name = os.path.join(self.hosts_path, f)
            os.rename(file_bak, file_name)
        shutil.rmtree(self.backup_path)
        if hasattr(self, 'vagrant_bak'):
            os.rename(self.vagrant_bak, self.vagrant_yaml)
        else:
            os.remove(self.vagrant_yaml)
        if hasattr(self, 'Vagrant_bak'):
            os.rename(self.Vagrant_bak, self.Vagrant_file)
        else:
            os.remove(self.Vagrant_file)
        shutil.rmtree(self.dotvagrant_dir)
        if hasattr(self, 'dotvagrant_bak'):
            os.rename(self.dotvagrant_bak, self.dotvagrant_dir)
        os.environ['OS_USERNAME'] = ''
        os.environ['OS_PASSWORD'] = ''
        os.environ['OS_REGION_NAME'] = ''
        os.environ['OS_AUTH_URL'] = ''
        os.environ['OS_TENANT_NAME'] = ''
        os.environ['OS_TENANT_ID'] = ''

    def test_cmd_up_local_rhel7(self):
        """
        Tests the 'stack up --rhel7' command
        """
        runner = CliRunner()
        result = runner.invoke(cmd_up.cli, ['--rhel7'])
        rhel_vm_file = os.path.join(self.hosts_path, 'rhel7-001.yaml')
        self.assertTrue(os.path.isfile(rhel_vm_file))
        self.ctx.logger.info('rhel7-001.yaml was found in dev-tenant-1/hosts.d')
        with open(rhel_vm_file, 'r') as vm_file:
            rhel_yaml = yaml.load(vm_file)
        self.assertEqual(rhel_yaml['groups'][1], 'rhel7')
        self.ctx.logger.info('Rhel7 VM group is rhel7 as expected')
        with open(self.vagrant_yaml, 'r') as vagrant_f:
            vagrant_yaml = yaml.load(vagrant_f)
        self.assertEqual(rhel_yaml['interfaces']['eth0']['ip_address'],
                         vagrant_yaml['hosts']['rhel7-001']['ip'])
        self.ctx.logger.info('rhel7-001.yaml and vagrant.yaml have the same IP')

    def test_cmd_up_remote_rhel7(self):
        """
        Tests the 'stack up --rhel7 -r' command
        """
        runner = CliRunner()
        result = runner.invoke(cmd_up.cli, ['--rhel7', '-r'])
        rhel_vm_file = os.path.join(self.hosts_path, 'rhel7-001.yaml')
        self.assertTrue(os.path.isfile(rhel_vm_file))
        self.ctx.logger.info('rhel7-001.yaml was found in dev-tenant-1/hosts.d')
        with open(rhel_vm_file, 'r') as vm_file:
            rhel_yaml = yaml.load(vm_file)
        self.assertEqual(rhel_yaml['groups'][1], 'rhel7')
        self.ctx.logger.info('Rhel7 VM group is %s as expected' % rhel_yaml['groups'][1])
        with open(self.vagrant_yaml, 'r') as vagrant_f:
            vagrant_yaml = yaml.load(vagrant_f)
        self.assertEqual(rhel_yaml['interfaces']['eth0']['ip_address'],
                         vagrant_yaml['hosts']['rhel7-001']['ip'],
                         '192.168.100.15')
        self.ctx.logger.info('rhel7-001.yaml and vagrant.yaml have the same IP')
        ispoweron, isremote = vagrant_utils.vm_isrunning('rhel7-001', self.ctx.path)
        if ispoweron > 1:
            self.ctx.logger.info('Unable to contact Openstack provider for VM status')
        else:
            self.assertEqual(ispoweron, 0)
            self.ctx.logger.info('VM is running')
            self.assertEqual(isremote, True)
            self.ctx.logger.info('VM is remotely installed')


if __name__ == '__main__':
    unittest.main()
