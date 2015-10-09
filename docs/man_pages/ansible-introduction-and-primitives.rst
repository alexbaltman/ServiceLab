
------------------------------------
Ansible introduction and primitives
------------------------------------


Ansible is a configuration management and provisioning tool, similar to Chef, Puppet or Salt.  It is found to be one of the simplest and the easiest to get started with. A lot of this is because it's "just SSH"; It uses SSH to connect to servers and run the configured Tasks.

One nice thing about Ansible is that it's very easy to convert bash scripts (still a popular way to accomplish configuration management) into Ansible Tasks. Since it's primarily SSH based, it's not hard to see why this might be the case - Ansible ends up running the same commands.

We could just script our own provisioners, but Ansible is much cleaner because it automates the process of getting context before running Tasks. With this context, Ansible is able to handle most edge cases - the kind we usually take care of with longer and increasingly complex scripts.

 

Core Ansible Concepts:

Idempotency:

Ansible Tasks are idempotent. Without a lot of extra coding, bash scripts are usually not safely run again and again. Ansible uses "Facts", which is system and environment information it gathers ("context") before running Tasks.

Facts:

Ansible uses these facts to check state and see if it needs to change anything in order to get the desired outcome. This makes it safe to run Ansible Tasks against a server over and over again.  Before running any Tasks, Ansible will gather information about the system it's provisioning. These are called Facts, and include a wide array of system information such as the number of CPU cores, available ipv4 and ipv6 networks, mounted disks, Linux distribution and more.  Facts are often useful in Tasks or Template configurations.

Inventory:

Ansible has a default inventory file used to define which servers it will be managing. Ansible works against multiple systems in your infrastructure at the same time. It does this by selecting portions of systems listed in Ansible’s inventory file, which defaults to being saved in the location /etc/ansible/hosts.  Not only is this inventory configurable, but you can also use multiple inventory files at the same time (explained below) and also pull inventory from dynamic or cloud sources.

Modules:

Ansible uses "modules" to accomplish most of its Tasks. Modules can do things like install software, copy files, use templates and much more.  Modules are the way to use Ansible, as they can use available context ("Facts") in order to determine what actions, if any need to be done to accomplish a Task.  Ansible ships with a number of modules (called the ‘module library’) that can be executed directly on remote hosts or through Playbooks.  Users can also write their own modules. These modules can control system resources, like services, packages, or files (anything really), or handle executing system commands.

Playbooks & Tasks:

Playbooks can run multiple Tasks and provide some more advanced functionality that we would miss out on using ad-hoc commands.  Playbooks and Roles in Ansible all use Yaml.  We can use Playbooks to run multiple Tasks, add in variables, define other settings and even include other playbooks. Playbooks are Ansible’s configuration, deployment, and orchestration language. They can describe a policy you want your remote systems to enforce, or a set of steps in a general IT process.

If Ansible modules are the tools in your workshop, playbooks are your design plans.  At a basic level, playbooks can be used to manage configurations of and deployments to remote machines. At a more advanced level, they can sequence multi-tier rollouts involving rolling updates, and can delegate actions to other hosts, interacting with monitoring servers and load balancers along the way.  Playbooks are designed to be human-readable and are developed in a basic text language. There are multiple ways to organize playbooks and the files they include, and we’ll offer up some suggestions on that and making the most out of Ansible.

Handlers:

A Handler is exactly the same as a Task (it can do anything a Task can), but it will run when called by another Task. You can think of it as part of an Event system; A Handler will take an action when called by an event it listens for.

This is useful for "secondary" actions that might be required after running a Task, such as starting a new service after installation or reloading a service after a configuration change.

Roles:

Roles are good for organizing multiple, related Tasks and encapsulating data needed to accomplish those Tasks. For example, installing Nginx may involve adding a package repository, installing the package and setting up configuration. We've seen installation in action in a Playbook, but once we start configuring our installations, the Playbooks tend to get a little more busy.

The configuration portion often requires extra data such as variables, files, dynamic templates and more. These tools can be used with Playbooks, but we can do better immediately by organizing related Tasks and data into one coherent structure: a Role.

Templates:

Template files can contain template variables, based on Python's Jinja2 template engine. Files in here should end in .j2, but can otherwise have any name. Similar to files, we won't find a main.yml file within the templates directory.

Six additional variables can be used in templates: ansible_managed (configurable via the defaults section of ansible.cfg) contains a string which can be used to describe the template name, host, modification time of the template file and the owner uid, template_host contains the node name of the template’s machine, template_uid the owner, template_path the absolute path of the template, template_fullpath is the absolute path of the template, and template_run_date is the date that the template was rendered. Note that including a string that uses a date in the template will result in the template being marked ‘changed’ each time.

Vault:

We often need to store sensitive data in our Ansible templates, Files or Variable files; It unfortunately cannot always be avoided. Ansible has a solution for this called Ansible Vault.  Vault allows you to encrypt any Yaml file, which typically boil down to our Variable files. Vault will not encrypt Files and Templates.  When creating an encrypted file, you'll be asked a password which you must use to edit the file later and when calling the Roles or Playbooks.

 
