#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from ansible import errors
import subprocess
import os

class LookupModule(object):

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir

    def run(self, terms, inject=None, **kwargs):

        hiera_bin = '/usr/bin/hiera'
        hiera_conf = '/etc/puppet/hiera.yaml'
        facts = {'environment': 'production'}

        ret = []

        # this can happen if the variable contains a string, strictly not desired for lookup
        # plugins, but users may try it, so make it work.
        if not isinstance(terms, list):
            terms = [ terms ]

        # verify there is a hiera file to read from
        if not os.path.isfile(hiera_conf):
            raise errors.AnsibleError('%s does not exist' % hiera_conf)

        for term in terms:
            cmd = [hiera_bin, '--config', hiera_conf, term]
            cmd.extend(map(lambda *env_var: '='.join(*env_var), facts.iteritems()))

            with open(os.devnull, 'w') as devnull:
                output = subprocess.check_output(cmd, stderr=devnull)

            values = output.strip().split("\n")

            for value in values:
                ret.append(value)

        return ret
