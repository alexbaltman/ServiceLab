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
    """Overwrites Vagrantfile

    The following attributes are written into/over the Vagrantfile:
        *header: version & mode
        *required ruby modules: listed in ruby_modules.yaml
        *required plugins: listed in vagrant_plugins.yaml
        *user & group: either vagrant or cloud-user (Vbox or OSP)
        *current services
        *command to load the hosts denoted in vagrant.yaml
        *VirtualBox provider Vagrantfile configuration

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.

    Returns:
        (int) The return code::
        0 -- Success
        1 -- Failure, caused by invalid or nonexistent yaml files

    Example Usage:
        >>> print overwrite_vagrantfile("/Users/aaltman/Git/servicelab/servicelab/.stack")
        0


    """
    Vfile = "Vagrantfile"
    with open(os.path.join(path, Vfile), 'w') as f:
        h1, h2, h3 = _set_vagrantfile_header()
        f.write(h1)
        f.write(h2)
        f.write(h3)
        returncode, ruby_modules = _required_ruby_modules(path)
        if returncode > 0:
            return 1
        else:
            f.write(ruby_modules)
        returncode, vagrant_plugins = _required_vagrant_plugins(path)
        if returncode > 0:
            return 1
        else:
            for i in vagrant_plugins:
                f.write(i)
        users = _set_vagrant_user_and_group()
        f.write(users)
        set_current_service = _set_current_service(path)
        f.write(set_current_service)
        load_vagrantyaml = _load_vagrantyaml(path)
        f.write(load_vagrantyaml)
        vbox_config = _vbox_provider_configure()
        f.write(vbox_config)


def _set_vagrantfile_header():
    """Sets the Vagrantfile header fields

    Returns:
        Returns three strings which define the Vagrantfile header:
            *h1, h2: sets mode in which vim editor opens Vagrantfile
            *h3: Vagrant API Version Number

    Example Usage:
        >>> print _set_vagrantfile_header()
        ("# -*- mode: ruby -*-", "# vi: set ft=ruby :", "VAGRANTFILE_API_VERSION = \"2\"")
    """
    h1 = "# -*- mode: ruby -*-\n"
    h2 = "# vi: set ft=ruby :\n"
    h3 = "VAGRANTFILE_API_VERSION = \"2\"\n"
    return h1, h2, h3


def _required_ruby_modules(path):
    """Compiles a list of the required ruby modules.

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.

    Returns:
        *(int) The return code::
        0 -- Success
        1 -- Failure, ruby_modules.yaml doesn't exist or improper syntax

        *s, a single string in the form:
            require 'a'
            require 'b'
            require 'c'
            ...
            ...
               where lowercase letters represent the required ruby modules defined in
               the ruby_modules.yaml in the ./servicelab/servicelab/.utils folder.

   Example Usage:
        >>> print _required_ruby_modules("/Users/aaltman/Git/servicelab/servicelab/.stack")
        (0, " require 'a.rb'\n require 'b.rb'\n require 'c.rb'\n ")
    """
    path_to_ruby_modules = os.path.join(path, "provision", "ruby_modules.yaml")
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
    """Compiles a list of the required Vagrant plugins.

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.

    Returns:
        *(int) The return code::
        0 -- Success
        1 -- Failure, vagrant_plugins.yaml doesn't exist or improper syntax

        *s, a list of four strings:
            *s   --  all required vagrant plugins separated by spaces
            *s2  --  the command to force install all plugins every time
            *s3  --  the command to install required plugins that don't exist
            *s4  --  constant string "end"

            The user will have two options to install the plugins, force install all, or
            just the ones needed.

    Example Usage:
        >>> print _required_vagrant_plugins("/Users/aaltman/Git/servicelab/
                                            servicelab/.stack")
        (0, "vagrant-hostmanager vagrant-openstack-plugin",
                    "required_plugins.each do |plugin|",
          " system \"vagrant plugin install #{plugin}\" unless Vagrant.has_plugin? plugin",
          "end")
    """
    path_to_vagrant_plugins = os.path.join(
        path, "provision", "vagrant_plugins.yaml")
    returncode = yaml_utils.validate_syntax(path_to_vagrant_plugins)
    if returncode == 0:
        stream = file(path_to_vagrant_plugins, 'r')
        vagrant_plugins = yaml.load(stream)
        vagrant_plugin_string = ""
        vagrant_plugin_string += " ".join(vagrant_plugins)
        # Note: We can either 1) force install plugins every time 2) place
        #       plugin requirements in vagrantfile for vagrant up to consume
        #       or check for vagrant plugins in local env and then do 1 or 2.

        s = "required_plugins = %w( " + vagrant_plugin_string + ")\n"
        # Note: in the vagrant file we need to do "something" in ruby with the
        # plugins
        s2 = "required_plugins.each do |plugin|\n"
        s3 = ("  system \"vagrant plugin install #{plugin}\" "
              "unless Vagrant.has_plugin? plugin\n")
        s4 = "end\n"
        all_strings = [s, s2, s3, s4]
        return 0, all_strings
    else:
        Vagrantfile_utils_logger.error("vagrant_plugins.yaml did not have valid\
                                        syntax.")

        return 1, all_strings


def _set_vagrant_user_and_group(user="vagrant", group="vagrant"):
    """Sets vagrant user and group

    Function used mainly to define either Virtualbox provisioning (vagrant user) or
    OpenStack Provider provisioning (cloud user)

    Args:
        user (str): Set to "vagrant" by default.
        group (str): Set to "vagrant" by default

    Returns:
        Returns a string in Ruby format that echoes the input user & group.

    Example Usage:
        >>> print _set_vagrant_user_and_group()
        $data = {:user => 'vagrant', :group => 'vagrant'}
    """
    s = "$data = {:user => '%s', :group => '%s'}\n" % (user, group)
    return s


def _set_current_service(path):
    """Returns string of current service.

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.

    Returns:
        Returns the name of the current service.

]   Example Usage:
        >>> print _set_current_service("/Users/aaltman/Git/servicelab/servicelab/.stack")
        dev

    """
    current_file = os.path.join(path, "current")
    f = open(current_file, 'r')
    # TODO: verify that current is set to something sane.
    current_service = f.readline()
    current_service = "service = '{0}'\n".format(current_service)
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


def _load_vagrantyaml(path):
    """Loads environment configuration

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.

    Returns:
        Returns a string with the command to load the vagrant.yaml file.

    Example Usage:
        >>> print _load_vagrantyaml("/Users/aaltman/Git/servicelab/servicelab/.stack")
        $envyaml = YAML::load_file("/Users/aaltman/Git/servicelab/servicelab/vagrant.yaml")
    """
    # Note: This should be the vagrant.yaml in the working directory
    vagrantyaml = os.path.join(path, "vagrant.yaml")
    s = "$envyaml = YAML::load_file('{0}')\n".format(vagrantyaml)
    return s
# Ruby: "$envyaml['hosts'].each do |name, h|"
# Ruby: File.open(".ccs_vagrant_hosts", "w") {|f|
# f.write(host_entries.join("\n")) }


def _vbox_os_provider_env_vars(float_net, tenant_nets):
    '''Function will accept a float_net string and a tenant_nets list of dicts.
        The dicts are of the format {'name':'network_name', 'ip':True}.
        The ip key will be true if vagrant.yaml has an ip for the host.
        It will return a dict with the OpenStack username, password,
        tenant_name, auth_url, network_url, image_url, floating_ip_pool and networks
        to be used for developing the Vagrant file'''
    env_vars = {}
    env_vars['username'] = os.environ.get('OS_USERNAME')
    env_vars['password'] = os.environ.get('OS_PASSWORD')
    env_vars['openstack_auth_url'] = os.environ.get('OS_AUTH_URL')
    env_vars['tenant_name'] = os.environ.get('OS_TENANT_NAME')
    env_vars['floating_ip_pool'] = str(float_net)
    networks = _vbox_os_provider_parse_multiple_networks(tenant_nets)
    env_vars['networks'] = networks
    openstack_network_url = None
    openstack_image_url = None
    if (env_vars.get('openstack_auth_url')):
        proto, baseurl, port = env_vars.get('openstack_auth_url').split(':')
        openstack_network_url = proto + ':' + baseurl + ":9696/v2.0"
        openstack_image_url = proto + ':' + baseurl + ":9292/v2/"
    env_vars['openstack_network_url'] = openstack_network_url
    env_vars['openstack_image_url'] = openstack_image_url
    return env_vars


def _vbox_os_provider_parse_multiple_networks(tenant_nets):
    '''Function accepts a list of dicts with each dict containing
       the tenant network name and a boolean to indicate if there is an ip in
       the vagrant.yaml. It will return a string of networks to be used in
       the construction of the Vagrantfile'''
    stl_without_ip = "{name: '%s'},"
    stl_with_ip = "{name: '%s', address: ho['ip']},"
    vagrant_network = ''
    for net in tenant_nets:
        if not net['ip']:
            vagrant_network = vagrant_network + stl_without_ip % net['name']
        if net['ip']:
            vagrant_network = vagrant_network + stl_with_ip % net['name']
    vagrant_network = '[' + vagrant_network[:-1] + ']'
    return vagrant_network


def _vbox_os_provider_host_vars(path, host):
    '''Function will except a path to the .stack directory and the host being
        booted. It will navigate to the ccs-devel directory, find the
        corresponding host.yaml file, parse it and return a dict with flavor,
        and image used for the host'''
    host_vars = {}
    relpath_to_yaml = 'services/ccs-data/sites/ccs-dev-1/environments/dev-tenant/hosts.d/'
    if (os.path.exists(path)):
        path = os.path.join(path, relpath_to_yaml)
        if (os.path.exists(path)):
            path = os.path.join(path, host.lower()+'.yaml')
            if os.path.exists(path):
                try:
                    with open(path) as host_yaml:
                        host_data = yaml.load(host_yaml)
                        host_vars['image'] = host_data.get('deploy_args').get('image')
                        host_vars['flavor'] = host_data.get('deploy_args').get('flavor')
                        return host_vars
                except:
                    return None


def _vbox_provider_configure():
    """Returns configuration for Vagrantfile with the VirtualBox provider

    Returns:
        Returns a single string outlining configuration specs that are applied to every host
        The string is a concatenation of four:
            *s    --  initial configuration: sets up box
            *net  --  private networking configuration: sets up shared folders, port
                      forwarding
            *hw   --  hardware configuration: sets up hardware specs of VBox
            *p    --  provisioning configuration: provisioner shell scripts to run ansible
                      playbooks on VMs

    Example Usage:
        >>> print _vbox_provider_configure()
        --see code for outputted string--
    """
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
           "      h.vm.host_name = \"#{name}.cis.local\"\n"
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
    p = ("      if name == 'infra-001' or name == 'infra-002'\n"
         "        config.vm.define 'infra-001' do |node|\n"
         "          h.vm.provision :shell, inline: \"echo role=#{ho['role']} > "
         "/etc/facter/facts.d/role.txt\"\n"
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
         "      else\n"
         "        h.vm.provision :shell, path: './provision/node.sh'\n"
         "        h.vm.provision :shell, inline: \"ansible-playbook /opt/ccs/"
         "services/redhouse-svc/dev/provision.yml -e"
         " hostname=#{name}.cis.local\"\n"
         "      end\n"
         "    end\n"
         "  end\n\n"
         "end"
         )

    return s + net + hw + p
