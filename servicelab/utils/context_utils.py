#!/usr/bin/env python
from servicelab.stack import Context


def getArtifactoryURL():
    ctx = Context()
    return ctx.get_artifactory_info()["url"]
