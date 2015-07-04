import subprocess32 as subprocess
import fileinput
import getpass
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


def sync_data(path, username, branch):
#def sync_data(path, data_reponame):
    data_reponame = "ccs-data" 
    # Note: These two lines are a bit tricky, here's what it does:
    #       The original file is moved to a backup file
    #       The standard output is redirected to the original file 
    #       within the loop. Thus print statements write back into the orig
    path_to_reporoot =  os.path.split(path)
    path_to_reporoot = os.path.split(path_to_reporoot[0])
    path_to_reporoot = path_to_reporoot[0]
    for line in fileinput.input(os.path.join(path_to_reporoot, ".gitmodules"), inplace=True):
        # TODO: replace aaltman --> can prob be more specific w/ the text to find and replace
        # Note: first string after var is search text and username is the replacement text
        #       current username can be found on win and linux using getpass.getuser()
        print line.replace("aaltman", username),

    if os.listdir(os.path.join(path, "services/%s" % (data_reponame))) == []: 
        output = subprocess.Popen(
            'git submodule init && git submodule update',
            stderr=subprocess.STDOUT, stdout=subprocess.PIPE,
            stdin=subprocess.PIPE, shell=True, close_fds=True,
            cwd=path_to_reporoot)
        myinfo = output.communicate()[0].strip()
        # Note: Want to checkout the right branch before returning anything.
        service_path = os.path.join(path, "services", data_reponame)
        subprocess.call('git checkout %s' % (branch), cwd=service_path, shell=True)
        return(output.returncode, myinfo)
    else:
        _git_pull_ff(path, branch, data_reponame)
        

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

def _link(path, service_name):
    
    f = open(os.path.join(path, "current"), 'w+')
    #text = f.read()
    #text = re.sub('foobar', 'bar', text)
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



_link('/Users/aaltman/Git/servicelab/servicelab/.stack', "service-sonarqube")
