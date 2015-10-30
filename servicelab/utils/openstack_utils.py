import os
import yaml
import time
import logging

from keystoneclient.exceptions import AuthorizationFailure, Unauthorized
from neutronclient.neutron import client as neutron_client
from keystoneclient.v2_0 import client

import helper_utils

# create logger
# TODO: For now warning and error print. Got to figure out how
#       to import the one in stack.py properly.
openstack_utils_logger = logging.getLogger('click_application')
logging.basicConfig()


class SLab_OS(object):

    def __init__(self, path, password, base_url, url_domain=".cisco.com", username=None,
                 os_tenant_name=''):
        """Init some of the variables we'll use to manipulate our Openstack tenant.

        Args:
            path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
            password (str): This is the string base password associated with your
                            Openstack (OS) tenant/project.
            username (str): This is the username associated with your project /
                            tenant in OS. It should be your CEC and, until we make
                            it less fragile, it should be the same on your laptop
                            as what's in the OS auth provider.
            base_url (str): This is the base url of where your horizon presents
                            an OS endpoint. It might look like "us-rdu-2" or
                            "us-rdu-3" or "rtp10-svc-1".
            url_domain (str): This is the domain associated with the horizon
                              endpoint. It may look like "cisco.com" or
                              "cloud.cisco.com".
            os_tenant_name (str): This is the Tenant aka project in OS to address.
                                  without this we won't know how to name our neutron
                                  items or what project to address under a user if
                                  there's more than one.

        Returns:
            Nothing. All these variables are instantiated as part of the
            instance of the class.

        Example Usage:
            >>> a = SLab_OS(password="donttell", base_url="us-rdu-3")
        """
        if not username:
            returncode, username = helper_utils.set_user(ctx.path)
            if returncode > 0:
                openstack_utils_logger.error("Couldn't set username.")
        self.path = path
        self.username = username
        self.password = password
        self.base_url = base_url
        self.url_domain = url_domain
        self.os_tenant_name = os_tenant_name
        self.auth_url = ""
        self.tenant_id = ""

    def login_or_gettoken(self, tenant_id=''):
        """Login to an Openstack endpoint (probably a tenant cloud) or get a keystone token.

        The reason for the dual logic here is because if you login to keystone without
        providing a tenant id you will get a token, but it's a limited token in that it
        doesn't belong to any tenant. If you use that token to attempt something you will
        get a lack of privledges error; however, if you login twice once without a
        tenant_id and the second time with a tenant_id b/c you're limited login allows you
        to geta tenant id you will avoid the error and can begin modifying your environment.

        Args:
            self.tenant_id (str): An openstack unique identifier for a project/tenant. It
                                  looks like this: "2e3e3bb7ce9f4ab6912da0e500a822ac".
            self.base_url (str): Not required input - uses the values from the instantiated
                                 instance of the class. It will build auth_url from this. It
                                 is a string that may look like "us-rdu-3" or "us-rdu-2".
            self.url_domain (str): Not required input - uses the values from the instantiated
                                   instance of the class. It will build auth_url from this.
                                   It is a string that looks like "cisco.com" or
                                   "cloud.cisco.com".
        Returns:
            self.auth_url (str): Not direct output - uses the values from the instantiated
                                 instance of the class to build this. If base_url is
                                 "us-rdu-2" and url_domain is "cisco.com" you'll get an auth
                                 url attached to self (instance of class) that looks like:
                                 "https://us-rdu-2.cisco.com:5000/v2.0".
            tenant_id (str): An openstack unique identifier for a project/tenant. It looks
                             like this: "2e3e3bb7ce9f4ab6912da0e500a822ac".
            self.token (str): An openstack string used for authentication into general OS or
                              specifically a project in OS that you are the owner of.
                              TODO: Add an example token here.
            Returncode (int):
                0 - Success
                1 - failure

        Example Usage:
            >>> print a.login_or_gettoken()
           0, 2e3e3bb7ce9f4ab6912da0e500a822ac, 4946e8af849f46879ea08796274d1d46
            >>> print a.login_or_gettoken(tenant_id="2e3e3bb7ce9f4ab6912da0e500a822ac")
           0, 2e3e3bb7ce9f4ab6912da0e500a822ac, 3e03f91d8ee549e6bf9337169141103e

        Example OS return of a list of tenant objects:
            [<Tenant {u'enabled': True, u'description': u'', u'name': u'ServiceLab',
                      u'id': u'2e3e3bb7ce9f4ab6912da0e500a822ac'}>]
        """
        self.auth_url = 'https://' + self.base_url + self.url_domain + ':5000/v2.0'

        try:
            if not tenant_id:
                keystone = client.Client(username=self.username, password=self.password,
                                         auth_url=self.auth_url)
                self.token = keystone.auth_token
                all_tenants = keystone.tenants.list()
                # TODO: Look for one in cache rather than just failing.

                for tenant in all_tenants:
                    if self.os_tenant_name == tenant.name:
                        self.tenant_id = tenant.id
                        break

                if not self.tenant_id:
                    openstack_utils_logger.error("Unable to determine tenant_id"
                                                 "for {}".format(self.os_tenant_name))
                    return 1, self.tenant_id, self.token
                return 0, self.tenant_id, self.token
            else:
                keystone = client.Client(username=self.username, password=self.password,
                                         auth_url=self.auth_url, tenant_id=self.tenant_id)
                self.token = keystone.auth_token
                return 0, self.tenant_id, self.token

        except AuthorizationFailure as auth_failure:
            openstack_utils_logger.error(auth_failure.message)
            return 1, self.tenant_id, self.token
        except Unauthorized as unauthorized:
            openstack_utils_logger.error(auth_failure.message)
            return 1, self.tenant_id, self.token

    def connect_to_neutron(self):
        """Connect to neutron post the dual keystone login.

        Now that you're connected authenticated to keystone you have to sync up to the
        neutron endpoint. It uses port 9696. It actually imports keystone again. They're
        looking to resolve this duplication so we may not have to do this in the future.
        We would still have to make a connection to port 9696 though for these REST calls.

        Args:
            None - the instance's variables should already be set for us to use this
                   function.

        Returns:
            Returncode:
                0 - Success --> currently doesn't catch any exceptions yet.
                TODO: Figure out what exceptions to capture and report back to calling
                      function. return 1 on failure.

        Example Usage:
            >>> print a.connect_to_neutron()
            0
        """
        self.endpoint_url = "https://" + self.base_url + self.url_domain + ":9696"
        self.neutron = neutron_client.Client('2.0', endpoint_url=self.endpoint_url,
                                             token=self.token)
        self.neutron.format = 'json'
        return 0

    def create_name_for(self, neutron_type, append=""):
        """Generates some consistent naming for us to use and reference.

        Args:
            neutron_type (str): The neutron type can be a subnet, network, or router.
                                We'll use this to help create a name.
            append (str): If you want more than the default name ie. "mgmt" included
                          in your naming scheme then you can add that extra piece
                          to the string there otherwise this will be "". It does not
                          get added to the end of the string, but after the username.

        Returns:
            name (str): A not so unique name is created depending on the type of
                        neutron object we're dealing with; however, we will still
                        get a unique id given from OS itself that we can cache
                        locally.

        Example Usage:
            >>> print a.create_name_for("subnet")
            SLAB_Servicelab2_aaltman_subnet
            >>> print a.create_name_for("subnet", "mgmt")
            SLAB_Servicelab2_aaltman_mgmt_subnet
        """
        if append:
            append = "_" + append

        sub_name = self.os_tenant_name or self.tenant_id[:8]
        name = "SLAB_%s%s_%s_%s" % (self.username, append, sub_name,
                                    neutron_type)
        return name

    def check_for_network(self, name):
        """Check to see if the named network exists.

        Args:
            name (str): The name of the network you would like to see if it
                        exists in your tenant/project or not. If needed and
                        you're not sure of the name you can always generate
                        it from the create_name_for() function.

        Returns:
            Returncode (int):
                0 - Success
                1 - Failure
            network (dict): It returns the first network that matches
                            the named network that you're looking for.
                            See the example for what that dict looks like.

        Example Usage:
            >>> print a.check_for_network("SLAB_aaltman_network")
            0, {u'status': u'ACTIVE',
                u'subnets': [],
                u'name': u'SLAB_aaltman_network',
                u'admin_state_up': True,
                u'tenant_id': u'2e3e3bb7ce9f4ab6912da0e500a822ac',
                u'shared': False,
                u'id': u'c42bf975-8ef3-43d3-94a4-fde3251b7cf3'
                }

        Example Networks list:
             {'networks': [{u'admin_state_up': True,
              u'id': u'364c4cc8-dbc0-406b-b996-b20f1e164b74',
              u'name': u'public-floating-602',
              u'router:external': True,
              u'shared': False,
              u'status': u'ACTIVE',
              u'subnets': [u'2a033745-4f29-4eaa-9fff-15a1fa62d8f7',
              u'386ef54a-2eb9-4e56-9c3b-421fe99cc17f'],
              u'tenant_id': u'5b7ae6322eed4f22958b2779f36bf7f4'},
             {u'admin_state_up': True,
              u'id': u'5e44df27-6940-4415-b0ab-216d4fd94ea6',
              u'name': u'SLAB_aaltman_network',
              u'router:external': False,
              u'shared': False,
              u'status': u'ACTIVE',
              u'subnets': [],
              u'tenant_id': u'2e3e3bb7ce9f4ab6912da0e500a822ac'}]}
        """
        networks = self.neutron.list_networks()
        network = ""
        parts = name.split('_')
        # ['SLAB', 'Servicelab2', 'aaltman', 'mgmt', 'network']
        parts = [i for i in parts if i in ['SLAB', 'mgmt', 'network', 'subnet', 'router']]
        # ['SLAB', 'mgmt', 'network']
        for network in networks['networks']:
            if all(i in network['name'] for i in parts):
                if 'mgmt' not in parts and 'mgmt' in network['name']:
                    continue
                else:
                    return 0, network
        return 1, network

    def check_for_subnet(self, name):
        """Check to see if the named subnet exists.

        Args:
            name (str): The name of the subnet you would like to see if it
                        exists in your tenant/project or not. If needed and
                        you're not sure of the name you can always generate
                        it from the create_name_for() function.

        Returns:
            Returncode (int):
                0 - Success
                1 - Failure
            subnet (dict): It returns the first subnet that matches
                            the named subnet that you're looking for.
                            See the example for what that dict looks like.

        Example Usage:
            >>> print a.check_for_subnet("SLAB_aaltman_subnet")
            0, {u'name': u'SLAB_aaltman_subnet',
                u'enable_dhcp': True,
                u'network_id': u'c42bf975-8ef3-43d3-94a4-fde3251b7cf3',
                u'tenant_id': u'2e3e3bb7ce9f4ab6912da0e500a822ac',
                u'dns_nameservers': [],
                u'ipv6_ra_mode': None,
                u'allocation_pools': [{u'start': u'192.168.100.2',
                                       u'end': u'192.168.100.254'}],
                u'gateway_ip': u'192.168.100.1',
                u'ipv6_address_mode': None,
                u'ip_version': 4,
                u'host_routes': [],
                u'cidr': u'192.168.100.0/24',
                u'id': u'bd738973-2d66-4e19-b67c-1ee261244a91'
                }

            We should expect in a return 0 scenario that the subnet was
            created and associated to a network of essentially the same
            name "SLAB_aaltman_network".
        """
        subnets = self.neutron.list_subnets()
        subnet = ""
        parts = name.split('_')
        # ['SLAB', 'Servicelab2', 'aaltman', 'mgmt', 'subnet']
        parts = [i for i in parts if i in ['SLAB', 'mgmt', 'network', 'subnet', 'router']]
        # ['SLAB', 'mgmt', 'subnet']
        for subnet in subnets['subnets']:
            if all(i in subnet['name'] for i in parts):
                if 'mgmt' not in parts and 'mgmt' in subnet['name']:
                    continue
                else:
                    return 0, subnet
        return 1, subnet

    def check_for_router(self, name):
        """Check to see if the named router exists.

        Args:
            name (str): The name of the router you would like to see if it
                        exists in your tenant/project or not. If needed and
                        you're not sure of the name you can always generate
                        it from the create_name_for() function.

        Returns:
            Returncode (int):
                0 - Success
                1 - Failure
            router (dict): It returns the first router that matches
                            the named router that you're looking for.
                            See the example for what that dict looks like.

        Example Usage:
            >>> print a.check_for_router("SLAB_aaltman_router")
            0, {u'status': u'ACTIVE',
                u'external_gateway_info': {u'network_id': u'364c4cc8-dbc0-406b\
                                                            -b996-b20f1e164b74'},
                u'name': u'SLAB_aaltman_router',
                u'admin_state_up': True,
                u'tenant_id': u'2e3e3bb7ce9f4ab6912da0e500a822ac',
                u'id': u'58c068d7-1937-4c63-ab09-d2025d9336d1'
                }
        """
        routers = self.neutron.list_routers()
        router = ""
        parts = name.split('_')
        # ['SLAB', 'Servicelab2', 'aaltman', 'mgmt', 'router']
        parts = [i for i in parts if i in ['SLAB', 'mgmt', 'network', 'subnet', 'router']]
        # ['SLAB', 'mgmt', 'router']
        for router in routers['routers']:
            if all(i in router['name'] for i in parts):
                if 'mgmt' not in parts and 'mgmt' in router['name']:
                    continue
                else:
                    return 0, router
        return 1, router

    def check_for_ports(self, mgmt=False):
        """Check to see if ports exist on router from SLAB's networks' subnets.

        Args:
            mgmt (bool): If it's true we're looking for Servicelab's mgmt network.
                         Otherwise we're looking for the regular servicelab network

        Returns:
            Returncode (int):
                0 - Success
                1 - Failure

        Example Usage:
            >>> print a.check_for_ports()
            0

        Data Structure:
            >>> a.neutron.list_ports()
           {'ports': [{u'admin_state_up': True,
           u'allowed_address_pairs': [],
           u'binding:vnic_type': u'normal',
           u'device_id': u'dhcp18d9e9ce-a714-5869-
                           a6df-8c5339b4a142-6d5d4d54-
                           fbec-41a0-91fe-e61c5b0d9ac2',
           u'device_owner': u'network:dhcp',
           u'extra_dhcp_opts': [],
           u'fixed_ips': [{u'ip_address': u'192.168.1.3',
             u'subnet_id': u'0007e613-64ee-4f55-91fb-b6ec7516abc5'}],
           u'id': u'0a205618-c716-4fd3-86ee-7450bdcf2201',
           u'mac_address': u'fa:16:3e:84:24:fc',
           u'name': u'',
           u'network_id': u'6d5d4d54-fbec-41a0-91fe-e61c5b0d9ac2',
           u'security_groups': [],
           u'status': u'ACTIVE',
           u'tenant_id': u'4ab4b8260df84a869782e2a3a5bf6101'},
          {u'admin_state_up': True,
           u'allowed_address_pairs': [],
           u'binding:vnic_type': u'normal',
           u'device_id': u'dhcp18d9e9ce-a714-5869-
                           a6df-8c5339b4a142-e29e9fa3-
                           9289-4430-b234-c1efa288c23e',
           u'device_owner': u'network:dhcp',
           u'extra_dhcp_opts': [],
           u'fixed_ips': [{u'ip_address': u'192.168.100.3',
             u'subnet_id': u'aa8eb260-5616-4cda-a02d-c57d731880dd'}],
           u'id': u'0cf53ade-c2bf-47ef-830b-e4ba705fbad5',
           u'mac_address': u'fa:16:3e:3d:25:fe',
           u'name': u'',
           u'network_id': u'e29e9fa3-9289-4430-b234-c1efa288c23e',
           u'security_groups': [],
           u'status': u'ACTIVE',
           u'tenant_id': u'4ab4b8260df84a869782e2a3a5bf6101'},]}
        """
        ports = self.neutron.list_ports()
        for i in ports['ports']:
            if i.get('device_owner') == 'network:router_interface':
                mysub = i.get('fixed_ips')
                mysub = self.neutron.show_subnet(mysub[0]['subnet_id'])
                if mgmt:
                    if all(i in mysub['subnet']['name'] for i in ['SLAB', 'mgmt']):
                        return 0
                else:
                    if 'SLAB' in mysub['subnet']['name']:
                        if 'mgmt' not in mysub['subnet']['name']:
                            return 0
        return 1

    def create_network(self, name=""):
        """Create a network in OS tenant/project.

        Args:
            name (str): The name for the neutron object you would
                        like created instead of the regular name
                        provided by create_name_for() function.

        Returns:
            Returncode:
                0 - Success
                1 - Failure
            network (dict): We return a dict of the network's attributes that
                            arises from the response to the creation of a network
                            in the project/tenant in OS.

        Example Usage:
            >>> print a.create_network()
            0, {u'status': u'ACTIVE',
                u'subnets': [],
                u'name': u'SLAB_aaltman_network',
                u'admin_state_up': True,
                u'tenant_id': u'2e3e3bb7ce9f4ab6912da0e500a822ac',
                u'shared': False,
                u'id': u'c42bf975-8ef3-43d3-94a4-fde3251b7cf3'
                }
        """
        if not name:
            name = self.create_name_for("network")

        returncode, network = self.check_for_network(name)
        if returncode == 1:
            network = {'name': name, 'admin_state_up': True, 'tenant_id': self.tenant_id}
            self.neutron.create_network({'network': network})
            returncode2, network = self.check_for_network(name)
            if returncode2 == 0:
                self.write_to_cache(network)
                return 0, network
            else:
                openstack_utils_logger.error("Tried to make the network, but failed.")
                return 1, network
        else:
            return 0, network

    def create_router(self, name=""):
        """Create a router in your OS tenant/project.

        Args:
            name (str): The name for the router you would
                        like created instead of the regular name
                        provided by create_name_for() function.
         Returns:
            Returncode:
                0 - Success
                1 - Failure
            router (dict): We return a dict of the router's attributes that
                           arises from the response to the creation of a router
                           in the project/tenant in OS.

        Example Usage:
            >>> print a.create_router()
            0, {u'status': u'ACTIVE',
                u'external_gateway_info': {u'network_id': u'364c4cc8-dbc0-406b\
                                                            -b996-b20f1e164b74'},
                u'name': u'SLAB_aaltman_router',
                u'admin_state_up': True,
                u'tenant_id': u'2e3e3bb7ce9f4ab6912da0e500a822ac',
                u'id': u'58c068d7-1937-4c63-ab09-d2025d9336d1'
                }
        """
        if not name:
            name = self.create_name_for("router")

        returncode, router = self.check_for_router(name)
        if returncode == 1:
                returncode2, external_net_id = self.find_floatnet_id()
                if returncode2 > 0:
                    openstack_utils_logger.error("Tried to make the router, but failed\
                                                  b/c can't find public floating network.")
                    return 1, router
                else:
                    router = {'name': name, 'admin_state_up': True, 'external_gateway_info':
                              {'network_id': external_net_id, 'external_snat': True}
                              }
                    self.neutron.create_router({'router': router})
                    returncode3, router = self.check_for_router(name)
                    if returncode3 == 0:
                        self.write_to_cache(router)
                        return 0, router
                    else:
                        openstack_utils_logger.error("Tried to make the router, "
                                                     "but failed.")
                        return 1, router
        else:
            return 0, router

    def check_for_security_group(self, name):
        """Check to see if the named security_group exists.

        Args:
            name (str): The name of the security_group you would like to see
                        if it exists in your tenant/project or not. If needed
                        and you're not sure of the name you can always generate
                        it from the create_name_for() function.

        Returns:
            Returncode (int):
                0 - Success
                1 - Failure
            security_group (dict): It returns the first security_group
                                   that matches the named subnet that
                                   you're looking for.
        Example Usage:
            >>> print a.check_for_security_group("SLAB_aaltman_security_group")

            We should expect in a return 0 scenario that the security_group was
            created.
        """
        security_groups = self.neutron.list_security_groups()
        security_group = ""
        parts = name.split('_')
        # ['SLAB', 'Servicelab2', 'aaltman', 'mgmt', 'subnet']
        parts = [i for i in parts if i in ['SLAB', 'mgmt', 'network',
                                           'subnet', 'router',
                                           'security_group']
                 ]
        # ['SLAB', 'mgmt', 'subnet']
        for security_group in security_groups['security_groups']:
            if all(i in security_group['name'] for i in parts):
                if 'mgmt' not in parts and 'mgmt' in security_group['name']:
                    continue
                else:
                    return 0, security_group
        return 1, security_group

    def create_security_group(self, name=""):
        """Create a security group in your OS tenant/project.

        Args:
            name (str): The name for the security group you would
                        like created
         Returns:
            Returncode:
                0 - Success
                1 - Failure
            security_group (dict): We return a dict of the security
                                   group attributes that arises from
                                   the response to the creation of a
                                   security_group in the project/tenant
                                   in OS.
        Example Usage:
            >>> print a.create_security_group()
        """
        if not name:
            name = self.create_name_for("security_group")

        returncode, security_group = self.check_for_security_group(name)
        if returncode == 1:
            security_group = {'name': name,
                              'description': 'SLAB default security group'
                              }
            self.neutron.create_security_group(
                {'security_group': security_group})
            returncode3, security_group = self.check_for_security_group(name)
            self.neutron.create_security_group_rule({
                'security_group_rule': {
                    'direction': 'ingress',
                    'remote_group_id': None,
                    'remote_ip_prefix': '0.0.0.0/0',
                    'port_range_min': None,
                    'ethertype': 'IPv4',
                    'port_range_max': None,
                    'protocol': 'icmp',
                    'tenant_id': security_group['tenant_id'],
                    'security_group_id': security_group['id']
                }})
            self.neutron.create_security_group_rule({
                'security_group_rule': {
                    'direction': 'ingress',
                    'remote_group_id': None,
                    'remote_ip_prefix': '0.0.0.0/0',
                    'port_range_min': 0,
                    'ethertype': 'IPv4',
                    'port_range_max': 65535,
                    'protocol': 'tcp',
                    'tenant_id': security_group['tenant_id'],
                    'security_group_id': security_group['id']
                }})
            returncode3, security_group = self.check_for_security_group(name)

            if returncode3 == 0:
                return 0, security_group
            else:
                openstack_utils_logger.error(
                    "Tried to make the security group, but failed.")
                return 1, security_group
        else:
            return 0, security_group

    def create_subnet(self, name="", cidr="192.168.100.0/24"):
        """Create a subnet in your teannt/project in OS.

        Args:
            cidr (str): A network (e.g. 192.168.100.0) with it's associated netmask
                        bits (e.g. /24, /8) to look like "192.168.100.0/24". For more
                        details see:
                        "https://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing".
        Returns:
            Returncode:
                0 - Success
                1 - Failure
            subnet (dict): We return a dict of the subnet's attributes that
                           arises from the response to the creation of a router
                           in the project/tenant in OS.

        Example Usage:
            >>> print a.create_subnet()
            0, {u'name': u'SLAB_aaltman_subnet',
               u'enable_dhcp': True,
               u'network_id': u'c42bf975-8ef3-43d3-94a4-fde3251b7cf3',
               u'tenant_id': u'2e3e3bb7ce9f4ab6912da0e500a822ac',
               u'dns_nameservers': [],
               u'ipv6_ra_mode': None,
               u'allocation_pools': [{u'start': u'192.168.100.2',
                                      u'end': u'192.168.100.254'}],
               u'gateway_ip': u'192.168.100.1',
               u'ipv6_address_mode': None,
               u'ip_version': 4,
               u'host_routes': [],
               u'cidr': u'192.168.100.0/24',
               u'id': u'bd738973-2d66-4e19-b67c-1ee261244a91'
               }
        """
        subnet = ""
        if not name:
            name = self.create_name_for("subnet")
            net_name = self.create_name_for("network")
            returncode, network = self.check_for_network(net_name)
            if returncode == 0:
                net_id = network['id']
            else:
                openstack_utils_logger.error("Can't attach subnet to network\
                                             provided because it doesn't exist.")
                return 1, subnet
        else:
            net_name = name.replace("subnet", "network")
            returncode, network = self.check_for_network(net_name)
            if returncode == 0:
                net_id = network['id']
            else:
                openstack_utils_logger.error("Can't attach subnet to network\
                                             provided because it doesn't exist.")
                return 1, subnet

        returncode2, subnet = self.check_for_subnet(name)
        if returncode2 == 1:
            base_cidr, bitmask = cidr.split('/')
            oct1, oct2, oct3, oct4 = base_cidr.split(".")
            oct4 = str(int(oct4) + 1)
            gateway_ip = ".".join([oct1, oct2, oct3, oct4])
            subnet = {'name': name, 'network_id': net_id, 'ip_version': 4,
                      'cidr': cidr, 'tenant_id': self.tenant_id, 'gateway_ip':
                      gateway_ip}
            self.neutron.create_subnet({'subnet': subnet})
            returncode3, subnet = self.check_for_subnet(name)
            if returncode3 == 0:
                self.write_to_cache(subnet)
                return 0, subnet
            else:
                openstack_utils_logger.error("Failed to create the subnet.")
                return 1, subnet
        else:
            return 0, subnet

    def create_floatingip(self):
        """Create floating ip in your OS project/tenant.

        Args:
            None.

        Returns:
            Returncode:
                0 - Success
                1 - Failure

        Example Usage:
            >>> print a.create_floatingip()
            0
        """
        returncode, external_net_id = self.find_floatnet_id()
        if returncode > 0:
            openstack_utils_logger.error("Tried to make the router, but failed\
                                          b/c can't find public floating network.")
            return 1
        floatingip = {'floating_network_id': external_net_id, 'tenant_id': self.tenant.id}
        floatingip = self.neutron.create_floatingip({'floatingip': floatingip})
        # TODO: check if success b4 returning 0
        self.write_to_cache(floatingip)
        return 0

    def find_floatnet_id(self, return_name=""):
        """Find the public floating network by searching all networks by name.

        This is a network that contains the publicly addressable ip range
        outside of OS. Typically this network is called "public-floating-601",
        but can differ depending on how many tenant clouds are sharing the same
        network backbone. For instance, in us-rdu-3 the public float is
        "public-floating-602".

        Args:
            return_name (str): Either empty so it resolves to false or Yes as
                               the preferred string. Right now it could take
                               anything technically.

        Returns:
            id (str): This is the unique identifier provided by OS on a
                      per component basis. For instance, if you create a new
                      subnet it will get an id or if you create a new router
                      it will get an id, etc.
                      Ex id:  364c4cc8-dbc0-406b-b996-b20f1e164b74
            name (str): If set to "Yes" you can get the name instead of the id.
            Returncode (int):
                0 - Success
                1 - Failure

        Example Usage:
            >>> print a.find_floatnet_id()
            0, 364c4cc8-dbc0-406b-b996-b20f1e164b74
        """
        _id = ""
        float_name = ""
        networks = self.neutron.list_networks()
        for i in networks['networks']:
            if "public-floating" in i['name']:
                _id = i['id']
                float_name = i['name']
                if return_name:
                    return 0, float_name
                return 0, _id
        openstack_utils_logger.error('Failed to find public-floating-\* '
                                     'in networks names')
        return 1, _id

    def del_in_project(self, neutron_type, id):
        """Delete a neutron object (subnet, network, router, floatingip) in a
           tenant/project in OS.

        TODO: This delete is going to get more complicated b/c you have to del
              things in order and often times they fail or you don't have the
              permissions to delete them so when we add that functionality
              we'll update.

        Args:
            neutron_type (str): The type of neutron object you're trying to
                                work with, including subnet, router, network,
                                or floatingip.
            id (str): This is the unique identifier provided by OS on a
                      per component basis. For instance, if you create a new
                      subnet it will get an id or if you create a new router
                      it will get an id, etc.
                      Ex id: 364c4cc8-dbc0-406b-b996-b20f1e164b74
        Returns:
            Returncode (int):
                0 - Success
                1 - Failure

        Example Usage:
            >>> print a.del_in_project(subnet, "bd738973-2d66-4e19-b67c-1ee261244a91")
            0
        """
        if neutron_type == "network":
            self.neutron.delete_network(id)
            returncode = self.check_for_network(id)
            if returncode > 0:
                return 0
            else:
                openstack_utils_logger.error("Failed to delete network.")
                return 1
        elif neutron_type == "router":
            self.neutron.delete_router(id)
            returncode = self.check_for_router(id)
            if returncode > 0:
                return 0
            else:
                return 1
        elif neutron_type == "subnet":
            self.neutron.delete_subnet(id)
            returncode = self.check_for_subnet(id)
            if returncode > 0:
                return 0
            else:
                return 1
        elif neutron_type == "floatingip":
            self.neutron.delete_floatingip(id)
            # TODO: return 1 until we have real check in place.
            return 1

    def add_int_to_router(self, router_id, subnet_id, mgmt=False):
        """Add a port to a router to an internal network.

        Args:
            subnet_id (str): This is the unique identifier provided by OS on a
                      per component basis, including the subnet..
                      TODO: Add example id.
            router_id (str): This is the unique identifier provided by OS on a
                      per component basis, including the router..

        Returns:
            Returncode (int):
                0 - Success
                1 - Failure

        Example Usage:
            >>> print a.add_int_to_router(subnet_id: "2a033745-4f29-4eaa-9fff-15a1fa62d8f7")
            0

        Example port add interface response:
            {u'subnet_id': u'bd738973-2d66-4e19-b67c-1ee261244a91',
             u'tenant_id': u'2e3e3bb7ce9f4ab6912da0e500a822ac',
             u'port_id': u'ca7c8de8-1b99-4a76-9297-0c171f804a13',
             u'id': u'58c068d7-1937-4c63-ab09-d2025d9336d1'}
        """
        # RFI: Read router id from cache and read subnet id from cache?
        returncode = self.check_for_ports(mgmt=mgmt)
        if returncode == 1:
            # Note: we'll get an exception here that will fail the code
            #       so there isn't a return 1 yet until that's processed.
            port = self.neutron.add_interface_router(router_id,
                                                     {'subnet_id': subnet_id}
                                                     )
        # TODO: write to cache if port has id returned aka is a success else fail.
            self.write_to_cache(port)
            return 0
        else:
            return 0

    def write_to_cache(self, writeit):
        """Write a dictionary item to cache.

        Args:
            writeit (dict): This should be a dictionary so that we can post
                    the data as yaml. We can append it

        Returns:
            Returncode (int):
                0 - Success
                1 - Failure

        Example Usage:
            >>> print a.write_to_cache({"this": "is", "a": "dictionary"})
            0

        TODO: catch exceptions so I can return 1 on failure. Or check to see if
              if an item is already in dict.
        """
        # Note: write should be a dictionary so we can write as yaml
        self.OS_ids_cachefile = os.path.join(self.path, "cache", "OS_ids.yaml")
        if os.path.exists(self.OS_ids_cachefile):
            with open(self.OS_ids_cachefile, 'a') as f:
                f.write(yaml.dump(writeit, default_flow_style=False))
                return 0
        else:
            with open(self.OS_ids_cachefile, 'w') as f:
                f.write(yaml.dump(writeit, default_flow_style=False))
                return 0

    def get_from_cache(self, neutron_type, get_this):
        """Get a dictionary item from yaml file serving as cache.

        Args:
            neutron_type (str): The type of neutron object you're trying to
                                work with, including subnet, router, network,
                                or floatingip.
            Get_this (str - dict key): This should be a relevant dictionary key
                                       for the neutron_type you're fetching.

        Returns:
            d (dict value): This could be a section of a dictionary or a single
                            value depending on what your input was. It will only
                            be related to what neutron_type was used in the call.
            Returncode (int):
                0 - Success
                1 - Failure

        Example Usage:
            >>> print a.get_from_cache("subnet", TODO: put maybe interpolated "id" here.)
            0, TODO: show example item
        """

        # Note: get_this should be some sort of key in one of the neutron
        #      types. Pls see the create function for more details.
        self.OS_ids_cachefile = os.path.join(self.path, cache, "OS_ids.yaml")
        if os.path.exists(self.OS_ids_cachefile):
            with open(OS_ids_cachefile, 'r') as f:
                d = yaml.load(f)
                return 0, d[get_this]
        else:
            return 1, d[get_this]


def os_ensure_network(path):
    """
    Args:
        path (str): Your working .stack directory, typically ctx.path

    Returns:
        Returncode (int):
            0 -
            1 -
        Float_net ():
        mynewnets ():
        security_groups ():

    Example Usage:
        >>> os_ensure_network(ctx.path)
        0, 'public-floating-602', [{u'status': u'ACTIVE', u'subnets':
                                   [u'5b4cb651-11f5-4a34-a18f-ea02c9d2a640'],
                                   u'name': u'SLAB_aaltman_mgmt_network', u'admin_state_up':
                                   True, u'tenant_id': u'4ab4b8260df84a869782e2a3a5bf6101',
                                   u'router:external': False, u'shared': False, u'id':
                                   u'788d801a-e98c-42cb-9938-f67a49f30258'}],

                                   Security group example --> to be filled in

    """
    password = os.environ.get('OS_PASSWORD')
    username = os.environ.get('OS_USERNAME')
    base_url = os.environ.get('OS_REGION_NAME')
    float_net = ''
    mynewnets = []
    security_groups = []

    if not password or not base_url:
        openstack_utils_logger.error('Can --not-- boot into OS b/c password or base_url is\
        not set')
        openstack_utils_logger.error('Exiting now.')
        return 1, float_net, mynewnets, security_groups

    a = SLab_OS(path=path, password=password, username=username,
                base_url=base_url)
    a.tenant_id = os.environ.get('OS_TENANT_ID')
    a.os_tenant_name = os.environ.get('OS_TENANT_NAME')
    if not a.tenant_id:
        returncode, a.tenant_id, temp_token = a.login_or_gettoken()
        if returncode > 0:
            openstack_utils_logger.error("Could not login to Openstack.")
            return 1, float_net, mynewnets, security_groups
    # Note: _ is same as above --> a.tenant_id
    returncode, _, token = a.login_or_gettoken(tenant_id=a.tenant_id)
    if returncode > 0:
        openstack_utils_logger.error("Could not get token to project.")
        return 1, float_net, mynewnets, security_groups

    a.connect_to_neutron()

    returncode, security_group = a.create_security_group()
    if returncode > 0:
        openstack_utils_logger.error("Could not create security group in project.")
        return 1, float_net, mynewnets, security_groups
    returncode, float_net = a.find_floatnet_id(return_name="Yes")
    if returncode > 0:
        openstack_utils_logger.error('Could not get the name for the '
                                     'floating network.')
        return 1, float_net, mynewnets, security_groups
    returncode, router = a.create_router()
    if returncode > 0:
        openstack_utils_logger.error("Could not create router in project.")
        return 1, float_net, mynewnets, security_groups
    router_id = router['id']
    returncode, network = a.create_network()
    if returncode > 0:
        openstack_utils_logger.error("Could not create network in project.")
        return 1, float_net, mynewnets, security_groups
    returncode, subnet = a.create_subnet()
    if returncode > 0:
        openstack_utils_logger.error("Could not create subnet in project.")
        return 1, float_net, mynewnets, security_groups
    openstack_utils_logger.debug('Sleeping 5s b/c of slow neutron create times.')
    time.sleep(5)
    a.add_int_to_router(router_id, subnet['id'])

    mgmtname = a.create_name_for("network", append="mgmt")
    returncode, mgmt_network = a.create_network(name=mgmtname)
    if returncode > 0:
        openstack_utils_logger.error("Could not create network in project.")
        return 1, float_net, mynewnets, security_groups
    mgmtsubname = a.create_name_for("subnet", append="mgmt")
    returncode, mgmt_subnet = a.create_subnet(name=mgmtsubname,
                                              cidr='192.168.1.0/24')
    if returncode > 0:
        openstack_utils_logger.error("Could not create subnet in project.")
        return 1, float_net, mynewnets, security_groups
    openstack_utils_logger.debug('Sleeping 5s b/c of slow neutron create times.')
    time.sleep(5)
    a.add_int_to_router(router_id, mgmt_subnet['id'], mgmt=True)
    mynets = a.neutron.list_networks()
    my_security_groups = a.neutron.list_security_groups()

    mynewnets = []
    for i in mynets['networks']:
        if i.get('name') == network['name']:
            mynewnets.append(i)
        elif i.get('name') == mgmt_network['name']:
            mynewnets.append(i)

    for i in my_security_groups['security_groups']:
        if i.get('name') == security_group['name']:
            security_groups.append(i)

    return 0, float_net, mynewnets, security_groups
