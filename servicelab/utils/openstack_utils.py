from keystoneclient.exceptions import AuthorizationFailure, Unauthorized
from neutronclient.neutron import client as neutron_client
from keystoneclient.v2_0 import client
import logging
import getpass
import yaml
import os


# create logger
# TODO: For now warning and error print. Got to figure out how
#       to import the one in stack.py properly.
openstack_utils_logger = logging.getLogger('click_application')
logging.basicConfig()


class SLab_OS(object):

    def __init__(self, password, base_url, url_domain=".cisco.com", username=None):
        """Init some of the variables we'll use to manipulate our Openstack tenant.

        Args:
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

        Returns:
            Nothing. All these variables are instantiated as part of the
            instance of the class.

        Example Usage:
            >>> alexs_instance = SLab_OS(password="donttell", base_url="us-rdu-3")
        """
        if not username:
            username = getpass.getuser()
        self.username = username
        self.password = password
        self.base_url = base_url
        self.url_domain = url_domain
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
            >>> a.login_or_gettoken()
           0, 2e3e3bb7ce9f4ab6912da0e500a822ac,
            >>> a.login_or_gettoken("2e3e3bb7ce9f4ab6912da0e500a822ac")
           0, 2e3e3bb7ce9f4ab6912da0e500a822ac, TODO: put ex token here.

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
            >>> a.connect_to_neutron()
            0
        """
        self.endpoint_url = "https://" + self.base_url + self.url_domain + ":9696"
        self.neutron = neutron_client.Client('2.0', endpoint_url=self.endpoint_url,
                                             token=self.token)
        self.neutron.format = 'json'
        return 0

    def create_name_for(self, neutron_type):
        """Generates some consistent naming for us to use and reference.

        Args:
            neutron_type (str): The neutron type can be a subnet, network, or router.
                                We'll use this to help create a name.
        Returns:
            name (str): A not so unique name is created depending on the type of
                        neutron object we're dealing with; however, we will still
                        get a unique id given from OS itself that we can cache
                        locally.

        Example Usage:
            >>> create_name_for("subnet")
            SLAB_aaltman_subnet
        """
        user = getpass.getuser()
        name = "SLAB" + + "_" + user + "_" + os_type
        return name

    def check_for_network(self, name):
        """Check to see if the named network exists.

        Args:
            name (str): The name of the network you would like to see if it
                        exists in your tenant/project or not. If needed and
                        you're not sure of the name you can always generate
                        it from the create_name_for() function.

        Returns
            Returncode (int):
                0 - Success
                1 - Failure

        Example Usage:
            >>> check_for_network("SLAB_aaltman_network")
            0
        """
        networks = self.neutron.list_networks(name=name)
        if networks['networks']['name'] == name:
            return 0
        else:
            return 1

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

        Example Usage:
            >>> check_for_subnet("SLAB_aaltman_subnet")
            0

            We should expect in a return 0 scenario that the subnet was
            created and associated to a network of essentially the same
            name "SLAB_aaltman_network".
        """
        subnets = self.neutron.list_subnets(name=name)
        if subnets['subnets']['name'] == name:
            return 0
        else:
            return 1

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

        Example Usage:
            >>> check_for_router("SLAB_aaltman_router")
            0
        """
        routers = self.neutron.list_routers(name=name)
        if routers['routers']['name'] == name:
            return 0
        else:
            return 1

    def create_in_project(self, path, neutron_type, tenant_id="self.tenant_id",
                          cidr="192.168.100.0/24", external_net="public-floating-602"):
        """Create a neutron object (subnet, router, network, floatingip) in a project /
           tenant in OS.

        Args:
            path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
            neutron_type (str): The type of neutron object you're trying to
                                work with, including subnet, router, network,
                                or floatingip.
            tenant_id (str): An openstack unique identifier for a project/tenant. It
                                  looks like this: "2e3e3bb7ce9f4ab6912da0e500a822ac".
            cidr (str): A network (e.g. 192.168.100.0) with it's associated netmask
                        bits (e.g. /24, /8) to look like "192.168.100.0/24". For more
                        details see:
                        "https://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing".
            external_net (str): This is a network that contains the publicly addressable
                                ip range outside of OS. Typically this network is called
                                "public-floating-601", but can differ depending on how
                                many tenant clouds are sharing the same network backbone.
                                For instance, in us-rdu-3 the public float is
                                "public-floating-602".

        Returns:
            Returncode:
                0 - Success
                1 - Failure

        Example Usage:
            >>> create_in_project("/Users/aaltman/Git/servicelab/servicelab/.stack",
                                  "subnet")
            0
        """
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
                    # TODO: Attempt to create network if it doesn't exist.
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
                      TODO: Add example id.
        Returns
            Returncode (int):
                0 - Success
                1 - Failure

        Example Usage:
            TODO: Add ex id here:
            >>> del_in_project(subnet, "")
            0
        """
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
        elif neutron_type == "floatingip":
            self.neutron.delete_floatingip
            # TODO: return 1 until flesh this out. fix this.
            return 1

    def verify_connect_router_subnet(self):
        pass

    def add_int_to_router(self, path, subnet_id):
        """Add a port to a router to an internal network.

        Args:
            path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
            subnet_id (str): This is the unique identifier provided by OS on a
                      per component basis, including the subnet..
                      TODO: Add example id.
        Returns
            Returncode (int):
                0 - Success
                1 - Failure

        Example Usage:
            >>> add_int_to_router("/Users/aaltman/Git/servicelab/servicelab/.stack",
                                  sbunet_id:"TODO: ID HERE")
            0
        """
        # Note: Adding port to router to internal network
        neutron.add_interface_router
        # RFI: Read router id from cache and read subnet id from cache?
        port = neutron.add_interface_router(router['router']['id'],
                                            {'subnet_id': subnet_id,
                                             'tenant_id': self.tenant_id}
                                            )
        # TODO: write to cache if port has id returned aka is a success else fail.
        write_to_cache(path, port)
        return 0

    def write_to_cache(self, path, writeit):
        """Write a dictionary item to cache.

        Args:
            path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
            writeit (dict): This should be a dictionary so that we can post
                    the data as yaml. We can append it

        Returns:
            Returncode (int):
                0 - Success
                1 - Failure

        Example Usage:
            >>> write_to_cache("/Users/aaltman/Git/servicelab/servicelab/.stack",
                               {"this": "is", "a": "dictionary"})
            0

        TODO: catch exceptions so I can return 1 on failure. Or check to see if
              if an item is already in dict.
        """
        # Note: write should be a dictionary so we can write as yaml
        self.OS_ids_cachefile = os.path.join(path, cache, "OS_ids.yaml")
        if os.path.exists(self.OS_ids_cachefile):
            with open(OS_ids_cachefile, 'a') as f:
                f.write(yaml.dump(writeit, default_flow_style=False))
                return 0
        else:
            with open(self.OS_ids_cachefile, 'w') as f:
                f.write(yaml.dump(writeit, default_flow_style=False))
                return 0

    def get_from_cache(self, path, neutron_type, get_this):
        """Get a dictionary item from yaml file serving as cache.

        Args:
            path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
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
            >>> get_from_cache("/Users/aaltman/Git/servicelab/servicelab/.stack",
                               "subnet", TODO: put maybe interpolated "id" here.)
            0, TODO: show example item
        """

        # Note: get_this should be some sort of key in one of the neutron
        #      types. Pls see the create function for more details.
        self.OS_ids_cachefile = os.path.join(path, cache, "OS_ids.yaml")
        if os.path.exists(self.OS_ids_cachefile):
            with open(OS_ids_cachefile, 'r') as f:
                d = yaml.load(f)
                return 0, d[get_this]
        else:
            return 1, d[get_this]
