import service_utils
import subprocess
import logging
import yaml
import sys


# create logger
# TODO: For now warning and error print. Got to figure out how
#       to import the one in stack.py properly.
check_yaml_utils_logger = logging.getLogger('click_application')
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
        check_yaml_utils_logger.error(cmd_info)
        return 1
    check_yaml_utils_logger.info(cmd_info)
    return 0


            # EXP: prints top level, aka "hosts"
            for d in doc:
                # EXP: prints at hostname lvl
                for x in doc[d]:
                    # EXP: prints last level, all the internals
                    #      memory, box, etc.
                    for y in doc[d][x]:
                        print doc[d][x][y]
    except IOError as error:
        vagrant_utils_logger.error('File error: ' + str(error))


def host_isexist_vagrantyaml(file_name, hostname):
    """Check if provided host is in vagrant.yaml file."""

    retcode = validate_syntax(file_name)
    if retcode > 0:
        check_yaml_utils_logger.error("Invalid yaml file")
        sys.exit(1)
    # Note: load vagrant yaml file
    try:
        with open(file_name, 'r') as f:
            doc = yaml.load(f)
            # EXP: Prints top lvl, aka d = "hosts", doc = dictofyaml
            for d in doc:
                # EXP: x = hostname for vagrantyaml
                for x in doc[d]:
                    if hostname == x:
                        check_yaml_utils_logger.debug( 
                        return 0 
                    else:
                        return 1
                    # EXP: prints last level all the internals
                    #      memory, box, etc. Currently unneeded
                    #      for checking if host exits. 
                    #for y in doc[d][x]
                        #print doc[d][x][y]
    except IOError as error:
        vagrant_utils_logger.error('File error: ' + str(error))


# RFI: Do we need to check if host is running or not
#      and if it is running, should we stop it??
# TODO: aaltman july 19 2015 - INCOMPLETE function.
def operate_on_vagrant_yaml(variable, operation):
    """Operate on a vagrant host or its settings.

    Operations could include add_host or remove_host.

    RFI: In the future should add modify host values and 
    return some level of reporting.
    """
    retcode = validate_syntax(file_name)
    if retcode > 0:
        check_yaml_utils_logger.error("Invalid yaml file")
        sys.exit(1)

    # Note: load vagrant yaml file
    try:
        with open(file_name, 'r') as f:
            doc = yaml.load(f)
            for d in doc:
                for x in doc[d]:
                    for y in doc[d][x]
                        print doc[d][x][y]
    except IOError as error:
        vagrant_utils_logger.error('File error: ' + str(error))


# small driver stub
if __name__ == "__main__":
    validate_syntax(sys.argv[1])
