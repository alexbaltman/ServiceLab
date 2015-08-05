from servicelab.utils import yaml_utils
import logging
import os
# import yaml
# create logger
# TODO: For now warning and error print. Got to figure out how
#       to import the one in stack.py properly.
# ccsbuildtools_utils_logger = logging.getLogger('click_application')
# logging.basicConfig()
# TODO: Implement, user-interactive ansyaml functions


def overwrite_ansyaml(path):
    """Overwrites answers-sample.yaml in ccs-build-tools, which is the file used to
    generate new site data.
    Args:
        path (str): path to working .stack directory. Typically looks
                    like ./servicelab/servicelab/stack
    """
    path_to_ans_yaml = os.path.join(path, "services", "ccs-build-tools", "ignition_rb",
                                    "answer-sample.yaml")
    with open(path_to_ans_yaml, 'w') as f:
        f.write("---\n")
        bom_version = _get_bom_version()
        # Gather IP Ranges
        f.write(bom_version)
        returncode, ip_ranges = _ip_ranges(path)
        if returncode > 0:
            return 1
        else:
            f.write(ip_ranges)
        # Gather Tenant Cloud Info
        returncode, tc_info = _tenant_cloud_info(path)
        if returncode > 0:
            return 1
        else:
            f.write(tc_info)
        # Gather Service Cloud Info
        returncode, svc_info = _service_cloud_info(path)
        if returncode > 0:
            return 1
        else:
            f.write(svc_info)


def _get_bom_version():
    """Sets bom version
    """
    return "bom: 4.2\n"


def _ip_ranges(path):
    """Returns a string with all the ip_ranges listed in ip_ranges.yaml
    """
    path_to_new_site_data = os.path.split(path)
    path_to_new_site_data = os.path.join(path_to_new_site_data[0], "utils", "new_site_data")
    path_to_ip_ranges = os.path.join(path_to_new_site_data, "ip_ranges.yaml")
    returncode = yaml_utils.validate_syntax(path_to_ip_ranges)
    if returncode == 0:
        with open(path_to_ip_ranges, 'r') as f:
            ip_ranges = f.read()[4:]
        return 0, ip_ranges
    else:
        # ccsbuildtools_utils_logger.error("ip_ranges.yaml did not have valid syntax")
        return 1, ""


def _tenant_cloud_info(path):
    """Returns a string with all the tenant cloud info listed in tenant_cloud.yaml
    """
    path_to_new_site_data = os.path.split(path)
    path_to_new_site_data = os.path.join(path_to_new_site_data[0], "utils", "new_site_data")
    path_to_tc_info = os.path.join(path_to_new_site_data, "tenant_cloud.yaml")
    returncode = yaml_utils.validate_syntax(path_to_tc_info)
    if returncode == 0:
        with open(path_to_tc_info, 'r') as f:
            tc_info = f.read()[4:]
        return 0, tc_info
    else:
        # ccsbuildtools_utils_logger.error("tenant_cloud.yaml did not have valid syntax")
        return 1, ""


def _service_cloud_info(path):
    """Returns a string with all the service_cloud listed in service_cloud.yaml
    """
    path_to_new_site_data = os.path.split(path)
    path_to_new_site_data = os.path.join(path_to_new_site_data[0], "utils", "new_site_data")
    path_to_svc_info = os.path.join(path_to_new_site_data, "service_cloud.yaml")
    returncode = yaml_utils.validate_syntax(path_to_svc_info)
    if returncode == 0:
        with open(path_to_svc_info, 'r') as f:
            svc_info = f.read()[4:]
        return 0, svc_info
    else:
        # ccsbuildtools_utils_logger.error("service_cloud.yaml did not have valid syntax")
        return 1, ""
