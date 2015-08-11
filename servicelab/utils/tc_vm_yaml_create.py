#!/usr/bin/env python

import os
import re
import sys
import yaml
import pprint
import argparse
import ipaddress
import yaml_utils


def open_env_yaml(filename):
    try:
        with open(filename, 'r') as stream:
            return(yaml.load(stream))
    except IOError:
        print 'Unable to open %s' % filename
        return None


def write_file(yaml_data, output_file):
    # Write the constructed data to file
    # with open(output_file, 'w') as outfile:
    #    outfile.write(yaml.dump(yaml_data, default_flow_style=False))
    print output_file
    print yaml.dump(yaml_data, default_flow_style=False)


def create_core_vms(source_data):
    # Pull data from repo env files
    source_data = extract_env_data(source_data)
    # List of all the VM types in order of IP assignment
    # Reference http://wikicentral.cisco.com/display/nimbus/Site+IP+Assignment+Schema
    vm_types = ['percona', 'rabbitmq', 'mongodb', 'keystonectl', 'glancectl', 'cinderctl',
                'neutronapi', 'novactl', 'horizon', 'heatctl', 'ceilometerctl']
    # Quick conversion from vm number to letter for SVC AZ
    num_switch = {1: 'a', 2: 'b', 3: 'c'}
    # VM type specific flavors
    flavor = {
        'percona': '8cpu.64ram.20-512ssd',
        'rabbitmq': '4cpu.8ram.20-96sas',
        'mongodb': '8cpu.64ram.20-512ssd',
        'keystonectl': '8cpu.32ram.20-96sas',
        'glancectl': '4cpu.8ram.20-96sas',
        'cinderctl': '4cpu.8ram.20-512sas',
        'neutronapi': '4cpu.8ram.20-96sas',
        'novactl': '4cpu.8ram.20-96sas',
        'horizon': '4cpu.8ram.20-512sas',
        'heatctl': '4cpu.8ram.20-96sas',
        'ceilometerctl': '4cpu.8ram.20-96sas',
    }
    vlan = ipaddress.IPv4Network(unicode(source_data['vlan68']), strict=False)
    ip = 8

    # Standard config is 3 of each type of VM, one in each AZ of the service cloud
    for vm_type in vm_types:
        for vm_number in range(1, 4):
            source_data['hostname'] = source_data['tc_region'] + '-' + vm_type + '-' + \
                                      str(vm_number).zfill(3)
            source_data['az'] = source_data['sc_region'] + '-' + num_switch[vm_number]
            source_data['flavor'] = flavor[vm_type]
            source_data['groups'] = ['virtual', 'redhouse-tenant']
            source_data['ip'] = str(vlan.network_address + ip)
            source_data['sec_groups'] = 'default'

            # Set the role data based on the VM type
            match = re.search('(\w+)(ctl|api)$', vm_type)
            if match:
                source_data['role'] = 'tenant_' + match.group(1) + '_' + match.group(2)
            else:
                source_data['role'] = 'tenant_' + vm_type

            # Call yaml data build sub
            yaml_data = build_yaml_data(source_data, vlan)

            # Type specific settings added
            if vm_type == 'glancectl':
                if vm_number == 1:
                    yaml_data['groups'].append('glance-images')
            elif vm_type == 'horizon':
                yaml_data['groups'].remove('redhouse-tenant')
                yaml_data['groups'].append('sa_client')
                yaml_data['groups'].append('horizon')
                yaml_data['deploy_args']['app_name'] = 'cisco'
                # This key was added at the request of the horizon team
                yaml_data['ssh_public_keys'] = [
                  str('ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCoG5udLI2/VjPAgRDX9Ed4XpnXjhu' +
                      'IfiVO6sQpg5TapxWsLcj4PM6L+x4ZdS2s8SqNOsWBkX53Ts0RYxz0l9fc724YG4T821' +
                      'm8zify/xvpSy/jub+Cuj6aTSKlK5psYlyXS+9z1mx1yFtEM89192y0IvA4C0R4IelEg' +
                      'Z9eIwOJgWh8MXVcIKBVkiOlsoQmQeevEgcRQTSPs6mKQmOm4inc3s/kSTeUnV0qpCm0' +
                      '3Tqnv02Exwk1KJda4BzlAs3qQrBIvzotq0EsLYe0sF+eFs86Z9SJ7Be5YfJlKbAEjQ7' +
                      'RkOAfKcsRRsZCeEUqSmgu2suJiCY5oNprhPK/UNzgkYfN')]
            elif vm_type == 'keystonectl' or vm_type == 'neutronapi':
                yaml_data['groups'].append('sa_client')
            output_file = os.path.join(source_data['tc_path'], 'hosts.d',
                                       str(source_data['hostname'] + '.yaml'))
            write_file(yaml_data, output_file)

            # End of the loop, next node IP
            ip += 1


def find_ip(source_data):
    """

    """
    pp = pprint.PrettyPrinter(indent=2)
    all_ips = yaml_utils.get_allips_forsite(source_data['repo_path'], source_data['sc_name'])
    pp.pprint(all_ips)
    # For now, make up an IP to use
    ip = '10.207.237.252'
    return ip


def create_vm(repo_path, hostname, sc_name, tc_name, flavor='2cpu.4ram.20-96sas', vlan_id=66,
              role='none', groups=['virtual'], sec_groups='default'):
    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(repo_path)
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
    source_data['ip'] = find_ip(source_data)
    source_data['vlan_id'] = str(source_data['vlan_prefix']) + str(source_data['vlan_id'])
    vlan = ipaddress.IPv4Network(unicode(source_data[str(vlan_id)]))
    yaml_data = build_yaml_data(source_data, vlan)
    output_file = os.path.join(source_data['tc_path'], 'hosts.d',
                               str(source_data['hostname'] + '.yaml'))
    write_file(yaml_data, output_file)


def determine_az(hostname):
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
    """
    Args:
        source_data {dict}: Should have all the data needed when build with extract_env_data
        vlan {object}: ipaddress module object used to extract gateway and netmask

    Returns:
        yaml_data {dict}: Structured data for host.yaml file creation
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
        source_data {dict}: Includes the following keys and values:
                            repo_path: Path too ccs-data repo
                            sc_name: Name of the service cloud
                            tc_name: Name of the tenant cloud

    Returns:
        source_data {dict}: Includes the original data plus the following:
                            tc_path: Path to the sites/sc/env/tc/ directory
                            domain: domain name for the SC
                            sc_region: SC region value
                            vlan66/67: subnet with /mask for both vlans
                            vlan_prefix: prefix of the real 66/67 id

    """
    pp = pprint.PrettyPrinter(indent=2)

    # Open the service cloud environment.yaml
    env_path = os.path.join(source_data['repo_path'], 'sites', source_data['sc_name'],
                            'environments/')
    sc_path = os.path.join(env_path, source_data['sc_name'])
    source_data['tc_path'] = os.path.join(env_path, source_data['tc_name'])
    env_file = os.path.join(sc_path, 'data.d', 'environment.yaml')
    env_data = open_env_yaml(env_file)
    # Check for and extract the admin password and controller internal vip
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
    env_data = open_env_yaml(env_file)
    if 'cobbler::dnsmasq_interfaces' in env_data:
        for vlan_dict in env_data['cobbler::dnsmasq_interfaces']:
            match = re.search('vlan(\d{0,2}68)$', vlan_dict['name'])
            if match:
                source_data['vlan68'] = vlan_dict['gatesay'] + '/' + vlandict['netmask']
                source_data['vlan_id'] = match.group(1)
    else:
        print 'Unable to find vlan information in %s' % env_file
        return 1
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


if __name__ == '__main__':
    # Parse CLI arguments then call create core vm
    parser = argparse.ArgumentParser(description='Create service VM yamls for tenant cloud',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog='''
    The source yaml file should contain the following:
    vlan2: x.x.x.x/y    # As listed in AM or router
    vlan68: x.x.x.x/y   # As listed in AM or router
    vlan_id: X68      # Number of the 68 vlan for the tenant cloud
    service_cloud: service-cloud-name
    tenant: tenant-cloud-name
    sc_region: csm      # or csx for prod sites
    tc_region: csl-a    # unique within the service cloud
                                    ''')
    parser.add_argument('--source-yaml', '-s', type=str,
                        help='[Mandatory] Site specific yaml.')
    parser.add_argument('--path', '-p', type=str,
                        help='[Mandatory] path to CCS Data repo')
    args = parser.parse_args()

    if not args.source_yaml:
        parser.error('Site yaml was not provided.  Run with -h for details')
        parser.print_help()
    elif not args.path:
        parser.error('CCS Data repo was not provided.  Run with -h for details')
        parser.print_help()
    else:
        # Open the source file
        try:
            with open(args.source_yaml, 'r') as stream:
                source_data = yaml.load(stream)
        except:
            print 'Unable to open %s' % input_yaml
            sys.exit(1)
        source_data['repo_path'] = args.path
        create_core_vms(source_data)
