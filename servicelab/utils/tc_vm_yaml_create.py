import os
import re
import yaml
import socket
import logging
import ipaddress


# Logger creation
tcvm_logger = logging.getLogger('click_application')
logging.basicConfig()


def open_yaml(filename):
    """Opens yaml file into dictionary

    Args:
        filename {str}: File path and name to open

    Returns:
        {dict}: PyYaml extracted dict of data from the opened file

    Example Usage:
        file_data = open_yaml('/some/path/to/my/environment.yaml')
    """
    try:
        with open(filename, 'r') as stream:
            return yaml.load(stream)
    except IOError:
        tcvm_logger.error('Unable to open %s' % filename)
        return 1


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
        tcvm_logger.error('%s already exists.  Aborting host create.' % output_file)
        return 1
    # default_flow_style=False breaks lists into individual lines with leading '-'
    with open(output_file, 'w') as outfile:
        outfile.write(yaml.dump(yaml_data, default_flow_style=False))
    tcvm_logger.info(output_file)
    tcvm_logger.info('File created successfully')


def find_vlan(source_data):
    """Determines which vlan the IP belongs to from the env data.  Generates a list of all
       IPs for each vlan found within the dictionary provided, then checks if the supplied
       IP is in the list.

    Args:
       source_data {dict}: Keys needed:
          ip: IP address in standard four octect format, no mask
          <vlan-ids>: Number of the vlan for the key, subnet with mask for the value
          tc_name: Name of the tenant cloud being worked on.  Used for error message.

    Returns:
        vlan {str}: VLAN ID as extracted from the environment.yaml or '1' if no valid match

    Example Usage:
        vlan_id = find_vlan(source_data)
    """
    for key in source_data:
        match = re.search('^(\d+)$', key)
        if match:
            subnet = ipaddress.IPv4Network(unicode(source_data[key]))
            subnet_ips = list(subnet.hosts())
            for subnet_ip in subnet_ips:
                if source_data['ip'] == str(subnet_ip):
                    return key

    tcvm_logger.error('Unable to find the vlan for %s within %s'
                      % (source_data['ip'], source_data['tc_name']))
    return 1


def find_ip(env_path, vlan):
    """Finds the first unassigned IP in the selected vlan.  Searches all host.yamls in the
       service cloud environments subdirs, and does a host lookup on the remaining IPs

    Args:
       env_path {str}: path to service cloud env - ccs-data/sites/sc/environments
       vlan {obj}: ipaddress object of vlan subnet data

    Returns:
       ip {str}: First unused / unassigned IP from vlan

    Example Usage:
        find_ip('<environments path>, ipaddress.IPv4Network(unicode(10.11.12.0/24))
    """
    # Create list of ipaddress module objects of all valid IPs in the subnet
    all_ips = list(vlan.hosts())
    # Remove the first 4 IPs.  They *should* be reserved in AM anyway.
    del all_ips[0:4]
    # Find all the envs within the site
    for env in os.listdir(env_path):
        hosts_path = os.path.join(env_path, env, 'hosts.d')
        # Find all the hosts within the env
        files = os.listdir(hosts_path)
        for f in files:
            hostfile = os.path.join(hosts_path, f)
            host_data = open_yaml(hostfile)
            if 'interfaces' in host_data:
                # Not all interface names are created equally
                for interface in host_data['interfaces']:
                    # Not all interfaces have an ip_address
                    if 'ip_address' in host_data['interfaces'][interface]:
                        addy = unicode(host_data['interfaces'][interface]['ip_address'])
                        # Turn IP into ipaddress module object for list search
                        ipaddy = ipaddress.IPv4Address(addy)
                        if ipaddy in all_ips:
                            all_ips.remove(ipaddy)
    for ip in all_ips:
        try:
            # Host lookup
            socket.gethostbyaddr(str(ip))
        # socket.herror means there was no DNS reservation found
        except socket.herror:
            return str(ip)


def create_vm(repo_path, hostname, sc_name, tc_name, flavor, vlan_id, role, groups,
              sec_groups, ip_address):
    """Combine the user inputs from 'stack create host' to create a host.yaml file in the
       appropriate tenant cloud hosts.d directory

    Args:
        repo_path {str}: Patch to the ccs-data repo
        hostname {str}: User supplied name of vm to create
        sc_name {str}: Service cloud name
        tc_name {str}: Tenant cloud name
        flavor {str}: Flavor (hardware requirements) of the vm
        vlan_id {str}: Vlan number to assign IP from.  This must be present in the tenant
                       environment.yaml file
        role {str}: Role of the vm
        groups {list}: List of groups the vm should be in
        sec_groups {str}: Comma delimited str of security groups
        ip_address {str}: Either a specific IP address, or 'False'

    Returns:
        Status code.  Calls various subroutines to gather data, build the host data, and
        write the host file.

    Example usage:
        tc_vm_yaml_create.create_vm(path=<path to ccs-data repo>, hostname='my-service-001',
                                    sc_name=<service cloud>, tc_name=<tenant cloud>,
                                    flavor=<some vm flavor>, vlan_id=<vlan number(66 or 67)>,
                                    role=<none, typically>, groups=<['default', 'other']>,
                                    sec_groups='default,something,somethingelse,maybe')
    """
    if sc_name == tc_name:
        tcvm_logger.error('Please select a tenant cloud within %s' % sc_name)
        return 1
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
    if source_data == 1:
        return 1
    if not re.search(source_data['tc_region'], source_data['hostname']):
        source_data['hostname'] = source_data['tc_region'] + '-' + source_data['hostname']
    source_data['az'] = source_data['sc_region'] + determine_az(hostname)
    source_data['vlan_id'] = str(source_data['vlan_prefix']) + source_data['vlan_id']
    if vlan_id not in source_data:
        tcvm_logger.error(('Vlan%s was not found within %s.  Please try a different vlan'
                          % (vlan_id, source_data['tc_name'])))
        return 1
    if not ip_address:
        vlan = ipaddress.IPv4Network(unicode(source_data[str(vlan_id)]))
        source_data['ip'] = find_ip(source_data['env_path'], vlan)
        if not source_data['ip']:
            if str(vlan_id + '-sup') in source_data:
                vlan = ipaddress.IPv4Network(unicode(source_data[str(vlan_id + '-sup')]))
                source_data['ip'] = find_ip(source_data['env_path'], vlan)
                source_data['sup'] = True
    else:
        source_data['ip'] = ip_address
        vlan_id = find_vlan(source_data)
        if vlan_id == 1:
            return 1
        vlan = ipaddress.IPv4Network(unicode(source_data[str(vlan_id)]))
    if not source_data['ip']:
        tcvm_logger.error('Vlan%s does not have any IP addresses available' % vlan_id)
        return 1
    yaml_data = build_yaml_data(source_data, vlan)
    if 'sup' in source_data:
        yaml_data['deploy_args']['subnet_name'] += '2'
    output_file = os.path.join(source_data['tc_path'], 'hosts.d',
                               str(source_data['hostname'] + '.yaml'))
    write_file(yaml_data, output_file)
    return 0


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
    fqdn = str(source_data['hostname'] + '.' + source_data['tc_name'] + '.' +
               source_data['domain'])
    yaml_data = {
        'deploy_args': {
            'availability_zone': source_data['az'],
            'flavor': source_data['flavor'],
            'image': 'RHEL-7',
            'network_name': 'Nimbus-Management-iv%s' % source_data['vlan_id'],
            'security_groups': source_data['sec_groups'],
            'subnet_name': 'Nimbus-Management-iv%s-subnet' % source_data['vlan_id'],
            'tenant': source_data['tc_name'],
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
    # Open the service cloud environment.yaml
    env_path = os.path.join(source_data['repo_path'], 'sites', source_data['sc_name'],
                            'environments/')
    source_data['env_path'] = env_path
    sc_path = os.path.join(env_path, source_data['sc_name'])
    source_data['tc_path'] = os.path.join(env_path, source_data['tc_name'])
    env_file = os.path.join(sc_path, 'data.d', 'environment.yaml')
    env_data = open_yaml(env_file)
    if env_data == 1:
        return 1
    if 'domain_name' in env_data:
        source_data['domain'] = env_data['domain_name']
    if 'region' in env_data:
        source_data['sc_region'] = env_data['region']
    if 'site_name' in env_data:
        regex = re.escape(env_data['site_name']) + '\.([\w.]+)'
        match = re.search(regex, source_data['domain'])
        if match:
            source_data['domain'] = match.group(1)
    if 'domain' in source_data:
        pass
    else:
        return 1

    # Open the tenant cloud environment.yaml
    env_file = os.path.join(source_data['tc_path'], 'data.d', 'environment.yaml')
    env_data = open_yaml(env_file)
    if env_data == 1:
        return 1
    if 'tc_region' in env_data:
        source_data['tc_region'] = env_data['tc_region']
    else:
        tcvm_logger.error('Unable to find ServiceLab data in %s' % env_file)
        return 1
    for vlan_key in env_data:
        match = re.search('^vlan(\d{0,2})(6[367])(-sup)?$', vlan_key)
        if match:
            if match.group(3):
                source_data[match.group(2) + match.group(3)] = env_data[vlan_key]
            else:
                source_data[match.group(2)] = env_data[vlan_key]
            source_data['vlan_prefix'] = match.group(1)

    return source_data