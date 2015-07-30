from keystoneclient.exceptions import AuthorizationFailure, Unauthorized
from neutronclient.neutron import client as neutron_client
from keystoneclient.v2_0 import client
import logging
import getpass


# create logger
# TODO: For now warning and error print. Got to figure out how
#       to import the one in stack.py properly.
vagrant_utils_logger = logging.getLogger('click_application')
logging.basicConfig()


class Setup_SLab_OS(object):

    def __init__(self, username=None, password, base_url, url_domain="cisco.com"):
        if not username:
            username = getpass.getuser()
        self.username = username
        self.password = password
        self.base_url = base_url
        self.url_domain = url_domain

    # RFI: how to handle not having tenant_id before auth. if you
    #      don't you'll get error from neutron client
    # RFI: Can we run this twice and not have a conflict?
    def login_or_gettoken(tenant_id=''):

        self.auth_url = 'https://' + self.base_url + self.url_domain + ':5000/v2.0'

        try:
            if not tenant_id:
                keystone = client.Client(username=self.username, password=self.password,
                                         auth_url=self.auth_url', tenant_id=self.tenant_id)
                self.token = keystone.auth_token
                return 0, self.token
            else:
                keystone = client.Client(username=self.username,
                                         password=self.password, auth_url=self.auth_url)
                all_tenants = keystone.tenants.list()
                if len(all_tenants) > 1:
                    openstack_utils_logger.error("Can't determine, which tenant to get tenant_id\
                                                  from b/c there's more than 1.")
                    return 1, self.tenant_id
                else:
                    self.tenant_id = all_tenants[0].id
                    return 0, self.tenant_id

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

    def check_for_network(self, net_name):
        networks = self.neutron.list_networks(name=net_name)
        # on success
        # {'networks': [{u'status': u'ACTIVE', u'subnets': [], u'name': u'aaltman-network',
        #                u'admin_state_up': True, u'tenant_id':
        #                u'2e3e3bb7ce9f4ab6912da0e500a822ac', u'router:external': False,
        #                u'shared': False, u'id': u'86bf6a31-0429-4c74-8b57-bd08d96e8936'}]}
        # on failure
        # {'networks': []}

    def create_network(self, net_name):
        network = {'name': net_name, 'admin_state_up': True, 'tenant_id': self.tenant_id}
        self.neutron.create_network({'network': network})

    def del_network(self, network_id):
        self.neutron.delete_network

    def check_for_subnet():
        self.neutron.list_subnets

    def create_subnet():
        pass

    def check_for_router():
        pass

    def create_router():
        pass

    def verify_connect_router_subnet():
        pass

    def connect_router_subnet():
        pass


# get the network id so ur not working by the name
network_id = networks['networks'][0]['id']
print network_id


# Delete network
# neutron.delete_network(network_id)
# when cleaning up like stack destroy or whatever, we'll
# want to clean up the networking too plus have the option to
# not clean up OS project
