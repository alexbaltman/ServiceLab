import os
import re
import sys
import yaml
import socket
import pprint
import argparse
import ipaddress
import yaml_utils


def open_yaml(filename):
    """Opens environment yaml into dictionary

    Args:
        filename {str}: File path and name to open

    Returns:
        {dict}: PyYaml extracted dict of data from the opened file

    Example Usage:
        file_data = open_yaml('/some/path/to/my/environment.yaml')
    """
    try:
        with open(filename, 'r') as stream:
            return(yaml.load(stream))
    except IOError:
        print 'Unable to open %s' % filename
        return None


def write_file(yaml_data, output_file):
    """Write the host.yaml file to the tenant cloud hosts.d directory.  Checks first to make
       sure the file does not already exist.

       **** NOTE ****
       The dictionary keys and subkeys will be written in alphabetical order.

    Args:
        yaml_data {dict}: Data generated by build_yaml_data subroutine
        output_file {str}: Full path and name of output file

    Returns:
        Nothing.  Writes file in tenant cloud hosts.d directory

    Example Usage:
        write_file(yaml_data, output_file)
    """
    if os.path.isfile(output_file):
        print '%s already exists.  Aborting host create.' % output_file
        return 1
    # Write the constructed data to file
    with open(output_file, 'w') as outfile:
        outfile.write(yaml.dump(yaml_data, default_flow_style=False))
    print output_file
    # print yaml.dump(yaml_data, default_flow_style=False)


def find_ip(env_path, vlan):
    """Finds the first unassigned IP in the selected vlan.  Searches all host.yamls in the
       service cloud directory, and does a host lookup on the remaining IPs

    Args:
       env_path {str}: path to service cloud env - ccs-data/sites/sc/environments
       vlan {obj}: ipaddress object of vlan subnet data

    Returns:
       ip {str}: First unused / unassigned IP from vlan

    Example Usage:
        find_ip('<environments path>, ipaddress.IPv4Network(unicode(10.11.12.0/24))
    """
    pp = pprint.PrettyPrinter(indent=2)
    # Create list of ipaddress module objects
    all_ips = list(vlan.hosts())
    # Remove the first 10 IPs.  They *should* be reserved in AM anyway.
    del all_ips[0:10]
    # Find all the clouds within the site
    for env in os.listdir(env_path):
        hosts_path = os.path.join(env_path, env, 'hosts.d')
        # Find all the hosts within the env
        files = os.listdir(hosts_path)
        for f in files:
            hostfile = os.path.join(hosts_path, f)
            host_data = open_yaml(hostfile)
            # There should not be any baremetal nodes using virtual vlans
            if 'type' in host_data:
                if host_data['type'] == 'virtual':
                    addy = unicode(host_data['interfaces']['eth0']['ip_address'])
                    # Turn IP into ipaddress module object for list search
                    ipaddy = ipaddress.IPv4Address(addy)
                    if ipaddy in all_ips:
                        all_ips.remove(ipaddy)
    remove_ips = list()
    for ip in all_ips:
        try:
            # Host lookup
            socket.gethostbyaddr(str(ip))
        except socket.herror:
            return str(ip)


def create_vm(repo_path, hostname, sc_name, tc_name, flavor, vlan_id, role, groups,
              sec_groups):
    """Combine the user inputs from 'stack create host' to create a host.yaml file in the
       appropriate tenant cloud hosts.d directory

    Args:
        repo_path {str}: Patch to the ccs-data repo
        hostname {str}: User supplied name of vm to create
        sc_name {str}: Service cloud name
        tc_name {str}: Tenant cloud name
        flavor {str}: Flavor (hardware requirements) of the vm
        vlan_id {str}: Vlan number to assign IP from
        role {str}: Role of the vm
        groups {list}: List of groups the vm should be in
        sec_groups {str}: Comma delimited str of security groups

    Returns:
        Nothing.  Calls various subroutines to gather data, build the host data, and write
        the host file.

    Example usage:
        tc_vm_yaml_create.create_vm(path=<path to ccs-data repo>, hostname='my-service-001',
                                    sc_name=<service cloud>, tc_name=<tenant cloud>,
                                    flavor=<some vm flavor>, vlan_id=<vlan number(66 or 67)>,
                                    role=<none, typically>, groups=<['default', 'other']>,
                                    sec_groups='default,something,somethingelse,maybe')
    """
    # import pdb
    # pdb.set_trace()
    pp = pprint.PrettyPrinter(indent=2)
    source_data = {'repo_path': repo_path,
                   'hostname': str(hostname),
                   'sc_name': sc_name,
                   'tc_name': tc_name,
                   'flavor': flavor,
                   'role': role,
                   'vlan_id': vlan_id,
                   'groups': groups,
                   'sec_groups': sec_groups,
                   }
    source_data = extract_env_data(source_data)
    if not re.search(source_data['tc_region'], source_data['hostname']):
        source_data['hostname'] = source_data['tc_region'] + '-' + source_data['hostname']
    source_data['az'] = source_data['sc_region'] + determine_az(hostname)
    source_data['vlan_id'] = str(source_data['vlan_prefix']) + source_data['vlan_id']
    vlan = ipaddress.IPv4Network(unicode(source_data[str(vlan_id)]))
    source_data['ip'] = find_ip(source_data['env_path'], vlan)
    yaml_data = build_yaml_data(source_data, vlan)
    output_file = os.path.join(source_data['tc_path'], 'hosts.d',
                               str(source_data['hostname'] + '.yaml'))
    write_file(yaml_data, output_file)


def determine_az(hostname):
    """Used to determine the availability zone for the vm.

    Args:
        hostname {str}: hostname as input by user from 'stack create host' command

    Returns:
        {str}: -<letter> [a-c] based on the input hostname trailing number, or -a if the
               hostname does not include a number

    Example Usage:
        my_availability_zone = determine_az('my-hostname-003')
    """
    match = re.search('(\d+)$', hostname)
    if match:
        num_switch = {1: '-a', 2: '-b', 3: '-c'}
        num = int(match.group(1))
        while num > 3:
            num -= 3
        return num_switch[num]
    else:
        return '-a'


def build_yaml_data(source_data, vlan):
    """Combines the gathered data into a dict used to write to host.yaml file

    Args:
        source_data {dict}: Should have all the data needed when build with extract_env_data
        vlan {object}: ipaddress module olbject used to extract gateway and netmask

    Returns:
        yaml_data {dict}: Structured data for host.yaml file creation

    Example Usage:
        my_vlan = ipaddress.IPv4Network(unicode(10.11.12.0/24))
        host_data = build_yaml_data(source_data, my_vlan)
    """
    # Create the core settings for all the VM types
    fqdn = str(source_data['hostname'] + '.' + source_data['tc_name'] + '.' +
               source_data['domain'])
    yaml_data = {
        'deploy_args': {
            # 'allowed_address_pairs': [],
            # 'auth_url': 'http://%s:5000/v2.0/' % str(source_data['cont_int_vip']),
            'availability_zone': source_data['az'],
            'flavor': source_data['flavor'],
            'image': 'RHEL-7',
            # 'key_name': 'tenant_deploy_key',
            'network_name': 'Nimbus-Management-iv%s' % source_data['vlan_id'],
            # 'password': source_data['admin_password'],
            # 'region': source_data['sc_region'],
            'security_groups': source_data['sec_groups'],
            'subnet_name': 'Nimbus-Management-iv%s-subnet' % source_data['vlan_id'],
            'tenant': source_data['tc_name'],
            # 'username': 'admin',
        },
        'groups': source_data['groups'],
        'hostname': fqdn,
        'interfaces': {
            'eth0': {
                'gateway': str(vlan.network_address + 1),
                'ip_address': source_data['ip'],
                'netmask': str(vlan.netmask),
            },
        },
        'role': source_data['role'],
        # 'server': source_data['server'],
        'type': 'virtual',
    }
    return yaml_data


def extract_env_data(source_data):
    """Extract needed data from SC and TC env.yaml files.

    Args:
        source_data {dict}: Includes the following keys and values
            repo_path: Path too ccs-data repo
            sc_name: Name of the service cloud
            tc_name: Name of the tenant cloud

    Returns:
        source_data {dict}: Includes the original data plus the following
            tc_path: Path to the sites/sc/env/tc/ directory
            domain: domain name for the SC
            sc_region: SC region value i.e. csm/csx
            vlan66/67: subnet with /mask for both vlans
            vlan_prefix: prefix of the real 66/67 id

    Example Usage:
        source_data = extract_env_data(source_data)
    """
    pp = pprint.PrettyPrinter(indent=2)

    # Open the service cloud environment.yaml
    env_path = os.path.join(source_data['repo_path'], 'sites', source_data['sc_name'],
                            'environments/')
    source_data['env_path'] = env_path
    sc_path = os.path.join(env_path, source_data['sc_name'])
    source_data['tc_path'] = os.path.join(env_path, source_data['tc_name'])
    env_file = os.path.join(sc_path, 'data.d', 'environment.yaml')
    env_data = open_yaml(env_file)
    if 'domain_name' in env_data:
        source_data['domain'] = env_data['domain_name']
    if 'region' in env_data:
        source_data['sc_region'] = env_data['region']
    # if 'cobbler::ip' in env_data:
        # source_data['server'] = env_data['cobbler::ip']
    # if 'controller_internal_vip' in env_data:
        # source_data['cont_int_vip'] = env_data['controller_internal_vip']
    # else:
        # print 'Unable to find controller_internal_vip in %s' % source_data['sc_name']
        # return 1
    # if 'admin_password' in env_data:
        # source_data['admin_password'] = env_data['admin_password']
    # else:
        # print 'Unable to find admin_password in %s' % source_data['sc_name']
        # return 1

    # Open the tenant cloud environment.yaml
    env_file = os.path.join(source_data['tc_path'], 'data.d', 'environment.yaml')
    env_data = open_yaml(env_file)
    if 'tc_region' in env_data:
        source_data['tc_region'] = env_data['tc_region']
    else:
        print 'Unable to find ServiceLab data in %s' % env_file
        return 1
    for vlan_key in env_data:
        match = re.search('^vlan(\d{0,2})(6[67])$', vlan_key)
        if match:
            source_data[match.group(2)] = env_data[vlan_key]
            source_data['vlan_prefix'] = match.group(1)

    return source_data
