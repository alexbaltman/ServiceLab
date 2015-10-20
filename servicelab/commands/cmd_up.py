import os
import sys
import time
from subprocess import CalledProcessError

import click
import yaml

from servicelab.utils import openstack_utils
from servicelab.utils import service_utils
from servicelab.utils import vagrant_utils
from servicelab.utils import helper_utils
from servicelab.stack import pass_context
from servicelab.utils import yaml_utils
from servicelab.utils import Vagrantfile_utils


@click.option('--full', is_flag=True, default=False, help='Boot complete openstack stack without ha, \
              unless --ha flag is set. You can not use the min flag with the full flag')
@click.option('--mini', is_flag=True, default=False, help='Boot min openstack stack without ha, \
              unless --ha flag is set. You can not use min flag with the full flag')
@click.option('--rhel7', is_flag=True, default=False, help='Boot a rhel7 vm.')
@click.option('--target', '-t', help='pick an OSP target vm to boot.')
@click.option('--service', '-s', default="", help='This is a service you would like to boot\
              a vm for. e.g. service-sonarqube')
@click.option('-r', '--remote', is_flag=True, default=False,
              help='Boot into an OS environment')
@click.option('--ha', is_flag=True, default=False, help='Enables HA for core OpenStack components \
              by booting the necessary extra VMs.')
@click.option('-b', '--branch', default="master", help='Choose a branch to run against \
              for service redhouse tenant and svc.')
@click.option('--data-branch', default="master", help='Choose a branch of ccs-data")
@click.option('--service-branch', default="master", help='Choose a branch of your service")
@click.option('-u', '--username', help='Enter the desired username')
@click.option('-i', '--interactive', help='Walk through booting VMs')
@click.group('up', invoke_without_command=True, short_help="Boots VM(s).")
@pass_context
def cli(ctx, full, mini, rhel7, target, service, remote, ha, branch, data_branch, service_branch,
        username, interactive):

    ## Things the user Should not do =================================
    if mini is True and full is True:
        ctx.logger.error("You can not use the mini flag with the full flag.")
        sys.exit(1)

    ## Gather as many requirements as possible for the user ==========
    if not username:
        username = ctx.get_username()

    if not any([full, mini, rhel7, target, service]):
        try:
            returncode, service = helper_utils.get_current_service(ctx.path)
        except TypeError:
            ctx.logger.error("Could not get the current service.")
            ctx.logger.error("Try: stack workon service-myservice")
            sys.exit(1)
        if returncode > 0:
            ctx.logger.debug("Failed to get the current service")
            sys.exit(1)

    if rhel7:
        hostname = str(name_vm("rhel7", ctx.path))
    elif service:
        hostname = str(name_vm(service, ctx.path))

    # Setup data and inventory
    yaml_utils.write_dev_hostyaml_out(ctx.path, hostname)
    yaml_utils.host_add_vagrantyaml(ctx.path, "vagrant.yaml", hostname,
                                    "ccs-dev-1")
    retc, myinfo = service_utils.build_data(ctx.path)
    if retc > 0:
        ctx.logger.error('Error building ccs-data ccs-dev-1: ' + myinfo)

    # Prep class Objects
    if not os.path.exists(os.path.join(ctx.path, 'Vagrantfile')):
        myvfile.init_vagrantfile()
    myvfile = Vagrantfile_utils.SlabVagrantfile(path=ctx.path)
    myvag_env = vagrant_utils.Connect_to_vagrant(vm_name=hostname,
                                                 path=ctx.path)

    # Setup Vagrantfile w/ vm
    if remote:
        returncode, float_net, mynets = os_ensure_network(ctx.path)
        if returncode > 0:
            ctx.logger.debug("No OS_ environment variables found")
            sys.exit(1)
        myvfile._vbox_os_provider_env_vars(float_net, mynets)
        returncode, host_dict = yaml_utils.gethost_byname(hostname, ctx.path)
        if returncode > 0:
            ctx.logger.error('Failed to get the requested host from your Vagrant.yaml')
            sys.exit(1)
        myvfile.add_openstack_vm(host_dict)
    else:
        returncode, host_dict = yaml_utils.gethost_byname(hostname, ctx.path)
        if returncode > 0:
            ctx.logger.error('Failed to get the requested host from your Vagrant.yaml')
            sys.exit(1)
        myvfile.add_virtualbox_vm(host_dict)

    # Get vm running
    a.v.up(vm_name=hostname)
    returncode, myinfo = service_utils.run_this('vagrant hostmanager', ctx.path)
    if returncode > 0:
        ctx.logger.error("Could not run vagrant hostmanager because\
                        {0}".format(myinfo))
        ctx.logger.error("Vagrant manager will fail if you have local vms and remote vms.")
        sys.exit(1)
    # You can exit safely now if you're just booting a rhel7 vm
    elif rhel7 and returncode == 0:
        sys.exit(0)

    ## SERVICE VM remaining workflow  ================================
    if service:
        if remote:
            returncode, infra_hostname = infra_ensure_up(mynets, float_net, path=ctx.path)
            if returncode == 1:
                ctx.logger.error("Could not boot a remote infra node")
                sys.exit(1)
        else:
            returncode, infra_hostname = infra_ensure_up(path=ctx.path)
            if returncode == 1:
                ctx.logger.error("Could not boot a local infra node")
                sys.exit(1)

        returncode, myinfo = service_utils.run_this('vagrant hostmanager', ctx.path)
        if returncode > 0:
            ctx.logger.error("Could not run vagrant hostmanager because\
                            {0}".format(myinfo))
            ctx.logger.error("Vagrant manager will fail if you have local vms and remote vms.")
            sys.exit(1)

        returncode, myinfo = service_utils.run_this(
                             'vagrant ssh {0} -c \"cd /opt/ccs/services/{1}/'
                             ' && sudo heighliner --dev --debug deploy"'.format(infra_hostname, service))
        if returncode > 0:
            ctx.logger.error('There was a failure during the heighliner deploy phase of"
                             "your service. Please see the following information"
                             "for debugging: ")
            ctx.logger.error(myinfo)
            sys.exit(1)
        else:
            sys.exit(0)
    elif target:
        redhouse_ten_path = os.path.join(ctx.path, 'services', 'service-redhouse-tenant')
        service_utils.sync_service(ctx.path, service_branch, username, "service-redhouse-tenant")
        a = vagrant_utils.Connect_to_vagrant(vm_name=target, path=redhouse_ten_path)
        if addto_inventory(target, ctx.path) > 0:
            ctx.logger.error('Could not add {0} to vagrant.yaml'.format(target))
            sys.exit(1)

        if not os.path.exists(os.path.join(ctx.path, 'services', 'ccs-data')):
            service_utils.sync_service(ctx.path, data_branch, username, 'ccs-data')

        if not os.path.exists(os.path.join(ctx.path, 'services', 'ccs-data', 'out')):
            returncode, myinfo = service_utils.build_data(ctx.path)
            if returncode > 0:
                ctx.logger.error('Failed to build ccs-data data b/c ' + myinfo)
                sys.exit(1)

        if not os.path.islink(os.path.join(redhouse_ten_path,
                                           "dev",
                                           "ccs-data")):
            ctx.logger.debug('WARNING: Linking ' + os.path.join(redhouse_ten_path, 'dev',
                                                                'ccs-data') + "with " +
                             os.path.join(ctx.path, "services", "ccs-data"))
            # Note: os.symlink(src, dst)
            os.symlink(os.path.join(ctx.path,
                                    "services",
                                    "ccs-data"
                                    ),
                       os.path.join(redhouse_ten_path,
                                    "dev",
                                    "ccs-data"))

        if remote:
            settingsyaml = {'openstack_provider': True}
            returncode = wr_settingsyaml(ctx.path, settingsyaml, hostname=target)
            if returncode > 0:
                ctx.logger.error('Failed to write settings yaml - make sure you have your OS'
                                 'cred.s sourced and have access to'
                                 'ccs-gerrit.cisco.com and have keys setup.')
                sys.exit(1)
            a.v.up(vm_name=target, provider='openstack')
        else:
            settingsyaml = {'openstack_provider': 'false'}
            returncode = wr_settingsyaml(ctx.path, settingsyaml=settingsyaml)
            if returncode > 0:
                ctx.logger.error('Failed to write settings yaml - make sure you have your OS'
                                 'cred.s sourced and have access to'
                                 'ccs-gerrit.cisco.com and have keys setup.')
                sys.exit(1)
            a.v.up(vm_name=target)
        returncode, myinfo = service_utils.run_this('vagrant hostmanager', ctx.path)
        if returncode > 0:
            ctx.logger.error("Could not run vagrant hostmanager because\
                             {0}".format(myinfo))
            sys.exit(1)
        else:
            sys.exit(0)

    service_utils.sync_service(ctx.path, branch, username, "service-redhouse-tenant")

    if mini:
        returncode, allmy_vms = yaml_utils.getmin_OS_vms(ctx.path)
    elif full:
        returncode, allmy_vms = yaml_utils.getfull_OS_vms(os.path.join(ctx.path,
                                                                       'provision'),
                                                          '001')
    if returncode > 0:
        ctx.logger.error("Couldn't get the vms from the vagrant.yaml.")
        sys.exit(1)
    try:
        # Note: not sure if this will work w/ vm_name set to infra-001 arbitrarily
        # Note: move path to ctx.path if able to boot OSP pieces via infra/heighliner
        redhouse_ten_path = os.path.join(ctx.path, 'services', 'service-redhouse-tenant')
        a = vagrant_utils.Connect_to_vagrant(vm_name='infra-001',
                                             path=os.path.join(redhouse_ten_path))
        myvfile = Vagrantfile_utils.SlabVagrantfile(path=ctx.path)
        returncode, float_net, mynets = os_ensure_network(ctx.path)
        if returncode > 0:
            ctx.logger.error('Failed to get float net and mynets')
            sys.exit(1)
        myvfile._vbox_os_provider_env_vars(float_net, mynets)
        if not os.path.exists(os.path.join(ctx.path, 'Vagrantfile')):
            myvfile.init_vagrantfile()
        for i in allmy_vms:
            if ha:
                ha_vm = i.replace("001", "002")
                returncode, ha_vm_dicts = yaml_utils.gethost_byname(ha_vm,
                                                                    os.path.join(ctx.path,
                                                                                 'provision')
                                                                    )
                if returncode > 0:
                    ctx.logger.error("Couldn't get the vm {0} for HA".format(ha_vm))
                    sys.exit(1)
                else:
                    allmy_vms.append(ha_vm_dicts)
            for host in i:
                retcode = yaml_utils.host_add_vagrantyaml(path=ctx.path,
                                                          file_name="vagrant.yaml",
                                                          hostname=host,
                                                          site='ccs-dev-1',
                                                          memory=(i[host]['memory'] / 512),
                                                          box=i[host]['box'],
                                                          role=i[host]['role'],
                                                          profile=i[host]['profile'],
                                                          domain=i[host]['domain'],
                                                          mac_nocolon=i[host]['mac'],
                                                          ip=i[host]['ip'],
                                                          )
                if retcode > 0:
                    ctx.logger.error("Failed to add host" + host)
                    ctx.logger.error("Continuing despite failure...")
            settingsyaml = {'openstack_provider': True}
            returncode = wr_settingsyaml(ctx.path, settingsyaml, hostname=host)
            if returncode > 0:
                ctx.logger.error('writing to settings yaml failed on: ' + host)
            if remote:
                myvfile.add_openstack_vm(i)
                a.v.up(vm_name=host, provider='openstack')
            else:
                myvfile.add_virtualbox_vm(i)
                a.v.up(vm_name=host)
    except IOError as e:
        ctx.logger.error("{0} for vagrant.yaml in {1}".format(e, ctx.path))
        sys.exit(1)


def name_vm(name, path):
    for i in xrange(1, 100):
        i = str(i)
        if len(i) == 1:
            i = "00" + i
        elif len(i) == 2:
            i = "0" + i
        hostname = name + "-" + i
        returncode = yaml_utils.host_exists_vagrantyaml(hostname, path)
        if returncode == 1:
            return hostname


def infra_ensure_up(mynets, float_net, path=None):
    '''Best effort to ensure infra-001 or -002 will be booted in correct env.

    Args:
        mynets (list): Comes from ensure_os_network.
                       See 'check_for_network' in openstack_utils data strctures.
        float_net(str): comes from ensure_os_network. looks like: 'Public-floating-602'
        path (str): The path to your working .stack directory

    Returns:
        0 - success, infra node has been sucessfully booted
        1 - failure

    Example:
        >>> infra_ensure_up()
            0

    Data Structure:
        From python-vagrant's status call.
        Out[3]: [Status(name='rhel7-001', state='running', provider='virtualbox')]

    Misc.:
        CalledProcessError --> subprocess exit 1 triggers this exception
    '''
    hostname = 'infra-001'
    if mynets and float_net:
        remote = True
    else:
        remote = False

    ispoweron, isremote = vm_isrunning(hostname=hostname, path=path)
    infra_connection = vagrant_utils.Connect_to_vagrant(vm_name=hostname,
                                                        path=path)

    # Note: Ensure 001 is in inventory even if we're using 002.
    if addto_inventory(hostname, path) > 0:
        return 1, hostname

    # Note: if requested remote or local and our vm's state is same then just
    #       make sure it's booted w/ ispoweron being 0 for that.
    if isremote == remote and ispoweron == 0:
        return 0, hostname
    # Note: it's what we want just not booted, so boot it.
    elif isremote == remote and ispoweron == 1:
        try:
            infra_connection.v.up(vm_name=hostname)
        except CalledProcessError:
            return 1, hostname
        return 0, hostname

    ## Shared code b/w remote and local vbox
    thisvfile = Vagrantfile_utils.SlabVagrantfile(path=path)

    # vm_isrunning currently doesn't manage these alternative states
    # so we fail
    if ispoweron == 3:
        # TODO: ERROR msg here
        return 1, hostname

    # Note: b/c the infra exists but isn't in desired location we alter hostname
    if isremote != remote:
        hostname = 'infra-002'
        infra_connection.vm_name = hostname
        if addto_inventory(hostname, path) > 0:
            return 1, hostname
        ispoweron, isremote = vm_isrunning(hostname=hostname, path=path)
        if isremote == remote and ispoweron == 0:
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

    # Note: If we're here we need to create an infra node where it was requested
    #       by the user.
    if remote:
        thisvfile._vbox_os_provider_env_vars(float_net, mynets)
        thisvfile.add_openstack_vm(host_dict)
        try:
            infra_connection.v.up(vm_name=hostname)
            return 0, hostname
        except CalledProcessError:
            return 1, hostname
    else:
        thisvfile.add_virtualbox_vm(host_dict)
        try:
            infra_connection.v.up(vm_name=hostname)
            return 0, hostname
        except CalledProcessError:
            return 1, hostname


def vm_isrunning(hostname, path):
    '''
    on/off then second return value is if it's remote.

    From python-vagrant up function (self, no_provision=False,
                                     provider=None, vm_name=None,
                                     provision=None, provision_with=None)
    '''
    vm_connection = vagrant_utils.Connect_to_vagrant(vm_name=hostname,
                                                     path=path)
    try:
        status = vm_connection.v.status()
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
    except CalledProcessError:
        # RFI: is there a better way to return here? raise exception?
        return 2, False
    # Note: 3 represent some other state --> suspended, aborted, etc.
    return 3, False


def os_ensure_network(path):
    password = os.environ.get('OS_PASSWORD')
    username = os.environ.get('OS_USERNAME')
    base_url = os.environ.get('OS_REGION_NAME')
    os_tenant_name = os.environ.get('OS_TENANT_NAME')
    float_net = ''
    mynewnets = []
    if not password or not base_url:
        # ctx.logger.error('Can --not-- boot into OS b/c password or base_url is\
        # not set')
        # ctx.logger.error('Exiting now.')
        return 1, float_net, mynewnets
    a = openstack_utils.SLab_OS(path=path, password=password, username=username,
                                base_url=base_url, os_tenant_name=os_tenant_name)
    returncode, tenant_id, temp_token = a.login_or_gettoken()
    if returncode > 0:
        # ctx.logger.error("Could not login to Openstack.")
        return 1, float_net, mynewnets
    returncode, tenant_id, token = a.login_or_gettoken(tenant_id=tenant_id)
    if returncode > 0:
        # ctx.logger.error("Could not get token to project.")
        return 1, float_net, mynewnets
    a.connect_to_neutron()

    returncode, float_net = a.find_floatnet_id(return_name="Yes")
    if returncode > 0:
        # ctx.logger.error('Could not get the name for the floating network.')
        return 1, float_net, mynewnets
    returncode, router = a.create_router()
    if returncode > 0:
        # ctx.logger.error("Could not create router in project.")
        return 1, float_net, mynewnets
    router_id = router['id']
    returncode, network = a.create_network()
    if returncode > 0:
        # ctx.logger.error("Could not create network in project.")
        return 1, float_net, mynewnets
    returncode, subnet = a.create_subnet()
    if returncode > 0:
        # ctx.logger.error("Could not create subnet in project.")
        return 1, float_net, mynewnets
    # ctx.logger.debug('Sleeping 5s b/c of slow neutron create times.')
    time.sleep(5)
    a.add_int_to_router(router_id, subnet['id'])

    mgmtname = a.create_name_for("network", append="mgmt")
    returncode, mgmt_network = a.create_network(name=mgmtname)
    if returncode > 0:
        # ctx.logger.error("Could not create network in project.")
        return 1, float_net, mynewnets
    mgmtsubname = a.create_name_for("subnet", append="mgmt")
    returncode, mgmt_subnet = a.create_subnet(name=mgmtsubname,
                                              cidr='192.168.1.0/24')
    if returncode > 0:
        # ctx.logger.error("Could not create subnet in project.")
        return 1, float_net, mynewnets
    # ctx.logger.debug('Sleeping 5s b/c of slow neutron create times.')
    time.sleep(5)
    a.add_int_to_router(router_id, mgmt_subnet['id'], mgmt=True)
    mynets = a.neutron.list_networks()

    mynewnets = []
    for i in mynets['networks']:
        if i.get('name') == network['name']:
            mynewnets.append(i)
        elif i.get('name') == mgmtname:
            mynewnets.append(i)

    return 0, float_net, mynewnets


def wr_settingsyaml(path, settingsyaml, hostname=''):
    doc = {}
    settings = os.path.join(path, 'services', 'service-redhouse-tenant', 'settings.yaml')

    returncode, float_net, mynewnets = os_ensure_network(path)
    mgmt_net = ''
    for x in mynewnets:
        if 'mgmt' in x.get('name'):
            mgmt_net = x.get('name')
    lab_net = ''
    for x in mynewnets:
        if 'SLAB' in x.get('name') and 'mgmt' not in x.get('name'):
            lab_net = x.get('name')

    base_url = os.environ.get('OS_REGION_NAME')
    if not base_url:
        # try to get base_url from settingsyaml
        # TODO: log error saying: source your OS environment's cred.s
        print('no env var base_url')
        return 1

    a = Vagrantfile_utils.SlabVagrantfile(path)
    # Note: setup host_vars under instance of class
    a.hostname = hostname
    a._vbox_os_provider_host_vars(path)

    try:
        with open(settings, 'w') as f:
            # Note: setup defaults - see service-redhouse-tenant Vagrantfile for
            #       $settings
            doc = {'openstack_provider': 'true',
                   'mgmt_network':       str(mgmt_net),
                   'lab_network':        str(lab_net),
                   'image':              a.host_vars['image'],
                   'flavor':             a.host_vars['flavor'],
                   'floating_ip_pool':   str(float_net),
                   'os_network_url':     'https://' + base_url + '.cisco.com:9696/v2.0',
                   'os_image_url':       'https://' + base_url + '.cisco.com:9292/v2',
                   }
            for k, v in settingsyaml.iteritems():
                doc[k] = v
            yaml.dump(doc, f, default_flow_style=False)
    except (OSError):
        # TODO: Log - don't have access to settings under
        # service-redhouse-tenant
        return 1


def addto_inventory(hostname, path):
    """Add a pre-defined host to inventory vagrant.yaml file, meaning
    it was created in the provision/vagrant.yaml and committed.

    Args:
        hostname (str): A string representing the hostname
        path (str):     The path to working .stack directory

    Returns:
        0 - success
        1 - failure

    Example:
        >>> addto_inventory('infra-001', ctx.path)
        0
    """
    hostexists = yaml_utils.host_exists_vagrantyaml(hostname, path)
    if not hostexists:
        returncode, host_dict = yaml_utils.gethost_byname(hostname,
                                                      os.path.join(path,
                                                                   'provision'))
        if returncode > 0:
            return 1
        returncode = yaml_utils.host_add_vagrantyaml(path=path,
                                                     file_name="vagrant.yaml",
                                                     hostname=hostname,
                                                     memory=(host_dict[hostname]['memory']/512),
                                                     box=host_dict[hostname]['box'],
                                                     role=host_dict[hostname]['role'],
                                                     profile=host_dict[hostname]['profile'],
                                                     domain=host_dict[hostname]['domain'],
                                                     mac_nocolon=host_dict[hostname]['mac'],
                                                     ip=host_dict[hostname]['ip'],
                                                     site='ccs-dev-1')
        if returncode > 0:
            return 1
    return 0

