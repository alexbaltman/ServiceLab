
-------------------
SDLC Setup Process
-------------------


This document outlines the steps to deploy various servers using the SDLC setup process.

The setup process will deploy the following servers:

Git/Gerrit, Jenkins and Apt repo servers

GO CD server

Before starting, it may be helping to read about the System and Software Lifecycle to get an idea of how Git/Gerrit fit into the software development cycle.

ssh to alln01-1-csx-infra-001 using CEC / softoken.

Clone the sandbox and load the ssl environment configuration.

git clone ssh://cis-gerrit.cisco.com:29418/cis-sandbox
cd cis-sandbox
fab load:cis-ssl]]>

Deploy to Production:

fab on:infra-dfw update # Install latest config deb package
fab on:infra-dfw noop # Run puppet noop to see expected changes
fab on:infra-dfw apply # Run puppet apply]]>

Nodes:

These two servers, GO CD and Artifactory, are deployed with the stratosphere-toolchain software.

First, download stratosphere-toolchain software

git clone ssh://your_cec@cis-gerrit.cisco.com:29418/stratosphere-toolchain]]>

 

Now install the required packages for the stratosphere-toolchain.

(cd into stratosphere-toolchain directory)
sudo pip install -r requirements.pip]]>

 

Get the Ansible vault password from greyboard.cisco.com under "Nimbus SDLC Admin'  (see this greyboard-tellme page for more information).

echo &#39;password&#39; &gt; .vaultpass.txt]]>

 

Ensure your SSH public key (e.g. id_rsa.pub) is in this file 'roles/common/vars/users_data.yml'.

 

Finally, we can deploy the GO CD and Artifactory servers into the 'rack1 production' environment, for example.

ansible-playbook -i inventory/rack1/production  plays/site.yml  --tags gocd-server
ansible-playbook -i inventory/rack1/production  plays/site.yml  --tags artifactory]]>

 

Or we can deploy all servers (cobbler, gocd, mirror, sa, ...) into the environment.

ansible-playbook -i inventory/rack1/production  plays/site.yml
]]>







