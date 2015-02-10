#!/bin/bash

if [ -f /vagrant/.stack/id_rsa.pub ]; then
  cat /vagrant/.stack/id_rsa.pub >> /home/vagrant/.ssh/authorized_keys
fi
