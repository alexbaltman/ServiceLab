"""
Test Functions for openstack_utils api set.
"""
import os
import unittest

from click.testing import CliRunner
from keystoneclient.v2_0 import client as keystone_client
from keystoneclient.exceptions import AuthorizationFailure
from keystoneclient.exceptions import Unauthorized

from neutronclient.v2_0 import client as neutron_client

from servicelab.stack import Context
from servicelab.commands import cmd_workon
from servicelab.utils import openstack_utils
from servicelab.utils.openstack_utils import SLab_OS
from servicelab.utils import helper_utils
from servicelab.utils import yaml_utils
from servicelab.utils import service_utils
from servicelab.utils import vagrantfile_utils
from servicelab.utils import vagrant_utils


class TestSLABNetworking(unittest.TestCase):
    """
    Base class for all the Test classes  for ServiceLab network.
    This sets up the environment with
    1. OS_AUTH_URL,
    2. OS_TENANT_NAME
    3. OS_TENANT_ID
    4. OS_USERNAME
    5. OS_PASSWORD
    6. OS_REGIONNAME

    Attributes:
        ctx:  Context object of servicelab module.
    """
    def __init__(self, *args, **kwargs):
        # set up the environment python style :-)
        os.environ["OS_AUTH_URL"] = "https://us-rdu-3.cisco.com:5000/v2.0"
        os.environ["OS_TENANT_NAME"] = "jenkins-slab"
        os.environ["OS_TENANT_ID"] = "dc4b64c3ddcc4ce5abbddd43a24b1b0a"
        os.environ["OS_USERNAME"] = "jenkins-test"
        os.environ["OS_PASSWORD"] = "Cisco12345"
        os.environ["OS_REGION_NAME"] = "us-rdu-3"
        self.ctx = Context()
        super(TestSLABNetworking, self).__init__(*args, **kwargs)

    @staticmethod
    def setup_neutron():
        """
        Setups and call python api for openstack-neutron and returns the neutron object
        """
        neutron = neutron_client.Client(username=os.getenv("OS_USERNAME"),
                                        password=os.getenv("OS_PASSWORD"),
                                        auth_url=os.getenv("OS_AUTH_URL"),
                                        tenant_name=os.getenv("OS_TENANT_NAME"))
        neutron.format = "json"
        return neutron

    @staticmethod
    def setup_keystone():
        """
        Setups and call python api for openstack-keystone and returns the keystone object
        """
        keystone = keystone_client.Client(username=os.getenv("OS_USERNAME"),
                                          password=os.getenv("OS_PASSWORD"),
                                          auth_url=os.getenv("OS_AUTH_URL"),
                                          tenant_name=os.getenv("OS_TENANT_NAME"))
        return keystone


class TestNetworking(TestSLABNetworking):
    """
    Test os_ensure_network of servicelab.utils.openstack_utils api set. Each  of the
    followings are checked
        1. login
        2. networks created
        3. router and interfaces created and validated against the values returned.
    """
    def __init__(self, *args, **kwargs):
        super(TestNetworking, self).__init__(*args, **kwargs)

    def setUp(self):
        ret_val, net, rdict, sgrp = openstack_utils.os_ensure_network(self.ctx.path)
        self.assertEquals(ret_val,
                          0,
                          "All networking test failed as test is "
                          "unable to setup network for tenant "
                          "{} on {}".format(os.getenv("OS_TENANT_NAME"),
                                            os.getenv("OS_AUTH_URL")))
        self.net_name = net
        self.network_dict = rdict
        self.sec_grp = sgrp

    def tearDown(self):
        openstack_utils.os_delete_networks(self.ctx.path, True)

    @unittest.skip("skipping as jenkins unable to run on us-rdu-3.cisco.com")
    def test_ensure_network(self):
        """
        Check each of the following things
        1. login
        2. networks created
        3. router and interfaces created and validated against the values returned.
        """
        try:
            username = os.getenv("OS_USERNAME")
            auth_url = os.getenv("OS_AUTH_URL")
            tenant_name = os.getenv("OS_TENANT_NAME")
            tenant_id = os.getenv("OS_TENANT_ID")

            # check the keystone values
            t_keystone = TestSLABNetworking.setup_keystone()
            found = False
            for tenant in t_keystone.tenants.list():
                if tenant.name == tenant_name:
                    if tenant_id == tenant.id:
                        found = True
            self.assertTrue(found,
                            "Unable to find the tenant({0}, {1}) information "
                            "in openstack {2}".format(tenant_name, tenant_id, auth_url))

            # get the router name from the SLAB as it should be created
            slab = SLab_OS(self.ctx.path,
                           os.getenv("OS_PASSWORD"),
                           os.getenv("OS_REGION_NAME"),
                           ".cisco.com",
                           username,
                           tenant_name)
            slab.tenant_id = os.getenv("OS_TENANT_ID")
            router_name = slab.create_name_for("router")

            # check if the name exist and is up
            t_neutron = TestSLABNetworking.setup_neutron()
            routers = t_neutron.list_routers(retrieve_all=True)
            found = False
            for router in routers["routers"]:
                if router_name == router['name']:
                    self.assertTrue(router["admin_state_up"],
                                    "Router {} available but down".format(router_name))
                    found = True
            self.assertTrue(found, "Router {} not created".format(router_name))

            # check the networks
            def _check_network(name):
                """
                utility fn to check network name from a dictionary of list of networks
                """
                return any(network['name'] == name for network in networks['networks'])

            networks = t_neutron.list_networks()
            net_name = slab.create_name_for("network")
            if not _check_network(net_name):
                self.fail("no network {} created for tenant {}".format(net_name,
                                                                       tenant_name))
            mgmt_net = slab.create_name_for("network", "mgmt")
            if not _check_network(mgmt_net):
                self.fail("no mgmt network {} created for tenant {}".format(mgmt_net,
                                                                            tenant_name))

            # check the subnets
            def _check_subnet(name):
                """
                utility fn to check subnet name from a dictionary of list of subnets
                """
                return any(subnet['name'] == name for subnet in subnets['subnets'])

            subnets = t_neutron.list_subnets()
            net_subnet = slab.create_name_for("subnet")
            mgmt_subnet = slab.create_name_for("subnet", "mgmt")
            if not _check_subnet(net_subnet):
                self.fail("no subnet {} created for network {}".format(net_subnet,
                                                                       net_name))
            if not _check_subnet(mgmt_subnet):
                self.fail("no subnet {} created for network {}".format(mgmt_subnet,
                                                                       mgmt_net))
        except AuthorizationFailure as auth_failure:
            self.fail("Authorization failue for User {} to "
                      "login in tenant {} on "
                      "openstack-environ {}".format(os.getenv("OS_USERNAME"),
                                                    os.getenv("OS_TENANT_NAME"),
                                                    os.getenv("OS_AUTH_URL")))
            self.ctx.logger.info(auth_failure)
        except Unauthorized as unauthorized:
            self.fail("User {} is unauthorized to "
                      "login in tenant {} on "
                      "openstack-environ {}".format(os.getenv("OS_USERNAME"),
                                                    os.getenv("OS_TENANT_NAME"),
                                                    os.getenv("OS_AUTH_URL")))
            self.ctx.logger.info(unauthorized)


class TestRouterSetup(TestSLABNetworking):
    """
    Test for router creation and deletion.

    Attributes:
        slab: servicelab openstack utility class
    """
    def __init__(self, *args, **kwargs):
        super(TestRouterSetup, self).__init__(*args, **kwargs)

    def setUp(self):
        # get the router name from the SLAB as it should be created
        self.slab = SLab_OS(self.ctx.path,
                            os.getenv("OS_PASSWORD"),
                            os.getenv("OS_REGION_NAME"),
                            ".cisco.com",
                            os.getenv("OS_USERNAME"),
                            os.getenv("OS_TENANT_NAME"))
        self.slab.tenant_id = os.getenv("OS_TENANT_ID")
        self.slab.login_or_gettoken(self.slab.tenant_id)
        self.slab.connect_to_neutron()

    def tearDown(self):
        pass

    @unittest.skip("skipping as jenkins unable to run on us-rdu-3.cisco.com")
    def test_router(self):
        """
        Test for router creation and deletion.
        """
        try:
            ret_val, ret_dict = self.slab.create_router()
            self.assertEqual(ret_val, 0, "unable to create the router")
            router_name = ret_dict['name']

            # get the token
            neutron = TestSLABNetworking.setup_neutron()

            # check and retrieve if the router is present
            routers = neutron.list_routers(retrieve_all=True)
            found = False
            for router in routers["routers"]:
                if router_name == router['name']:
                    self.assertTrue(router["admin_state_up"],
                                    "Router {} available but down".format(router_name))
                    found = True
                    break
            self.assertTrue(found, "Router {} not created".format(router_name))

            # delete and check for router existence
            openstack_utils.os_delete_routers(self.slab.neutron, True)
            found = False
            routers = neutron.list_routers(retrieve_all=True)
            for router in routers["routers"]:
                if router_name == router['name']:
                    self.fail("Router {} found".format(router["name"]))

        except AuthorizationFailure as auth_failure:
            self.fail("Authorization failue for User {} to "
                      "login in tenant {} on "
                      "openstack-environ {}".format(os.getenv("OS_USERNAME"),
                                                    os.getenv("OS_TENANT_NAME"),
                                                    os.getenv("OS_AUTH_URL")))
            self.ctx.logger.info(auth_failure)
        except Unauthorized as unauthorized:
            self.fail("User {} is unauthorized to "
                      "login in tenant {} on "
                      "openstack-environ {}".format(os.getenv("OS_USERNAME"),
                                                    os.getenv("OS_TENANT_NAME"),
                                                    os.getenv("OS_AUTH_URL")))
            self.ctx.logger.info(unauthorized)


class TestNetworkSetup(TestSLABNetworking):
    """
    Test network setup and cleanup.


    Attributes:
        slab: servicelab openstack utility class
    """
    def __init__(self, *args, **kwargs):
        super(TestNetworkSetup, self).__init__(*args, **kwargs)

    def setUp(self):
        # get the router name from the SLAB as it should be created
        self.slab = SLab_OS(self.ctx.path,
                            os.getenv("OS_PASSWORD"),
                            os.getenv("OS_REGION_NAME"),
                            ".cisco.com",
                            os.getenv("OS_USERNAME"),
                            os.getenv("OS_TENANT_NAME"))
        self.slab.tenant_id = os.getenv("OS_TENANT_ID")
        self.slab.login_or_gettoken(self.slab.tenant_id)
        self.slab.connect_to_neutron()

        def _check_assert(tup, msg):
            """
            Utility function to assert and return value.
            """
            self.assertEqual(tup[0], 0, msg)
            return tup[1]

        router = _check_assert(self.slab.create_router(),
                               "unable to create the router for network setup")
        _check_assert(self.slab.create_network(), "unable to setup network")
        subnet = _check_assert(self.slab.create_subnet(), "unable to setup up the subnet")
        self.slab.add_int_to_router(router, subnet['id'])

    def tearDown(self):
        pass

    @unittest.skip("skipping as jenkins unable to run on us-rdu-3.cisco.com")
    def test_networking(self):
        """
        Test for network setup. including creating and deletion of
        1. network
        2. subnets
        3. interaface to the subnets
        """
        try:
            neutron = TestSLABNetworking.setup_neutron()

            # get network list and check if the network is created
            def _check_network(name):
                """
                utility fn to check network name from a dictionary of list of networks
                """
                return any(network['name'] == name for network in networks['networks'])

            networks = neutron.list_networks()
            net_name = self.slab.create_name_for("network")
            if not _check_network(net_name):
                self.fail("no network {} created "
                          "for tenant {}".format(net_name, self.slab.os_tenant_name))

            # check subnet exists
            def _check_subnet(name):
                """
                utility fn to check subnet name from a dictionary of list of subnets
                """
                return any(subnet['name'] == name for subnet in subnets['subnets'])

            subnets = neutron.list_subnets()
            net_subnet = self.slab.create_name_for("subnet")
            if not _check_subnet(net_subnet):
                self.fail("no subnet {} created for network {}".format(net_subnet, net_name))

            # now delete the subnet and check if it exists
            _, t_net = self.slab.check_for_network(net_name)
            openstack_utils.os_delete_subnets(self.slab.neutron, t_net)
            subnets = neutron.list_subnets()
            if _check_subnet(net_subnet):
                self.fail("unable to delete subnet {} "
                          "created for network {}".format(net_subnet, net_name))

            # delete the network and check if it exists
            openstack_utils.os_delete_networking_components(self.slab.neutron, t_net)
            if not _check_network(net_name):
                self.fail("unable to delete network {}".format(net_name))

        except AuthorizationFailure as auth_failure:
            self.fail("Authorization failue for User {} to "
                      "login in tenant {} on "
                      "openstack-environ {}".format(os.getenv("OS_USERNAME"),
                                                    os.getenv("OS_TENANT_NAME"),
                                                    os.getenv("OS_AUTH_URL")))
            self.ctx.logger.info(auth_failure)
        except Unauthorized as unauthorized:
            self.fail("User {} is unauthorized to "
                      "login in tenant {} on "
                      "openstack-environ {}".format(os.getenv("OS_USERNAME"),
                                                    os.getenv("OS_TENANT_NAME"),
                                                    os.getenv("OS_AUTH_URL")))
            self.ctx.logger.info(unauthorized)


class TestInfraNode(TestSLABNetworking):
    """
    Test infra node setup for a service first does setup of the environment by
    installing
        1. ccs-data
        2. service-horizon
    It will install the infra-node for the service-horizon.
    If unable to install the test fails.
    """
    def __init__(self, *args, **kwargs):
        super(TestInfraNode, self).__init__(*args, **kwargs)

    def setUp(self):
        runner = CliRunner()
        result = runner.invoke(cmd_workon.cli,
                               ["ccs-data"])
        self.assertNotEqual(result,
                            1,
                            "unable to get service-horizon")
        result = runner.invoke(cmd_workon.cli,
                               ["service-horizon"])
        self.assertNotEqual(result,
                            1,
                            "unable to get service-horizon")

        # get the hostname
        self.hostname = str(helper_utils.name_vm("service-horizon", self.ctx.path))

    def tearDown(self):
        my_vm_connection = vagrant_utils.Connect_to_vagrant(vm_name=self.hostname,
                                                            path=self.ctx.path)
        my_vm_connection.v.destroy(vm_name=self.hostname)
        my_vm_connection.v.destroy(vm_name=self.infra_name)
        openstack_utils.os_delete_networks(self.ctx.path, True)

    @unittest.skip("skipping as jenkins unable to run on us-rdu-3.cisco.com")
    def test_ensure_network(self):
        yaml_utils.host_add_vagrantyaml(self.ctx.path, "vagrant.yaml",
                                        self.hostname, "ccs-dev-1")
        yaml_utils.write_dev_hostyaml_out(self.ctx.path, self.hostname)
        result, info = service_utils.build_data(self.ctx.path)

        slab_vagrant_file = vagrantfile_utils.SlabVagrantfile(path=self.ctx.path)
        slab_vagrant_file.init_vagrantfile()
        vagrant_env = vagrant_utils.Connect_to_vagrant(vm_name=self.hostname,
                                                       path=self.ctx.path)

        ret_val, float_net, mynets, sgrp = openstack_utils.os_ensure_network(self.ctx.path)
        self.assertEquals(ret_val,
                          0,
                          "All networking test failed as test is "
                          "unable to setup network for tenant "
                          "{} on {}".format(os.getenv("OS_TENANT_NAME"),
                                            os.getenv("OS_AUTH_URL")))
        slab_vagrant_file.set_env_vars(float_net, mynets, sgrp)
        returncode, host_dict = yaml_utils.gethost_byname(self.hostname, self.ctx.path)
        slab_vagrant_file.add_openstack_vm(host_dict)

        vagrant_env.v.up(self.hostname)
        result, self.infra_name = vagrant_utils.infra_ensure_up(mynets, float_net,
                                                                sgrp, path=self.ctx.path)
        self.assertNotEqual(result, 1, "unable to install and start an infrastructure node")


if __name__ == '__main__':
    unittest.main()
