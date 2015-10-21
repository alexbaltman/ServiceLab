#!/bin/bash

sudo rm -f /etc/yum.repos.d/epel*
cp /vagrant/provision/build_mirror.repo /etc/yum.repos.d/build_mirror.repo


sudo mkdir -p /root/.ssh/
sudo mkdir /etc/puppet


sudo chown -R cloud-user:cloud-user /etc/puppet


# SSH stuff
if [ -f /vagrant/id_rsa.pub ]; then
  cat /vagrant/id_rsa.pub >> /home/cloud-user/.ssh/authorized_keys
  sudo cat /vagrant/id_rsa.pub | sudo tee -a /root/.ssh/authorized_keys
fi


# Note: This could be dev or dev-tenant
# TODO: Create a switch here somehow --> prob in ruby
sudo echo "export CCS_ENVIRONMENT=dev-tenant" | sudo tee -a /root/.bashrc
echo "export CCS_ENVIRONMENT=dev-tenant" >> /home/cloud-user/.bashrc
echo "localhost ansible_connection=local" > /etc/ansible/hosts
sed -i 's/\s//g' /etc/puppet/puppet.conf
sed -r -i 's/search.*/search cis.local/g' /etc/resolv.conf


