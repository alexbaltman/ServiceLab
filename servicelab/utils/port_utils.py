import subprocess32 as subprocess
import os


# Note: This is completely separate from ssh keys involved w/ gerrit actions.
#       It's for Vagrant.
def setup_vagrant_sshkeys(path):
    if not os.path.isfile(os.path.join(path, "id_rsa")):
        output = subprocess.call(
            'ssh-keygen -q -t rsa -N "" -f %s/id_rsa' % (path),
            stderr=subprocess.STDOUT, shell=True
                                )
        return (output)


def sync_service(path, branch, username, service_name):
    # Note: Branch defaults to master in the click application
    check_for_git_output = _check_for_git()
    if check_for_git_output[0] == 0:
        # TODO: refactor this back in -->or os.listdir(os.path.join(path,
        #       "services/%s" % (service_name))) == []: on the or part
        #       we'll want to rm the dir if it's there but empty b/c this
        #       isn't handling that.
        if os.path.isdir(os.path.join(path, "services/%s" % (service_name))):
            try:
                print "fast forward pull"
                _git_pull_ff(path, branch, service_name)
            except:
                raise RuntimeError("Git failed to do a fast forward pull.")
        else:
            try:
                print "trying clone"
                _git_clone(path, branch, username, service_name)
            except:
                raise RuntimeError("Git failed to clone service_name.")
    else:
        print "Could not find git executable based off of: type git"
        return 1


def sync_data():
        pass


def _git_clone(path, branch, username, service_name):
    # Note: Branch defaults to master in the click application"""
    # DEBUG: print "Executing subprocess for git clone"
    # DEBUG: print 'git clone -b %s ssh://%s@cis-gerrit.cisco.com:29418/%s
    #        %s/services/%s' % (branch, username, service_name, path,
    #        service_name)
    # TODO: ADD error handling here - specifically, I encountered a bug where
    #       if a branch in upstream doesn't exist and you've specified it, the
    #       call fails w/ only the poor err msg from the calling function.
    output = subprocess.Popen(
        'git clone -b %s ssh://%s@cis-gerrit.cisco.com:29418/%s %s/services/%s'
        % (branch, username, service_name, path, service_name),
        stderr=subprocess.STDOUT, stdout=subprocess.PIPE,
        stdin=subprocess.PIPE, shell=True, close_fds=True)
    myinfo = output.communicate()[0].strip()
    # DEBUG: print "clone returncode: " + str(output.returncode)
    return(output.returncode, myinfo)


def _git_pull_ff(path, branch, service_name):
    # Note: Branch defaults to master in the click application
    service_path = os.path.join(path, "services", service_name)
    # TODO: Do more error checking here --> after debugging, definitely
    # TODO: checkout a branch ifexists in origin only--> not replacing git
    #       or setup a tracking branch if there's nothing local or fail.
    subprocess.call('git checkout %s' % (branch), cwd=service_path, shell=True)
    output = subprocess.Popen(
                              'git -C %s pull --ff-only origin %s' %
                              (service_path, branch), stderr=subprocess.STDOUT,
                              stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                              shell=True, close_fds=True
                              )
    myinfo = output.communicate()[0].strip()
    # DEBUG: print "pull ff returncode: " + str(output.returncode)
    return(output.returncode, myinfo)


def _check_for_git():
    if os.name == "posix":
        # Note: Using type git here to establish if posix system has a binary
        #       called git instead of which git b/c which often doesn't return
        #       proper 0 or 1 exit status' and type does. Which blah on many
        #       systems returns 0, which is bad.
        output = subprocess.Popen('type git', shell=True,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, close_fds=True
                                  )
        myinfo = output.communicate()[0].strip()
        return(output.returncode, myinfo)
    elif os.name == "nt":
        # test windows for git
        pass
    else:
        pass
