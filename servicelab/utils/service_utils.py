import subprocess32 as subprocess
import fileinput
import getpass
import sys
import os


def sync_service(path, branch, username, service_name):
    """Synchronize a service with servicelab.

    Do a git clone or fast forward pull to bring a given
    service to latest on the given branch.

    """
    # Note: Branch defaults to master in the click application
    check_for_git_output, myinfo = _check_for_git()
    if check_for_git_output[0] == 0:
        # TODO: refactor this back in -->or os.listdir(os.path.join(path,
        #       "services/%s" % (service_name))) == []: on the or part
        #       we'll want to rm the dir if it's there but empty b/c this
        #       isn't handling that.
        if os.path.isdir(os.path.join(path, "services/%s" % (service_name))):
            print "fast forward pull"
            returncode, myinfo = _git_pull_ff(path, branch, service_name)
            if returncode > 0:
                print "Error: " + myinfo
            else:
                print "Service has been sync'ed."
        else:
            print "trying clone"
            returncode, myinfo = _git_clone(path, branch, username, service_name)
            if returncode > 0:
                print "Error: " + myinfo
    else:
        print "Could not find git executable."


def sync_data(path, username, branch):
    """Synchronize ccs-data with servicelab.

    Do a git clone or fast forward pull to bring ccs-data
    to the latest on the given branch.

    """
    data_reponame = "ccs-data"
    # Note: The fileinput lines are a bit tricky, here's what it does:
    #       The original file is moved to a backup file
    #       The standard output is redirected to the original file
    #       within the loop. Thus print statements write back into the orig
    path_to_reporoot = os.path.split(path)
    path_to_reporoot = os.path.split(path_to_reporoot[0])
    path_to_reporoot = path_to_reporoot[0]
    for line in fileinput.input(os.path.join(path_to_reporoot, ".gitmodules"), inplace=True):
        # TODO: replace aaltman --> can prob be more specific w/ the text to find and replace
        # Note: first string after var is search text and username is the replacement text
        #       current username can be found on win and linux using getpass.getuser()
        print line.replace("aaltman", username),

    if os.listdir(os.path.join(path, "services/%s" % (data_reponame))) == []:
        print "Initializing ccs-data as submodule and updating it."
        returncode, myinfo = _run_this('git submodule init && git submodule update',
                                       path_to_reporoot)
        if returncode > 0:
            print "Error: " + myinfo
        else:
            print "Init and update done, now checking out %s" % (branch)
        # Note: Want to checkout the right branch before returning anything.
        service_path = os.path.join(path, "services", data_reponame)
        returncode, myinfo = _run_this('git checkout %s' % (branch),
                                       service_path)
        if returncode > 0:
            print "Error: " + myinfo
        else:
            print "Checkout of %s done." % (branch)
    else:
        print "Pulling latest data (fast forward only)."
        returncode, myinfo = _submodule_pull_ff(path, branch)
        if returncode > 0:
            print "Error: " + myinfo
        else:
            print "Pulled data successfully."


def _build_data(path):
    """Build ccs-data for site ccs-dev-1."""

    data_reponame = "ccs-data"
    print "Building the data."
    returncode, myinfo = _run_this('./lightfuse.rb -c hiera-bom-unenc.yaml --site ccs-dev-1 && cd ..',
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
    returncode, myinfo = _run_this('git clone -b %s ssh://%s@cis-gerrit.cisco.com:29418/%s %s/services/%s'
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
    returncode, myinfo = _run_this('git -C %s pull --ff-only origin %s' %
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
    returncode, myinfo = _run_this('git submodule foreach git pull --ff-only origin %s' %
                                   (branch), path_to_reporoot)
    return(returncode, myinfo)


def _check_for_git():
    """Check if git is available on the current system."""

    # Note: Using type git here to establish if posix system has a binary
    #       called git instead of which git b/c which often doesn't return
    #       proper 0 or 1 exit status' and type does. Which blah on many
    #       systems returns 0, which is bad.
    if os.name == "posix":
        returncode, myinfo = _run_this('type git')
        return(returncode, myinfo)
    elif os.name == "nt":
        # test windows for git
        pass


# Note: This is completely separate from ssh keys involved w/ gerrit actions.
#       It's for Vagrant.
# TODO: Check for ssh commands
def _setup_vagrant_sshkeys(path):
    """Ensure ssh keys are present."""

    if not os.path.isfile(os.path.join(path, "id_rsa")):
        returncode, myinfo = _run_this('ssh-keygen -q -t rsa -N "" -f %s/id_rsa' % (path))
        return (returncode, myinfo)


def _link(path, service_name):
    """Set the current service."""

    f = open(os.path.join(path, "current"), 'w+')
    f.seek(0)
    f.write(service_name)
    f.truncate()
    f.close()
    if not os.path.islink(os.path.join(path, "service")):
        # Note: What to link is first arg, where to link is second aka src dest
        os.symlink(os.path.join(path, "services", service_name), os.path.join(path, "current_service"))

    f = open(os.path.join(path, "hosts"), 'w+')
    f.seek(0)
    f.write("[%s]\nvm-001\nvm-002\nvm-003\n" % (service_name))


def _clean(path):
    """Clean up services and symlinks created from working on services."""

    returncode, myinfo = _run_this('vagrant destroy -f')
    os.remove(os.path.join(path, "current"))
    os.unlink(os.path.join(path, "current_service"))


def _run_this(command_to_run, cwd=os.getcwd()):
    """Run a command via the shell and subprocess."""

    output = subprocess.Popen(command_to_run, shell=True,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, close_fds=True,
                              cwd=cwd
                              )
    myinfo = output.communicate()[0].strip()
    if output.returncode > 0:
        print myinfo
    return(output.returncode, myinfo)


def log(msg, *args):
    """Logs a message to stderr."""
    if args:
        msg %= args
        msg, file = sys.stderr


def vlog(msg, llevel, *args):
    """Logs a message to stderr depending on the loglevel.

    Log Level clarified --> 0 = none, 1 = regular, 2 = verbose, 3 =
    extra verbose, 4 = debug. Default is 1.
    """

    if verbose:
        loglevel = 2
    if vverbose:
        loglevel = 3
    if debug:
        loglevel = 4
    if llevel <= loglevel:
        log(msg, *args)

log("test, testing")
