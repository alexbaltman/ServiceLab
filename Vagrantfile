# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

required_plugins = %w( vagrant-hostmanager )
required_plugins.each do |plugin|
  system "vagrant plugin install #{plugin}" unless Vagrant.has_plugin? plugin
end

service = 'dev'
if File.exist?('.stack/current')
  service = IO.read('.stack/current').strip
else
  raise 'No service configured. Run `./stack workon [service]`'
end

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.define "infra-001" do |node|
    node.vm.box = "http://cis-kickstart.cisco.com/ccs-rhel-7.box"
    node.vm.network :private_network, :ip => '192.168.78.10'
    node.vm.provision :hosts
    node.vm.provision "shell", path: ".stack/provision/infra.sh"
    node.vm.provision :file, source: ".stack/provision/ssh-config", destination: "/home/vagrant/.ssh/config"
    node.vm.provision :file, source: ".stack/id_rsa", destination: "/home/vagrant/.ssh/id_rsa"
    node.vm.provision :file, source: ".stack/hosts", destination: "/etc/ansible/hosts"
    node.vm.synced_folder "services", "/opt/ccs/services"
    node.vm.synced_folder ".stack/ccs-data/out/ccs-dev-1/dev/etc/ansible/group_vars", "/etc/ansible/group_vars"
  end

  (1..3).each do |count|
    config.vm.define "vm-00#{count}" do |node|
      node.vm.box = "http://cis-kickstart.cisco.com/ccs-rhel-7.box"
      node.vm.network :private_network, :ip => "192.168.78.10#{count}"
      node.vm.provision :hosts
      node.vm.provision "shell", path: ".stack/provision/node.sh"
      node.vm.synced_folder "services", "/opt/ccs/services"
    end
  end
end
