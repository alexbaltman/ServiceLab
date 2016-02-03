"""
Git check utilities
"""
from __future__ import unicode_literals, absolute_import
from __future__ import division, print_function

import os
import re
import subprocess
from subprocess import PIPE
import shlex
import click

from servicelab.stack import Logger

ctx = Logger()


# Global vars
class Gitcheckutils(object):
    """
    Git check utilities class
    """
    debugmod = False
    watchInterval = 0
    srch_dir = None
    ignoreBranch = r'^$'  # empty string

    # Search all local repositories from current directory
    @staticmethod
    def search_repositories(srch_dir):
        """
        searches repositories
        """
        ctx.logger.log(15, 'Searching for git repos')
        if srch_dir is not None and srch_dir[-1:] == '/':
            srch_dir = srch_dir[:-1]
        curdir = os.path.abspath(os.getcwd()) if srch_dir is None else srch_dir

        repo = []

        for directory, dirnames, dummy_filenames in os.walk(curdir):
            if '.git' in dirnames:
                repo.append(directory)

        repo.sort()
        return repo

    @staticmethod
    def get_to_push(ischange, remotes, rep, branch):
        """
        Gets all branches to be pushed
        """
        ctx.logger.log(15, 'Determining branches to be pushed')
        topush = ""
        for remote in remotes:
            count = len(Gitcheckutils.get_local_to_push(rep, remote, branch))
            ischange = ischange or (count > 0)
            if count > 0:
                topush += " %s[To Review:%s files]" % (
                    remote,
                    count
                )
        return topush

    @staticmethod
    def get_to_pull(ischange, remotes, rep, branch):
        """
        Get all branches to be pulled
        """
        ctx.logger.log(15, 'Determining branches to be pulled')
        topull = ""
        for remote in remotes:
            count = len(Gitcheckutils.get_remote_to_pull(rep, remote, branch))
            ischange = ischange or (count > 0)
            if count > 0:
                topull += " %s[To Pull:%s files]" % (
                    remote,
                    count
                )
        return topull

    @staticmethod
    def display_reviews(remotes, rep, branch):
        """
        Displays all display_reviews
        """
        ctx.logger.log(15, 'Displaying all reviews')
        for remote in remotes:
            commits = Gitcheckutils.get_local_to_push(rep, remote, branch)
            if len(commits) > 0:
                rname = "  |--%(remote)s" % locals()
                click.echo(rname)
                for commit in commits:
                    pcommit = "     |--[To Review] %s" % (
                        commit)
                    click.echo(pcommit)

        return

    @staticmethod
    def display_pulls(remotes, rep, branch):
        """
        Displays all display_pulls
        """
        ctx.logger.log(15, 'Displaying all pulls')
        for remote in remotes:
            commits = Gitcheckutils.get_remote_to_pull(rep, remote, branch)
            if len(commits) > 0:
                rname = "  |--%(remote)s" % locals()
                click.echo(rname)
                for commit in commits:
                    pcommit = "     |--[To Pull] %s" % (
                        commit)
                    click.echo(pcommit)

        return

    @staticmethod
    def get_rep_name(rep):
        """
        Gets the repository name
        """
        ctx.logger.log(15, 'Determining repo name')
        # Remove trailing slash from repository/directory name
        if rep[-1:] == '/':
            rep = rep[:-1]

        # Do some magic to not show the absolute path as repository name
        # Case 1: script was started in a directory that is a git repo
        if rep == os.path.abspath(os.getcwd()):
            (_, tail) = os.path.split(rep)
            if tail != '':
                repname = tail
        # Case 2: script was started in a directory with possible
        # subdirs that contain git repos
        elif rep.find(os.path.abspath(os.getcwd())) == 0:
            repname = rep[len(os.path.abspath(os.getcwd())) + 1:]
        # Case 3: script was started with -d and above cases do not apply
        else:
            repname = rep

        return repname

    # Check state of a git repository
    def check_repository(self, rep):
        """
        Checks repository
        """
        ctx.logger.log(15, 'Checking repo')
        branch = Gitcheckutils.get_default_branch(rep)
        if re.match(self.ignoreBranch, branch):
            return False

        changes = Gitcheckutils.get_local_files_change(rep)
        ischange = len(changes) > 0

        branch = Gitcheckutils.get_default_branch(rep)
        if branch != "":
            remotes = Gitcheckutils.get_remote_repositories(rep)
            topush = Gitcheckutils.get_to_push(ischange, remotes, rep, branch)
            topull = Gitcheckutils.get_to_pull(ischange, remotes, rep, branch)

        repname = Gitcheckutils.get_rep_name(rep)

        if len(changes) > 0:
            strlocal = "Local["
            len_files_chnaged = len(Gitcheckutils.get_local_files_change(rep))
            strlocal = strlocal + "To Commit:%s files" % (
                len_files_chnaged
            )
            strlocal += "]"
        else:
            strlocal = ""

        click.echo(
            "%s/%s %s%s%s" %
            (repname, branch, strlocal, topush, topull))

        if ischange > 0:
            filename = "  |--Local"
            for change in changes:
                filename = "     |--%s %s" % (
                    change[0],
                    change[1])
                click.echo(filename)
        if branch != "":
            remotes = Gitcheckutils.get_remote_repositories(rep)
            Gitcheckutils.display_reviews(remotes, rep, branch)

        if branch != "":
            remotes = Gitcheckutils.get_remote_repositories(rep)
            Gitcheckutils.display_pulls(remotes, rep, branch)

        return

    @staticmethod
    def get_local_files_change(rep):
        """
        Gets changed files
        """
        ctx.logger.lob(15, 'Determining changed files')
        files = []
        snbchange = re.compile(r'^(.{2}) (.*)')
        only_tracked_arg = ""
        result = Gitcheckutils.git_exec(rep, "status -s" + only_tracked_arg)
        lines = result.split('\n')
        for line in lines:
            member = snbchange.match(line)
            if member:
                files.append([member.group(1), member.group(2)])

        return files

    @staticmethod
    def has_remote_branch(rep, remote, branch):
        """
        checks for remote branch
        """
        ctx.logger.log(15, 'Checking for remote branch')
        result = Gitcheckutils.git_exec(rep, 'branch -r')
        return '%s/%s' % (remote, branch) in result

    @staticmethod
    def get_local_to_push(rep, remote, branch):
        """
        checks if local exists for push
        """
        ctx.logger.log(15, 'Checking for branch on local repo')
        if not Gitcheckutils.has_remote_branch(rep, remote, branch):
            return []
        result = Gitcheckutils.git_exec(rep, "log %(remote)s/%(branch)s..HEAD \
                          --oneline" % locals())

        return [x for x in result.split('\n') if x]

    @staticmethod
    def get_remote_to_pull(rep, remote, branch):
        """
        checks if remote exists for pull
        """
        ctx.logger.log(15, 'Checking for branch on remote repo')
        if not Gitcheckutils.has_remote_branch(rep, remote, branch):
            return []
        result = Gitcheckutils.git_exec(rep, "log HEAD..%(remote)s/%(branch)s \
                          --oneline" % locals())

        return [x for x in result.split('\n') if x]

    @staticmethod
    def get_default_branch(rep):
        """
        gets default branch
        """
        ctx.logger.log(15, 'Determining default branch')
        sbranch = re.compile(r'^\* (.*)', flags=re.MULTILINE)
        gitbranch = Gitcheckutils.git_exec(rep, "branch" % locals())

        branch = ""
        member = sbranch.search(gitbranch)
        if member:
            branch = member.group(1)

        return branch

    @staticmethod
    def get_remote_repositories(rep):
        """
        gets remote repo
        """
        ctx.logger.log(15, 'Determining remote repos')
        result = Gitcheckutils.git_exec(rep, "remote" % locals())

        remotes = [x for x in result.split('\n') if x]
        return remotes

    @staticmethod
    def git_exec(path, cmd):
        """
        executes git command
        """
        ctx.logger.log(15, 'Executing git command %s' % cmd)
        command_to_execute = "git %s" % (cmd)
        cmdargs = shlex.split(command_to_execute)
        prog = subprocess.Popen(cmdargs, stdout=PIPE, stderr=PIPE, cwd=path)
        output, errors = prog.communicate()
        if prog.returncode:
            ctx.logger.error('Failed running %s' % command_to_execute)
            raise Exception(errors)
        return output.decode('utf-8')

    # Check all git repositories
    def git_check(self, srch_dir):
        """
        Does git check
        """
        ctx.logger.log(15, 'Checking all git repos')
        repos = Gitcheckutils.search_repositories(srch_dir)

        for repo in repos:
            if "ccs-data" not in repo:
                self.check_repository(repo)
