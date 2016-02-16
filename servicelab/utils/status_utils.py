"""
Utility functions for status command.
"""
import os
import click

from subprocess import CalledProcessError
from servicelab.utils.gitcheck_utils import Gitcheckutils
from servicelab import settings

import vagrant_utils
import logger_utils

slab_logger = logger_utils.setup_logger(settings.verbosity, 'stack.utils.status')
SERVICE_DIR = "services"
VM_NAME = "infra001"


def show_repo_status(path):
    """
    Shows the details of git repos.
    """
    slab_logger.log(15, 'Extracting git repos details')
    service_dir = os.path.join(path, SERVICE_DIR)

    if os.path.isdir(service_dir) is True and os.walk(service_dir).next()[1]:
        click.echo('\nShowing git repo status of services :')
        Gitcheckutils().git_check(service_dir)
    else:
        slab_logger.error("Cannot show repository status "
                         "since no projects found in directory : %s \n"
                         % (service_dir))


def show_vm_status(path):
    """
    Shows the status of vms.
    """
    slab_logger.log(15, 'Extracting vm statuses')
    click.echo('\nShowing vm status of services :')
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
