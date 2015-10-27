import os
import yaml
import shutil
import unittest
import tempfile

from tests.helpers import temporary_dir
from servicelab.stack import Context
from servicelab.utils import Vagrantfile_utils


class TestVagrantFileUtils(unittest.TestCase):
    """
    TestVagrantFileUtils class is a unittest class for vagrantfile_utils.
    Attributes:

    """
    ctx = Context()
    host_var_tempdir = tempfile.mkdtemp()

    def setUp(self):
        """ Setup variables required to test the os_provider functions
        """
        self.box = 'http://cis-kickstart.cisco.com/ccs-rhel-7.box'
        self.float_net = 'public-floating-602'
        self.networks = [{'name': 'SLAB_test_mgmt'},
                         {'name': 'SLAB_test_lab'}]
        self.parsed_nets = "[{name: 'SLAB_test_mgmt'}," + \
                           "{name: 'SLAB_test_lab', address: 192.168.100.6}]"
        self.noaddr_nets = "[{name: 'SLAB_test_mgmt'}," + \
                           "{name: 'SLAB_test_lab', address: "
        self.yaml_nested_path = 'services/ccs-data/sites/ccs-dev-1/environments/' + \
                                'dev-tenant/hosts.d/'
        self.test_yaml_dir = os.path.join(self.host_var_tempdir, self.yaml_nested_path)
        self.vagrant_file = os.path.join(self.host_var_tempdir, 'Vagrantfile')
        self.vf_utils = Vagrantfile_utils.SlabVagrantfile(self.host_var_tempdir)
        os.makedirs(self.test_yaml_dir)
        self.vagrant_data = ("# -*- mode: ruby -*-\n# vi: set ft=ruby :\n"
                             "VAGRANTFILE_API_VERSION = \"2\"\n"
                             "required_plugins = %w( vagrant-hostmanager "
                             "vagrant-openstack-provider )\n"
                             "required_plugins.each do |plugin|\n"
                             "  system \"vagrant plugin install #{plugin}\" unless\n"
                             "Vagrant.has_plugin? plugin\nend\n"
                             "Vagrant.configure(VAGRANTFILE_API_VERSION) do |cluster|\n")
        self.vm_yaml_data = '''
            deploy_args:
                flavor: 4cpu.8ram.20-96sas
                image: RHEL-7
            groups:
            - virtual
            hostname: test_neutron_api.service.cloud.com
            role: tenant_neutron_api
            server: 10.10.10.10
            type: virtual '''
        self.test_host = 'test_host'
        self.test_yaml_file = os.path.join(self.test_yaml_dir, self.test_host+'.yaml')
        with open(self.test_yaml_file, 'w') as yaml:
            yaml.write(self.vm_yaml_data)
        self.host_vars = {'flavor': '4cpu.8ram.20-96sas', 'image': 'RHEL-7'}
        self.host_dict = {self.test_host: {'box': self.box,
                                           'domain': '1',
                                           'ip': '192.168.100.6',
                                           'mac': '020027000006',
                                           'memory': '1024',
                                           'profile': 'null',
                                           'role': 'none',
                                           }
                          }
        os.environ['OS_USERNAME'] = 'test_user'
        os.environ['OS_PASSWORD'] = 'test_pw'
        os.environ['OS_AUTH_URL'] = 'http://slab.cisco.com:5000/v2.0/'
        os.environ['OS_TENANT_NAME'] = 'dev-tenant'

    def tearDown(self):
        """ Tear down variables and files created to test the os_provider functions
        """
        shutil.rmtree(self.host_var_tempdir)
        os.environ['OS_USERNAME'] = ''
        os.environ['OS_PASSWORD'] = ''
        os.environ['OS_AUTH_URL'] = ''
        os.environ['OS_TENANT_NAME'] = ''

    def test_init_vagrantfile(self):
        """
        Tests the init_vagrantfile method
        """
        self.vf_utils.init_vagrantfile()
        with open(self.vagrant_file, 'r') as f:
            my_data = f.read()
        self.assertEqual(my_data, self.vagrant_data + '\n')
        self.ctx.logger.info('Vagrantfile init passed')

    def test_write_it(self):
        """
        Tests the write_it method
        """
        data_1 = 'first line\n'
        data_2 = 'second line\n'
        data_3 = 'another line\n'
        data_4 = 'I forgot where I was going with this\n'
        all_data = data_1 + data_2 + data_3 + data_4 + '\n'
        self.vf_utils.write_it(data_1, data_2, data_3, data_4)
        with open(self.vagrant_file, 'r') as f:
            my_data = f.read()
        self.assertEqual(my_data, all_data)
        self.ctx.logger.info('Write new Vagrantfile passed')

    def test_append_it(self):
        """
        Test the append_it method
        """
        data_1 = 'first new line\n'
        data_2 = 'second new line\n'
        data_3 = 'Do you see what I did there?\n'
        data_4 = 'Because I do not\n'
        all_data = self.vagrant_data + data_1 + data_2 + data_3 + data_4 + 'end\nend\n'
        with open(self.vagrant_file, 'w') as f:
            f.write(self.vagrant_data)
            f.write('\n')
        self.vf_utils.append_it(data_1, data_2, data_3, data_4)
        with open(self.vagrant_file, 'r') as f:
            my_data = f.read()
        self.assertEqual(my_data, all_data)
        self.ctx.logger.info('Append to Vagrantfile passed')

    def test_add_virtualbox_vm(self):
        """
        Test the add_virtualbox_vm method
        """
        compare_data = str(self.vagrant_data +
                           'cluster.vm.define \"' + self.test_host + '\" do |config|\n'
                           '  config.hostmanager.enabled = true\n'
                           '  config.hostmanager.include_offline = true\n'
                           '  config.vm.box = "' + self.box + '"\n'
                           '  config.vm.provider :virtualbox do |vb, override|\n'
                           '    vb.customize ["modifyvm", :id, "--memory", "1024"]\n'
                           '  end\n  config.vm.hostname = "test_host"\n'
                           '  config.vm.network :private_network, ip: "192.168.100.6", '
                           'mac: "020027000006"\n'
                           '  config.vm.provision "shell", path: "provision/infra.sh"\n'
                           '  config.vm.provision "shell", path: "provision/node.sh"\n'
                           '  config.vm.provision "file", source: "provision/ssh-config",'
                           'destination:"/home/vagrant/.ssh/config"\n'
                           '  config.vm.provision "file", source: "hosts", destination: '
                           '"/etc/hosts"\n'
                           '  config.vm.synced_folder "services", "/opt/ccs/services/"\n'
                           'end\nend\n'
                           )
        with open(self.vagrant_file, 'w') as f:
            f.write(self.vagrant_data)
            f.write('\n')
        self.vf_utils.add_virtualbox_vm(self.host_dict)
        with open(self.vagrant_file, 'r') as f:
            file_data = f.read()
        self.assertEqual(file_data, compare_data)
        self.ctx.logger.info('Add virtualbox vm to Vagrantfile passed')

    def test_add_openstack_vm(self):
        """
        Test the add_openstack_vm method
        """
        compare_data = ('cluster.vm.define "' + self.test_host + '" do |config|\n'
                        '  cluster.ssh.username = \'cloud-user\' \n'
                        '  config.hostmanager.enabled = true\n'
                        '  config.hostmanager.include_offline = true\n'
                        '  config.vm.provider :openstack do |os, override|\n'
                        '    os.openstack_auth_url   = "http://slab.cisco.com:5000/v2.0/"\n'
                        '    os.username             = "test_user"\n'
                        '    os.password             = "test_pw"\n'
                        '    os.tenant_name          = "dev-tenant"\n'
                        '    os.flavor               = "4cpu.8ram.20-96sas"\n'
                        '    os.image                = "RHEL-7"\n'
                        '    os.floating_ip_pool     = "public-floating-602"\n'
                        '    os.openstack_network_url= "http://slab.cisco.com:9696/v2.0"\n'
                        '    os.openstack_image_url  = "http://slab.cisco.com:9292/v2/"\n'
                        '    os.networks             = ' + self.parsed_nets + '\n'
                        '    os.security_groups      = [{name: \'default\'}]\n'
                        '    override.vm.box = "openstack"\n'
                        '  end\n'
                        '  config.vm.provision "shell", path: "provision/infra-OS.sh"\n'
                        '  config.vm.provision "shell", path: "provision/node-OS.sh"\n'
                        '  config.vm.provision "file", source: "provision/ssh-config", '
                        'destination:"/home/cloud-user/.ssh/config"\n'
                        '  config.vm.provision "file", source: "hosts", destination: '
                        '"/etc/hosts"\n'
                        '  config.vm.synced_folder "services", "/opt/ccs/services/"\n'
                        )
        compare_data = self.vagrant_data + compare_data + 'end\nend\n'
        with open(self.vagrant_file, 'w') as f:
            f.write(self.vagrant_data)
            f.write('end\n')
        sec_groups = [{'name': "default"}]
        self.vf_utils._vbox_os_provider_env_vars(self.float_net, self.networks, sec_groups)
        self.vf_utils.add_openstack_vm(self.host_dict)
        with open(self.vagrant_file, 'r') as f:
            file_data = f.read()
        self.assertEqual(file_data, compare_data)
        self.ctx.logger.info('Add openstack vm to Vagrantfile passed')

    def test_vbox_os_provider_env_vars(self):
        """
        Test the _vbox_os_provider_env_vars method
        """
        compare_data = {'username': 'test_user',
                        'openstack_auth_url': 'http://slab.cisco.com:5000/v2.0/',
                        'tenant_name': 'dev-tenant',
                        'floating_ip_pool': self.float_net,
                        'openstack_image_url': 'http://slab.cisco.com:9292/v2/',
                        'openstack_network_url': 'http://slab.cisco.com:9696/v2.0',
                        'password': 'test_pw',
                        'networks': self.noaddr_nets,
                        'security_groups': "[{name: 'default'}]"}
        sec_groups = [{'name': "default"}]
        self.vf_utils._vbox_os_provider_env_vars(self.float_net, self.networks, sec_groups)
        self.assertEqual(self.vf_utils.env_vars, compare_data)
        self.ctx.logger.info('Created env_vars with expected data')

    def test_vbox_os_provider_parse_multiple_networks(self):
        """
        Test the _vbox_os_provider_parse_multiple_networks method
        """
        net = self.vf_utils._vbox_os_provider_parse_multiple_networks(self.networks)
        self.assertEqual(net, self.noaddr_nets)
        self.ctx.logger.info('Tenant networks data parsed as expected')

    def test_vbox_os_provider_parse_security_groups(self):
        """
        Test the _vbox_os_provider_parse_security_groups method
        """
        compare_data = "[{name: 'default'},{name: 'something'},{name: 'myfancysecgroup'}]"
        sec_groups = [{'name': 'default',
                       'something': 'stuff'},
                      {'name': 'something'},
                      {'name': 'myfancysecgroup'}
                      ]
        parsed_groups = self.vf_utils._vbox_os_provider_parse_security_groups(sec_groups)
        self.assertEqual(parsed_groups, compare_data)
        self.ctx.logger.info('Security group data parsed as expected')

    def test_vbox_os_provider_host_vars(self):
        """
        Test the _vbox_os_provider_host_vars method
        """
        compare_data = {'image': 'slab-RHEL7.1v7', 'flavor': '2cpu.4ram.20sas'}
        self.vf_utils.hostname = self.test_host
        self.vf_utils._vbox_os_provider_host_vars(self.ctx.path)
        self.assertEqual(self.vf_utils.host_vars, compare_data)
        self.ctx.logger.info('Host variables parsed as expected')


if __name__ == '__main__':
    unittest.main()
