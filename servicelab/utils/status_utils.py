"""
Utility functions for status command.
"""
import os
from subprocess import CalledProcessError

import click

from servicelab.utils.gitcheck_utils import Gitcheckutils
from servicelab.utils import vagrant_utils

SERVICE_DIR = "services"
VM_NAME = "infra001"


def show_repo_status(path):
    """
    Shows the details of git repos.
    """
    click.echo('\nShowing repo status of services')
    service_dir = os.path.join(path, SERVICE_DIR)
    Gitcheckutils().git_check(service_dir)


def show_vm_status(path):
    """
    Shows the details of git repos.
    """
    click.echo('\nShowing vm status of services')
    vm_connection = vagrant_utils.Connect_to_vagrant(vm_name=VM_NAME,
                                                     path=path)
    try:
        statuses = vm_connection.v.status()
        for status in statuses:
            click.echo("VM name : {}   VM status : {} ".
                       format(status[0], status[1]))
    except CalledProcessError:
        return 2, False

    return 1, True