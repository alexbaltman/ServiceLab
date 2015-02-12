#!/bin/bash

sudo yum install -y python-heighliner

sudo chown -R vagrant:vagrant /etc/ansible

if [ ! -d /root/.ssh ]; then
  sudo mkdir /root/.ssh/
fi

if [ -f /vagrant/.stack/id_rsa ]; then
  sudo cp /vagrant/.stack/id_rsa /root/.ssh/
fi

if [ -f /vagrant/.stack/ssh-config ]; then
  sudo cp /vagrant/.stack/ssh-config /root/.ssh/config
fi

if [ -f /vagrant/.stack/.ccs.vaultpass.txt ]; then
  sudo cp /vagrant/.stack/.ccs.vaultpass.txt /etc/ansible/
fi
