#!/bin/bash
sudo rm -f /etc/yum.repos.d/epel*

sudo mkdir -p /etc/ansible
sudo mkdir -p /var/lib/cobbler
sudo mkdir -p /etc/puppet/data/hiera_data
sudo mkdir -p /etc/ccs/data/environments/dev-tenant
sudo mkdir -p /usr/share/ansible_plugins/lookup_plugins


sudo chown cloud-user:cloud-user /etc/hosts
sudo chown -R cloud-user:cloud-user /etc/ccs/
sudo chown -R cloud-user:cloud-user /usr/share/
sudo chown -R cloud-user:cloud-user /etc/puppet
sudo chown -R cloud-user:cloud-user /etc/ansible
sudo chown -R cloud-user:cloud-user /var/lib/cobbler
sudo chown -R cloud-user:cloud-user /etc/yum.repos.d


cp /vagrant/provision/nimbus.py /etc/ansible/nimbus.py
cp /vagrant/provision/hiera.yaml /etc/puppet/hiera.yaml
cp /etc/hosts /var/lib/cobbler/cobbler_hosts_additional
cp /vagrant/provision/ansible.cfg /etc/ansible/ansible.cfg
cp /vagrant/provision/build_mirror.repo /etc/yum.repos.d/build_mirror.repo
cp /vagrant/provision/hiera.py /usr/share/ansible_plugins/lookup_plugins/hiera.py
cp /opt/ccs/services/ccs-data/out/ccs-dev-1/dev-tenant/etc/ccs/data/hosts /etc/hosts
cp /opt/ccs/services/ccs-data/out/ccs-dev-1/dev-tenant/etc/ccs/data/site.yaml /etc/puppet/data/hiera_data/site.yaml
cp /opt/ccs/services/ccs-data/out/ccs-dev-1/dev-tenant/etc/ccs/data/site.yaml /etc/ccs/data/environments/dev-tenant/site.yaml
cp /opt/ccs/services/ccs-data/out/ccs-dev-1/dev-tenant/etc/ccs/data/hosts.yaml /etc/ccs/data/environments/dev-tenant/hosts.yaml

cp /vagrant/provision/hydsslg2.crt /etc/pki/ca-trust/source/anchors
sudo update-ca-trust


sudo yum install -y python-heighliner


chmod +x /etc/ansible/nimbus.py
chmod +x /usr/share/ansible_plugins/lookup_plugins/hiera.py


echo "localhost ansible_connection=local" > /etc/ansible/hosts
echo "export CCS_ENVIRONMENT=dev-tenant" >> /home/cloud-user/.bashrc
echo "export CCS_ENVIRONMENT=dev-tenant" | sudo tee -a /root/.bashrc
sudo echo "Defaults env_keep += \"CCS_ENVIRONMENT\"" | sudo tee -a /etc/sudoers


# SSH stuff
if [ ! -d /root/.ssh ]; then
  sudo mkdir /root/.ssh/
fi

if [ -f /vagrant/id_rsa ]; then
  sudo cp /vagrant/id_rsa /root/.ssh/
  sudo chmod 0600 /root/.ssh/id_rsa
fi

if [ -f /vagrant/provision/ssh-config ]; then
  sudo cp /vagrant/provision/ssh-config /root/.ssh/config
fi

# Vault pass for decrypting keys
if [ -f /vagrant/.ccs.vaultpass.txt ]; then
  sudo cp /vagrant/.ccs.vaultpass.txt /etc/ansible/
else
  echo "changeme" > /etc/ansible/.ccs.vaultpass.txt
fi
