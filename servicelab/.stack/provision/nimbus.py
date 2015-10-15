#!/usr/bin/env python

import json
import os
import socket
import sys
import yaml
import argparse

class NimbusInventory(object):
    def __init__(self):
        self.set_environ()
        hosts_data = {}
        ansible_ssh_conf = [
            ('ssh_user', 'ansible_ssh_user'),
            ('ssh_key', 'ansible_ssh_private_key_file'),
            ('ssh_host', 'ansible_ssh_host'),
            ('ssh_port', 'ansible_ssh_port')
        ]
        self.inventory = yaml.load(open('/etc/ccs/data/environments/%s/hosts.yaml' % self.environ,'r'))
        self.parse_cli_args()
        hosts_data = self.build_groups(self.inventory)
        hosts_data['_meta'] = {'hostvars': {}}
        for host,values in self.inventory.iteritems():
            hosts_data['_meta']['hostvars'][host] = values
            if host == socket.gethostname().split('.')[0]:
                hosts_data['_meta']['hostvars'][host]['ansible_connection'] = 'local'
            else:
                try:
                    hosts_data['_meta']['hostvars'][host]['ansible_ssh_host'] = values['interfaces']['eth0']['ip_address']
                except:
                    pass
                for ssh_setting, ansible_setting in ansible_ssh_conf:
                    if ssh_setting in values.keys():
                        hosts_data['_meta']['hostvars'][host][ansible_setting] = values[ssh_setting]
        if self.environ != 'switch':
          try:
            group_vars = yaml.load(open('/etc/ccs/data/environments/%s/site.yaml' % self.environ, 'r'))
            hosts_data['all']['vars'] = group_vars
          except:
            pass
        print json.dumps(hosts_data, sort_keys=True, indent=2)

    def set_environ(self):
        cur_env = os.getenv('CCS_ENVIRONMENT')
        if cur_env is None:
            sys.exit(1)
        else:
            self.environ = cur_env

    def parse_cli_args(self):
        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on Cobbler')
        parser.add_argument('--list', action='store_true', default=True, help='List instances (default: True)')
        parser.add_argument('--host', action='store', help='Get all the variables about a specific instance')
        self.args = parser.parse_args()

    def build_groups(self, hosts):
        groups = {'all': {'hosts': [], 'vars': {}}}
        for host,values in hosts.iteritems():
            groups['all']['hosts'].append(host)
            if 'role' in values.keys():
                if values['role'] not in groups.keys():
                    groups[values['role']] = []
                groups[values['role']].append(host)
            if 'groups' not in values.keys():
                continue
            for group in values['groups']:
                if group not in groups.keys():
                    groups[group] = [host]
                else:
                    groups[group].append(host)
        return groups

# Really, primarily used for Havana sites
class CompatInventory(object):
    def __init__(self):
        hosts_data = {}
        self.inventory = yaml.load(open('/etc/puppet/data/role_mappings.yaml'))
        self.data = yaml.load(open('/etc/puppet/data/cobbler/cobbler.yaml'))
        self.parse_cli_args()
        hosts_data = self.build_groups(self.inventory)
        hosts_data['_meta'] = {'hostvars': {}}
        for host,values in self.data.iteritems():
            hosts_data['_meta']['hostvars'][host] = values
        print json.dumps(hosts_data, sort_keys=True, indent=2)

    def parse_cli_args(self):
        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on Cobbler')
        parser.add_argument('--list', action='store_true', default=True, help='List instances (default: True)')
        parser.add_argument('--host', action='store', help='Get all the variables about a specific instance')
        self.args = parser.parse_args()

    def build_groups(self, hosts):
        groups = {'all': {'hosts': [], 'vars': {}}}
        for host in hosts:
            groups['all']['hosts'].append(host)
            if hosts[host] not in groups.keys():
                groups[hosts[host]] = []
            groups[hosts[host]].append(host)
        return groups

# If we are in an older environment, Havana, and there is no switch or
# hosts.yaml, then we should revert to a compatible inventory with the same
# end results
if os.getenv('CCS_ENVIRONMENT') is None and not os.path.isfile('/etc/puppet/data/hosts.yaml'):
    CompatInventory()
else:
    NimbusInventory()
