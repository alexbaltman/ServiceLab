import os
import yaml
import shutil
import unittest
import tempfile

from tests.helpers import temporary_dir
from servicelab.stack import Context
from servicelab.utils import vagrantfile_utils


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
                           "{name: 'SLAB_test_lab', address: '192.168.100.6'}]"
        self.noaddr_nets = "[{name: 'SLAB_test_mgmt'}," + \
                           "{name: 'SLAB_test_lab', address: "
        self.yaml_nested_path = 'services/ccs-data/sites/ccs-dev-1/environments/' + \
                                'dev-tenant/hosts.d/'
        self.test_yaml_dir = os.path.join(self.host_var_tempdir, self.yaml_nested_path)
        self.vagrant_file = os.path.join(self.host_var_tempdir, 'Vagrantfile')
        self.vf_utils = vagrantfile_utils.SlabVagrantfile(self.host_var_tempdir)
        os.makedirs(self.test_yaml_dir)
        self.vagrant_data = """\
# -*- mode: ruby -*-
# vi: set ft=ruby :
VAGRANTFILE_API_VERSION = "2"
required_plugins = %w( vagrant-hostmanager vagrant-openstack-provider )
required_plugins.each do |plugin|
  system "vagrant plugin install #{plugin}" unless
Vagrant.has_plugin? plugin
end

#---------------- Setup to pass the envirionment variable -------------------

def get_rcmd(rcmd, variable)
  if ENV[variable]
    if rcmd
      rcmd << "
"
    end
    value = ENV[variable]
    rcmd = rcmd + "export #{variable}=#{value}"
  end
  return rcmd
end

def get_rcmdlst(rcmd)
  env_var_cmd = ""
  if rcmd
    env_var_cmd = <<CMD
echo "#{rcmd}" | tee -a /home/vagrant/.bash_profile
CMD
  end
  return env_var_cmd
end

remote_cmd = ""
remote_cmd = get_rcmd(remote_cmd, 'HEIGHLINER_DEPLOY_TARGET_HOSTS')
remote_cmd = get_rcmd(remote_cmd, 'HEIGHLINER_DEPLOY_TAGS')
remote_cmd = get_rcmd(remote_cmd, 'CCS_ENVIRONMENT')
env_var_cmd = get_rcmdlst(remote_cmd)

heighliner_script = <<SCRIPT
#{env_var_cmd}
SCRIPT
#---------------- END -------------------------------------------------------
Vagrant.configure(VAGRANTFILE_API_VERSION) do |cluster|
"""

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
                           '  config.vm.provision:shell, :inline => heighliner_script\n'
                           '  config.vm.provision "shell", path: "provision/node.sh"\n'
                           '  config.vm.provision "file", source: "provision/ssh-config",'
                           'destination:"/home/vagrant/.ssh/config"\n'
                           '  config.vm.provision "file", source: "hosts", destination: '
                           '"/etc/hosts"\n'
                           '  config.vm.synced_folder "services", "/opt/ccs/services"\n'
                           'end\nend\n'
                           )
        with open(self.vagrant_file, 'w') as f:
            f.write(self.vagrant_data)
            f.write('\n')
        self.vf_utils.add_virtualbox_vm(self.host_dict)
        with open(self.vagrant_file, 'r') as f:
            file_data = f.read()
        self.assertEqual(file_data, compare_data)

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
        self.vf_utils.set_env_vars(self.float_net, self.networks, sec_groups)
        self.vf_utils.add_openstack_vm(self.host_dict)
        with open(self.vagrant_file, 'r') as f:
            file_data = f.read()
        self.assertEqual(file_data, compare_data)

    def test_env_vars_settings(self):
        """
        Test the set_env_vars method
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
        self.vf_utils.set_env_vars(self.float_net, self.networks, sec_groups)
        self.assertEqual(self.vf_utils.env_vars, compare_data)

    def test_multiple_networks_data(self):
        """
        Test the get_multiple_networks method
        """
        net = self.vf_utils.get_multiple_networks(self.networks)
        self.assertEqual(net, self.noaddr_nets)

    def test_securitygroups_namelst_fetch(self):
        """
        Test the get_securitygroups_namelst method
        """
        compare_data = "[{name: 'default'},{name: 'something'},{name: 'myfancysecgroup'}]"
        sec_groups = [{'name': 'default',
                       'something': 'stuff'},
                      {'name': 'something'},
                      {'name': 'myfancysecgroup'}
                      ]
        parsed_groups = self.vf_utils.get_securitygroups_namelst(sec_groups)
        self.assertEqual(parsed_groups, compare_data)

    def test_host_image_flavors_setting(self):
        """
        Test the set_host_image_flavors method
        """
        compare_data = {'image': 'slab-RHEL7.1v9', 'flavor': '2cpu.4ram.20sas'}
        self.vf_utils.hostname = self.test_host
        self.vf_utils.set_host_image_flavors(self.ctx.path)
        self.assertEqual(self.vf_utils.host_vars, compare_data)


if __name__ == '__main__':
    unittest.main()
