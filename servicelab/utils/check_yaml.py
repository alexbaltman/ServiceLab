import sys
import subprocess
import service_utils


def validate_syntax(file_name):
    """Syntax checker for a yaml file

    Returns:
        yaml-syntax)checkere returns 0 for success. It returns 1 for failure.
        The failure can occure because :
        - the file has yaml syntax error
        - the file does not exist or is not readable.
        - or ruby is not installed and 1 if there are any syntax errors.
        The Service Utils Log file contains the command output.
    """
    code = "\"require 'yaml'; YAML.load_file('" + file_name + "');\""
    cmd = "ruby -e " + code
    cmd_returncode, cmd_info = service_utils.run_this(cmd)
    if cmd_returncode > 0:
        service_utils.service_utils_logger.error(cmd_info)
        return 1
    service_utils.service_utils_logger.info(cmd_info)
    return 0


# small driver stub
if __name__ == "__main__":
    yaml_syntax_checker(sys.argv[1])
