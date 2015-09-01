#!/bin/bash
vagrant  up
vagrant ssh << EOF
sudo yum update -y
wget ftp://rpmfind.net/linux/centos/6.7/os/x86_64/Packages/libxml2-2.7.6-20.el6.x86_64.rpm
sudo rpm --oldpackage -Uvh  libxml2-2.7.6-20.el6.x86_64.rpm
EOF
vagrant reload
