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
    """ Use vagrant to create a vm.

        Providers: virtualbox, openstack.
        In the future may accept docker.
    """

    def __init__(self, vmname, path, provider="virtualbox", default_vbox="Cisco/rhel7",
                 default_vbox_url='http://cis-kickstart.cisco.com/ccs-rhel7.box'):
        self.vmname = vmname
        self.provider = provider
        self.default_vbox = default_vbox
        self.default_vbox_url = 'default_vbox_url'
        self.path = path
        # Note: The quiet is so we know what's happening during
        #       vagrant commands in the term.
        # Note: Setup vagrant client.
        self.v = vagrant.Vagrant(quiet_stdout=False, quiet_stderr=False)
        v = self.v

    def add_box(self):
        # Note: Look for the rhel7 image and create/add it if it's not there.
        # if not ([image.name or None for image in images
        # if image.name == default_vbox]):
        if not ([image.name or None for image in v.BASE_BOXES
                 if image.name == default_vbox]):
            v.box_add(default_vbox, default_vbox_url, provider=provider, force=True)

    def create_Vagrantfile(path):
        # EXP: Check for vagrant file, otherwise init, and insert box into file
        # RFI: Create Vagrantfile in Current_Services?
        vagrant_file = os.path.join(path, "services", "current_service", "Vagrantfile")
        if (os.path.isfile(vagrant_file)):
            # Note: We're removing their file b/c we want to standardize how we're
            #       using vagrant.
            # TODO: we should really just back this up then remove.
            os.remove(vagrant_file)
        v.init(box_name=default_vbox)

    @staticmethod
    def backup_vagrantfile(path):
        vagrant_file = os.path.join(path, "services", "current_service", "Vagrantfile")
        # EXP: Create backup
        if not (os.path.isfile(vagrant_file + '.bak')):
            os.rename(vagrant_file, vagrant_file + '.bak')
        else:
            os.rename(vagrant_file + '.bak', vagrant_file + '.stack')

    @staticmethod
    def rename_vmname_in_vagrantfile(vagrant_file, vmname):
            # EXP: Execute a touch of ruby to rename vm to mytest
            with open(vagrant_file, 'w') as vfile:
                with open(vagrant_file+'.bak', 'r') as bfile:
                    for line in bfile:
                        if (line.rfind('config.vm.box = "%s"' % (default_vbox)) != -1):
                            line = ' %s.vm.box = "%s"' % (vmname, default_vbox)
                            # Note: Need the space before config.
                            line = str(' config.vm.define "%s" do |%s|\n%s' % (vmname,
                                       vmname + "vm", line))
                            line = str(line + '\n end')
                            vfile.write(line)

    def setup_vagrant_vm(vmname):
        env.hosts = [v.user_hostname_port(vm_name='%s' % (vmname))]
        env.key_filename = v.keyfile(vm_name='%s' % (vmname))
        env.disable_known_hosts = True

    # Note: Requires fabric env.hosts to be set
    # Note: Good for yum pkg "cloud-init".
    @staticmethod
    @task
    def install_pkg_on_vm(pkg):
        """
        Installs a package on a linux VM with yum.
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


def export_vm(path, vmname):
    vbox = virtualbox.VirtualBox()
    machines = [machine for machine
                in vbox.machines
                if machine.name.rfind('MyTest') != -1]
    vm = machines[0]
    run_this("VBoxManage export vm.name -o %s.ova --ovf10" % (vmname))
    ovf_path = os.path.join(path, vmname + ".ova")
