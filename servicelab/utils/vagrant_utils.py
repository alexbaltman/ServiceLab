"""
Utility functions for vagrant related tasks.
"""
import os
from subprocess import CalledProcessError

import vagrant
import virtualbox
from fabric.api import env, task
from fabric.contrib.files import sed

import yaml_utils
import service_utils
import vagrantfile_utils
import logger_utils
from servicelab import settings

slab_logger = logger_utils.setup_logger(settings.verbosity, 'stack.utils.vagrant')


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


def vm_isrunning(hostname, path):
    '''This function determines the state of a vm in our environment. With this
    information we'll make decisions on what to do w/ certain requests. This is a
    a very important function.

    Args:
        hostname (str):
        path (str): The ctx.path aka the .stack/ working directory

    Returns:
        Returncode (int):
            0 - if vm is ON
            1 - if vm is OFF, SAVED, NOT_CREATED
            2 - no vm exists
            3 - other state: suspended, aborted, etc.
        Return (boolean):
            True - if vm is remote
            False - if vm is local

    Example Usage:
        >>> vm_isrunning('infra-001', ctx.path)
        0, True

    Data Structure:
        from vm_connection.v.status(hostname):
            [Status(name='infra-001', state='running', provider='virtualbox')]

    Misc:
    From python-vagrant up function (self, no_provision=False,
                                     provider=None, vm_name=None,
                                     provision=None, provision_with=None)

    '''
    slab_logger.log(15, 'Determining the running state of %s' % hostname)
    vm_connection = Connect_to_vagrant(vm_name=hostname,
                                       path=path)
    try:
        status = vm_connection.v.status(vm_name=hostname)
        # Note: local vbox value: running
        if status[0][1] == 'running':
            return 0, False
        # Note: local vbox value: poweroff
        elif status[0][1] == 'poweroff':
            return 1, False
        # Note: remote OS value: active
        elif status[0][1] == 'active':
            return 0, True
        # Note: remote OS value: shutoff
        elif status[0][1] == 'shutoff':
            return 1, True
        # Note: remote OS value: saved
        elif status[0][1] == 'saved':
            return 1, True
        # Note: remote OS value: un created
        elif status[0][1] == 'not_created':
            return 1, False
    except CalledProcessError:
        # RFI: is there a better way to return here? raise exception?
        return 2, False
    # Note: 3 represent some other state --> suspended, aborted, etc.
    return 3, False


def infra_ensure_up(mynets, float_net, my_security_groups, nfs, path=None):
    '''Best effort to ensure infra-001 or -002 will be booted in correct env.

    Args:
        mynets (list): Comes from ensure_os_network.
                       See 'check_for_network' in openstack_utils data strctures.
        float_net(str): comes from ensure_os_network. looks like: 'Public-floating-602'
        path (str): The path to your working .stack directory

    Returns:
        0 - success, infra node has been sucessfully booted
        1 - failure
        hostname (str): infra-001 or infra-002

    Example:
        >>> infra_ensure_up(None, None, None, ctx.path)
            0, infra-001

    Data Structure:
        From python-vagrant's status call.
        Out[3]: [Status(name='rhel7-001', state='running', provider='virtualbox')]

    Misc.:
        CalledProcessError --> subprocess exit 1 triggers this exception
    '''
    slab_logger.log(15, 'Ensuring that an infra node is booted in the correct environment')
    hostname = 'infra-001'
    if mynets and float_net:
        remote = True
    else:
        remote = False

    slab_logger.debug("Checking for an existing {}"
                      "infra node.".format("remote " if remote else ""))
    ispoweron, isremote = vm_isrunning(hostname=hostname, path=path)
    infra_connection = Connect_to_vagrant(vm_name=hostname, path=path)

    # Note: Ensure 001 is in inventory even if we're using 002.
    slab_logger.debug("Adding {} to local inventory.".format(hostname))
    if yaml_utils.addto_inventory(hostname, path) > 0:
        return 1, hostname

    # Note: if requested remote or local and our vm's state is same then just
    #       make sure it's booted w/ ispoweron being 0 for that.
    if isremote == remote and ispoweron == 0:
        infra_connection.v.reload(hostname, 'provision')
        return 0, hostname
    # Note: it's what we want just not booted, so boot it.
    elif isremote == remote and ispoweron == 1:
        try:
            infra_connection.v.up(vm_name=hostname)
        except CalledProcessError:
            return 1, hostname
        return 0, hostname

    # Shared code b/w remote and local vbox
    thisvfile = vagrantfile_utils.SlabVagrantfile(path=path)

    # vagrant_utils.vm_isrunning currently doesn't manage these alternative states
    # so we fail
    if ispoweron == 3:
        # TODO: ERROR msg here
        return 1, hostname

    # Note: b/c the infra exists but isn't in desired location we alter hostname
    if isremote != remote:
        # Added in case remote hypervisor did not find infra-001
        if not ispoweron == 2:
            hostname = 'infra-002'
        infra_connection.vm_name = hostname
        if yaml_utils.addto_inventory(hostname, path) > 0:
            return 1, hostname
        ispoweron, isremote = vagrant_utils.vm_isrunning(hostname=hostname, path=path)
        if isremote == remote and ispoweron == 0:
            infra_connection.v.reload(hostname)
            return 0, hostname
        elif isremote == remote and ispoweron == 1:
            try:
                infra_connection.v.up(vm_name=hostname)
            except CalledProcessError:
                return 1, hostname
            return 0, hostname
        elif ispoweron == 3:
            return 1, hostname
        elif isremote != remote and ispoweron != 2:
            return 1, hostname

    # Note: At this point infra node (hostname) should be in the inventroy
    #       else error out
    ret_code, host_dict = yaml_utils.gethost_byname(hostname, path)
    if ret_code > 0:
        return 1, hostname

    if remote:
        thisvfile.set_env_vars(float_net, mynets, my_security_groups)
        thisvfile.add_openstack_vm(host_dict)
        try:
            infra_connection.v.up(vm_name=hostname)
            return 0, hostname
        except CalledProcessError:
            return 1, hostname
    else:
        thisvfile.add_virtualbox_vm(host_dict, path, nfs)
        try:
            infra_connection.v.up(vm_name=hostname)
            return 0, hostname
        except CalledProcessError:
            return 1, hostname


def check_vm_is_available(path):
    """
    Checks if an active VM exists

    Args:
        path

    Returns:
        True if active VM exists
        False if active VM does not exist

    Example Usage:
        my_class_var.check_vm_is_available(path)
    """
    slab_logger.log(15, 'Checking vm availablity')

    def fn(vagrant_folder, vm_name):
        try:
            if not os.path.isfile(os.path.join(vagrant_folder, "Vagrantfile")):
                return False
            v = vagrant.Vagrant(vagrant_folder)
            return v.status(vm_name)[0].state != 'not_created'
        except:
            return False

    dir = ['services/service-redhouse-tenant', '']

    # get the names of the machines
    vm_lst = map(lambda x: os.path.join(path, '.vagrant/machines', x), dir)
    vm_lst = filter(lambda x: os.path.isdir(x), vm_lst)
    vm_lst = [vm for dir_name in vm_lst for vm in os.listdir(dir_name)]

    # check if they are installed or not
    for folder in map(lambda x: os.path.join(path, x), dir):
        slab_logger.debug("checking {}".format(folder))
        for vm in vm_lst:
            if fn(folder, vm):
                slab_logger.debug("VM {} is available".format(vm))
                return True
    return False
