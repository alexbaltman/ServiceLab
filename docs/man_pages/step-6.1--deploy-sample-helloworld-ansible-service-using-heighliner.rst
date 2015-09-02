
----------------------------------
Step 6.1  Deploy sample helloworld
----------------------------------


Purpose:

This write-up of sample helloworld-ansible is to serve as an example on how to create code to deploy a service using Ansible and heighliner.

Here are the basic steps to prepare your service deployment package:

The descriptions below outline the details of these service deployment steps.

Development Environment:

This helloworld-ansible sample has been created and tested on the computing environment as outlined in table below.   Other environments or variations are not addressed here, due to the possible numerous combinations and the resulting complications.

Vagrant v1.6.3

VirtualBox 4.3.20 for OS X hosts

Virtual environment tool - link to Installing Vagrant

Hypervisor - link to Download VirtualBox

RHEL7 VM is instantiated by Vagrant,using Vagrant box from http://cis-kickstart.cisco.com/ccs-rhel-7.box

Two VMs are created and used as follows:

Get sample skeleton code:

Instructions to setup SDLC Git and Gerrit can be found in this Confluence link.

git clone ssh://your_cec@cis-gerrit.cisco.com:29418/helloworld-ansible
]]>

Prerequisite:

For example:

[helloworld-servers]
ansible2
]]>

How to deploy helloworld-ansible service:

*NOTE: Some of these manual steps may not be performed, given that the deployment is automated. However they may be helpful for the purpose of understanding and testing.

First verify `heighliner` is already installed.

$ whereis heighliner
heighliner: /usr/bin/heighliner
]]>

Change directory to where `helloworld-ansible` service is installed and perform a heighliner check. Heighliner uses the `.nimbus.yml` file in this directory for running check.

$ cd  /opt/ccs/services/helloworld-ansible
$ heighliner check
Running check
check passed
]]>

The `helloworld-ansible` directory should look like this:

├── ansible
│   ├── helloworld.yml
│   └── roles
│       └── helloworld-test
│           ├── files
│           │   └── append-helloworld.sh
│           └── tasks
│               └── main.yml
├── doc
│   └── README.md
└── .nimbus.yml
]]>

Now let's deploy the `helloworld-ansible` service:

[vagrant@ansible1 ~]$ cd helloworld-ansible
[vagrant@ansible1 helloworld-ansible]$ heighliner deploy
Running deploy

PLAY [helloworld-servers] *************************************************************

GATHERING FACTS ***************************************************************
ok: [ansible2]

TASK: [helloworld-test | Install bash program] ********************************
ok: [ansible2]

TASK: [helloworld-test | Create hello_world file] *****************************
changed: [ansible2]

PLAY RECAP ********************************************************************
ansible2                   : ok=3    changed=1    unreachable=0    failed=0
]]>

The above Ansible task `Install bash program` is harmless since bash is already installed, and thus no install is performed. It is intended to test yum package manager.

You will now find the new file created by this deployment in your target servers.

vagrant@ansible2:~$ cat /tmp/helloworld.txt
Hello world from CCS (Created by Ansible on [Wed Dec 17 19:17:45 UTC 2014])
]]>

How setup your deployment package:

`heighliner deploy` reads the `.nimbus.yml` file to determine the Ansible playbook to run subsequently. In our example, it is the `helloworld.yml` playbook.

$ cat .nimbus.yml
service: helloworld-ansible
version: 0.1.0
check:
script: echo &quot;check passed&quot;
build: _
deploy:
type: ansible
playbook: &#39;helloworld.yml&#39;
script: &#39;ansible-playbook ./ansible/helloworld.yml&#39;


$ cat ./ansible/helloworld.yml
---
- hosts: helloworld-servers

remote_user: root

roles:
- helloworld-test
]]>

In summary, examining and executing the sample helloworld-ansible code, together with this description, would help to enhance your understanding in deploying your cloud service.







