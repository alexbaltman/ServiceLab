#!/usr/bin/env python

import time
import copy
import sys
import uuid
import requests
import argparse
import os
import requests
import xml.etree.ElementTree as ET


def _get_config(configXMLURL, auth=None):
    print "Retrieving go config"
    if auth:
        r = requests.get(configXMLURL, auth=auth)
    else:
        r = requests.get(configXMLURL)
    if r.status_code == 200:
        try:
            root = ET.fromstring(r.text)
        except:
            print "Failure parsing xml from request"
            sys.exit(1)
    else:
        print "Request failed"
        sys.exit(1)

    return (r.headers['x-cruise-config-md5'], root)


def _push_config(configXMLURL, md5, xmlfile, auth=None):
    print "Uploading go config"
    payload = {
        'md5': md5,
        'xmlFile': xmlfile
    }

    if auth:
        p = requests.post(configXMLURL,
                          auth=auth, data=payload)
    else:
        p = requests.post(configXMLURL, data=payload)
    if p.status_code != 200:
        print p.status_code, p.text
        sys.exit(1)
    time.sleep(1)


def _create_pipeline(root, name, new_name):
    """Creates a pipeline.

    Args:
        name (str): Name of existing name
        new_name(str): Name of the new pipeline

    Returns:
    Example Usage:
        >>> print _create_pipeline(root,
        name, new_name)
    """
    pipeline = root.find('.//pipeline[@name="%s"]' % name)
    pipeline_parent = root.find('.//pipeline[@name="%s"]/..' % name)

    new_pipeline = root.find('.//pipeline[@name="%s"]' % new_name)
    if new_pipeline is not None:
        print "The pipeline name : %s provided already exists. Please \
                  provide a different pipeline name. " % new_name
        sys.exit(1)

    if pipeline is None:
        print "The original pipeline does not exist: %s" % name
        sys.exit(1)

    new_pipeline = copy.deepcopy(pipeline)
    print "Setting pipeline name: %s" % new_name
    new_pipeline.set('name', new_name)
    pipeline_parent.append(new_pipeline)

    return root
