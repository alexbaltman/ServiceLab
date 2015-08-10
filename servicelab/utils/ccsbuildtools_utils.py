from servicelab.utils import yaml_utils
import logging
import os
import yaml
from prettytable import PrettyTable
# create logger
# TODO: For now warning and error print. Got to figure out how
#       to import the one in stack.py properly.
# ccsbuildtools_utils_logger = logging.getLogger('click_application')
# logging.basicConfig()
# TODO: Implement, user-interactive ansyaml functions


DEFAULT_IP_RANGES = {'vlan2': '10.202.64.0/25',
                     'vlan4': '10.202.64.128/28',
                     'vlan65': '10.202.76.128/27',
                     'vlan68': '10.202.76.0/25',
                     'vlan82': '10.202.72.0/22',
                     'vlan83': '10.202.78.0/24',
                     'vlan84': '10.202.79.0/24',
                     'vlan67': '10.202.65.0/25',
                     'vlan906': '10.203.228.0/22',
                     }


def gather_site_info(path):
    """Gathers data from user to write into answers-sample.yaml. Stores data into
    new_site_data.
    Args:
        path(str): path to working .stack directory. Typically looks like
                  ./servicelab/servicelab/stack
        site_name(str): name of website
    """
    ip_ranges = {}
    service_cloud = {}
    tenant_clouds = []
    num_tenant_clouds = 1
    print "--- Retreiving site data for service cloud ---"
    service_cloud = {}
    site_name = _input_cloud_info(service_cloud, True)
    # Get user input for tenant clouds
    print "--- Retrieving site data for tenant cloud environments ---"
    print "How many tenant environments do you want in your site?"
    num_tenant_clouds = int(raw_input())
    while _sanity_check(num_tenant_clouds) > 0:
        num_tenant_clouds = raw_input()
    num_tenant_clouds = 1  # right now can only support one tenant cloud
    for i in range(1, num_tenant_clouds+1):
        print "Getting user input for tenant cloud #" + repr(i) + ": "
        tenant_cloud = {}
        _input_cloud_info(tenant_cloud, False)
        tenant_clouds.append(tenant_cloud)
    # Get user input for bom and secret
    print "--- BOM & Password Information ---"
    bom_version = raw_input("Enter the BOM version: ")
    while _sanity_check(bom_version) > 0:
        bom_version = raw_input("Enter the BOM version: ")
    password = raw_input("Enter password to encrypt site: ")
    while _sanity_check(password) > 0:
        password = raw.input("Enter password to encrypt site: ")
    # Get user input for ip_ranges
    print "--- Retrieving site data for ip_ranges ---\n"
    ip_ranges = DEFAULT_IP_RANGES
    while True:
        print "Here are your ip_ranges. Type c to confirm and use these values,\n\
        e to edit/remove ranges, a to add new ranges. \n"
        returncode, ip_ranges = _input_ip_ranges(ip_ranges)
        if returncode == 0:
            break
        elif returncode == 1:
            continue
        else:
            print "error"
            return
    ansyaml_dict = {}
    ansyaml_dict['bom'] = 4.2
    ansyaml_dict['secret'] = 'password'
    ansyaml_dict['ip_ranges'] = ip_ranges
    ansyaml_dict['service_cloud'] = service_cloud
    ansyaml_dict['tenant_cloud'] = tenant_clouds[0]
    path_to_ansyaml = os.path.join(path, "services", "ccs-build-tools",
                                   "ignition_rb", "answer-sample.yaml"
                                   )
    # Dump yaml so user can recheck fields
    with open(path_to_ansyaml, 'w') as f:
        f.write("---\n")
        yaml.dump(ansyaml_dict, f, default_flow_style=False)
    return 0, site_name


def _input_cloud_info(cloud, is_svc):
    """Interacts with user to receive data for building service or tenant cloud.

    Receives user input for all required data for a cloud and inputs it into
    dictionary.

    Args:
        cloud (dict(str -> str/int)): dictionary which will receive input for
                                      cloud's data
        is_svc (bool): flag set to True if dealing with service cloud
    Returns:
        site_name (str) : returns the user-defined name of the site
    """
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
    svc_nodes = ['num_nova2', 'num_nova3']
    svc_nodes_prompts = ['# Nova Nodes for Nova Ctl #2',
                         '# Nova Nodes for Nova Ctl #3'
                         ]
    _user_input_for_list(cloud_input_fields, cloud_input_fields_prompts, cloud, False)
    cloud['controller_count'] = 3
    cloud['cloud_nodes'] = {}
    if is_svc is False:
        _user_input_for_list(tc_nodes, tc_nodes_prompts, cloud['cloud_nodes'], True)
    else:
        _user_input_for_list(svc_nodes, svc_nodes_prompts, cloud['cloud_nodes'], True)
    return cloud['site_name']


def _user_input_for_list(input_fields, prompts, dictionary, is_int):
    """Processes the items in a list, and receives user input for each item.

    Reads each item in input list and prompts the user for its input.

    Args:
        input_fields (list(str)) : a list of fields required for user to input
        prompt (list(str)): list of prompts to ask user for each data field
        dictionary : the dictionary which stores the user inputs
        is_int (bool) : flag which states whether or not receiving ints or strings
    """
    for i in input_fields:
        if is_int is True:
            dictionary[i] = int(raw_input("Enter " +
                                          prompts[input_fields.index(i)] + ": "
                                          )
                                )
            while _sanity_check(dictionary[i]) > 0:
                dictionary[i] = int(raw_input("Enter " +
                                              prompts[input_fields.index(i)] + ": "
                                              )
                                    )
        else:
            dictionary[i] = raw_input("Enter " +
                                      prompts[input_fields.index(i)] + ": "
                                      )
            while _sanity_check(dictionary[i]) > 0:
                dictionary[i] = raw_input("Enter " +
                                          prompts[input_fields.index(i)] + ": "
                                          )


def _input_ip_ranges(ip_ranges):
    """Interacts with user to receive ip address input
    """

    table = PrettyTable(['vlan', 'ip range'])
    table.padding_width = 1
    table.align['vlan'] = 'r'
    table.align['ip range'] = 'l'
    table.sortby = 'vlan'
    for i in ip_ranges:
        table.add_row([i[4:], ip_ranges[i]])
    print table
    print "(c,e,a):"
    input = _get_valid_input(['c', 'e', 'a'])
    if input == 'c':
        return 0, ip_ranges
    elif input == 'a':
        vlan_num, ip_range = _get_new_ip_range()
        if "vlan" + repr(vlan_num) not in ip_ranges:
            ip_ranges["vlan" + vlan_num] = ip_range
        else:
            print "vlan" + repr(vlan_num) + " already exists."
        return 1, ip_ranges
    elif input == 'e':
        returncode, ip_ranges = _edit_dictionary_fields(ip_ranges)
        return 1, ip_ranges


def _edit_dictionary_fields(dictionary):
    """Edit fields in a dictionary
    """
    new_dict = {}
    for i in dictionary:
        print i + "\t : " + dictionary[i] + "\t remove(r), modify(m), keep(k)"
        input = _get_valid_input(['r', 'm', 'k'])
        if input == 'r':
            continue
        elif input == 'm':
            print i + "\t : " + "input new field: "
            new_field = raw_input()
            while _sanity_check(new_field) > 0:
                new_field = raw_input()
            new_dict[i] = new_field
        elif input == 'k':
            new_dict[i] = dictionary[i]
        else:
            return 1, {}
    return 0, new_dict


def _get_new_ip_range():
    """Get new vlan-ip_range pair
    """
    vlan_num = raw_input("Enter vlan number: ")
    while _sanity_check(vlan_num) > 0:
        vlan_num = raw_input("Enter vlan number: ")
    new_range = raw_input("Enter ip_range: ")
    while _sanity_check(new_range) > 0:
        new_range = raw_input("Enter ip_range: ")
    return vlan_num, new_range


def _get_valid_input(valid_args):
    """Make sure user input valid option
    """
    input = raw_input().lower()
    while input not in valid_args:
        print "Please provide a valid input: (" + ", ".join(valid_args) + ")"
        input = raw_input().lower()
    return input.lower()


def _sanity_check(input):
    """Let user confirm data input

    Args:
        input: user input
    Returns:
        0 if user agrees with input, 1 if not
    """
    print "Confirm input: (y, n) " + str(input)
    if _get_valid_input(['y', 'n']) == 'y':
        return 0
    else:
        return 1
