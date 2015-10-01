import logging
import yaml
import os

# create logger
# TODO: For now warning and error print. Got to figure out how
#       to import the one in stack.py properly.
Vagrantfile_utils_logger = logging.getLogger('click_application')
logging.basicConfig()


class SlabVagrantfile(object):

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

        def _set_header():
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
            startvms = "Vagrant.configure(VAGRANTFILE_API_VERSION) do |cluster|\n"
            return startvms

        h1, h2, req_plugin = _set_header()
        startvms = _beg_vm_config()
        # Note: until write_it is fixed, have to move list out from middle
        self.write_it(h1, h2, req_plugin, startvms)
        self.set_header = True

    def write_it(self, *text):
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
        '''
        Vbox expecting in host_dict:
            hostname

        '''
        setitup = ''
        self.host_dict = host_dict
        self.hostname = self.host_dict.keys()[0]
        ip = self.host_dict[self.hostname]['ip']
        try:
            setitup = ("cluster.vm.define \"" + self.hostname + "\" do |config|\n"
                       "  config.hostmanager.enabled = true\n"
                       "  config.hostmanager.manage_host = true\n"
                       "  config.hostmanager.include_offline = true\n"
                       "  config.vm.box = \"" + self.host_dict[self.hostname]['box'] + "\"\n"
                       # RFI: non-win config --> use hosts keypair so set insert_key to F
                       #      then enable agent forwarding.
                       "  config.ssh.insert_key = false\n"
                       "  config.ssh.forward_agent = true\n"
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
            self.append_it(setitup)
            return 0
        except KeyError:
            Vagrantfile_utils_logger.error('Can not add host b/c of missing Key')
            return 1

    def add_openstack_vm(self, host_dict):
        '''
        host_dict 'flavor', host_dict[hostname].get('image')
        '''
        self.host_dict = host_dict
        self.hostname = self.host_dict.keys()[0]
        env_vars = self.env_vars
        self._vbox_os_provider_host_vars(self.path)
        setitup = ("cluster.vm.define \"" + self.hostname + "\" do |config|\n",
                   "  cluster.ssh.username = 'cloud-user' \n",
                   "  config.hostmanager.enabled = true\n"
                   "  config.hostmanager.manage_host = true\n"
                   "  config.hostmanager.include_offline = true\n"
                   "  config.vm.provider :openstack do |os, override|\n")

        setitup += ("    os.openstack_auth_url   = \"" + env_vars['openstack_auth_url'] +
                    "\"\n",
                    "    os.username             = \"" + env_vars['username'] + "\"\n",
                    "    os.password              = \"" + env_vars['password'] + "\"\n",
                    "    os.tenant_name          = \"" + env_vars['tenant_name'] + "\"\n")

        try:
            setitup += ("    os.flavor               = \"" + self.host_vars['flavor'],
                        "\"\n",
                        "    os.image                = \"" + self.host_vars['image'],
                        "\"\n")

        except KeyError:
            Vagrantfile_utils_logger.error('Could not set host flavor or img from\
                                            ccs-data')
        setitup += ("    os.floating_ip_pool     = \"" + env_vars['floating_ip_pool'] +
                    "\"\n",
                    "    os.openstack_network_url=\"" + env_vars['openstack_network_url'] +
                    "\"\n",
                    "    os.openstack_image_url  = \"" + env_vars['openstack_image_url'] +
                    "\"\n",
                    "    os.networks             = " + env_vars['networks'] + "\n",
                    "    override.vm.box = \"openstack\"\n"
                    "  end\n")
        self.append_it(setitup)

    def _vbox_os_provider_env_vars(self, float_net, tenant_nets):
        '''Function will accept a float_net string and a tenant_nets list of dicts.
            The dicts are of the format {'name':'network_name', 'ip':True}.
            The ip key will be true if vagrant.yaml has an ip for the host.
            It will return a dict with the OpenStack username, password,
            tenant_name, auth_url, network_url, image_url, floating_ip_pool and networks
            to be used for developing the Vagrant file'''
        self.env_vars['username'] = os.environ.get('OS_USERNAME')
        self.env_vars['password'] = os.environ.get('OS_PASSWORD')
        self.env_vars['openstack_auth_url'] = os.environ.get('OS_AUTH_URL')
        self.env_vars['tenant_name'] = os.environ.get('OS_TENANT_NAME')
        self.env_vars['floating_ip_pool'] = str(float_net)
        networks = self._vbox_os_provider_parse_multiple_networks(tenant_nets)
        self.env_vars['networks'] = networks
        openstack_network_url = None
        openstack_image_url = None
        if (self.env_vars.get('openstack_auth_url')):
            proto, baseurl, port = self.env_vars.get('openstack_auth_url').split(':')
            openstack_network_url = proto + ':' + baseurl + ":9696/v2.0"
            openstack_image_url = proto + ':' + baseurl + ":9292/v2/"
            self.env_vars['openstack_network_url'] = openstack_network_url
            self.env_vars['openstack_image_url'] = openstack_image_url

    def _vbox_os_provider_parse_multiple_networks(self, tenant_nets):
        '''Function accepts a list of dicts with each dict containing
           the tenant network name and a boolean to indicate if there is an ip in
           the vagrant.yaml. It will return a string of networks to be used in
           the construction of the Vagrantfile'''
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

    def _vbox_os_provider_host_vars(self, path):
        '''Func_vbox_os_provider_env_vars(stion will accept a path to the .stack
           directory and the host being booted. It will navigate to the ccs-devel directory,
           find the corresponding host.yaml file, parse it and return a dict with flavor,
           and image used for the host'''
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
