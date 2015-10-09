
----------------------------------
Ansible playbook runtime commands
----------------------------------


To run Ansible, you need to run ansible on your playbook you created.  See below for specific commands and options available

ansible-playbook <filename.yml> ... [options]


filename.yml - The names of one or more YAML format files to run as ansible playbooks.

 

Options

Verbose mode, more output from successful actions will be shown. Give up to three times for more output.

-v, --verbose


The PATH to the inventory hosts file, which defaults to /etc/ansible/hosts.

-i PATH, --inventory=PATH


The DIRECTORY to load modules from. The default is /usr/share/ansible.

-M DIRECTORY, --module-path=DIRECTORY


Extra variables to inject into a playbook, in key=value key=value format.

-e VARS, --extra-vars=VARS


Level of parallelism. NUM is specified as an integer, the default is 5.

-f NUM, --forks=NUM


Prompt for the SSH password instead of assuming key-based authentication with ssh-agent.

-k, --ask-pass


Prompt for the password to use for playbook plays that request sudo access, if any.

-K, --ask-sudo-pass


Desired sudo user (default=root).

-U, SUDO_USER, --sudo-user=SUDO_USER


Connection timeout to use when trying to talk to hosts, in SECONDS.

-T SECONDS, --timeout=SECONDS


Force all plays to use sudo, even if not marked as such.

-s, --sudo


Use this remote user name on playbook steps that do not indicate a user name to run as.

-u USERNAME, --remote-user=USERNAME


Connection type to use. Possible options are paramiko (SSH), ssh, and local. local is mostly useful for crontab or kickstarts.

-c CONNECTION, --connection=CONNECTION


Further limits the selected host/group patterns.

-l SUBSET, --limit=SUBSET


 

Environment information

The following environment variables may specified.

ANSIBLE_HOSTS - Override the default ansible hosts file

ANSIBLE_LIBRARY - Override the default ansible module library path

 

Files

/etc/ansible/hosts - Default inventory file

/usr/share/ansible/ - Default module library

/etc/ansible/ansible.cfg - Config file, used if present

~/.ansible.cfg - User config file, overrides the default config if present

 
