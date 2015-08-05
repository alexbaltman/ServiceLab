from servicelab.utils import yaml_utils
import logging
import yaml
import os

# create logger
# TODO: For now warning and error print. Got to figure out how
#       to import the one in stack.py properly.
Vagrantfile_utils_logger = logging.getLogger('click_application')
logging.basicConfig()


def overwrite_vagrantfile(path):
    Vfile = "Vagrantfile"
    with open(os.path.join(path, Vfile), 'w') as f:
        h1, h2, h3 = _set_vagrantfile_header()
        f.write(h1)
        f.write(h2)
        f.write(h3)
        f.write("\n")
        returncode, ruby_modules = _required_ruby_modules(path)
        if returncode > 0:
            return 1
        else:
            f.write(ruby_modules)
        returncode, vagrant_plugins = _required_vagrant_plugins(path)
        if returncode > 0:
            return 1
        else:
            f.write(str(vagrant_plugins))
        users = _set_vagrant_user_and_group()
        f.write(users)
        set_current_service = _set_current_service(path)
        for item in set_current_service:
            f.write(item)
        load_vagrantyaml = _load_vagrantyaml(path)
        f.write(load_vagrantyaml)
        vbox_config = _vbox_provider_configure()
        f.write(vbox_config)


def _set_vagrantfile_header():
    h1 = "# -*- mode: ruby -*-"
    h2 = "# vi: set ft=ruby :"
    h3 = "VAGRANTFILE_API_VERSION = \"2\""
    return h1, h2, h3


def _required_ruby_modules(path):
    path_to_utils = os.path.join(path, "utils")
    path_to_ruby_modules = os.path.join(path_to_utils, "ruby_modules.yaml")
    returncode = yaml_utils.validate_syntax(path_to_ruby_modules)
    s = ""
    if returncode == 0:
        stream = file(path_to_ruby_modules, 'r')
        ruby_modules = yaml.load(stream)
        for item in ruby_modules:
            s += "require \'" + item + "\'\n"
        return 0, s
    else:
        Vagrantfile_utils_logger.error("ruby_modules.yaml did not have valid\
                                        syntax.")
        return 1, s


def _required_vagrant_plugins(path):
    path_to_utils = os.path.join(path, "utils")
    path_to_vagrant_plugins = os.path.join(
        path_to_utils, "vagrant_plugins.yaml")
    returncode = yaml_utils.validate_syntax(path_to_vagrant_plugins)
    if returncode == 0:
        stream = file(path_to_vagrant_plugins, 'r')
        vagrant_plugins = yaml.load(stream)
        vagrant_plugin_string = ""
        vagrant_plugin_string += " ".join(vagrant_plugins)
        # Note: We can either 1) force install plugins every time 2) place
        #       plugin requirements in vagrantfile for vagrant up to consume
        #       or check for vagrant plugins in local env and then do 1 or 2.

        s = "required_plugins = %w( " + vagrant_plugin_string + ")"
        # Note: in the vagrant file we need to do "something" in ruby with the
        # plugins
        s2 = "required_plugins.each do |plugin|"
        s3 = ("  system \"vagrant plugin install #{plugin}\" "
              "unless Vagrant.has_plugin? plugin")
        s4 = "end"
        all_strings = [s, s2, s3, s4]
        return 0, all_strings
    else:
        Vagrantfile_utils_logger.error("vagrant_plugins.yaml did not have valid\
                                        syntax.")

        return 1, all_strings


def _set_vagrant_user_and_group(user="vagrant", group="vagrant"):
    s = "$data = {:user => '%s', :group => '%s'}" % (user, group)
    return s


def _set_current_service(path):
    current_file = os.path.join(path, "current")
    f = open(current_file, 'r')
    # TODO: verify that current is set to something sane.
    current_service = f.readline()
    return current_service


# Ruby Yaml merge - allow settings to be set here? prob not,
# do in stack.py w/ configparser
# default_settings in yaml file:
# cache_packages: false
# puppet_mode: apply
# provision_on_boot: true
#
# $default_settings = YAML::load_file('.default_settings.yaml')
# if File.exists?('settings.yaml')
#   $user_settings = YAML::load_file('settings.yaml')
#   $settings = $default_settings.merge($user_settings)
# else
#   $settings = $default_settings
# end


# Load environment config
def _load_vagrantyaml(path):
    # Note: This should be the vagrant.yaml in the working directory
    vagrantyaml = os.path.join(path, "vagrant.yaml")
    s = "$envyaml = YAML::load_file('{0}')".format(vagrantyaml)
    return s
# Ruby: "$envyaml['hosts'].each do |name, h|"
# Ruby: File.open(".ccs_vagrant_hosts", "w") {|f|
# f.write(host_entries.join("\n")) }


def _vbox_provider_configure():

    # Init. Config.
    s = (
        "Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|\n\n"
        "  $envyaml['hosts'].each do |name, ho|\n"
        "    config.vm.define name.split('.')[0] do |h|\n"
        "      if ho['box']\n"
        "        h.vm.box = ho['box']\n"
        "      else\n"
        "        h.vm.box = 'ccs-rhel-7'\n"
        "        h.vm.box_url = "
        "'http://cis-kickstart.cisco.com/ccs-rhel-7.box'\n"
        "      end\n\n")

    # Private Networking
    net = ("      h.vm.network 'private_network', "
           "ip: ho['ip'], mac: ho['mac']\n"
           "      h.vm.host_name = '#{name}.cis.local'\n"
           "      h.vm.synced_folder './services/ccs-data/out/ccs-dev-1"
           "/dev/etc/ccs/data/', '/etc/ccs/data/environments/dev'\n"
           "      h.vm.synced_folder './services/ccs-data/out/ccs-dev-1"
           "/dev/etc/puppet/data/hiera_data', '/etc/puppet/data/hiera_data'\n"
           "      h.vm.synced_folder './services/service-redhouse-svc', "
           "'/opt/ccs/services/redhouse-svc'\n"
           "      h.vm.synced_folder './services/service-redhouse-tenant', "
           "'/opt/ccs/services/redhouse-tenant'\n\n"

           "      if ho['ports']\n"
           "        ho['ports'].each do |port|\n"
           "          h.vm.network 'forwarded_port', guest: port['guest'], "
           "host: port['host']\n"
           "        end\n"
           "      end\n"
           )

    # Virtualbox Hardware
    hw = (
        "      h.vm.provider :virtualbox do |vb|\n"
        "        if ho['memory']\n"
        "          vb.customize ['modifyvm', :id, '--memory', "
        "ho['memory']]\n"
        "        end\n"
        "        vb.customize ['modifyvm', :id, '--usb', 'off']\n"
        "        if ho['storage_disks']\n"
        "          vb.customize ['storagectl', :id, '--name', "
        "'SATA Controller', '--add', 'sata']\n"
        "          disk_port_num = 2\n"
        "          ho['storage_disks'].each do |sd|\n"
        "            disk_port_num += 1\n"
        "            file_to_disk = '#{name}-disk-#{sd}'\n"
        "            unless File.exist?(file_to_disk)\n"
        "              vb.customize ['createhd', '--filename', file_to_disk, "
        "'--size', 102400]\n"
        "            end\n"
        "            vb.customize ['storageattach', :id, '--storagectl', "
        "'SATA Controller', '--port', disk_port_num, '--device', 0, "
        "'--type', 'hdd', '--medium', 'file_to_disk' + '.vdi']\n"
        "         end\n"
        "       end\n"
        "     end\n")

    # Provision
    p = ("h.vm.provision :shell, inline: echo 'role=#{ho['role']} > "
         "/etc/facter/facts.d/role.txt'\n"
         "      if name = 'infra-001' or name = 'infra-002'\n"
         "        config.vm.define 'infra-001' do |node|\n"
         "          h.vm.provision :hostmanager\n"
         "          h.vm.provision :file, source: './provision/ssh-config', "
         "destination: '/home/vagrant/.ssh/config'\n"
         "          h.vm.provision :file, source: './id_rsa', destination: "
         "'/home/vagrant/.ssh/id_rsa'\n"
         "          h.vm.provision :file, source: './hosts', destination: "
         "'/etc/ansible/hosts'\n"
         "          h.vm.synced_folder './services', '/opt/ccs/services'\n"
         "          h.vm.provision 'shell', path: './provision/infra.sh'\n"
         # There is no out ansible group_vars
         # h.vm.synced_folder './services/ccs-data/out/ccs-dev-1/dev/etc/ \
         # ansible/group_vars', '/etc/ansible/group_vars'
         "        end\n"
         "      else:\n"
         "        h.vm.provision :shell, path: './provision/node.sh'\n"
         "        h.vm.provision :shell, inline: 'ansible-playbook /opt/ccs/"
         "services/redhouse-svc/dev/provision.yml -e"
         " hostname=#{name}.cis.local'\n"
         "      end\n"
         "    end\n"
         "  end\n\n"
         "end"
         )

    return s + net + hw + p
