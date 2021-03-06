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
    slab_logger.log(15, 'Synchronizing %s in servicelab/.stack/services/' % service_name)
    # Note: Branch defaults to master in the click application
    returncode, myinfo = _check_for_cmd('git')
    if not returncode == 0:
        slab_logger.error("Could not find git executable.")
        return False
    else:
        service_path = os.path.join(path, "services", service_name)
        if os.path.isdir(service_path):
            # Check for and remove empty service_name directory within .stack/services
            # Will encounter git errors if the dir is not empty, but is not a gerrit repo
            if os.listdir(service_path) == []:
                shutil.rmtree(service_path)
            slab_logger.debug("Sync'ing repo %s" % service_name)
            returncode, myinfo = _git_pull_ff(path, branch, service_name)
            if not returncode == 0:
                slab_logger.error(myinfo)
                return False
            else:
                slab_logger.debug("%s has been sync'ed." % service_name)
                return True
        else:
            slab_logger.debug("Cloning repo %s." % service_name)
            returncode, myinfo = _git_clone(path, branch, username, service_name)
            if returncode != 0:
                slab_logger.error(myinfo)
                return False
            else:
                slab_logger.debug("%s cloned successful." % service_name)
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
    if not os.path.isdir(os.path.join(path, 'services', 'ccs-data')):
        return(1, 'Could not find ccs-data repo.  Pleas try "stack workon ccs-data"')
    if yaml_utils.decrypt_set(path) != 0:
        return(1, "unable to decrypt the pulp password")

    data_reponame = "ccs-data"
    slab_logger.debug("Building the data.")
    returncode, myinfo = run_this(
        './lightfuse.rb -c hiera-bom-unenc.yaml --site ccs-dev-1 && cd ..',
        cwd=os.path.join(path, "services", data_reponame))
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
        source_path = os.path.join(ctx.path, 'provision')
        puppet_path = os.path.join(ctx.path, 'services', 'service-redhouse-tenant', 'puppet')
        returncode = service_utils.copy_certs(source_path, puppet_path)
    """
    slab_logger.log(15, 'Copying certs to ccs puppet module')
    if not os.path.exists(topath):
        slab_logger.error('Unable to find %s.\nPlease ensure that "stack workon" '
                          'has been run for the appropriate service' % topath)
        return 1
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
    # DETAIL: "Executing subprocess for git clone"
    # DEBUG: print 'git clone -b %s ssh://%s@cis-gerrit.cisco.com:29418/%s
    #        %s/services/%s' % (branch, username, service_name, path,
    #        service_name)
    returncode, myinfo = run_this(
        "git clone --depth=1 -b %s ssh://%s@cis-gerrit.cisco.com:29418/%s %s/services/%s"
        % (branch, username, service_name, path, service_name))
    if not returncode == 0:
        slab_logger.error(myinfo)
        return(1, myinfo)
    # check if failure because of unresolved references
    pstr = "fatal: pack has [0-9]+ unresolved deltas\nfatal: index-pack failed"
    ptrn = re.compile(pstr)
    if ptrn.search(myinfo):
        # we are going to ignore any unresolved references as we are doing only
        # shallow copy with depth 1
        slab_logger.info("Ignoring unresolved references as slab does a shallow clone of "
                         "the service repo")
        returncode = 0
        myinfo = ""
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
    slab_logger.debug("Checking for remote references in %s " % (service_path))
    returncode, output = run_this('git show-ref %s' % (branch), cwd=service_path)
    if not returncode == 0:
        return(returncode, output)
        slab_logger.error('"git show-ref %s" returned an error for %s\ncmd output: %s'
                          % (branch, service_name, output))
    if branch not in output:
        slab_logger.log(25, "Remote git branch not found : %s " % (branch))
        slab_logger.log(25, "Setting remote origin in .git/config to :"
                            " +refs/heads/*:refs/remotes/origin/*")
        command_to_run = 'git config --replace-all  remote.origin.fetch'\
                         '  "+refs/heads/*:refs/remotes/origin/*"'
        returncode, output = run_this(command_to_run, cwd=service_path)
        if not returncode == 0:
            return(returncode, output)
        slab_logger.debug("Fetching all remote branches. It might take a few minutes. %s"
                          % (service_path))
        returncode, output = run_this('git fetch --unshallow', cwd=service_path)
        if not returncode == 0:
            return(returncode, output)
        slab_logger.debug("Done Fetching all remote branches.  Updating remotes.")
        returncode, output = run_this('git remote update', cwd=service_path)
        if not returncode == 0:
            return(returncode, output)
        slab_logger.debug("Remote updates completed. ")
        command_to_run = "git show-ref %s" % (branch)
        returncode, output = run_this(command_to_run, cwd=service_path)
        if not returncode == 0:
            return(returncode, output)
        if branch not in output:
            slab_logger.error("Remote branch %s not found." % (branch))
            returncode, output = run_this("git show-ref", cwd=service_path)
            if not returncode == 0:
                return(returncode, output)
            ref_info = output.communicate()[0]
            slab_logger.log(25, "The following branches were found : %s " % ref_info)
            slab_logger.log(25, "Branch not found. Please, check branch name. Exiting.")
            return(1, 'Unable to find remote branch')
    # TODO: Do more error checking here --> after debugging, definitely
    # TODO: checkout a branch ifexists in origin only--> not replacing git
    #       or setup a tracking branch if there's nothing local or fail.
    returncode, output = run_this('git checkout %s' % (branch), cwd=service_path)
    if not returncode == 0:
        return(returncode, output)
    returncode, myinfo = run_this('git pull --ff-only origin %s' % (branch), service_path)
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


def _check_for_cmd(command):
    """Check if the supplied command is available on the current system.

    Returns:
        returncode (int) -- 0 if command exists, otherwise doesn't
        myinfo (str)     -- stderr/stdout logs of the attempted "type <command>"

    Example Usage:
        >>> print _check_for_git()
        (0, "")
    """
    slab_logger.log(15, 'Checking if %s is installed' % command)
    # Note: Using type git here to establish if posix system has a binary
    #       called git instead of which git b/c which often doesn't return
    #       proper 0 or 1 exit status' and type does. Which blah on many
    #       systems returns 0, which is bad.
    if os.name == "posix":
        returncode, myinfo = run_this('type %s' % command)
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
        if returncode == 0:
            slab_logger.debug('SSH keys have been made for Vagrant')
        else:
            slab_logger.debug('Failed to make ssh keys for Vragrant')
        return (returncode, myinfo)
    else:
        slab_logger.debug('Vagrant ssh keys were already installed')
        return(0, '')


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
            slab_logger.error('Unable to determine the current service.  '
                              'Please enter a service to work on.')
            return 1

    returncode = set_current_service(path, service_name)
    if not returncode == 0:
        slab_logger.error('Unable to write to "current" file')
        return 1

    if not os.path.islink(os.path.join(path, "current_service")):
        # Note: What to link is first arg, where to link is second aka src dest
        if os.path.isdir(os.path.join(path, "services", service_name)):
            os.symlink(os.path.join(path, "services", service_name),
                       os.path.join(path, "current_service"))
            slab_logger.debug('Made symlink for %s' % service_name)
            return 0
        else:
            slab_logger.debug('Could not find source for symlink.  '
                              'Attempting re-clone of %s.' % service_name)
            returncode = sync_service(path, branch, username, service_name)
            if returncode:
                os.symlink(os.path.join(path, "services", service_name),
                           os.path.join(path, "current_service"))
                slab_logger.debug('Made symlink for %s' % service_name)
                return 0
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
    slab_logger.debug('.stack/current file deleted')
    if os.path.islink(os.path.join(path, "current_service")):
        os.unlink(os.path.join(path, "current_service"))
        slab_logger.debug('Symlink removed for .stack/current_service')


def check_service(path, service_name):
    """Checks gerrit for a repo matching service_name.

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
            slab_logger.error('Current file does not exist and service set to current.  '
                              'Please enter a service to work on."')
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

        # Note: We didn't succeed in finding a match.
        slab_logger.error("Could not find repo in ccs-gerrit.")
    slab_logger.debug('Pulling all projects from gerrit')
    ret_val, ret_str = run_this(
        'ssh -p 29418 ccs-gerrit.cisco.com "gerrit ls-projects" > %s'
        % (os.path.join(path, "cache", "projects")))
    if ret_val != 0:
        slab_logger.error("Unable to fetch project list from gerrit")
        slab_logger.error("error {}".format(ret_str))
        return 1

    for line in open(os.path.join(path, "cache", "projects"), 'r'):
        if re.search(service_name, line):
            return 0
    # Note: We didn't succeed in finding a match.
    slab_logger.error("Could not find repo %s in ccs-gerrit." % service_name)
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
        output = subprocess.Popen(command_to_run,
                                  shell=True,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT,
                                  close_fds=True,
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
            returncode = set_current_service(path, service)
            if not returncode == 0:
                return False

        input_path = os.path.realpath(os.path.join(path, "services", service))
        current_path = os.path.join(path, "current_service")
        if not (os.path.isdir(input_path) and
                os.path.isdir(current_path)):
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
            slab_logger.error(ret_info)
            return 1

        cmd = "echo {} | sudo -S chmod o-w /etc/exports".format(rootpassword)
        ret_code, ret_info = run_this(cmd)
        if ret_code != 0:
            slab_logger.error(ret_info)
            return 1

        cmd = "echo {} | sudo -S nfsd update".format(rootpassword)
        ret_code, ret_info = run_this(cmd)
        if ret_code != 0:
            slab_logger.error(ret_info)
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
            slab_logger.error(ret_info)
            return 1

        cmd = "echo {} | sudo -S chmod o-w /etc/exports".format(rootpassword)
        ret_code, ret_info = run_this(cmd)
        if ret_code != 0:
            slab_logger.error(ret_info)
            return 1

        cmd = "echo {} | sudo exportfs -ra".format(rootpassword)
        ret_code, ret_info = run_this(cmd)
        if ret_code != 0:
            slab_logger.error(ret_info)
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
            slab_logger.error(ret_info)
            return 1

        # check if the ip exist with the options
        exp_list = ExportsConfig(path="/etc/exports")
        exp_list.load()
        for opt in exp_list.tree.exports:
            if opt.name == path and __check(opt) is True:
                return 0

        # add the mount
        return __update()


def set_current_service(path, service_name):
    """
    Set the current service in the .stack/current file

    Arguments:
        path (str): Path to .stack directory
        service_name (str): Name of the service

    Returns:
        0 for success
        1 for failure
    """
    slab_logger.log(15, 'Setting the current service to %s' % service_name)
    try:
        with open(os.path.join(path, "current"), 'w+') as service_file:
            service_file.seek(0)
            service_file.write(service_name)
            service_file.truncate()
    except IOError:
        return 1
    return 0
