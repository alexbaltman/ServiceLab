import service_utils
import subprocess
import logging
import yaml
import sys
import os


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


def host_isexist_vagrantyaml(file_name, hostname, path):
    """Check if provided host is in vagrant.yaml file.

    path is either the vagrant.yaml in utils or the live
    working file in .stack.
    """
    retcode = validate_syntax(os.path.join(path, file_name))
    if retcode > 0:
        yaml_utils_logger.error("Invalid yaml file")
        sys.exit(1)
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
        # Note: Don't fail the program here - if file doesn't exist
        #       we should assume that the host is not in the file
        #       mostly b/c (again) that file doesn't exist.
        yaml_utils_logger.error('File error: ' + str(error))


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
        sys.exit(1)

    if storage >= 12:
        yaml_utils_logger.error("Too many storage disks requested.")
        sys.exit(1)
    elif storage > 0:
        storage_disks = []
        while storage >= 0:
            storage_disks.append(string.ascii_lowercase[disk])
            storage -= 1

    memory *= 512
    if not host_isexist_vagrantyaml(file_name, hostname, path):
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
        except IOError as error:
            yaml_utils_logger.error('File error: ' + str(error))
    else:
        yaml_utils_logger.debug("Host %s already exists in vagrant.yaml" % (hostname))


# RFI: Do we need to check if host is running or not
#      and if it is running, should we stop it??
def host_del_vagrantyaml(path, file_name, hostname):
    if host_isexist_vagrantyaml(file_name, hostname, path):
        try:
            with open(os.path.join(path, file_name), 'r') as f:
                doc = yaml.load(f)
                for d in doc:
                    del doc[d][hostname]
            stream = file(os.path.join(path, file_name), 'w')
            yaml_utils_logger.debug('Deleting host: ' + hostname)
            yaml.dump(doc, stream, default_flow_style=False)
        except IOError as error:
            yaml_utils_logger.error('File error: ' + str(error))
    else:
        yaml_utils_logger.debug("Host was not matched or doesn't exist.")


def next_ip_vagrantyaml():
    pass


def next_mac_vagrantyaml():
    pass


# small driver stub
if __name__ == "__main__":
    validate_syntax(sys.argv[1])
