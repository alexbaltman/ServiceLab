from keystoneclient.exceptions import AuthorizationFailure, Unauthorized
from neutronclient.neutron import client as neutron_client
from keystoneclient.v2_0 import client
import logging
import getpass
import os


# create logger
# TODO: For now warning and error print. Got to figure out how
#       to import the one in stack.py properly.
openstack_utils_logger = logging.getLogger('click_application')
logging.basicConfig()


class SLab_OS(object):

    def __init__(self, password, base_url, url_domain=".cisco.com", username=None):
        if not username:
            username = getpass.getuser()
        self.username = username
        self.password = password
        self.base_url = base_url
        self.url_domain = url_domain
        self.auth_url = ""
        self.tenant_id = ""

    # RFI: how to handle not having tenant_id before auth. if you
    #      don't you'll get error from neutron client
    # RFI: Can we run this twice and not have a conflict?
    def login_or_gettoken(self, tenant_id=''):

        self.auth_url = 'https://' + self.base_url + self.url_domain + ':5000/v2.0'

        try:
            if not tenant_id:
                keystone = client.Client(username=self.username, password=self.password,
                                         auth_url=self.auth_url)
                self.token = keystone.auth_token
                all_tenants = keystone.tenants.list()
                if len(all_tenants) > 1:
                    openstack_utils_logger.error("Can't determine, which tenant to get tenant_id\
                                                  from b/c there's more than 1.")
                    return 1, self.tenant_id, self.token
                else:
                    self.tenant_id = all_tenants[0].id
                    return 0, self.tenant_id, self.token

                return 0, self.tenant_id, self.token
            else:
                keystone = client.Client(username=self.username, password=self.password,
                                         auth_url=self.auth_url, tenant_id=self.tenant_id)
                self.token = keystone.auth_token
                return 0, self.tenant_id, self.token

        except AuthorizationFailure as auth_failure:
            # blah log.error(auth_failure.message)
            pass
        except Unauthorized as unauthorized:
            # blah log.error(unauthorized.message)
            pass

# returned --> [<Tenant {u'enabled': True, u'description': u'', u'name': u'ServiceLab',
#                        u'id': u'2e3e3bb7ce9f4ab6912da0e500a822ac'}>]

    def connect_to_neutron(self):
        self.endpoint_url = "https://" + self.base_url + self.url_domain + ":9696"
        self.neutron = neutron_client.Client('2.0', endpoint_url=self.endpoint_url,
                                             token=self.token)
        self.neutron.format = 'json'

    def create_name_for(self, neutron_type):
        user = getpass.getuser()
        name = "SLAB" + user + "_" + os_type
        return name

    def check_for_network(self, name):
        networks = self.neutron.list_networks(name=name)
        if networks['networks']['name'] == name:
            return 0
        else:
            return 1

    def check_for_subnet(self, name):
        subnets = self.neutron.list_subnets(name=name)
        if subnets['subnets']['name'] == name:
            return 0
        else:
            return 1

    def check_for_router(self, name):
        routers = self.neutron.list_routers(name=name)
        if routers['routers']['name'] == name:
            return 0
        else:
            return 1

    # Note: neutron_type --> subnet, router, network, floatingip
    def create_in_project(self, path, neutron_type, tenant_id="self.tenant_id",
                          cidr="192.168.100.0/24", external_net="public-floating-602"):
        name = create_name_for(neutron_type)
        network_id = ""

        if neutron_type == "network":
            network = {'name': name, 'admin_state_up': True, 'tenant_id': self.tenant_id}
            network = self.neutron.create_network({'network': network})
            network_id = networks['networks'][0]['id']
            write_to_cache(path, network)
            returncode = check_for_network(name)
            if returncode == 0:
                return 0
            else:
                openstack_utils_logger.error("Tried to make the network, but failed.")
                return 1
        elif neutron_type == "router":
            router = {'name': name, 'admin_state_up': True, 'external_gateway_info':
                      {'network_id': external_net, 'external_snat': True}
                      }
            router = self.neutron.create_router({'router': router})
            write_to_cache(path, router)
            returncode = check_for_router(name)
            if returncode == 0:
                return 0
            else:
                openstack_utils_logger.error("Tried to make the router, but failed.")
                return 1
        elif neutron_type == "subnet":
            if not network_id:
                name = create_name_for("network")
                returncode = check_for_network(name)
                if returncode > 0:
                    openstack_utils_logger.error("Can't attach subnet to network\
                                                 provided because it doesn't exist.")
                    return 1
                else:
                    networks = self.neutron.list_networks(name=name)
                    network_id = networks['networks'][0]['id']
                    subnets_name = create_name_for("subnet")
                    base_cidr, bitmask = cidr.split('/')
                    oct1, oct2, oct3, oct4 = base_cidr.split(".")
                    oct4 = str(int(oct4) + 1)
                    gateway_ip = ".".join([oct1, oct2, oct3, oct4])
                    subnet = {'name': name, 'network_id': network_id, 'ip_version': 4,
                              'cidr': cidr, 'tenant_id': self.tenant_id, gateway_ip}
                    subnet = self.neutron.create_subnet({'subnet': subnet})
                    write_to_cache(path, subnet)
                    returncode = check_for_subnet(name)
                    if returncode == 0:
                        return 0
                    else:
                        return 1
        elif neutron_type == "floating_ip":
            floatingip = {'floating_network_id' = external_net, 'tenant_id': self.tenant.id}
            floatingip = self.neutron.create_floatingip({'floatingip': floatingip})
            # check if success b4 returning 0
            write_to_cache(path, floatingip)
            return 0

    def del_in_project(self, neutron_type, id):
        if neutron_type == "network":
            self.neutron.delete_network(id)
            returncode = check_for_network(id)
            if returncode > 0:
                return 0
            else:
                openstack_utils_logger.error("Failed to delete network.")
                return 1
        elif neutron_type == "router":
            self.neutron.delete_router(id)
            returncode = check_for_router(id)
            if returncode > 0:
                return 0
            else:
                return 1
        elif neutron_type == "subnet":
            self.neutron.delete_subnet(id)
            returncode = check_for_subnet(id)
            if returncode > 0:
                return 0
            else:
                return 1

    def verify_connect_router_subnet(self):
        pass

    def add_int_to_router(self, path, subnet_id):
        # Note: Adding port to router to internal network
        neutron.add_interface_router
        # Read router id from cache and read subnet id from cache?
        port = neutron.add_interface_router(router['router']['id'],
                                            {'subnet_id': subnet_id,
                                             'tenant_id': self.tenant_id}
                                            )
        write_to_cache(path, port)

    def write_to_cache(self, path, writeit):
        OS_ids_cachefile = os.path.join(path, cache, "OS_ids")
        with open(OS_ids_cachefile, 'a') as f:
            f.write(writeit)


# neutron.disconnect_network_gateway
