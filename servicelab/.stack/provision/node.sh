#!/bin/bash

sudo mkdir /root/.ssh/

if [ -f /vagrant/.stack/id_rsa.pub ]; then
  cat /vagrant/.stack/id_rsa.pub >> /home/vagrant/.ssh/authorized_keys
  cat /vagrant/.stack/id_rsa.pub >> /root/.ssh/authorized_keys
fi
