#!/bin/bash
set -e

#setup vagrant if vagrant
echo "Running check.sh..."
OS=`cat /etc/redhat-release | awk {'print $1'}`
echo "OS value is ..... $OS"
if [ "$OS" == "Red" ]
then
sudo yum -y install wget
wget https://dl.bintray.com/mitchellh/vagrant/vagrant_1.7.2_x86_64.rpm -O vagrant_1.7.2_x86_64.rpm
sudo yum -y localinstall vagrant_1.7.2_x86_64.rpm
fi

sudo pip install -r requirements.txt
sudo pip install -r test-requirements.txt

pep8 --max-line=93 servicelab/stack.py
pep8 --max-line=93 servicelab/commands/*.py
pep8 --max-line=93 servicelab/utils/*.py
pep8 --max-line=93 tests/*.py
python -m unittest discover .
