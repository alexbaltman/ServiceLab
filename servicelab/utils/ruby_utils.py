import service_utils
import helper_utils
import logging
import os
import re

from servicelab.stack import SLAB_Logger

ctx = SLAB_Logger()

ctx.logger. = logging.getLogger('click_application')


def setup_gems(path, ccsdata_repo=0):
    """ Set up gems in Gemfile to be used by bundler.

    Runs `bundle install` to setup gems in ccs-data if repo is present,
    and in home directory otherwise.

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
        ccsdata_repo (int): set to 0 if ccs-data repo exists, 1 if it doesn't

    Returns:
        returncode (int):
            0 -- Success
            1 -- Failure, caused by failed bundle install

    Example Usage:
        >>> print setup_gems("/Users/aaltman/Git/servicelab/servicelab/.stack", 0)
        0
            #bundle install will have been performed in the servicelab root directory
    """
    ctx.logger.log(15, 'Setting up gems in Gemfile to be used by bundler')
    check_for_gems("bundler")

    if ccsdata_repo == 0:
        path_to_reporoot = os.path.join(path, "services", "ccs-data")
    else:
        path_to_reporoot = os.path.split(path)
        path_to_reporoot = os.path.split(path_to_reporoot[0])
        path_to_reporoot = path_to_reporoot[0]

    returncode, myinfo = service_utils.run_this("bundle install",
                                                path_to_reporoot)
    if returncode == 1:
        ctx.logger.error("Error on bundle install: %s" % (myinfo))
        return(returncode)
    else:
        return(returncode)


def uninstall_gem(gem):
    """ Uninstall a specific gem.

    Args:
        gem(str): gem to uninstall

    Returns:
        returncode (int) -- 0 if successful, failure otherwise
        myinfo (str)     -- stderr/stdout logs of the attempted gem uninstall

    Example Usage:
        >>> print uninstall_gem("bundler")
        0
    """
    ctx.logger.log(15, 'Uninstalling gem %s' % gem)
    returncode, myinfo = service_utils.run_this("gem uninstall -aIx %s" % (gem))
    return returncode


def check_for_gems(gem):
    """ Check that a gem exists.

    Before checking for gem, runs `type gem` command to check that gem commands are
    available.
    Outputs log as it checks for gem.

    Args:
        gem(str): gem to search for

    Returns:
        returncode (int) -- 0 if successful find, 1 otherwise (either not found or gem
                                                              command unavailable)

    Example Usage:
        >>> print check_for_gems("bundler")
        0
    """
    ctx.logger.log(15, 'Checking for gem %s' % gem)
    returncode, myinfo = service_utils.run_this("type gem")
    if returncode == 0:
        returncode_b, myinfo_b = service_utils.run_this('gem list | grep -q %s'
                                                        % (gem))
        if returncode_b == 1:
            ctx.logger.error("Cannot find gem(%s): %s" % (gem, myinfo_b))
            return(returncode_b)
        else:
            return(returncode_b)

    else:
        ctx.logger.error("Cannot find gem command: %s" % (myinfo))
        return(returncode)


def setup_ruby(username=None):
    """ Ruby set up.

    Installs rvm
    Sets username if none set.

    Args:
        username (str): defaults to None

    Returns:
        Returns no variables.

    Example Usage:
        >>> print setup_ruby()
            #rvm installed
            #username is set to aaltman
    """
    ctx.logger.log(15, 'Installing rvm')
    # Note: I needed this on my CentOS7 machine, but not my MAC.
    #       Being allowed to fail for now.
    service_utils.run_this("gpg2 --keyserver hkp://keys.gnupg.net \
              --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3")
    returncode = service_utils.run_this("curl -L get.rvm.io | bash -s stable")
    if returncode > 0:
        ctx.logger.error("Failed to install RVM.")
        return(1)
    else:
        if username:
            pass
        else:
            returncode, username = helper_utils.get_gitusername(ctx.path)
            if returncode > 0:
                ctx.logger.error("Couldn't set user.")
    # Add user(s) to rvm group
    # Make sure rvm is in path in .bashrc/.zshrc
    # service_utils.run_this("rvm install ruby-2.0.0-p481")
    # service_utils.run_this("rvm 2.0.0-p481@servicelab --create --ruby-version")


def get_ruby_version():
    """ Returns the version of Ruby.

    Returns:
        Returns ruby version # or nothing if command `ruby -v` fails.

    Example Usage:
        >>> print get_ruby_version()
        2.1.6
    """
    ctx.logger.log(15, 'Determining ruby version')
    returncode, cmd_info = service_utils.run_this('ruby -v')
    if returncode != 0:
        return None
    match = re.search("[0-9]+.[0-9]+.[0-9]+", cmd_info)
    return match.group(0)


def check_devenv():
    """ Check that there is a proper development environment installed.

    Returns:
        True  -- if a Redhat Variant or Windows
        False -- Ubuntu or other machines
    Example Usage:
        >>> print check_devenv()
        True
    """
    ctx.logger.log(15, 'Determining OS environment')
    if os.name == "posix":
        # this only works for RedHat and its variants. It does not work for Ubuntu.
        returncode, cmd_info = service_utils.run_this("yum list ruby-devel")
        if returncode == 0:
            return True
        return False
    return True
