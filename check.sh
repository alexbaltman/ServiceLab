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
sudo yum -y install java-1.7.0-openjdk
sudo yum -y install git
sudo yum -y install httpd-tools
wget http://download.go.cd/gocd-rpm/go-server-15.2.0-2248.noarch.rpm
wget http://dl.bintray.com/gocd/gocd-rpm/go-agent-15.2.0-2248.noarch.rpm
sudo yum -y install procps
sudo htpasswd -cbs  /tmp/passwd slab badger
sudo yum -y localinstall go-server-15.2.0-2248.noarch.rpm
sudo yum -y localinstall go-agent-15.2.0-2248.noarch.rpm
sudo cp cruise-config.xml /etc/go
sudo /etc/init.d/go-server restart
sudo /etc/init.d/go-agent restart
sudo cat /etc/go/cruise-config.xml
sleep 60
echo "Accessing Go : "
curl http://localhost:8153
curl 'http://localhost:8153/go/api/pipelines.xml'   -u 'slab:badger'
fi

if [[ "$OSTYPE" == "darwin"* ]]
then
cd osx
./checkosx.sh
cd ..
fi

sudo pip install -r requirements.txt
sudo pip install -r test-requirements.txt
sudo pip install -e .

pep8 --max-line=93 servicelab/stack.py
pep8 --max-line=93 servicelab/commands/*.py
pep8 --max-line=93 servicelab/utils/*.py
pep8 --max-line=93 tests/*.py

stack workon ccs-data
python -m unittest discover .
