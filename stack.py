#!/usr/bin/env python

import click
import os
import sys
import logging
import glob

# TODO: "This is a stub so we can grep out all TODO items in the code
# RFI:  "This is a stub where we need to make a coordinated decision about something. Request for input/information.
# --> no stub regular comment. More of the why less of the what or how.


# Load Plugins
# RFI: Do we want logger and debug/vvv stuff separate? we could log when plugindir doesn't exit
plugin_folder = os.path.join(os.path.dirname(__file__), 'commands')


class DaCLI(click.MultiCommand):

    def list_cmds(self):
        cmds = []
        for filename in os.listdir(plugin_folder):
            if filename.endswith('.py'):
                cmds.append(filename[:-3])
        cmds.sort()
        return cmds

    def get_cmds(self, name):
        ns = {}
        fn = os.path.join(plugin_folder, name + '.py')
        with open(fn) as f:
            code = compile(f.read(), fn, 'exec')
            eval(code, ns, ns)
        return ns['cli']

stack = DaCLI(help='blah')

if __name__ == '__main__':
    stack()
