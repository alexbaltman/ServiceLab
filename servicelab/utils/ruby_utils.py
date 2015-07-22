import service_utils
import logging
import getpass
import os
import re


# create logger
# TODO: For now warning and error print. Got to figure out how
#       to import the one in stack.py properly.
ruby_utils_logger = logging.getLogger('click_application')
logging.basicConfig()


def setup_gems(path, ccsdata_repo=""):
    """ Set ccsdata_repo to 0 for yes 1 for no. This will
        setup the gems in the Gemfile, using bundler."""

    check_for_gems("bundler")

    if ccsdata_repo:
        path_to_reporoot = os.path.join(path, "services", "ccs-data")
    else:
        path_to_reporoot = os.path.split(path)
        path_to_reporoot = os.path.split(path_to_reporoot[0])
        path_to_reporoot = path_to_reporoot[0]

    returncode, myinfo = service_utils.run_this("bundle install",
                                                path_to_reporoot)
    if returncode == 1:
        ruby_utils_logger.error("Error on bundle install: %s" (myinfo))
        return(returncode)
    else:
        return(returncode)


def check_for_gems(gem):
    returncode, myinfo = service_utils.run_this("type gem")
    if returncode == 0:
        returncode_b, myinfo_b = service_utils.run_this('gem list | grep -q %s'
                                                        % (gem))
        if returncode_b == 1:
            ruby_utils_logger.error("Cannot find gem(%s): %s"
                                    % (gem, myinfo_b))
            return(returncode_b)
        else:
            return(returncode_b)

    else:
        ruby_utils_logger.error("Cannot find gem command: %s" % (myinfo))
        return(returncode)


def setup_ruby(username=None):
    # Note: I needed this on my CentOS7 machine, but not my MAC.
    #       Being allowed to fail for now.
    service_utils.run_this("gpg2 --keyserver hkp://keys.gnupg.net \
              --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3")
    returncode = service_utils.run_this("curl -L get.rvm.io | bash -s stable")
    if returncode > 0:
        ruby_utils_logger.error("Failed to install RVM.")
        return(1)
    else:
        if username:
            pass
        else:
            username = getpass.getuser()
    # Add user(s) to rvm group
    # Make sure rvm is in path in .bashrc/.zshrc
    # service_utils.run_this("rvm install ruby-2.0.0-p481")
    # service_utils.run_this("rvm 2.0.0-p481@servicelab --create --ruby-version")


def get_ruby_version():
    returncode, cmd_info = service_utils.run_this('ruby -v')
    if returncode != 0:
        return ""
    match = re.search("[0-9]+.[0-9]+[0-9]+", cmd_info)
    return match.group(0)
