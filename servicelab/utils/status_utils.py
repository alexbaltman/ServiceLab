"""
Utility functions for status command
"""
import os

import click

from servicelab.utils.gitcheck_utils import Gitcheckutils

SERVICE_DIR = "services"
VM_NAME = "infra001"


def show_repo_status(path):
    """
    Shows the details of git repos.
    """
    click.echo('Showing repo status of services')
    service_dir = os.path.join(path, SERVICE_DIR)
    Gitcheckutils().git_check(service_dir)
