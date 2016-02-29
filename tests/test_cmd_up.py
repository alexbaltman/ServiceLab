import os
import yaml
import shutil
import unittest
import ipaddress

from click.testing import CliRunner
from servicelab.stack import Context
from servicelab.commands import cmd_up
from servicelab.commands import cmd_workon
from servicelab.utils import service_utils
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
        if not os.path.isdir(os.path.join(self.ctx.path, 'services', 'ccs-data')):
            service_utils.sync_service(self.ctx.path, 'master', self.ctx.username,
                                       'ccs-data')
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
        elif os.path.isfile(self.vagrant_yaml):
            os.remove(self.vagrant_yaml)
        if hasattr(self, 'Vagrant_bak'):
            os.rename(self.Vagrant_bak, self.Vagrant_file)
        elif os.path.isfile(self.Vagrant_file):
            os.remove(self.Vagrant_file)
        if os.path.isdir(self.dotvagrant_dir):
            shutil.rmtree(self.dotvagrant_dir)
        if hasattr(self, 'dotvagrant_bak'):
            os.rename(self.dotvagrant_bak, self.dotvagrant_dir)
        self.host = ''
        os.environ['OS_USERNAME'] = ''
        os.environ['OS_PASSWORD'] = ''
        os.environ['OS_REGION_NAME'] = ''
        os.environ['OS_AUTH_URL'] = ''
        os.environ['OS_TENANT_NAME'] = ''
        os.environ['OS_TENANT_ID'] = ''

    def cmd_up_runner(self, args, hostname, group, remote):
        """
        Run the 'stack up' command for each of the various tests

        Args:
            args {list}: CLI args
            hostname {str}: Name of the vm
            group {str}: Name of the group the vm belongs to
            remote {bool}: True - OpenStack hypervisor
                           False - VirtualBox hypervisor

        Returns:
            Nothing.  Runs tests based on the environment setup

        Example Usage:
            self.cmd_up_runner(['--rhel7'], 'rhel7-001', False)
        """
        if not group == 'rhel7':
            repo_name = str('service-' + group)
            if not os.path.isdir(os.path.join(self.ctx.path, 'services', repo_name)):
                service_utils.sync_service(
                    self.ctx.path,
                    'master',
                    self.ctx.username,
                    repo_name)
        runner = CliRunner()
        host_yaml = hostname + '.yaml'
        result = runner.invoke(cmd_up.cli, args)
        if result > 0:
            return
        vm_yaml_file = os.path.join(self.hosts_path, host_yaml)
        self.assertTrue(os.path.isfile(vm_yaml_file))
        with open(vm_yaml_file, 'r') as yaml_file:
            vm_yaml_data = yaml.load(yaml_file)
        self.assertEqual(vm_yaml_data['groups'][1], group)
        with open(self.vagrant_yaml, 'r') as vagrant_f:
            vagrant_data = yaml.load(vagrant_f)
        self.assertEqual(vm_yaml_data['interfaces']['eth0']['ip_address'],
                         vagrant_data['hosts'][hostname]['ip'],
                         '192.168.100.15')
        if remote:
            hypervisor = "OpenStack"
        else:
            hypervisor = "VirtualBox"
        ispoweron, isremote = vagrant_utils.vm_isrunning(hostname, self.ctx.path)
        if ispoweron > 1:
            print('Unable to contact %s for VM status' % hypervisor)
        elif ispoweron == 1:
            print('VM is offline in %s' % hypervisor)
        else:
            self.assertEqual(ispoweron, 0)
            self.assertEqual(isremote, remote)

    def destroy_vm(self, hostname):
        """
        Destroys vms based on the Vagrantfile data

        Args:
            hostname {str}: Name of the vm

        Returns:
            Nothing.  Destroys the VM within the hypervisor

        Example Usage:
            self.destroy_vm('rhel7-001')
        """
        my_vm_connection = vagrant_utils.Connect_to_vagrant(vm_name=hostname,
                                                            path=self.ctx.path)
        ispoweron, isremote = vagrant_utils.vm_isrunning(hostname, self.ctx.path)
        # ispoweron states:
        # 0 - VM is online
        # 1 - VM is offline
        # 2 - Vagrant command error, usually cannot find vm or contact hypervisor
        # 3 - Other errors
        if ispoweron == 0:
            my_vm_connection.v.destroy(vm_name=hostname)

    def test_local_rhel7(self):
        """
        Tests the 'stack up --rhel7' command
        """
        args = ['--rhel7']
        hostname = 'rhel7-001'
        group = 'rhel7'
        remote = False
        self.cmd_up_runner(args, hostname, group, remote)
        self.destroy_vm(hostname)

    def test_remote_rhel7(self):
        """
        Tests the 'stack up --rhel7 -r' command
        """
        args = ['--rhel7', '-r']
        hostname = 'rhel7-001'
        group = 'rhel7'
        remote = True
        self.cmd_up_runner(args, hostname, group, remote)
        self.destroy_vm(hostname)

    def test_local_service(self):
        """
        Tests the 'stack up -s <servicename>' command
        """
        args = ['-s', 'service-sonarqube']
        hostname = 'service-sonarqube-001'
        group = 'sonarqube'
        remote = False
        self.cmd_up_runner(args, hostname, group, remote)
        self.destroy_vm(hostname)
        self.destroy_vm('infra-001')

    def test_remote_service(self):
        """
        Tests the 'stack up -s <servicename> -r' comman
        """
        args = ['-s', 'service-sonarqube', '-r']
        hostname = 'service-sonarqube-001'
        group = 'sonarqube'
        remote = True
        self.cmd_up_runner(args, hostname, group, remote)
        self.destroy_vm(hostname)
        self.destroy_vm('infra-001')


if __name__ == '__main__':
    unittest.main()
