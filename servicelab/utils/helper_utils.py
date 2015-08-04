import logging
import fnmatch
import os
import sys

# create logger
# TODO: For now warning and error print. Got to figure out how
#       to import the one in stack.py properly.
helper_utils_logger = logging.getLogger('click_application')
logging.basicConfig()


def find_all_yaml_recurs(full_path):
    matches = []
    if os.path.exists(full_path):
        for dirpath, dirnames, filenames in os.walk(full_path):
            # Note: Don't have to look for yml b/c lightfuse
            #       doesn't compile to "yml"s only "yaml"s
            for filename in fnmatch.filter(filenames, '*.yaml'):
                matches.append(os.path.join(dirpath, filename))
    else:
        helper_utils_logger.error("Could not find files in %s"
                                  % (full_path))
        sys.exit(1)

    return matches
