import logging
import sys
import os

# create logger
# TODO: For now warning and error print. Got to figure out how
#       to import the one in stack.py properly.
service_utils_logger = logging.getLogger('click_application')
logging.basicConfig()
    
def list_envs_or_sites(path, envs_or_sites):
    """List either a site or an environment in ccs-data."""
    
    envs = []
    # TODO: JIC we want to list services in the future
    services = []

    os.listdir(path) 
    # TODO: Add error handling and possibly return code
    ccsdata_reporoot = os.path.join(path, "services", "ccs-data") 
    ccsdata_sitedir = os.path.join(ccsdata_reporoot, "sites")
    our_sites = os.listdir(ccsdata_sitedir)
    our_sites.sort()
    if envs_or_sites == "sites":
        return(our_sites)
    elif envs_or_sites == "envs":
        for item in our_sites:
            # Note: os.walk provides dirpath, dirnames, and files, but next()[1]
            #       provides us just dirnames for an absolute path.
            # Note: Expected to print data.d/ and environments/
            #for dirnames in os.walk(os.path.join(ccsdata_sitedir, item)).next()[1]:
                # Note: Assumption - every site will have dir "environments"
            for dirnames in os.walk(os.path.join(ccsdata_sitedir, item, 
                                                 "environments")).next()[1]:
                envs.append(dirnames)
        envs.sort()
        return(envs)
                        