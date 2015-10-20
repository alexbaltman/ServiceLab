import logging
from servicelab.utils import service_utils
# Note: from here --> python-vagrant fabric cuisine pyvbox
from fabric.api import env, execute, task
from fabric.contrib.files import sed
import virtualbox
import subprocess32 as subprocess
import cuisine
import vagrant
import yaml
import os


# create logger
# TODO: For now warning and error print. Got to figure out how
#       to import the one in stack.py properly.
vagrant_utils_logger = logging.getLogger('click_application')
logging.basicConfig()


class Connect_to_vagrant(object):
    """Vagrant class for booting, provisioning and managing a virtual machine."""

    def __init__(
            self,
            vm_name,
            path,
            provider="virtualbox",
            default_vbox="Cisco/rhel-7",
            default_vbox_url='http://cis-kickstart.cisco.com/ccs-rhel-7.box'):
        """
        Constructor for Vagrant Class

        Assigns member variables to constructor parameters.
        Sets up Vagrant Client.

        Args:
            self                -- self-referencing pointer
            vname               -- name of the virtual machine
            path                -- The path to your working .stack directory. Typically,
                                   this looks like ./servicelab/servicelab/.stack where "."
                                   is the path to the root of the servicelab repository.
            provider            -- vagrant provider, defaults to virtualbox
            default_vbox        -- default virtualbox, defaults to "Cisco/Rhel7"
            default_vbox_url    -- hyperlink to the default_vbox
        """
        self.vm_name = vm_name
        self.provider = provider
        self.default_vbox = default_vbox
        self.default_vbox_url = default_vbox_url
        self.path = path
        # Note: The quiet is so we know what's happening during
        #       vagrant commands in the term.
        # Note: Setup vagrant client.
        vagrant_dir = path
        self.v = vagrant.Vagrant(
            root=vagrant_dir,
            quiet_stdout=False,
            quiet_stderr=False)

        # check for installed plugins

        # over here we will install the plugins.
        # this is an extra step but by this we can avoid extra command repitition
        # the other alternative is to put it in vagrantfile but this can be a problem
        # as we may have to exec over the running  process
        # please see stack discussion
        # http://stackoverflow.com/questions/19492738/demand-a-vagrant-plugin-within-the-vagrantfile
        req_lst = ["vagrant-hostmanager", "vagrant-openstack-provider"]
        plugin_lst = self.v.plugin_list()
        for plugin in req_lst:
            if plugin not in plugin_lst:
                service_utils.run_this('vagrant plugin install {}'.format(plugin))

    def add_box(self):
        """
        Member function which adds a virtualbox to the Vagrant environment.
        Also creates RHEL7 image if it doesn't exist.

        Args:
            self -- self-referencing pointer

        """
        v = self.v
        if not os.path.exists(v.root):
            os.makedirs(v.root)

        box_list = v.box_list()

        # Note: Look for the rhel7 image and create/add it if it's not there.
        # if not ([image.name or None for image in images
        # if image.name == default_vbox]):
        if not ([image.name or None for image in box_list
                 if image.name == self.default_vbox]):
            v.box_add(
                self.default_vbox,
                self.default_vbox_url,
                provider=self.provider,
                force=True)

    def create_Vagrantfile(self, path):
        """
        Member function which creates/overwrites a Vagrantfile. Then it uses
        the Vagrantfile to reinitialize the class instance.

        Args:
            path                -- The path to your working .stack directory. Typically,
                                   this looks like ./servicelab/servicelab/.stack where "."
                                   is the path to the root of the servicelab repository.

        """
        # EXP: Check for vagrant file, otherwise init, and insert box into file
        # RFI: Create Vagrantfile in Current_Services?
        v = self.v
        vagrant_file = os.path.join(v.root, "Vagrantfile")

        if (os.path.isfile(vagrant_file)):
            # Note: We're removing their file b/c we want to standardize how we're
            #       using vagrant.
            # TODO: we should really just back this up then remove.
            os.remove(vagrant_file)
        v.init(box_name=self.default_vbox)

    @staticmethod
    def backup_vagrantfile(path):
        """
        Member function which backs up the existing Vagrantfile.

        Args:
            path    -- The path to your working .stack directory. Typically,
                       this looks like ./servicelab/servicelab/.stack where "."
                       is the path to the root of the servicelab repository.
        """
        vagrant_file = os.path.join(
            path, "services", "current_service", "Vagrantfile")
        # EXP: Create backup
        if not (os.path.isfile(vagrant_file + '.bak')):
            os.rename(vagrant_file, vagrant_file + '.bak')
        else:
            os.rename(vagrant_file + '.bak', vagrant_file + '.stack')

    @staticmethod
    def rename_vm_name_in_vagrantfile(vagrant_file, vm_name):
        """
        Member function which renames the virtual machine name. Replaces all
        old names in the Vagrantfile with the new inputted one.

        Args:
            vagrant_file    -- Path to the existing Vagrantfile.
            vm_name          -- new name to assign to VM
        """
        # EXP: Execute a touch of ruby to rename vm to vname
        with open(vagrant_file, 'w') as vfile:
            with open(vagrant_file+'.bak', 'r') as bfile:
                for line in bfile:
                    if (line.rfind('config.vm.box = "%s"' % (default_vbox)) != -1):
                        line = ' %s.vm.box = "%s"' % (vm_name, default_vbox)
                        # Note: Need the space before config.
                        line = str(' config.vm.define "%s" do |%s|\n%s' % (vm_name,
                                   vm_name + "vm", line))
                        line = str(line + '\n end')
                        vfile.write(line)

    def setup_vagrant_vm(vm_name):
        """
        Member function which sets up the VM.

        Opens up host port to vm_name, sets file name and disables known hosts.

        Args:
            vm_name  --  name to assign to VM
        """
        env.hosts = [v.user_hostname_port(vm_name='%s' % (vm_name))]
        env.key_filename = v.keyfile(vm_name='%s' % (vm_name))
        env.disable_known_hosts = True

    # Note: Requires fabric env.hosts to be set
    # Note: Good for yum pkg "cloud-init".
    @staticmethod
    @task
    def install_pkg_on_vm(pkg):
        """
        Installs a package on a linux VM with yum.

        Args:
            pkg  --  name of package to be installed
        """
        cuisine.package_ensure_yum(pkg)

    @staticmethod
    @task
    def configure_cloud_init():
        """
        Configures cloud-init.
        """
        sed('/etc/cloud/cloud.cfg', 'user:', 'user: vagrant\n#')

# execute(install_pkg_on_vm("cloud-init"))
# execute(configure_cloud_init)


def export_vm(path, vm_name):
    """
    Exports the virtualmachine to Virtualbox.

    Args:
        path  --  The path to your working .stack directory. Typically,
                  this looks like ./servicelab/servicelab/.stack where "."
                  is the path to the root of the servicelab repository.
        vm_name  --  name of virtualmachine
    """
    vbox = virtualbox.VirtualBox()
    machines = [machine for machine
                in vbox.machines
                if machine.name.rfind('MyTest') != -1]
    vm = machines[0]
    run_this("VBoxManage export vm.name -o %s.ova --ovf10" % (vm_name))
    ovf_path = os.path.join(path, vm_name + ".ova")
