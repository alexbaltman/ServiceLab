#!/bin/bash

sudo yum install -y python-heighliner


sudo mkdir /etc/ansible
sudo mkdir /etc/puppet


sudo chown -R vagrant:vagrant /etc/ansible
sudo chown -R vagrant:vagrant /etc/puppet


cp /etc/hosts /var/lib/cobbler/cobbler_hosts_additional


echo "localhost ansible_connection=local" > /etc/ansible/hosts
echo "export CCS_ENVIRONMENT=dev" >> /root/.bashrc
echo "export CCS_ENVIRONMENT=dev" >> /home/vagrant/.bashrc

# SSH stuff
if [ ! -d /root/.ssh ]; then
  sudo mkdir /root/.ssh/
fi

if [ -f /vagrant/.stack/id_rsa ]; then
  sudo cp /vagrant/.stack/id_rsa /root/.ssh/
fi

if [ -f /vagrant/.stack/provision/ssh-config ]; then
  sudo cp /vagrant/.stack/provision/ssh-config /root/.ssh/config
fi

# Vault pass for decrypting keys
if [ -f /vagrant/.stack/.ccs.vaultpass.txt ]; then
  sudo cp /vagrant/.stack/.ccs.vaultpass.txt /etc/ansible/
else
  echo "changeme" > /etc/ansible/.ccs.vaultpass.txt
fi


sudo rm -f /etc/yum.repos.d/epel*
