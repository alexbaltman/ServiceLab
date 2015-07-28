import service_utils
import helper_utils
import subprocess32 as subprocess
import logging
import yaml
import sys
import os
import re


# create logger
# TODO: For now warning and error print. Got to figure out how
#       to import the one in stack.py properly.
yaml_utils_logger = logging.getLogger('click_application')
logging.basicConfig()


def validate_syntax(file_name):
    """Syntax checker for a yaml file

    Returns:
        yaml-syntax checker returns 0 for success. It returns 1 for failure.
        The failure can occur because:
        - the file has yaml syntax error
        - the file does not exist or is not readable.
        - or ruby is not installed and 1 if there are any syntax errors.
        The Service Utils Log file contains the command output.
    """
    code = "\"require 'yaml'; YAML.load_file('" + file_name + "');\""
    cmd = "ruby -e " + code
    cmd_returncode, cmd_info = service_utils.run_this(cmd)
    if cmd_returncode > 0:
        yaml_utils_logger.error(cmd_info)
        return 1
    yaml_utils_logger.info(cmd_info)
    return 0


def host_exists_vagrantyaml(file_name, hostname, path):
    """Check if provided host is in vagrant.yaml file.

    path is either the vagrant.yaml in utils or the live
    working file in .stack.
    """
    retcode = validate_syntax(os.path.join(path, file_name))
    if retcode > 0:
        yaml_utils_logger.error("Invalid yaml file")
        return 1
    # Note: load vagrant yaml file
    try:
        with open(os.path.join(path, file_name), 'r') as f:
            doc = yaml.load(f)
            # EXP: Prints top lvl, aka d = "hosts", doc = dictofyaml
            for d in doc:
                # EXP: x = hostname for vagrantyaml
                for x in doc[d]:
                    if hostname == x:
                        yaml_utils_logger.debug("Found host:" + hostname)
                        return 0
                    else:
                        return 1
    except IOError as error:
        yaml_utils_logger.error('File error: ' + str(error))
        return 1


def host_add_vagrantyaml(path, file_name, hostname, memory=2,
                         box='http://cis-kickstart.cisco.com/ccs-rhel7.box',
                         role=None, profile=None, domain=1, storage=0):
    """Add a host to the vagrant.yaml file.

    Memory is given as an integer and multiplied by 512.
    Storage is given as an integer and translated into desired # of disks
    up to 11, which corresponds to "k" alphabetically.
    """

    retcode = validate_syntax(file_name)
    if retcode > 0:
        yaml_utils_logger.error("Invalid yaml file")
        return 1

    if storage >= 12:
        yaml_utils_logger.error("Too many storage disks requested.")
        return 1
    elif storage > 0:
        storage_disks = []
        while storage >= 0:
            storage_disks.append(string.ascii_lowercase[disk])
            storage -= 1

    memory *= 512
    if not host_exists_vagrantyaml(file_name, hostname, path):
        # Note: load vagrant yaml file
        try:
            with open(os.path.join(path, file_name), 'r') as f:
                doc = yaml.load(f)
                for d in doc:
                    doc[d][hostname] = {'role': role,
                                        'domain': domain,
                                        'profile': profile,
                                        'ip': '192.168.100.111',
                                        'mac': '000027000111',
                                        'memory': memory,
                                        'box':
                                        'http://cis-kickstart.cisco.com/ccs-rhel7.box',
                                        }
                if storage > 0:
                    doc[d][hostname] = {storage: storage_disks}

            stream = file(os.path.join(path, 'vagrant.yaml'), 'w')
            yaml_utils_logger.debug("Adding %s to vagrant environment now." % hostname)
            yaml.dump(doc, stream, default_flow_style=False)
            return 0
        except IOError as error:
            yaml_utils_logger.error('File error: ' + str(error))
            return 1
    else:
        yaml_utils_logger.debug("Host %s already exists in vagrant.yaml" % (hostname))


# RFI: Do we need to check if host is running or not
#      and if it is running, should we stop it??
def host_del_vagrantyaml(path, file_name, hostname):
    if host_exists_vagrantyaml(file_name, hostname, path):
        try:
            with open(os.path.join(path, file_name), 'r') as f:
                doc = yaml.load(f)
                for d in doc:
                    del doc[d][hostname]
            stream = file(os.path.join(path, file_name), 'w')
            yaml_utils_logger.debug('Deleting host: ' + hostname)
            yaml.dump(doc, stream, default_flow_style=False)
            return 0
        except IOError as error:
            yaml_utils_logger.error('File error: ' + str(error))
            return 1
    else:
        yaml_utils_logger.debug("Host was not matched or doesn't exist.")
        return 1


# Note: I had to separate this logic out from the
#       get_allips_foryaml b/c of the recursion that
#       that function is using --> aka I couldn't
#       wrap it w/o breaking it.
def get_allips_forsite(path, site):
    full_path = os.path.join(path, "services", "ccs-data",
                             "out", site)
    if not os.path.exists(full_path):
        # Note: Takes reg. path to .stack and builds rest
        service_utils.build_data(path)
    allips = []
    yaml_files = helper_utils.find_all_yaml_recurs(full_path)
    for yaml_f in yaml_files:
        with open(os.path.join(path, yaml_f), 'r') as f:
            doc = yaml.load(f)
            allips.append(get_allips_foryaml(doc))

    # Note: flat b/c list of lists turned into a list
    flat_allips = [item for sublist in allips for item in sublist]

    # Note: Use set to make list unique, it's the best way, but unorders
    #       the list b/c makes it hashable so do it before we sort, then
    #       turn the data set back into a list for easy handling.
    flat_allips = list(set(flat_allips))

    # Note: Pre-process list to sort
    for i in range(len(flat_allips)):
        # Note: %3s is put 3 items sequentially in there from the for loop.
        #       for instance 10.10.10.10 might become " 10. 10. 10. 10"
        #       note the spaces.
        flat_allips[i] = "%3s.%3s.%3s.%3s" % tuple(flat_allips[i].split("."))
    # Note: now it's easier/possible to sort. Builtin sort = very fast
    #       and the old cmp function very inefficient comparitively.
    flat_allips.sort()
    # Note: Now remove the spaces aka post-processing
    for i in range(len(flat_allips)):
        flat_allips[i] = flat_allips[i].replace(" ", "")

    # for i in flat_allips:
    #    print i

    return flat_allips


# Note: d as in dict
# TODO: needs to be refactored, besides the fact it's not
#       very elegant it also doesn't handle nested lists aka
#       lists of lists, etc. Fortunately it just seems to
#       skip them.
def get_allips_foryaml(d):
    regex = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    matches = []

    for k, v in d.iteritems():
        if isinstance(v, dict):
            # Note: Recurse here
            get_allips_foryaml(v)
        else:
            # Note: Function Breaks on lists so you have to
            #       break up the list to the items in it.
            #       There's prob. a better way to do this.
            if isinstance(k, list):
                for i in k:
                    # Note: Turn to string in case an int gets through
                    #       and tears down my shitty wall.
                    for match in re.finditer(regex, str(i)):
                        matches.append(i)
            elif isinstance(v, list):
                for i in v:
                    for match in re.finditer(regex, str(i)):
                        matches.append(i)
            else:
                for match in re.finditer(regex, str(k)):
                    matches.append(k)
                for match in re.finditer(regex, str(v)):
                    matches.append(v)

    return matches


def next_macip_for_devsite(path, site):
    # Note: We're assuming a pre-sorted list here from
    #       get_allips_forsite, otherwise we'd have to here.
    l = get_allips_forsite(path, site)
    # [i.split(".")[0] for i in l]
    for ip in l:
        # Note: oct, meaning octet of an ip.
        oct1, oct2, oct3, oct4 = ip.split(".")
        if int(oct1) == 192 and int(oct2) == 168 and int(oct3) == 100:
            # Note: oct4 is str so to add 1 need to make int and then
            #       to compare to list need to make str again.
            oct4 = str(int(oct4)+1)
            # Note: Recreate string w/ new oct 4 for list comparison.
            ip = ".".join([oct1, oct2, oct3, oct4])
            if ip == "192.168.100.1":
                # Note: Don't want to match the gateway.
                continue
            elif ip == "192.168.100.255":
                yaml_utils_logger.error("No ips remaining on the \
                                         192.168.100.0/24 block.")
                return 1
            if ip not in l:
                returncode, mac_colon, mac_nocolon = gen_mac_from_ip(ip)
                if returncode == "0":
                    return 0, ip, mac_colon, mac_nocolon
                else:
                    # Note: everything after the 1 should be None b/c
                    #       of the failure in that function.
                    return 1, ip, mac_colon, mac_nocolon


def gen_mac_from_ip(ip):
    """For dev site only currently - we can get more
       sophisticated in the future"""
    oct1, oct2, oct3, oct4 = ip.split(".")
    # Note: Both missing last 3 digits.
    # Note: x2, x6, xA, xE are all avail for fake macs.
    mac_colon = "02:00:27:00:0"
    mac_nocolon = "020027000"
    if len(oct4) <= 2:
        if len(oct4) == 1:
            oct4 = "0" + oct4
        mac_colon += "0:"
        mac_colon += oct4
        mac_nocolon += "0"
        mac_nocolon += oct4
        return 0, mac_colon, mac_nocolon
    elif len(oct4) == 3:
        for i in oct4:
            if len(mac_colon) == 14:
                mac_colon += ":"
            mac_colon += i
            mac_nocolon += i
        return 0, mac_colon, mac_nocolon
    else:
        yaml_utils_logger.error("Too many digits to be an ip.")
        return 1, mac_colon, mac_nocolon


def write_dev_hostyaml_out(path, hostname, role=None, site="ccs-dev-1",
                           env="dev-tenant"):

    deploy_hostyaml_to = os.path.join(path, "services", "ccs-data", "sites",
                                      site, "environments", env, "hosts.d")

    ret, ip, mac_colon, mac_nocolon = next_macip_for_devsite(path, site)
    if ret > 0:
        return 1

    with open("ccsdata_dev_example_host.yaml", 'r') as f:

        doc = yaml.load(f)
        doc['deploy_args']['mac_address'] = mac_colon
        doc['hostname'] = hostname
        doc['interfaces']['eth0']['ip_address'] = ip
        doc['role'] = role

        if os.path.exists(os.path.join(deploy_hostyaml_to, hostname + ".yaml")):
            yaml_utils_logger.error("Host yaml already exists.")
            return 1
        else:
            stream = file(os.path.join(deploy_hostyaml_to, hostname + ".yaml"), 'w')
            yaml.dump(doc, stream, default_flow_style=False)
            return 0


# small driver stub
if __name__ == "__main__":
    validate_syntax(sys.argv[1])
