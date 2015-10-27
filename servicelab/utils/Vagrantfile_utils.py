import logging
import yaml
import os

# create logger
# TODO: For now warning and error print. Got to figure out how
#       to import the one in stack.py properly.
Vagrantfile_utils_logger = logging.getLogger('click_application')
logging.basicConfig()


class SlabVagrantfile(object):
    """
    Create and append data to Vagrantfile

    Args:
        path {str}: Path to write or append Vagrantfile

    Returns:
        Varies per method.  See method docstrings for details

    Example Usage:
        from servicelab.utils import Vagrantfile_utils
        my_class_var = Vagrantfile_utils.SlabVagrantfile('/path/to/use/for/vagrant/')
        my_class_var.<method_name>(args)
    """

    def __init__(self, path):
        self.path = path
        self.set_header = False
        # OS RC file vars
        self.env_vars = {}
        # passed in from yaml_utils calls
        self.host_dict = {}
        # ccs-data flavor image settings
        self.host_vars = {}
        self.default_flavor = '2cpu.4ram.20sas'
        self.default_image = 'slab-RHEL7.1v7'

    def init_vagrantfile(self):
        """
        Creates a new Vagrantfile with the needed header information

        Args:
            None

        Returns:
            Nothing, instead a Vagrantfile is written to the class.path directory

        Example Usage:
            my_class_var.init_vagrantfile()
        """

        def _set_header():
            """
            Creates the standard headers for Vagrantfile

            Args:
                None

            Returns:
                h1 {str}:  Always the same data
                h2 {str}:  Always the same data
                req_plugin {str}:  Always the same data

            Example Usage:
                h1, h2, req_plugin = _set_header()
            """
            h1 = ("# -*- mode: ruby -*-\n"
                  "# vi: set ft=ruby :\n")
            h2 = "VAGRANTFILE_API_VERSION = \"2\"\n"
            req_plugin = ("required_plugins = %w( vagrant-hostmanager ",
                          "vagrant-openstack-provider )\n",
                          "required_plugins.each do |plugin|\n",
                          "  system \"vagrant plugin install #{plugin}\" unless\n",
                          "Vagrant.has_plugin? plugin\n",
                          "end\n")

            return h1, h2, req_plugin

        def _beg_vm_config():
            """
            Creates vm start data for Vagrantfile

            Args:
                None

            Returns:
                startvms {str}:  Always the same data

            Example Usage:
                startvms = _beg_vm_config()
            """
            startvms = "Vagrant.configure(VAGRANTFILE_API_VERSION) do |cluster|\n"
            return startvms

        h1, h2, req_plugin = _set_header()
        startvms = _beg_vm_config()
        # Note: until write_it is fixed, have to move list out from middle
        self.write_it(h1, h2, req_plugin, startvms)
        self.set_header = True

    def write_it(self, *text):
        """
        Writes a new Vagrantfile to the class.path directory

        Args:
            Any number of inputs

        Returns:
            Nothing, instead a Vagrantfile is created in the class.path directory

        Example Usage:
            my_class_var.write_it(text_var_1, text_var_2, ... text_var_n)
        """
        # Note: Doesn't close the vagrant loop w/ an 'end'. Use append_it for that.
        mystr = ''
        with open(os.path.join(self.path, "Vagrantfile"), 'w') as f:
            for i in text:
                if isinstance(i, (list, tuple)):
                    for x in i:
                        mystr += x
                else:
                    mystr += i
            f.write(mystr)
            # Note: This buffers us from append_it function
            f.write("\n")

    def append_it(self, *text):
        """
        Appends data to the class.path Vagrantfile

        Args:
            Any number of inputs

        Returns:
            Nothing, instead the class.path Vagrantfile is appended with the provided data

        Example Usage:
            my_class_var.append_it(text_var_1, text_var_2, ... text_var_n)
        """
        lines = ''
        with open(os.path.join(self.path, "Vagrantfile"), 'r') as f:
            lines = f.readlines()
            # Note: Remove the last line always so we get rid of the 'end' and
            #       add our own.
            lines = lines[:-1]
        with open(os.path.join(self.path, "Vagrantfile"), 'w') as f:
            for line in lines:
                f.write(line)
            for i in text:
                try:
                    f.write(text)
                except TypeError:
                    for x in i:
                        f.write(x)
            f.write('end\n')
            f.write('end')
            f.write('\n')

    def add_virtualbox_vm(self, host_dict):
        """
        Adds a virtual box to Vagrantfile

        Args:
            host_dict {dict}: Nested dict built from yaml_utils.gethost_byname
                {'hostname': {'box': 'http://cis-kickstart.cisco.com/ccs-rhel-7.box',
                              'profile': 'null',
                              'domain': '1',
                              'ip': '192.168.100.6',
                              'mac': '020027000006',
                              'role': 'none',
                              'memory': '1024'
                              }
                 }

        Returns:
            0 or 1 for success or failure.  Also calls append_it to add data to Vagrantfile

        Example Usage:
            return_code = my_class_var.add_openstack_vm(host_dict)
        """
        setitup = ''
        self.host_dict = host_dict
        self.hostname = self.host_dict.keys()[0]
        ip = self.host_dict[self.hostname]['ip']
        try:
            setitup = ("cluster.vm.define \"" + self.hostname + "\" do |config|\n"
                       "  config.hostmanager.enabled = true\n"
                       "  config.hostmanager.include_offline = true\n"
                       "  config.vm.box = \"" + self.host_dict[self.hostname]['box'] + "\"\n"
                       "  config.vm.provider :virtualbox do |vb, override|\n")

            for k, v in host_dict[self.hostname].iteritems():
                # TODO: incorporate the storage and storage controller here too.
                if k in ['memory', 'cpus']:
                    try:
                        setitup += ("    vb.customize [\"modifyvm\", :id, \"--{0}\", \"" +
                                    str(v) + "\"]\n").format(k)
                    except KeyError as e:
                        Vagrantfile_utils_logger.debug('Non-fatal - may not be set')
                        Vagrantfile_utils_logger.debug('Failed to set vm attribute: ' + e)
            setitup += '  end\n'
            setitup += "  config.vm.hostname = \"" + self.hostname + "\"\n"
            try:
                setitup += "  config.vm.network :private_network, ip: \"" + ip
                setitup += "\", mac: \"" + host_dict[self.hostname]['mac'] + "\"\n"
            except KeyError:
                setitup += "  config.vm.network :private_network, ip: \"" + ip + "\"\n"
            setitup += "  config.vm.provision \"shell\", path: \"provision/infra.sh\"\n"
            setitup += "  config.vm.provision \"shell\", path: \"provision/node.sh\"\n"
            setitup += ("  config.vm.provision \"file\", source: " +
                        "\"provision/ssh-config\"," +
                        "destination:\"/home/vagrant/.ssh/config\"\n")
            setitup += ("  config.vm.provision \"file\", source: \"hosts\", " +
                        "destination: \"/etc/hosts\"\n")
            setitup += ("  config.vm.synced_folder \"services\", " +
                        "\"/opt/ccs/services/\"\n")
            self.append_it(setitup)
            return 0
        except KeyError:
            Vagrantfile_utils_logger.error('Can not add host b/c of missing Key')
            return 1

    def add_openstack_vm(self, host_dict):
        """
        Adds an Openstack VM to the Vagrantfile

        Args:
            self.env_vars {dict}: Built by _vbox_os_provider_env_vars
                {'username': 'test_user',
                 'openstack_auth_url': 'http://slab.cisco.com:5000/v2.0/',
                 'tenant_name': 'dev-tenant',
                 'floating_ip_pool': 'public-floating-602',
                 'openstack_image_url': 'http://slab.cisco.com:9292/v2/',
                 'openstack_network_url': 'http://slab.cisco.com:9696/v2.0',
                 'password': 'test_pw',
                 'networks': "[{name: 'test_management'}," + \
                             "{name: 'test_dual_home', address: ho['ip']}]",
                 'security_groups': "[{name: 'default'}]"
                 }
            host_dict {dict}: Nested dict built from yaml_utils.gethost_byname
                {'hostname': {'box': 'http://cis-kickstart.cisco.com/ccs-rhel-7.box',
                              'profile': 'null',
                              'domain': '1',
                              'ip': '192.168.100.6',
                              'mac': '020027000006',
                              'role': 'none',
                              'memory': '1024'
                              }
                 }

        Returns:
            Nothing, appends the VM data to the class.path Vagrantfile

        Example Usage:
            my_class_var.add_openstack_vm(host_dict)
        """
        self.host_dict = host_dict
        self.hostname = self.host_dict.keys()[0]
        env_vars = self.env_vars
        self._vbox_os_provider_host_vars(self.path)
        setitup = ("cluster.vm.define \"" + self.hostname + "\" do |config|\n"
                   "  cluster.ssh.username = 'cloud-user' \n"
                   "  config.hostmanager.enabled = true\n"
                   "  config.hostmanager.include_offline = true\n"
                   "  config.vm.provider :openstack do |os, override|\n")

        setitup += ("    os.openstack_auth_url   = \"" + env_vars['openstack_auth_url'] +
                    "\"\n"
                    "    os.username             = \"" + env_vars['username'] + "\"\n"
                    "    os.password             = \"" + env_vars['password'] + "\"\n"
                    "    os.tenant_name          = \"" + env_vars['tenant_name'] + "\"\n")

        try:
            setitup += ("    os.flavor               = \"" + self.host_vars['flavor'] +
                        "\"\n"
                        "    os.image                = \"" + self.host_vars['image'] +
                        "\"\n")

        except KeyError:
            Vagrantfile_utils_logger.error('Could not set host flavor or img from\
                                            ccs-data')
        setitup += ("    os.floating_ip_pool     = \"" + env_vars['floating_ip_pool'] +
                    "\"\n"
                    "    os.openstack_network_url= \"" + env_vars['openstack_network_url'] +
                    "\"\n"
                    "    os.openstack_image_url  = \"" + env_vars['openstack_image_url'] +
                    "\"\n"
                    "    os.networks             = " + env_vars['networks'] +
                    "\n" + "    os.security_groups      = " +
                    ''.join(env_vars['security_groups']) + "\n"
                    "    override.vm.box = \"openstack\"\n"
                    "  end\n")
        setitup += ("  config.vm.provision \"shell\", path: \"provision/infra-OS.sh\"\n")
        setitup += ("  config.vm.provision \"shell\", path: \"provision/node-OS.sh\"\n")
        setitup += ("  config.vm.provision \"file\", source: \"provision/ssh-config\", "
                    "destination:\"/home/cloud-user/.ssh/config\"\n")
        setitup += ("  config.vm.provision \"file\", source: \"hosts\", destination: "
                    "\"/etc/hosts\"\n")
        setitup += ("  config.vm.synced_folder \"services\", \"/opt/ccs/services/\"\n")

        self.append_it(setitup)

    def _vbox_os_provider_env_vars(self, float_net, tenant_nets, tenant_security_groups):
        """
        Creates self.env_vars from shell variables and called methods

        Args:
            # All three imputs are built from cmd_up.os_ensure_network
            float_net {str}: 'public-floating-602'
                [{'name': 'test_management', 'ip': False},
                 {'name': 'test_dual_home', 'ip': True}]
            tenant_security_groups {list of dicts}:
                [{'name': "default"}, {'name': 'my_sec_group'}]

        Returns:
            Nothing, but builds the self.env_vars dict with the following keys:
                'username': 'test_user'
                'openstack_auth_url': 'http://example.cisco.com:5000/v2.0/'
                'tenant_name': 'dev-tenant'
                'floating_ip_pool': 'public-floating-602'
                'openstack_image_url': 'http://example.cisco.com:9292/v2/'
                'openstack_network_url': 'http://example.cisco.com:9696/v2.0'
                'password': 'test_pw'
                'networks': "[{name: 'test_management'}," + \
                            "{name: 'test_dual_home', address: ho['ip']}]"
                'security_groups': "[{name: 'default'}]"

        Example Usage:
            my_class_var._vbox_os_provider_env_vars(float_net, tenant_nets, sec_groups)
        """
        self.env_vars['username'] = os.environ.get('OS_USERNAME')
        self.env_vars['password'] = os.environ.get('OS_PASSWORD')
        self.env_vars['openstack_auth_url'] = os.environ.get('OS_AUTH_URL')
        self.env_vars['tenant_name'] = os.environ.get('OS_TENANT_NAME')
        self.env_vars['floating_ip_pool'] = str(float_net)
        networks = self._vbox_os_provider_parse_multiple_networks(tenant_nets)
        security_groups = self._vbox_os_provider_parse_security_groups(
                          tenant_security_groups)
        self.env_vars['networks'] = networks
        self.env_vars['security_groups'] = security_groups
        openstack_network_url = None
        openstack_image_url = None
        if (self.env_vars.get('openstack_auth_url')):
            proto, baseurl, port = self.env_vars.get('openstack_auth_url').split(':')
            openstack_network_url = proto + ':' + baseurl + ":9696/v2.0"
            openstack_image_url = proto + ':' + baseurl + ":9292/v2/"
            self.env_vars['openstack_network_url'] = openstack_network_url
            self.env_vars['openstack_image_url'] = openstack_image_url

    def _vbox_os_provider_parse_multiple_networks(self, tenant_nets):
        """
        Parses tenant networks data

        Args:
            tenant_nets {list of dicts}:
                [{'name': 'test_management', 'ip': False},
                 {'name': 'test_dual_home', 'ip': True}]

        Returns:
            vagrant_network {list of dicts}:
                [{name: 'test_management'},"
                {name: 'test_dual_home', address: ho['ip']}]

        Example Usage:
            vagrant_net = my_class_var._vbox_os_provider_parse_multiple_networks(networks)
        """
        stl_without_ip = "{name: '%s'},"
        stl_with_ip = "{name: '%s', address: ho['ip']},"
        vagrant_network = ''
        for net in tenant_nets:
            try:
                if net['ip']:
                    vagrant_network = vagrant_network + stl_with_ip % net['name']
                else:
                    vagrant_network = vagrant_network + stl_without_ip % net['name']
            except KeyError:
                vagrant_network = vagrant_network + stl_without_ip % net['name']
        vagrant_network = '[' + vagrant_network.strip(",") + ']'
        return vagrant_network

    def _vbox_os_provider_parse_security_groups(self, security_groups):
        """
        Parses security groups data, removing any keys other than 'name'

        Args:
            security_groups {list of dicts}:
                [{'name': 'default', 'note': 'this is the default sec group'},
                 {'name': 'my_sec_group', 'note': 'not for general use'}]

        Returns:
            vagrant_security_group {list of dicts}:
                [{'name': 'default'},
                 {'name': 'my_sec_group'}]

        Example Usage:
            sec_group_names = my_class_var._vbox_os_provider_parse_security_groups(sec_grps)
        """
        stl_security_group = "{name: '%s'},"
        vagrant_security_group = ''
        for security_group in security_groups:
            vagrant_security_group = vagrant_security_group + \
                                     stl_security_group\
                                     % security_group['name']
        vagrant_security_group = '[' + vagrant_security_group.strip(",") + ']'
        return vagrant_security_group

    def _vbox_os_provider_host_vars(self, path):
        """
        Sets the host_vars image and flavor keys from VM host.yamls, or the defaults

        Args:
            path {str}: Path to servicelab .stack directory
                '/home/me/repo/servicelab/servicelab/.stack/'

        Returns:
            Nothing, instead sets the self.host_vars 'image' and 'flavor' key values
            self.host_vars['flavor'] = '2cpu.4ram.20sas'
            self.host_vars['image']  = 'slab-RHEL7.1v7'

        Example Usage:
            my_class_var._vbox_os_provider_host_vars(self.ctx.path)
        """
        relpath_toyaml = 'services/ccs-data/sites/ccs-dev-1/environments/dev-tenant/hosts.d/'
        if (os.path.exists(path)):
            path = os.path.join(path, relpath_toyaml)
            if (os.path.exists(path)):
                path = os.path.join(path, self.hostname.lower() + '.yaml')
                if os.path.exists(path):
                    try:
                        with open(path) as host_yaml:
                            host_data = yaml.load(host_yaml)
                            self.host_vars['image'] = host_data['deploy_args']['image']
                            self.host_vars['flavor'] = host_data['deploy_args']['flavor']
                    except:
                        Vagrantfile_utils_logger.error('Could not set host flavor or img from\
                                                        ccs-data')
                        self.host_vars['image'] = self.default_image
                        self.host_vars['flavor'] = self.default_flavor
        if self.host_vars.get('image') is None:
            self.host_vars['image'] = self.default_image
        if self.host_vars.get('flavor') is None:
            self.host_vars['flavor'] = self.default_flavor
