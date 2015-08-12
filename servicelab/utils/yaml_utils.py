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
    """Syntax checker for a yaml file.

    Writes command output to Service Utils Log file.

    Args:
        file_name (str): pathway to file to validate

    Returns:
        0 -- Success
        1 -- failure, possibly because
                - the file has yaml syntax error
                - the file does not exist or is not readable.
                - or ruby is not installed and 1 if there are any syntax errors.

    Example Usage:
        >>> print validate_syntax("~/vagrant.yaml")
        0
    """
    code = "\"require 'yaml'; YAML.load_file('" + file_name + "');\""
    cmd = "ruby -e " + code
    cmd_returncode, cmd_info = service_utils.run_this(cmd)
    if cmd_returncode > 0:
        yaml_utils_logger.error(cmd_info)
        return 1
    yaml_utils_logger.info(cmd_info)
    return 0


def host_exists_vagrantyaml(hostname, pathto_yaml):
    """Check if provided host is in vagrant.yaml file.

    Args:
        hostname (str): The name of the host you would like added to the
                        yaml file.
        pathto_yaml (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
                    But, it can be to the ./servicelab/servicelab/Utils
                    where the reference vagrant.yaml file is.

    Returns:
        Returncode (int):
            0 -- Success
            1 -- Failure

    Example vagrant.yaml format:
            Hosts:
              keystonectl-001:
                role: tenant_keystone_ctl
                domain: 1
                profile: tenant
                ip: 192.168.100.111
                mac: "000027000111"
                memory: 1024
                box: "http://cis-kickstart.cisco.com/ccs-rhel-7.box"
              keystonectl-002:
                etc.

    Example Usage:
        >>> print host_exists_vagrantyaml( "proxyinternal-001",
                                          "/Users/aaltman/Git/servicelab/servicelab/.stack")
        0
    """
    retcode = validate_syntax(os.path.join(pathto_yaml, "vagrant.yaml"))
    if retcode > 0:
        yaml_utils_logger.error("Invalid yaml file")
        return 1
    # Note: load vagrant yaml file
    try:
        with open(os.path.join(pathto_yaml, "vagrant.yaml"), 'r') as f:
            doc = yaml.load(f)

            # EXP: Prints top lvl, aka d = "hosts", doc = dictofyaml
            for d in doc:
                # EXP: x = hostname for vagrantyaml
                for x in doc[d]:
                    if hostname == x:
                        yaml_utils_logger.debug("Found host:" + hostname)
                        return 0
            return 1
    except IOError as error:
        yaml_utils_logger.error('File error: ' + str(error))
        return 1


def gethost_byname(hostname, pathto_yaml):
    """Return a vagrant.yaml single host values dictionary from
       the long dictionary of hostnames.

    Args:
        hostname (str): The name of the host you would like grabbed from the
                        yaml file.
        pathto_yaml (str): The path to your the yaml file directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
    Returns:
        Returncode (int):
            0 -- Success
            1 -- Failure
        Host key values (dict): See the example usage for the data structure
                                that is returned.

    Example Usage:
        >>> print path
        /Users/aaltman/Git/servicelab/servicelab/utils/
        >>> print gethost_byname("vagrant.yaml", "aio-001",
                                  path)
        0, {'aio-001': {'profile': 'aio',
                        'box': 'http://cis-kickstart.cisco.com/ccs-rhel-7.box',
                        'domain': 1,
                        'role': 'aio',
                        'memory': 1024,
                        'ip': '192.168.100.21',
                        'mac': '000027000021'}
           }
    """
    retcode = validate_syntax(os.path.join(pathto_yaml, "vagrant.yaml"))
    if retcode > 0:
        yaml_utils_logger.error("Invalid yaml file")
        return 1
    # Note: load vagrant yaml file
    try:
        with open(os.path.join(pathto_yaml, "vagrant.yaml"), 'r') as f:
            doc = yaml.load(f)
            yourdict = doc['hosts'][hostname]
            if not yourdict:
                yaml_utils_logger.debug("Found host:" + hostname)
                return 1, yourdict
            else:
                yourdict = {hostname: yourdict}
                return 0, yourdict
    except IOError as error:
        yaml_utils_logger.error('File error: ' + str(error))
        return 1, yourdict


def getmin_OS_vms(pathto_yaml, path):
    """Return a list of host dictionaries that have min set to True in the vagrant.yaml

       This is the minimum set of hosts required to have a working ccs platform
       Openstack environment running. Only a few hosts have min: True set in the
       vagrant.yaml.

    Args:
        pathto_yaml (str): The path to your the yaml file directory. This should
                           really be your template vagrant.yaml file where we have
                           already set the expected values for a given host.
    Returns:
        Returncode (int):
            0 -- Success
            1 -- Failure
        Hosts (list): This is a list of dictionaries. See the example usage for
                      the data structure that is returned.

    Example Usage:
        >>> print getmin_OS_vms('/Users/aaltman/Git/servicelab/servicelab/utils')
        0, [{'aio-001': {'profile': 'aio',
                         'box': 'http://cis-kickstart.cisco.com/ccs-rhel-7.box',
                         'domain': 1,
                         'role': 'aio',
                         'memory': 1024,
                         'ip': '192.168.100.21',
                         'mac': '000027000021'},
            }
            {'db-001': { 'role': 'tenant_db'
                         'domain': 1
                         'profile': 'tenant'
                         'ip': '192.168.100.12'
                         'mac': '000027000012'
                         'memory': 512
                         'box': 'http://cis-kickstart.cisco.com/ccs-rhel-7.box'
                         'min': True
            }
            ...
           ]

    RFI: min: True the true is boolean/string?
    """
    host_list = []
    retcode = validate_syntax(os.path.join(pathto_yaml, "vagrant.yaml"))
    if retcode > 0:
        yaml_utils_logger.error("Invalid yaml file")
        return 1, host_list
    # Note: load vagrant yaml file
    try:
        with open(os.path.join(pathto_yaml, "vagrant.yaml"), 'r') as f:
            doc = yaml.load(f)
            for host in doc['hosts']:
                for k in doc['hosts'][host]:
                    if k == "min":
                        returncode, host_dict = gethost_byname(host, pathto_yaml)
                        if returncode == 0:
                            host_list.append(host_dict)
                        else:
                            yaml_utils_logger.error('failed to retrieve a host from\
                                                    vagrant.yaml')
                            return 1, host_list

        if not host_list:
            yaml_utils_logger.error('No hosts in host_list')
            return 1, host_list
        else:
            return 0, host_list
    except IOError as error:
        yaml_utils_logger.error('File error: ' + str(error))
        return 1, host_list


def host_add_vagrantyaml(path, file_name, hostname, site, memory=2,
                         box='http://cis-kickstart.cisco.com/ccs-rhel-7.box',
                         role=None, profile=None, domain=1, storage=0):
    """Add a host to the working (servicelab/servicelab/.stack/) vagrant.yaml file.

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
        file_name (str): Typically vagrant.yaml, but can be any yaml file
                         containing host definitions that follows the
                         structure {host: {hostname_here: {etc.
        hostname (str): The name of the host you would like added to the
                        yaml file.
        site (str): The name of site to lookup the ips.
        memory (int): Memory is given as an integer 1, 2, 3, etc. and multiplied
                      by 512. The default is 2, which results in 2*512 = 1024.
        box (str): The default box is from cis-kickstart called ccs-rhel-7. You can
             swap this variable with a box of your choosing.
        role (str): Primarily for puppet based automation and OSP team compatability.
              The current roles are:
                                    * build
                                    * tenant_keystone_ctl
                                    * tenant_glance_ctl
                                    * tenant_cinder_ctl
                                    * tenant_nova_ctl
                                    * tenant_horizon
                                    * tenant_ceilometer_ctl
                                    * tenant_heat_ctl
                                    * tenant_network_agents
                                    * tenant_proxy_internal
                                    * tenant_proxy_external
                                    * tenant_compute
                                    * tenant_db
                                    * ceph_mon
                                    * ceph_osd
                                    * ceph_rgw
                                    * compute_local
                                    * aio

        profile (str): Primarily for puppet based systems and OSP team compatability.
                 The current profiles are:
                                    * tenant
                                    * aio,tenant
                                    * aio

        domain (str): We're currently using the faux domain of "1"; however, you may
                override the default as needed.
        storage (int): Storage is given as an integer and translated into the
                       desired number of disks up to 11, which corresponds to
                       the letter "k" that the system will see (aka "sdk")

    Returns:
        (int) The return code::
        0 -- Success
        1 -- Failure

    Example Usage:
        >>> print host_add_vagrantyaml("/Users/aaltman/Git/servicelab/servicelab/.stack",
                                       "vagrant.yaml", "infra-001", memory=2, role="build")
        0

    The yaml file will add in the infra node under "Hosts" like this:
        Hosts:
          infra-001:
            role: build
            domain: 1
            profile: None
            ip: 192.168.100.30
            mac: "000027000030"
            memory: 1024
            box: "http://cis-kickstart.cisco.com/ccs-rhel7.box"

    One last note the ip and mac are autogenerated from a couple other
    functions. TODO: add ref to funct here for shortlink.
    """
    retcode = validate_syntax(file_name)
    if retcode > 0:
        yaml_utils_logger.error("Invalid yaml file")
        return 1

    if storage >= 12:
        yaml_utils_logger.error("Invalid yaml file")
        yaml_utils_logger.error("Too many storage disks requested.")
        return 1
    elif storage > 0:
        yaml_utils_logger.error("Invalid yaml file")
        storage_disks = []
        while storage >= 0:
            storage_disks.append(string.ascii_lowercase[disk])
            storage -= 1

    memory *= 512
    if host_exists_vagrantyaml(hostname, path):
        # Note: load vagrant yaml file
        try:
            with open(os.path.join(path, file_name), 'r') as f:
                doc = yaml.load(f)
                returncode, ip, mac_colon, mac_nocolon = next_macip_for_devsite(path, site)
                if returncode > 0:
                    yaml_utils_logger.error("couldn't write file because no ip provided.")
                    return 1
                for d in doc:
                    doc[d][hostname] = {'role': role,
                                        'domain': domain,
                                        'profile': profile,
                                        'ip': ip,
                                        'mac': mac_nocolon,
                                        'memory': memory,
                                        'box':
                                        'http://cis-kickstart.cisco.com/ccs-rhel7.box',
                                        }
                if storage > 0:
                    doc[d][hostname] = {storage: storage_disks}
            stream = file(os.path.join(path, 'vagrant.yaml'), 'w')
            yaml_utils_logger.debug(
                "Adding %s to vagrant environment now." %
                hostname)
            yaml.dump(doc, stream, default_flow_style=False)
            return 0
        except IOError as error:
            yaml_utils_logger.error('File error: ' + str(error))
            return 1
    else:
        yaml_utils_logger.debug("Host %s already exists in vagrant.yaml" % (hostname))
        return 0


# RFI: Do we need to check if host is running or not
#      and if it is running, should we stop it??
def host_del_vagrantyaml(path, file_name, hostname):
    """Remove a host from the working (.stack/) vagrant.yaml.

       Args:
            path (str): The path to your working .stack directory. Typically,
                        this looks like ./servicelab/servicelab/.stack where "."
                        is the path to the root of the servicelab repository.
            file_name (str): Typically vagrant.yaml, but can be any yaml file
                        containing host definitions that follows the
                        structure {host: {hostname_here: {etc.
            hostname (str): The name of the host you would like removed from the
                        vagrant.yaml file.

    Returns:
        (int) The return code::
        0 -- Success
        1 -- Failure

    Example Usage:
        >>> print host_del_vagrantyaml("vagrant.yaml", "keystonectl-001",
                                    "/Users/aaltman/Git/servicelab/servicelab/.stack")
        0
    """
    if not host_exists_vagrantyaml(hostname, path):
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
    """Crawl the known relative path given the base part
        of the path and find all the yaml files to pass to
        another function to pull the ips from.

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
        site (str): You can use the list sites function to find out what
                    sites are available. We're primarily using ccs-dev-1
                    with servicelab.

    Returns:
        Returns a list of strings that look something like xxx.xxx.xxx.xxx,
        where x is a number and there can be between 1 and 3 digits per
        section. For example, "192.168.10.1".

    Example Usage:
        >>> print get_allips_forsite(
                  "/Users/aaltman/Git/servicelab/servicelab/.stack",
                  "ccs-dev-1")
        ['192.168.100.0', '192.168.100.2', '192.168.100.4']
    """
    full_path = os.path.join(path, "services", "ccs-data",
                             "out", site)
    if not os.path.exists(full_path):
        # Note: Takes reg. path to .stack and builds rest
        service_utils.build_data(path)
    allips = []
    returncode, yaml_files = helper_utils.find_all_yaml_recurs(full_path)
    if returncode > 0:
        yaml_utils_logger.error("Failed to get the yamls...exiting")
        sys.exit(1)
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
    """Given a yaml file match all the ips and put them into a list.

    Given a yaml file pull all the matches for the following
    regex:  r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$" -->
    should be a match for an ip. The regex itself says match
    the beginning of the line, immediately followed by by 1-3
    digits, immediately followed by a period, etc. until EOL.

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
        site (str): You can use the list sites function to find out what
                    sites are available. We're primarily using ccs-dev-1
                    with servicelab.

    Returns:
        Returns a list of strings that look something like xxx.xxx.xxx.xxx,
        where x is a number and there can be between 1 and 3 digits per
        section. For example, "192.168.10.1".

    Example Usage:
        >>> print get_allips_forsite(
                  "/Users/aaltman/Git/servicelab/servicelab/.stack",
                  "ccs-dev-1")
        ['192.168.100.0', '192.168.100.2', '192.168.100.4']
    """
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
    """Gets the next ip for the dev site. Calls helper function for mac.

    The reason is it's hardcoded to what ips are being used at the dev site.
    Specifically the 192.168.100.0/24 ip range b/c we don't "yet" have a
    better way for discovering that.

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
        site (str): You can use the list sites function to find out what
                    sites are available. We're primarily using ccs-dev-1
                    with servicelab.

    Returns:
        returncode (int): 0 - Success, 1 - Failure
        ip (str): String of form xxx.xxx.xxx.xxx where x is a number and
                  there can be between 1 and 3 digits per section.
        mac_colon (str): 12 hexadecimal number where every two digits are
                         separated by a ":". I.e. "02:00:27:00:00:99"
        mac_nocolon (str): Same as above except it does not include the
                           colon

    Example Usage:
        >>> print next_macip_for_devsite(
                  "/Users/aaltman/Git/servicelab/servicelab/.stack",
                  "ccs-dev-1")
        (0, '192.168.100.3', '02:00:27:00:00:03', '020027000003')
    """
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
                if returncode == 0:
                    return 0, ip, mac_colon, mac_nocolon
                else:
                    # Note: everything after the 1 should be None b/c
                    #       of the failure in that function.
                    return 1, ip, mac_colon, mac_nocolon


def gen_mac_from_ip(ip):
    """Given an ip address generate a mac address.

    Mac will be in form: 02:00:27:00:0x:xx where the Xs will depend
    on the ip provided. The fourth octet gets turned into those last
    three digits on the end. If it's short we prefix a 0 onto it
    preceding the last colon.

    The macs that we're using are all reserved for private usage.
    Anything that is in form x2:... x6:... xA... or XE... and 12
    digits long and x is a digit is fair game. I went with x2 for
    ours.

    Args:
        ip (str): String of form xxx.xxx.xxx.xxx where x is a number and
                  there can be between 1 and 3 digits per section.

    Returns:
        returncode (int): 0 - Success, 1 - Failure
        mac_colon (str): 12 hexadecimal number where every two digits are
                         separated by a ":". I.e. "02:00:27:00:00:99"
        mac_nocolon (str): Same as above except it does not include the
                           colon

    Example Usage:
        >>> print gen_mac_from_ip("192.168.100.3")
        (0, '02:00:27:00:00:03', '020027000003')
    """
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
    """Given an ip address generate a mac address.

    Mac will be in form: 02:00:27:00:0x:xx where the Xs will depend
    on the ip provided. The fourth octet gets turned into those last
    three digits on the end. If it's short we prefix a 0 onto it
    preceding the last colon.

    The macs that we're using are all reserved for private usage.
    Anything that is in form x2:... x6:... xA... or XE... and 12
    digits long and x is a digit is fair game. I went with x2 for
    ours.

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
        hostname (str): The name of the host you would like added to
                        ccs-data in the ccs-dev-1 site.
        role (str): Primarily for puppet based automation and OSP team compatability.
              The current roles are:
                                    * build
                                    * tenant_keystone_ctl
                                    * tenant_glance_ctl
                                    * tenant_cinder_ctl
                                    * tenant_nova_ctl
                                    * tenant_horizon
                                    * tenant_ceilometer_ctl
                                    * tenant_heat_ctl
                                    * tenant_network_agents
                                    * tenant_proxy_internal
                                    * tenant_proxy_external
                                    * tenant_compute
                                    * tenant_db
                                    * ceph_mon
                                    * ceph_osd
                                    * ceph_rgw
                                    * compute_local
                                    * aio
        site (str): You can use the stack list sites command to find out what
                    sites are available. We're primarily using ccs-dev-1
                    with servicelab. The default is set to ccs-dev-1.
        env (str): You can use the stack list envs command to find out what
                    sites are available. We're primarily using dev-tenant
                    with servicelab. The default is set to dev-tenant.

    Returns:
        returncode (int): 0 - Success, 1 - Failure

    Example Usage:
        >>> print write_dev_hostyaml_out("/Users/aaltman/Git/servicelab/servicelab/.stack",
                                         "testingtesting")
        0

        If you look in:

            "/Users/aaltman/Git/servicelab/servicelab/.stack/services/
            ccs-data/sites/ccs-dev-1/site/environments/dev-tenant-1/
            hosts.d/"

        Altering the aaltman for your username you'll see a new host.yaml where host
        is the hostname you gave this function. and dev-tenant-1 and ccs-dev-1 could
        be different depending on what was provided.

        Finally, the host.yaml file will look something like a physical yaml elsewhere:

            deploy_args:
              cobbler_kickstart: /etc/cobbler/preseed/rhel-preseed
              cobbler_pass: ''
              cobbler_profile: rhel-server-7.0-x86_64
              mac_address: "'00:00:27:00:00:12'"
              management_ip: 192.168.100.254
              management_pass: cisco
              management_type: cimc
            hostname: db-001
            interfaces:
              eth0:
                gateway: 192.168.100.2
                ip_address: 192.168.100.12
                netmask: 255.255.255.0
            nameservers: 192.168.100.2
            role: tenant_db
            server: sdlc-mirror.cisco.com
            type: physical
    """
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
