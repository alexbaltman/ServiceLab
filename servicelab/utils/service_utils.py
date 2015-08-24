import subprocess32 as subprocess
import fileinput
import logging
import helper_utils
import sys
import os
import re

# create logger
# TODO: For now warning and error print. Got to figure out how
#       to import the one in stack.py properly.
service_utils_logger = logging.getLogger('click_application')
logging.basicConfig()


def sync_service(path, branch, username, service_name):
    """Synchronize a service with service-lab.

    Do a git clone or fast forward pull to bring a given
    service to latest on the given branch.

    Also prints a log message. If the service directory to be synced exists,
    it pulls the latest branch from git. If it doesn't exist, the function
    tries to clone its latest version.

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
        branch (str): The branch you want to check out to.
        username (str): name of user
        service_name(str): name of service

    Returns:
        True  -- Success
        False -- Failure

    Example Usage:
        >>> print sync_service("/Users/aaltman/Git/servicelab/servicelab/.stack",
                                "master", "aaltman", "ccs-data")
        Sync'ing Service
        Fast forward pull
        Service has been sync'ed
        True
    """

    # Note: Branch defaults to master in the click application
    check_for_git_output, myinfo = _check_for_git()
    if not check_for_git_output == 0:
        service_utils_logger.error("Could not find git executable.")
        return False
    else:
        # TODO: refactor this back in -->or os.listdir(os.path.join(path,
        #       "services/%s" % (service_name))) == []: on the or part
        #       we'll want to rm the dir if it's there but empty b/c this
        #       isn't handling that.
        if os.path.isdir(os.path.join(path, "services/%s" % (service_name))):
            service_utils_logger.debug("Sync'ing service.")
            service_utils_logger.debug("Fast Forward Pull.")
            returncode, myinfo = _git_pull_ff(path, branch, service_name)
            if returncode != 0:
                service_utils_logger.error(myinfo)
                return False
            else:
                service_utils_logger.debug("Service has been sync'ed.")
                return True
        else:
            service_utils_logger.debug("Trying clone.")
            returncode, myinfo = _git_clone(path, branch, username, service_name)
            if returncode != 0:
                service_utils_logger.error(myinfo)
                return False
            else:
                service_utils_logger.debug("Clone successful.")
                return True


def build_data(path):
    """Build ccs-data for site ccs-dev-1.

    Build the data via lightfuse.rb, the BOM generation script.

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.

    Returns:

        returncode (str) -- 0 if success, failure otherwise
        myinfo (str)     -- stderr/stdout of running lightfuse

    Example Usage:
        >>> print build_data("/Users/aaltman/Git/servicelab/servicelab/.stack")
        Building the data
        (0,"")

    """
    data_reponame = "ccs-data"
    service_utils_logger.debug("Building the data.")
    returncode, myinfo = run_this('./lightfuse.rb -c hiera-bom-unenc.yaml\
                                  --site ccs-dev-1 && cd ..',
                                  cwd=os.path.join(path, "services",
                                                   data_reponame
                                                   )
                                  )
    return(returncode, myinfo)


def _git_clone(path, branch, username, service_name):
    """Clone the repository of the passed service.

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
        branch (str): The branch you want to check out to.
        username (str): name of user
        service_name(str): name of service

    Returns:
        returncode (int) -- 0 if successful, failure otherwise
        myinfo (str)     -- stderr/stdout logs of the attempted git clone

    Example Usage:
        >>> print _git_clone("/Users/aaltman/Git/servicelab/servicelab/.stack", "master",
                              "aaltman", "ccs-data")
        (0, "")

    """
    # Note: Branch defaults to master in the click application
    # DEBUG: print "Executing subprocess for git clone"
    # DEBUG: print 'git clone -b %s ssh://%s@cis-gerrit.cisco.com:29418/%s
    #        %s/services/%s' % (branch, username, service_name, path,
    #        service_name)
    # TODO: ADD error handling here - specifically, I encountered a bug where
    #       if a branch in upstream doesn't exist and you've specified it, the
    #       call fails w/ only the poor err msg from the calling function.
    returncode, myinfo = run_this('git clone --depth=1 -b %s \
                                  ssh://%s@cis-gerrit.cisco.com:29418/%s \
                                  %s/services/%s' % (branch, username, service_name, path,
                                  service_name))
    return(returncode, myinfo)


def _git_pull_ff(path, branch, service_name):
    """Fast forward only pull of a service on the given Branch.

    Do a fast forward pull to bring a given
    service to latest on the given branch.

    Does NOT clone the git repository if it doesn't exist.

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
        branch (str): The branch you want to check out to.
        service_name(str): name of service

    Returns:
        returncode (int) -- 0 if successful, failure otherwise
        myinfo (str)     -- stderr/stdout logs of the attempted git pull

    Example Usage:
        >>> print _git_pull_ff("/Users/aaltman/Git/servicelab/servicelab/.stack",
                               "master", "ccs-data")
        (0, "")

    """
    # Note: Branch defaults to master in the click application
    service_path = os.path.join(path, "services", service_name)
    # TODO: Do more error checking here --> after debugging, definitely
    # TODO: checkout a branch ifexists in origin only--> not replacing git
    #       or setup a tracking branch if there's nothing local or fail.
    subprocess.call('git checkout %s' % (branch), cwd=service_path, shell=True)
    returncode, myinfo = run_this('git pull --ff-only origin %s' %
                                  (branch), service_path)
    return(returncode, myinfo)


def _submodule_pull_ff(path, branch):
    """Fast forward pull of all ccs-data submodules.

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
        branch (str): The branch you want to check out to.

    Returns:
        returncode (int) -- 0 if successful, failure otherwise
        myinfo (str)     -- stderr/stdout logs of the attempted git pull

    Example Usage:
        >>> print _submodule_pull_ff("/Users/aaltman/Git/servicelab/servicelab/
                                     .stack", "master")
        (0, "")
    """
    # Note: Branch defaults to master in the click application
    # TODO: Do more error checking here --> after debugging, definitely
    # TODO: checkout a branch ifexists in origin only--> not replacing git
    #       or setup a tracking branch if there's nothing local or fail.
    path_to_reporoot = os.path.split(path)
    path_to_reporoot = os.path.split(path_to_reporoot[0])
    path_to_reporoot = path_to_reporoot[0]
    returncode, myinfo = run_this('git submodule foreach git pull --ff-only origin %s' %
                                  (branch), path_to_reporoot)
    return(returncode, myinfo)


def _check_for_git():
    """Check if git is available on the current system.
    Returns:
        returncode (int) -- 0 if git exists, otherwise doesn't
        myinfo (str)     -- stderr/stdout logs of the attempted "type git"

    Example Usage:
        >>> print _check_for_git()
        (0, "")
    """
    # Note: Using type git here to establish if posix system has a binary
    #       called git instead of which git b/c which often doesn't return
    #       proper 0 or 1 exit status' and type does. Which blah on many
    #       systems returns 0, which is bad.
    if os.name == "posix":
        returncode, myinfo = run_this('type git')
        return(returncode, myinfo)
    elif os.name == "nt":
        # test windows for git
        pass


# Note: This is completely separate from ssh keys involved w/ gerrit actions.
#       It's for Vagrant.
# TODO: Check for ssh commands
def setup_vagrant_sshkeys(path):
    """Ensure ssh keys for Vagrant are present.

    Uses ssh-keygen to generate a keypair if they don't exist.

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.

    Returns:
        returncode (int) -- 0 if successful, failure otherwise
        myinfo (str)     -- stderr/stdout logs of the attempted git pull



    Example Usage:
        >>> setup_vagrant_sshkeys("/Users/aaltman/Git/servicelab/servicelab/.stack",
                                  "master", "ccs-data")
        (0, "")
    """
    if not os.path.isfile(os.path.join(path, "id_rsa")):
        returncode, myinfo = run_this('ssh-keygen -q -t rsa -N "" -f %s/id_rsa' % (path))
        return (returncode, myinfo)


def link(path, service_name, branch, username):
    """Set the current service.

    Sets current service to input service in current file.
    Links the services directory to the current service if link doesn't exist.
    Adds service to hosts file in the form "<name>\nvm-001\nvm-002\nvm-003\n"

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
        service_name(str): name of service
        branch (str): The branch you want to check out to.
        username (str): name of user

    Returns:
        Returns 1 if error, tried to read file that doesn't exist.

    Example Usage:
        >>> print link("/Users/aaltman/Git/servicelab/servicelab/.stack", "ccs-data",
                       "master", "aaltman"")
    """
    if service_name == "current":
        if os.path.isfile(os.path.join(path, "current")):
            f = open(os.path.join(path, "current"), 'r')
            f.seek(0)
            service_name = f.readline()
        else:
            service_utils_logger.error("Current file doesn't exist\
                                        and service set to current\
                                        . Please enter a service to\
                                        work on.")
            return(1)

    f = open(os.path.join(path, "current"), 'w+')
    f.seek(0)
    f.write(service_name)
    f.truncate()
    f.close()

    if not os.path.islink(os.path.join(path, "current_service")):
        # Note: What to link is first arg, where to link is second aka src dest
        if os.path.isdir(os.path.join(path, "services", service_name)):
            os.symlink(os.path.join(path, "services", service_name),
                       os.path.join(path, "current_service"))
        else:
            service_utils_logger.debug("Could not find source for symlink.\
                                       Attempting re-clone of source.")
            sync_service(path, branch, username, service_name)
            if os.path.isdir(os.path.join(path, "services", service_name)):
                os.symlink(os.path.join(path, "services", service_name),
                           os.path.join(path, "current_service"))
            else:
                service_utils_logger.error("Failed to find source for symlink: " +
                                           os.path.join(path, "services", service_name))
                return(1)
    else:
        service_utils_logger.debug("Link already exists.")

    f = open(os.path.join(path, "hosts"), 'w+')
    f.seek(0)
    f.write("[%s]\nvm-001\nvm-002\nvm-003\n" % (service_name))


def clean(path):
    """Clean up services and symlinks created from working on services.

    Destroys all booted VMs.
    Removes current file denoting the current service.
    Removes symbolic link of the current_service.

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.

    Returns:
        Returns no variables.


    Example Usage:
        >>> print clean("/Users/aaltman/Git/servicelab/servicelab/.stack")
    """
    returncode, myinfo = run_this('vagrant destroy -f')
    os.remove(os.path.join(path, "current"))
    if os.path.islink(os.path.join(path, "current_service")):
        os.unlink(os.path.join(path, "current_service"))


def check_service(path, service_name):
    """Checks gerrit for a repo matching service_name.

    Destroys all booted VMs.
    Removes current file denoting the current service.
    Removes symbolic link of the current_service.

    Args:
        path (str): The path to your working .stack directory. Typically,
                    this looks like ./servicelab/servicelab/.stack where "."
                    is the path to the root of the servicelab repository.
        service_name(str): name of service

    Returns:
        returncode (int) -- 0 if successful, failure otherwise

    Example Usage:
        >>> check_service("/Users/aaltman/Git/servicelab/servicelab/.stack", "ccs-data")
        0
    """
    if service_name == "current":
        if os.path.isfile(os.path.join(path, "current")):
            f = open(os.path.join(path, "current"), 'r')
            f.seek(0)
            service_name = f.readline()
        else:
            service_utils_logger.error("Current file doesn't exist\
                                        and service set to current\
                                        . Please enter a service to\
                                        work on.")
            return(1)

    if os.path.exists(os.path.join(path, "cache")):
        if os.path.isfile(os.path.join(path, "cache", "projects")):
            for line in open(os.path.join(path, "cache", "projects"), 'r'):
                # Note: re.search takes a search term as 1st arg and what to
                #       search as second arg.
                if re.search(service_name, line):
                    returncode = 0
                    return(returncode)

            run_this('ssh -p 29418 ccs-gerrit.cisco.com "gerrit ls-projects">\
                     %s' % (os.path.join(path, "cache", "projects"))
                     )
            for line in open(os.path.join(path, "cache", "projects"), 'r'):
                if re.search(service_name, line):
                    returncode = 0
                    return(returncode)

            # Note: We didn't succeed in finding a match.
            returncode = 1
            service_utils_logger.error("Could not find repo in ccs-gerrit.")
            return(returncode)
    else:
        os.makedirs(os.path.join(path, "cache"))
        f = open(os.path.join(path, "cache", "projects"), 'w+')
        # Note: We close right away b/c we're just trying to
        #       create the file.
        f.close()
        run_this('ssh -p 29418 ccs-gerrit.cisco.com "gerrit ls-projects" > %s'
                 % (os.path.join(path, "cache", "projects"))
                 )
        for line in open(os.path.join(path, "cache", "projects"), 'r'):
            if re.search(service_name, line):
                returncode = 0
                return(returncode)

        # Note: We didn't succeed in finding a match.
        returncode = 1
        service_utils_logger.error("Could not find repo in ccs-gerrit.")
        return(returncode)


def run_this(command_to_run, cwd=os.getcwd()):
    """Run a command via the input shell and subprocess.

    Args:
        command_to_run (str): The shell command you want to run.
        cwd (str): The subprocess to run the command. Defaults to the
                   subprocess of the current working directory.

    Returns:
        Return code of the shell command's output and any stderr/stdout data:
        1 -- Failure, couldn't create subprocess/run command
        0 -- Success


    Example Usage:
        >>> print run_this('echo a')
        echo a
        a
    """
    try:
        output = subprocess.Popen(command_to_run, shell=True,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, close_fds=True,
                                  cwd=cwd
                                  )

        myinfo = output.communicate()[0]
        myinfo.strip()
        return(output.returncode, myinfo)
    except OSError, e:
        service_utils_logger.error(e)
        return (1, str(e))
