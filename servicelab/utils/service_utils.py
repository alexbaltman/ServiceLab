"""
Stack utility functions
"""
import os
import re
import shutil

import platform
import subprocess32 as subprocess
from reconfigure.configs import ExportsConfig

import yaml_utils
import logger_utils
from servicelab import settings

slab_logger = logger_utils.setup_logger(settings.verbosity, 'stack.utils.service')


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
    slab_logger.log(15, 'Synchronizing %s in servicelab/.stack/services' % service_name)
    # Note: Branch defaults to master in the click application
    check_for_git_output, myinfo = _check_for_git()
    if not check_for_git_output == 0:
        slab_logger.error("Could not find git executable.")
        return False
    else:
        # TODO: refactor this back in -->or os.listdir(os.path.join(path,
        #       "services/%s" % (service_name))) == []: on the or part
        #       we'll want to rm the dir if it's there but empty b/c this
        #       isn't handling that.
        if os.path.isdir(os.path.join(path, "services", service_name)):
            slab_logger.debug("Sync'ing service.")
            slab_logger.debug("Fast Forward Pull.")
            returncode, myinfo = _git_pull_ff(path, branch, service_name)
            if returncode != 0:
                slab_logger.error(myinfo)
                return False
            else:
                slab_logger.debug("Service has been sync'ed.")
                return True
        else:
            slab_logger.debug("Trying clone.")
            returncode, myinfo = _git_clone(path, branch, username, service_name)
            if returncode != 0:
                slab_logger.error(myinfo)
                return False
            else:
                slab_logger.debug("Clone successful.")
                return True


def build_data(path):
    """Build ccs-data for site ccs-dev-1 and move built hosts into .stack/

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
    slab_logger.log(15, 'Building ccs-dev-1 site in ccs-data')
    if yaml_utils.decrypt_set(path) != 0:
        return(1, "unable to decrypt the pulp password")

    data_reponame = "ccs-data"
    slab_logger.debug("Building the data.")
    returncode, myinfo = run_this('./lightfuse.rb -c hiera-bom-unenc.yaml '
                                  '--site ccs-dev-1 && cd .',
                                  cwd=os.path.join(path, "services",
                                                   data_reponame))
    if returncode == 0:
        try:
            # src, dest
            shutil.copyfile(os.path.join(path,
                                         'services',
                                         data_reponame,
                                         'out',
                                         'ccs-dev-1',
                                         'dev-tenant',
                                         'etc',
                                         'ccs',
                                         'data',
                                         'hosts'),
                            os.path.join(path,
                                         'hosts'))
        except IOError as err:
            return(1, err)
    return(returncode, myinfo)


def copy_certs(frompath, topath):
    """Copy certs to ccs puppet module.

    Args:
        frompath (str): Where the certs currently reside.
        topath (str): The base path to puppet dir.

    Returns:
        returncode (int) -- 0 if successful, failure otherwise

    Example Usage:
        returncode = service_utils.copy_certs(ctx.reporoot_path(),puppet_path)
    """
    slab_logger.log(15, 'Copying certs to ccs puppet module')
    certdir = os.path.join(topath, "modules", "ccs", "files", "certs", "dev-csi-a")
    if not os.path.exists(certdir):
        os.mkdir(certdir)
    returncode = 0
    for certfile in ['ccsapi.dev-csi-a',
                     'meter.dev-csi-a',
                     'ha_dev-csi-a',
                     'ha_storage.dev-csi-a']:
        try:
            shutil.copy("{0}/{1}.cis.local.pem".format(frompath, certfile),
                        certdir)
        except:
            returncode = 1
    return returncode


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
    slab_logger.log(15, 'Cloning %s into servicelab/.stack/services' % service_name)
    # Note: Branch defaults to master in the click application
    # DEBUG: print "Executing subprocess for git clone"
    # DEBUG: print 'git clone -b %s ssh://%s@cis-gerrit.cisco.com:29418/%s
    #        %s/services/%s' % (branch, username, service_name, path,
    #        service_name)
    # TODO: ADD error handling here - specifically, I encountered a bug where
    #       if a branch in upstream doesn't exist and you've specified it, the
    #       call fails w/ only the poor err msg from the calling function.
    returncode, myinfo = run_this("git clone --depth=1 -b %s "
                                  "ssh://%s@cis-gerrit.cisco.com:29418/%s "
                                  "%s/services/%s" % (branch, username,
                                                      service_name, path,
                                                      service_name))
    if returncode != 0:
        # check if failure because of unresolved references
        pstr = "fatal: pack has [0-9]+ unresolved deltas\nfatal: index-pack failed"
        ptrn = re.compile(pstr)
        if ptrn.search(myinfo):
            # we are going to ignore any unresolved references as we are doing only
            # shallow copy with depth 1
            SERVICE_UTILS_LOGGER.info("Ignoring unresolved references as "
                                      "slab does a shallow clone of the "
                                      "service repo")
            returncode = 0
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
    slab_logger.log(15, 'Fast forward only pull of %s branch %s' % (service_name, branch))
    # Note: Branch defaults to master in the click application
    service_path = os.path.join(path, "services", service_name)

    # Before doing git checkout, check if the remote ref exists
    # if it does not then take some steps to get it and run checks
    try:
        slab_logger.log(25, "Checking for remote references in %s " % (service_path))
        command_to_run = "git show-ref %s" % (branch)
        output = subprocess.Popen(command_to_run, shell=True,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, close_fds=True,
                                  cwd=service_path)
        ref_info = output.communicate()[0]
        if branch not in ref_info:
            slab_logger.log(25, "Remote git branch not found : %s " % (branch))
            slab_logger.log(25, "Setting remote origin in .git/config to :"
                                " +refs/heads/*:refs/remotes/origin/*")
            command_to_run = "git config --replace-all  remote.origin.fetch"\
                "  \"+refs/heads/*:refs/remotes/origin/*\""
            output = subprocess.Popen(command_to_run, shell=True,
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT, close_fds=True,
                                      cwd=service_path)
            command_to_run = "git fetch --unshallow"
            slab_logger.log(25, "Fetching all remote branches. "
                            "It might take a few minutes. %s " % (service_path))
            subprocess.call('git fetch --unshallow', cwd=service_path, shell=True)
            slab_logger.log(25, "Done Fetching all remote branches.")
            slab_logger.log(25, "Updating remotes. ")
            call(["git", "remote", "update"], cwd=service_path)
            slab_logger.log(25, "Done update remotes. ")
            command_to_run = "git show-ref %s" % (branch)
            output = subprocess.Popen(command_to_run, shell=True,
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT, close_fds=True,
                                      cwd=service_path)
            ref_info = output.communicate()[0]
            if branch not in ref_info:
                slab_logger.log(25, "Remote branch %s not found." % (branch))
                command_to_run = "git show-ref"
                output = subprocess.Popen(
                    command_to_run,
                    shell=True,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    close_fds=True,
                    cwd=service_path)
                ref_info = output.communicate()[0]
                slab_logger.log(25, "Following branches found : %s " % ref_info)
                slab_logger.log(25, "Branch not found. Please, check branch name. Exiting.")
    except OSError, ex:
        SERVICE_UTILS_LOGGER.error(ex)
        return (1, str(ex))

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
    slab_logger.log(15, 'Fast forward pull of all ccs-data submodules')
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
    slab_logger.log(15, 'Checking if git is installed')
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


def _check_for_libpup():
    """Check if librarian-puppet is available on the current system.

    Returns:
        returncode (int) -- 0 if git exists, otherwise doesn't
        myinfo (str)     -- stderr/stdout logs of the attempted "type git"

    Example Usage:
        >>> print _check_for_libpup()
        (0, "")
    """
    slab_logger.log(15, 'Checking for librarian-puppet')
    # Note: Using 'type' here to establish if posix system has a binary
    #       called librarian-puppet instead of 'which' b/c which often doesn't return
    #       proper 0 or 1 exit status' and type does. Which blah on many
    #       systems returns 0, which is bad.
    if os.name == "posix":
        returncode, myinfo = run_this('type librarian-puppet')
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
    slab_logger.log(15, 'Checking for Vagrant ssh keys in the .stack directory')
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
    slab_logger.log(15, 'Setting the current service to %s' % service_name)
    if service_name == "current":
        if os.path.isfile(os.path.join(path, "current")):
            currentf = open(os.path.join(path, "current"), 'r')
            currentf.seek(0)
            service_name = currentf.readline()
        else:
            slab_logger.error("Current file doesn't exist\
                                        and service set to current\
                                        . Please enter a service to\
                                        work on.")
            return 1

    with open(os.path.join(path, "current"), 'w+') as service_file:
        service_file.seek(0)
        service_file.write(service_name)
        service_file.truncate()

    if not os.path.islink(os.path.join(path, "current_service")):
        # Note: What to link is first arg, where to link is second aka src dest
        if os.path.isdir(os.path.join(path, "services", service_name)):
            os.symlink(os.path.join(path, "services", service_name),
                       os.path.join(path, "current_service"))
        else:
            slab_logger.debug("Could not find source for symlink.\
                                       Attempting re-clone of source.")
            sync_service(path, branch, username, service_name)
            if os.path.isdir(os.path.join(path, "services", service_name)):
                os.symlink(os.path.join(path, "services", service_name),
                           os.path.join(path, "current_service"))
            else:
                slab_logger.error("Failed to find source for symlink: " +
                                  os.path.join(path, "services", service_name))
                return 1
    else:
        slab_logger.debug("Link already exists.")
        return 0


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
    slab_logger.log(15, 'Cleaning up services and services symlinks')
    run_this('vagrant destroy -f')
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
    slab_logger.log(15, 'Checking gerrit for %s' % service_name)
    if service_name == "current":
        if os.path.isfile(os.path.join(path, "current")):
            cfile = open(os.path.join(path, "current"), 'r')
            cfile.seek(0)
            service_name = cfile.readline()
        else:
            slab_logger.error("Current file doesn't exist and service set to current\
                                        . Please enter a service to work on.")
            return 1

    if os.path.exists(os.path.join(path, "cache")):
        if os.path.isfile(os.path.join(path, "cache", "projects")):
            for line in open(os.path.join(path, "cache", "projects"), 'r'):
                # Note: re.search takes a search term as 1st arg and what to
                #       search as second arg.
                if re.search(service_name, line):
                    return 0

            ret_val, ret_str = run_this('ssh -p 29418 ccs-gerrit.cisco.com '
                                        '"gerrit ls-projects" > %s'
                                        % (os.path.join(path, "cache", "projects")))
            if ret_val != 0:
                SERVICE_UTILS_LOGGER.error("Unable to fetch project list from gerrit")
                SERVICE_UTILS_LOGGER.error("error {}".format(ret_str))
                return 1
            for line in open(os.path.join(path, "cache", "projects"), 'r'):
                if re.search(service_name, line):
                    return 0

            # Note: We didn't succeed in finding a match.
            slab_logger.error("Could not find repo in ccs-gerrit.")
            return 1
    else:
        os.makedirs(os.path.join(path, "cache"))
        cachef = open(os.path.join(path, "cache", "projects"), 'w+')
        # Note: We close right away b/c we're just trying to
        #       create the file.
        cachef.close()
        ret_val, ret_str = run_this('ssh -p 29418 ccs-gerrit.cisco.com '
                                    '"gerrit ls-projects" > %s'
                                    % (os.path.join(path, "cache", "projects")))
        if ret_val != 0:
            SERVICE_UTILS_LOGGER.error("Unable to fetch project list from gerrit")
            SERVICE_UTILS_LOGGER.error("error {}".format(ret_str))
            return 1

        for line in open(os.path.join(path, "cache", "projects"), 'r'):
            if re.search(service_name, line):
                return 0

        # Note: We didn't succeed in finding a match.
        slab_logger.error("Could not find repo in ccs-gerrit.")
        return 1


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
    slab_logger.debug('Running shell command "%s"' % command_to_run)
    try:
        output = subprocess.Popen(command_to_run, shell=True,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, close_fds=True,
                                  cwd=cwd)

        myinfo = output.communicate()[0]
        myinfo.strip()
        return(output.returncode, myinfo)
    except OSError, ex:
        slab_logger.error(ex)
        return (1, str(ex))


def installed(service, path):
    """ Checks if the service is installed in the stack

    Args:
        service (str): Service name
        path (str): The stack path

    Returns:
        Return true if the service is installed and false if current is
        not set to the correct service or if the service is not instaleld
        in the service dircetory

    """
    slab_logger.log(15, 'Checks if %s is installed in the stack' % service)
    # check if the current is set to correct service
    try:
        with open(os.path.join(path, "current"), 'r') as currentf:
            service_name = currentf.readline()
        if service_name != service:
            return False

        input_path = os.path.realpath(os.path.join(path, "services", service))
        current_path = os.path.join(path, "current_service")
        if not (os.path.isdir(input_path) or
                os.path.isdir(current_path)):
            return False
        if not os.path.samefile(input_path, current_path):
            return False
    except Exception as ex:
        slab_logger.error(ex)
        return False
    return True


def export_for_nfs(rootpassword, path, ip):
    """
    This function is currently not in use. It is vagrant responsibilty to
    update the /etc/exports file.
    """
    def __darwin_check_option(existing_opt):
        flag = False
        entry = existing_opt.clients
        for opt in entry:
            if opt.name == ip:
                flag = True
                break

        if not flag:
            return flag

        # now we check other options including userid, gid
        flag = False
        for opt in entry:
            if opt.name == "-alldirs":
                flag = True
                break

        if not flag:
            return flag

        cstr = "-mapall={}:{}".format(os.getuid(), os.getgid())
        flag = False
        for opt in entry:
            if opt.name == cstr:
                flag = True
                break
        return flag

    def __darwin_update():
        cmd = "echo {} | sudo -S chmod o+w /etc/exports".format(rootpassword)
        ret_code, ret_info = run_this(cmd)
        if ret_code != 0:
            return 1

        line = '\\"{}\\" {} -alldirs -mapall={}:{}'.format(path,
                                                           ip,
                                                           os.getuid(),
                                                           os.getgid())
        cmd = 'echo \"{}\" >> /etc/exports'.format(line)
        ret_code, ret_info = run_this(cmd)
        if ret_code != 0:
            SERVICE_UTILS_LOGGER.error(ret_info)
            return 1

        cmd = "echo {} | sudo -S chmod o-w /etc/exports".format(rootpassword)
        ret_code, ret_info = run_this(cmd)
        if ret_code != 0:
            SERVICE_UTILS_LOGGER.error(ret_info)
            return 1

        cmd = "echo {} | sudo -S nfsd update".format(rootpassword)
        ret_code, ret_info = run_this(cmd)
        if ret_code != 0:
            SERVICE_UTILS_LOGGER.error(ret_info)
            return 1
        return 0

    def __linux_check_option(existing_opt):
        flag = False
        entry = existing_opt.clients
        for opt in entry:
            if opt.name == ip:
                flag = True
                break
        if not flag:
            return flag

    def __linux_update():
        cmd = "echo {} | sudo -S chmod o+w /etc/exports".format(rootpassword)
        ret_code, ret_info = run_this(cmd)
        if ret_code != 0:
            return 1

        line = '(rw,no_subtree_check,all_squash,anonuid={},anongid={},fsid=1777472711)'
        line = '\\"{}\\" {}'+line
        line = line.format(path, ip, os.getuid(), os.getgid())
        cmd = 'echo \"{}\" >> /etc/exports'.format(line)
        ret_code, ret_info = run_this(cmd)
        if ret_code != 0:
            SERVICE_UTILS_LOGGER.error(ret_info)
            return 1

        cmd = "echo {} | sudo -S chmod o-w /etc/exports".format(rootpassword)
        ret_code, ret_info = run_this(cmd)
        if ret_code != 0:
            SERVICE_UTILS_LOGGER.error(ret_info)
            return 1

        cmd = "echo {} | sudo exportfs -ra".format(rootpassword)
        ret_code, ret_info = run_this(cmd)
        if ret_code != 0:
            SERVICE_UTILS_LOGGER.error(ret_info)
            return 1
        return 0

    vagrant_responsibility = True
    if not vagrant_responsibility:
        if platform.system() == 'Darwin':
            __check = __darwin_check_option
            __update = __darwin_update
        elif platform.system() == 'Linux':
            __check = __linux_check_option
            __update = __linux_update
        else:
            ret_info = "servicelab support nfs mount for mac os or redhat/linux only"
            SERVICE_UTILS_LOGGER.error(ret_info)
            return 1

        # check if the ip exist with the options
        exp_list = ExportsConfig(path="/etc/exports")
        exp_list.load()
        for opt in exp_list.tree.exports:
            if opt.name == path and __check(opt) is True:
                return 0

        # add the mount
        return __update()
    return 0
