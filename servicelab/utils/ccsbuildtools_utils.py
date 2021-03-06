import logging
import os
import yaml

from prettytable import PrettyTable

import yaml_utils
import ccsdata_utils
import logger_utils
from servicelab import settings

slab_logger = logger_utils.setup_logger(settings.verbosity, 'stack.utils.ccsbuildtools')


def gather_site_info(path, cont):
    """Gathers data from user for compiling site data into ccs-data.

    Example data gathered/required for building a site:
    ---
    bom: 4.2
    secret: example_password
    ip_ranges:
      vlan2: 10.202.64.0/25
      vlan4: 10.202.64.128/28
      vlan65: 10.202.76.128/27
      vlan68: 10.202.76.0/25
      vlan82: 10.202.72.0/22
      vlan83: 10.202.78.0/24
      vlan84: 10.202.79.0/24
      vlan67: 10.202.65.0/25
      vlan906: 10.203.228.0/22
    service_cloud:
      site_name: iad10-svc-1
      az: csm
      domain: cloud.cisco.com
      controller_count: 3
      cloud_nodes:
        num_nova2: 5
        num_nova3: 10
    tenant_cloud:
      site_name: us-virginia-1
      az: csx-a
      domain: cloud.cisco.com
      controller_count: 3
      cloud_nodes:
        num_nova1: 306
        num_nova2: 124
        num_nova3: 44
        num_ceph: 51
        num_net: 4
        num_haproxy: 2

    This function gathers all this input and writes the yaml file into the
    services/ccs-build-tools/ignition_rb directory.

    Args:
        path(str): path to working .stack directory. Typically looks like
                   ./servicelab/servicelab/stack
        cont(bool): flag which causes writes/reads to and from persistent data about
                    site held in yaml file in cache
    Returns:
        returncode(int): 0 - success, 1 - failure (no directory to write yaml into)
        site_dictionary: information about the site
    """
    slab_logger.debug('Gathering input data to build the answer.yaml needed for ignition')
    # Set up file to store persistent site data
    path_to_cache = os.path.join(path, "cache")
    if not os.path.exists(path_to_cache):
        os.makedirs(path_to_cache)
    path_to_temp_file = os.path.join(path_to_cache, "temp_site_data.yaml")
    if os.path.isfile(path_to_temp_file) and cont:
        with open(path_to_temp_file) as f:
            site_dictionary = yaml.load(f)
    else:
        site_dictionary = get_input_requirements_for_ccsbuildtools()
    # These if clauses are skipped if they've already been completed by user
    # (i.e.) loaded from the temp_site_data.yaml file
    # Program exits and gathered data stored to yaml file as per user request
    if site_dictionary['service_cloud']['site_name'] is None:
        print "--- Retreiving site data for service cloud ---"
        resume = _input_cloud_info(site_dictionary['service_cloud'], True)
        if resume > 0:
            exit_input(site_dictionary, path_to_temp_file, True)
            return 1, {}
    if site_dictionary['tenant_cloud']['site_name'] is None:
        print "--- Retrieving site data for tenant cloud ---"
        resume = _input_cloud_info(site_dictionary['tenant_cloud'], False)
        if resume > 0:
            exit_input(site_dictionary, path_to_temp_file, True)
            return 1, {}
    # Always confirm ip ranges
    print "--- Retrieving site data for ip_ranges ---\n"
    resume = _edit_ip_ranges(site_dictionary['ip_ranges'])
    if resume > 0:
        exit_input(site_dictionary, path_to_temp_file, True)
        return 1, {}
    if site_dictionary['bom'] is None:
        print "--- Retreiving site data for BOM ---"
        site_dictionary['bom'] = get_valid_input_or_option("Enter "
                                                           "the BOM version: ",
                                                           1, [])
    # Note that CIMC password is required by ccsbuildtools along with out of band VPN
    #        http://wikicentral.cisco.com/display/nimbus/CCS+VPN+Client+Setup
    # access to properly populate/generate hosts from the created answer-yaml file.
    # You can find the CIMC password in some host.yaml files of ccs-data.
    if site_dictionary['ucs_password'] is None:
        print "--- Retreiving site data for password ---"
        site_dictionary['ucs_password'] = get_valid_input_or_option("Enter "
                                                                    "UCS password: ",
                                                                    3, [])
    path_to_ccsbuildtools = os.path.join(path, "services", "ccs-build-tools")
    exit_input(site_dictionary, os.path.join(path_to_ccsbuildtools,
                                             "answer-sample.yaml"
                                             ),
               False
               )
    return 0, site_dictionary


def gather_env_info(path):
    """Gathers data from user for compiling environment data for injecting a tenant
    cloud on top of an existing service cloud site in ccs-data.

    Limited to ccs-data sites that were created with servicelab, i.e `stack create site`.
    This function checks every site in ccs-data for an answer-<site_name>.yaml file, which
    makes it eligible for having a new environment built on top if it by the ccs-build-tools
    repo.

    Example data gathered/required for building a site:
    ---
    bom: 4.2
    secret: example_password
    ip_ranges:
      vlan2: 10.202.64.0/25
      vlan4: 10.202.64.128/28
      vlan65: 10.202.76.128/27
      vlan68: 10.202.76.0/25
      vlan82: 10.202.72.0/22
      vlan83: 10.202.78.0/24
      vlan84: 10.202.79.0/24
      vlan67: 10.202.65.0/25
      vlan906: 10.203.228.0/22
    service_cloud:
      site_name: iad10-svc-1
      az: csm
      domain: cloud.cisco.com
      controller_count: 3
      cloud_nodes:
        num_nova2: 5
        num_nova3: 10
    tenant_cloud:
      site_name: us-virginia-1
      az: csx-a
      domain: cloud.cisco.com
      controller_count: 3
      cloud_nodes:
        num_nova1: 306
        num_nova2: 124
        num_nova3: 44
        num_ceph: 51
        num_net: 4
        num_haproxy: 2

    This function gathers only the tenant cloud data input and writes the yaml file into the
    services/ccs-build-tools/ignition_rb directory.

    Args:
        path(str): path to working .stack directory. Typically looks like
                   ./servicelab/servicelab/stack

    Returns:
        returncode(int): 0 - success, 1 - failure
        site_dictionary: information about the site
    """
    slab_logger.debug('Gathering data for tenant cloud')
    tenant_cloud = {}
    print "Here are the existing sites in ccs-data with which you can inject " \
          "a new tenant cloud environment on top of. Select the number of the " \
          "site to get started. "
    ret_code, our_sites = ccsdata_utils.list_envs_or_sites(path)
    if ret_code > 0:
        return(1, {})
    all_sites = []
    path_to_ccs_data = os.path.join(path, "services", "ccs-data")
    if not os.path.isdir(path_to_ccs_data):
        print "ccs-data directory doesn't exist."
        return 1, {}
    for i in our_sites:
        if os.path.isfile(os.path.join(path_to_ccs_data, "sites", i, "data.d",
                                       "answer-%s.yaml" % (i)
                                       )
                          ):
            all_sites.append(i)
    all_sites.sort()
    site_name = table_selection(all_sites, 'Site_Name')
    with open(os.path.join(path_to_ccs_data, "sites",
                           site_name, "data.d", "answer-%s.yaml" % (site_name)
                           )
              ) as f:
        site_dictionary = yaml.load(f)
    print "---Gathering user input for new tenant cloud for %s---" % (site_name)
    tenant_cloud_name = _input_cloud_info(tenant_cloud, False)
    site_dictionary['tenant_cloud'] = tenant_cloud
    path_to_ansyaml = os.path.join(path, "services", "ccs-build-tools",
                                   "answer-sample.yaml"
                                   )
    exit_input(site_dictionary, path_to_ansyaml, False)
    return 0, site_dictionary


def table_selection(options, topic_name):
    """Table selection, return option that was selected
    """
    table = PrettyTable(['#', topic_name])
    table.align['#'] = 'r'
    table.align[topic_name] = 'l'
    x = 1
    for i in options:
        table.add_row([x, i])
        x = x + 1
    print table
    valid_opts = range(1, x)
    for i in valid_opts:
        i = repr(i)
    num = get_valid_input_or_option("Enter number: ", 0, valid_opts)
    table.header = False
    table.border = False
    return table.get_string(fields=[topic_name], start=int(num)-1,
                            end=int(num)
                            ).strip()


def get_input_requirements_for_ccsbuildtools():
    """Returns a dictionary of all the keys required by the ccsbuildtools repo to properly
    build a site. All values are set to None, except for the ip ranges, which are given
    default values.
    """
    return {'bom': 4.2,
            'ucs_inventory': './cimc_inventory.yaml',
            'ucs_password': "example_password",
            'ip_ranges': {'vlan2': '10.202.64.0/25',
                          'vlan4': '10.202.64.128/28',
                          'vlan65': '10.202.76.128/27',
                          'vlan68': '10.202.76.0/25',
                          'vlan82': '10.202.72.0/22',
                          'vlan83': '10.202.78.0/24',
                          'vlan84': '10.202.79.0/24',
                          'vlan67': '10.202.65.0/25',
                          'vlan906': '10.203.228.0/22',
                          },
            'service_cloud': {'site_name': 'iad10-svc-1',
                              'az': 'csm',
                              'domain': 'cloud.cisco.com',
                              'controller_count': 3,
                              'cloud_nodes': {'num_nova2': 5,
                                              'num_nova3': 10,
                                              'num_ceph': 1,
                                              }
                              },
            'tenant_cloud': {'site_name': 'us-virginia-1',
                             'az': 'csx-a',
                             'domain': 'cloud.cisco.com',
                             'controller_count': 3,
                             'cloud_nodes': {'num_nova1': 306,
                                             'num_nova2': 124,
                                             'num_nova3': 44,
                                             'num_ceph': 51,
                                             'num_net': 4,
                                             'num_haproxy': 2,
                                             }
                             },
            'windows_infra': {'site_name': 'us-virginia-1',
                              'hostname_prefix': 'iad-p1',
                              'forest': 'cisinfra.local',
                              'domain': 'mgmt.cisinfra.local',
                              'cloud_nodes': {'num_primaryforestdc': 0,
                                              'num_primarydomaindc': 0,
                                              'num_forestdc': 2,
                                              'num_dc': 2,
                                              'num_kms': 2,
                                              'num_scdp': 2,
                                              'num_scomgw': 1,
                                              'num_svc': 1,
                                              'num_jump': 1,
                                              'num_sw': 1,
                                              }
                              }
            }


def exit_input(site_dictionary, path_to_dump, exit):
    """exit input
    """
    slab_logger.debug('Saving completed data and exiting the stack create command')
    if exit:
        print "Data input for site terminated. use continue option to resume where you "\
              "left off. If you do another stack create site without the --continue option"\
              " your data will get deleted."
    with open(path_to_dump, 'w') as f:
        f.write("---\n")
        yaml.dump(site_dictionary, f, default_flow_style=False)
    return


def _input_cloud_info(cloud, is_svc):
    """Interacts with user to receive data for building service or tenant cloud.

    Receives user input for all required data for a cloud and inputs it into
    dictionary. Input fields are listed by cloud_input_fields, tc_nodes and svc_nodes.

    Args:
        cloud (dict(str -> str/int)): dictionary which will receive input for
                                      cloud's data
        is_svc (bool): flag set to True if dealing with service cloud
    Returns:
        site_name (str) : returns the user-defined name of the cloud
    """
    slab_logger.debug('Prompting for user input for site data')
    cloud_input_fields = ['site_name', 'az', 'domain']
    cloud_input_fields_prompts = ['Site Name', 'Availability Zone', 'Domain Name']
    tc_nodes = ['num_nova1', 'num_nova2', 'num_nova3',
                'num_net', 'num_haproxy', 'num_ceph'
                ]
    tc_nodes_prompts = ['# Nova Nodes for Nova Ctl #1',
                        '# Nova Nodes for Nova Ctl #2',
                        '# Nova Nodes for Nova Ctl #3',
                        '# Net Nodes', ' # Haproxy Nodes', '# Ceph Nodes'
                        ]
    svc_nodes = ['num_nova2', 'num_nova3', 'num_ceph']
    svc_nodes_prompts = ['# Nova Nodes for Nova Ctl #2',
                         '# Nova Nodes for Nova Ctl #3',
                         '# Ceph Nodes'
                         ]
    _user_input_for_list(cloud_input_fields, cloud_input_fields_prompts, cloud, False)
    cloud['controller_count'] = 3
    cloud['cloud_nodes'] = {}
    if is_svc is False:
        _user_input_for_list(tc_nodes, tc_nodes_prompts, cloud['cloud_nodes'], True)
    else:
        _user_input_for_list(svc_nodes, svc_nodes_prompts, cloud['cloud_nodes'], True)
    if get_valid_input_or_option("Type 'c' to continue building site or "
                                 "'q' to save changes, quit and resume data input "
                                 "at a later time: ", 3, ['c', 'q']) == 'q':
        return 1
    else:
        return 0


def _edit_ip_ranges(ip_ranges):
    """User-interactive function for editting the ip ranges of the vlan numbers used in
    ccs-build-tools.

    Modifies the input dictionary with updated user input data.

    Args:
        ip_ranges: dictionary mapping vlan numbers to ip ranges
    """
    slab_logger.debug('Prompting for user input of vlan data')
    while True:
        print "Here are your ip ranges. Type c to confirm and use these values, " \
              "or enter the digit of the vlan range you want to modify. "
        table = PrettyTable(['vlan num', 'ip range'])
        table.padding_width = 1
        table.align['ip range'] = 'l'
        table.sortby = 'vlan num'
        valid_opts = ['c']
        for i in ip_ranges:
            table.add_row([i[4:], ip_ranges[i]])
            valid_opts.append(i[4:])
        print table
        choice = get_valid_input_or_option("Confirm ranges or enter "
                                           "vlan num you want to edit: ",
                                           3, valid_opts)
        if choice.lower() == 'c':
            break
        else:
            ip_ranges["vlan" + choice] = get_valid_input_or_option("Enter new "
                                                                   "range for vlan" +
                                                                   choice + ": ",
                                                                   3, [])
    if get_valid_input_or_option("Type 'c' to continue building site or "
                                 "'q' to save changes, quit and resume data input "
                                 "at a later time: ", 3, ['c', 'q']) == 'q':
        return 1
    else:
        return 0


def _user_input_for_list(input_fields, prompts, dictionary, is_int):
    """Processes the items in a list, and receives user input for each item.

    Reads each item in input list and prompts the user for its input.

    Args:
        input_fields (list(str)) : a list of fields required for user to input
        prompt (list(str)): list of prompts to ask user for each data field
        dictionary : the dictionary which stores the user inputs
        is_int (bool) : flag which states whether or not receiving ints or strings
    """
    slab_logger.debug('Prompting user for input of needed data')
    for i in input_fields:
        if is_int:
            dictionary[i] = get_valid_input_or_option("Enter " +
                                                      prompts[input_fields.index(i)] + ": ",
                                                      0, [])
        else:
            dictionary[i] = get_valid_input_or_option("Enter " +
                                                      prompts[input_fields.index(i)] + ": ",
                                                      3, [])


def get_valid_input_or_option(prompt, parameter_type, options):
    """Gets input from user, asks user to double check it and ensures it matches a list of
    options if one is provided.

    Args:
        prompt(str): The message to ask the user for input with.
        want_digit(bool): True if the input must be a number, false if it can be a string.
        options(str[]): list of appropriate options the input must match

    Returns:
        input(str or int): the user input
    """
    while True:
        if parameter_type == 0:
            try:
                input = int(raw_input(prompt))
            except ValueError:
                print "Please enter a valid integer."
                continue
        elif parameter_type == 1:
            try:
                input = float(raw_input(prompt))
            except ValueError:
                print "Please enter a valid float."
                continue
        else:
            input = str(raw_input(prompt))
        if options and input not in options:
            print "Not a valid option"
            continue
        elif not raw_input("Confirm input (y, n): ").lower() == 'y':
            print "Input not confirmed. Try again."
            continue
        else:
            return input
