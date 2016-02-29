#!/usr/bin/env python

"""
Build a yaml file in servicelab/services/.stack/cache to improve the speed of the
'stack list flavors' command
"""
import os
import yaml

import ccsdata_utils
from servicelab.stack import Context

ctx = Context()
yaml_data = {}
sites_path = os.path.join(ctx.path, 'services', 'ccs-data', 'sites')
for site in os.listdir(sites_path):
    site_env_path = os.path.join(ctx.path, 'services', 'ccs-data', 'sites', site,
                                 'environments')
    if os.path.exists(site_env_path):
        yaml_data[site] = ccsdata_utils.get_flavors_from_site(site_env_path)

my_file = os.path.join(ctx.path, 'cache', 'all_sites_flavors.yaml')
with open(my_file, 'w') as output_file:
    output_file.write(yaml.dump(yaml_data, default_flow_style=False))
