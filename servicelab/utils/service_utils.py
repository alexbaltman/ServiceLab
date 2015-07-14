import subprocess32 as subprocess
import fileinput
import logging
import getpass
import sys
import os
import re

# create logger
# TODO: For now warning and error print. Got to figure out how
#       to import the one in stack.py properly.
service_utils_logger = logging.getLogger('click_application')
logging.basicConfig()


def sync_service(path, branch, username, service_name):
    """Synchronize a service with servicelab.

    Do a git clone or fast forward pull to bring a given
    service to latest on the given branch.

    """
    # Note: Branch defaults to master in the click application
    check_for_git_output, myinfo = _check_for_git()
    if check_for_git_output == 0:
        # TODO: refactor this back in -->or os.listdir(os.path.join(path,
        #       "services/%s" % (service_name))) == []: on the or part
        #       we'll want to rm the dir if it's there but empty b/c this
        #       isn't handling that.
        if os.path.isdir(os.path.join(path, "services/%s" % (service_name))):
            print "Sync'ing service."
            print "Fast forward pull."
            returncode, myinfo = _git_pull_ff(path, branch, service_name)
            if returncode > 0:
                service_utils_logger.error(myinfo)
            else:
                print "Service has been sync'ed."
        else:
            print "Trying clone"
            returncode, myinfo = _git_clone(path, branch, username, service_name)
            if returncode > 0:
                service_utils_logger.error(myinfo)
            else:
                print "Clone successfull."
    else:
        print "Could not find git executable."


def sync_data(path, username, branch):
    """Synchronize ccs-data with servicelab.

    Do a git clone or fast forward pull to bring ccs-data
    to the latest on the given branch.

    """
    data_reponame = "ccs-data"
    path_to_reporoot = os.path.split(path)
    path_to_reporoot = os.path.split(path_to_reporoot[0])
    path_to_reporoot = path_to_reporoot[0]
    # Note: The fileinput lines are a bit tricky, here's what it does:
    #       The original file is moved to a backup file
    #       The standard output is redirected to the original file
    #       within the loop. Thus print statements write back into the orig
    for line in fileinput.input(os.path.join(path_to_reporoot, ".gitmodules"), inplace=True):
        # TODO: replace aaltman --> can prob be more specific w/ the text to find and replace
        # Note: first string after var is search text and username is the replacement text
        #       current username can be found on win and linux using getpass.getuser()
        print line.replace("aaltman", username),

    if not os.path.isdir(os.path.join(path, "services/%s" % (data_reponame))):
       os.makedirs(os.path.join(path, "services/%s" % (data_reponame)))

    if os.listdir(os.path.join(path, "services/%s" % (data_reponame))) == []:
        print "Initializing ccs-data as submodule and updating it."
        returncode, myinfo = run_this('git submodule init && git submodule update',
                                       path_to_reporoot)
        if returncode > 0:
            service_utils_logger.error(myinfo)
        else:
            print "Init and update done, now checking out %s" % (branch)
        # Note: Want to checkout the right branch before returning anything.
        service_path = os.path.join(path, "services", data_reponame)
        returncode, myinfo = run_this('git checkout %s' % (branch),
                                       service_path)
        if returncode > 0:
            service_utils_logger.error(myinfo)
        else:
            print "Checkout of %s done." % (branch)
    else:
        print "Pulling latest data (fast forward only)."
        returncode, myinfo = _submodule_pull_ff(path, branch)
        if returncode > 0:
            service_utils_logger.error(myinfo)
        else:
            print "Pulled data successfully."


def _build_data(path):
    """Build ccs-data for site ccs-dev-1."""

    data_reponame = "ccs-data"
    print "Building the data."
    returncode, myinfo = run_this('./lightfuse.rb -c hiera-bom-unenc.yaml --site ccs-dev-1 && cd ..',
                                   cwd=os.path.join(path, "services",
                                                    data_reponame)
                                   )
    return(returncode, myinfo)


def _git_clone(path, branch, username, service_name):
    """Clone the repository of the passed service."""

    # Note: Branch defaults to master in the click application
    # DEBUG: print "Executing subprocess for git clone"
    # DEBUG: print 'git clone -b %s ssh://%s@cis-gerrit.cisco.com:29418/%s
    #        %s/services/%s' % (branch, username, service_name, path,
    #        service_name)
    # TODO: ADD error handling here - specifically, I encountered a bug where
    #       if a branch in upstream doesn't exist and you've specified it, the
    #       call fails w/ only the poor err msg from the calling function.
    returncode, myinfo = run_this('git clone -b %s ssh://%s@cis-gerrit.cisco.com:29418/%s %s/services/%s'
                                   % (branch, username, service_name, path,
                                      service_name))
    # DEBUG: print "clone returncode: " + str(output.returncode)
    return(returncode, myinfo)


def _git_pull_ff(path, branch, service_name):
    """Fast forward only pull of a service on the given Branch."""

    # Note: Branch defaults to master in the click application
    service_path = os.path.join(path, "services", service_name)
    # TODO: Do more error checking here --> after debugging, definitely
    # TODO: checkout a branch ifexists in origin only--> not replacing git
    #       or setup a tracking branch if there's nothing local or fail.
    subprocess.call('git checkout %s' % (branch), cwd=service_path, shell=True)
    returncode, myinfo = run_this('git -C %s pull --ff-only origin %s' %
                                   (service_path, branch))
    return(returncode, myinfo)


def _submodule_pull_ff(path, branch):
    """Fast forward pull of a ccs-data submodule."""

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
    """Check if git is available on the current system."""

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
    """Ensure ssh keys are present."""

    if not os.path.isfile(os.path.join(path, "id_rsa")):
        returncode, myinfo = run_this('ssh-keygen -q -t rsa -N "" -f %s/id_rsa' % (path))
        return (returncode, myinfo)


def link(path, service_name):
    """Set the current service."""

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
            os.symlink(os.path.join(path, "services", service_name), os.path.join(path, "current_service"))
        else:
            service_utils_logger.error("Failed to find source for symlink: " + os.path.join(path, "services", service_name))
            return(1)
    else:
        service_utils_logger.debug("Link already exists.")

    f = open(os.path.join(path, "hosts"), 'w+')
    f.seek(0)
    f.write("[%s]\nvm-001\nvm-002\nvm-003\n" % (service_name))


def clean(path):
    """Clean up services and symlinks created from working on services."""

    returncode, myinfo = run_this('vagrant destroy -f')
    os.remove(os.path.join(path, "current"))
    if os.islink(os.path.join(path, "current_service")):
        os.unlink(os.path.join(path, "current_service"))


def check_service(path, service_name):
    """Checks gerrit for a repo matching service_name."""

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
    """Run a command via the shell and subprocess."""

    output = subprocess.Popen(command_to_run, shell=True,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, close_fds=True,
                              cwd=cwd
                              )
    myinfo = output.communicate()[0].strip()
    if output.returncode > 0:
        service_utils_logger.error(myinfo)
    return(output.returncode, myinfo)
