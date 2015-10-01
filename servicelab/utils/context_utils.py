#!/usr/bin/env python
from servicelab.stack import Context

"""
 context_utils : Wrapper utilities for Context
"""


def get_artifactory_url():
    ctx = Context()
    return ctx.get_artifactory_info()["url"]


def get_gocd_ip():
    ctx = Context()
    return ctx.get_gocd_info()["ip"]


def get_jenkins_url():
    ctx = Context()
    return ctx.get_jenkins_info()["url"]
