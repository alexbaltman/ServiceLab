Commands
========

create
------

**repo**

   1. Takes argument name
   2. Initializes a git repository in ccs-gerrit.cisco.com
   3. Makes first commit
   4. Sets up the directory structure depending your configuration
   5. Sets up initial template of the .nimbus.yml and prints information

**host**

   Creates a host.yaml file in an environment so that a VM can then be booted

**site**

   Creates a whole site in ccs-data

**env**

   Creates a new environment in a site in ccs-data

**vip**

   Creates a new VIP in a site in ccs-data in order to integrate your service with haproxy to that particular site.

ex::

   >>> stack create site rtp42-svc-test

destroy
-------

**vm**

   Destroys VMs

**repo**

   Destroys a repo in Gerrit.

**artifact**

   Destroys artifact in Artifactory.

ex::

   >>> stack destroy repo service-test


enc
---

Encrypts a value to be put into ccs-data.


ex::

   >>> stack enc


find
----
Helps you search for resources in the SDLC pipeline.

**repo**

   Searches through Gerrit's API for a repo using your search term.

**review**

   Searches through Gerrit's API for a repo using your search term.

**build**

   Searches through Jenkins API for pipelines using your search term.

**artifact**

   Searches through Artifactory's API for artifacts using your search term.

**pipe**

   Searches through GO's API for pipelines using your search term.

ex::

   >>> stack find repo service


list
----
Listing sites and services of ccs-data

**sites**

   Here we list all the sites using the git submodule ccs-data.

**envs**

   Here we list all the environments using the git submodule ccs-data.

**hosts**

   Here we list all the hosts usings the git submodule ccs-data.

**artifacts**

   Lists artifacts using Artifactory's API.

ex::

   >>> stack list sites

nuclear
-------
Cleans everything.


review
------
Helps you work with Gerrit.

**inc**

   Searches through Gerrit's API for incoming review for your username.

**out**

   Searches through Gerrit's API for outgoing reviews.

**plustwo**

   Approves and merges a gerrit change set.

**plusone**

   Approves, but does not merge a gerrit change set, which means change set
   requires another approver.

ex::

   >>> stack review


show
-----
Helps you show the details of resources in the SDLC pipeline.


**repo**

   Shows the details of git repos using Gerrit's API.


**review**

   Shows the details of a review using Gerrit's API.


**build**

   Shows the details of a build in Jenkins.


**artifact**

   Shows the details of an artifact.


**pipe**

   Shows the details of a deployment pipelien using GO's API.

ex::

   >>> stack show repo


status
------

Shows the status of your working servicelab environment.

ex::

   >>> stack status


up
--
Boots the Vagrant VMs

Options:

   ``--ha, is_flag=True, default=False`` : Enables HA for core OpenStack components by booting the necessary extra VMs.

   ``--full`` : Boot complete openstack stack without ha, unless --ha flag is set.

   ``--osp-ai`` : Boot a full CCS implementation of the OpenStack Platform on one VM. Note: This is not the same as the AIO node deployed in the service cloud.'

   ``-i, --interactive,`` : Walk through booting VMs.

   ``-b, --branch`` : Choose a branch to run against or ccs-data.

   ``--rhel7`` : Boot a rhel7 vm.

   ``--target, -t``, Pick an osp target to boot.

   ``-u, --username`` : Enter the password for the username.

Example::

   >>> stack up --full

validate
--------
Validates a yaml file's syntax.


ex::

   >>> stack validate test.yml


workon
------
Calls a service that you would like to work on. Inits the repo, links it, creates vagrant, and sets it in /.stack.

If it doesn't work, change the username = getpass.getuser()

Use a userid that matches your CEC

Options:
   ``-i, --interactive``: Walk through booting VMs

   ``-b, --branch``, default=``master``:  Choose a branch to run against for your service.

   ``-u, --username``:  Enter the password for the username

Args:
   param1 (str): service_name


ex::

   >>> stack workon service-redhouse-tenant
