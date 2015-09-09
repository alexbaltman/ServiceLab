#!/usr/bin/env python

import requests
from jenkinsapi.jenkins import Jenkins


def get_server_instance(jenkins_server, jenkinsuser, jenkinspass):
    requests.packages.urllib3.disable_warnings()
    server = Jenkins(jenkins_server, username=jenkinsuser,
                     password=jenkinspass)
    return server
