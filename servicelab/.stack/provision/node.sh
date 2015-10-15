#!/bin/bash

sudo rm -f /etc/yum.repos.d/epel*
cp /vagrant/provision/build_mirror.repo /etc/yum.repos.d/build_mirror.repo

sudo mkdir /root/.ssh/
sudo mkdir /etc/puppet
sudo mkdir /var/lib/cobbler


sudo chown -R vagrant:vagrant /etc/puppet
sudo chmod -R 777 /var/lib/cobbler


cp /etc/hosts /var/lib/cobbler/cobbler_hosts_additional


# SSH stuff
if [ -f /vagrant/id_rsa.pub ]; then
  cat /vagrant/id_rsa.pub >> /home/vagrant/.ssh/authorized_keys
  cat /vagrant/id_rsa.pub >> /root/.ssh/authorized_keys
fi


# Note: This could be dev or dev-tenant
# TODO: Create a switch here somehow --> prob in ruby
echo "export CCS_ENVIRONMENT=dev-tenant" >> /root/.bashrc
echo "export CCS_ENVIRONMENT=dev-tenant" >> /home/vagrant/.bashrc
echo "localhost ansible_connection=local" > /etc/ansible/hosts
sed -i 's/\s//g' /etc/puppet/puppet.conf
sed -r -i 's/search.*/search cis.local/g' /etc/resolv.conf


