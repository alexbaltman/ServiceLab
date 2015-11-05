#!/bin/bash
set -e

#setup vagrant if vagrant
echo "Running check.sh..."
OS=`cat /etc/redhat-release | awk {'print $1'}`
echo "OS value is ..... $OS"
if [ "$OS" == "Red" ]
then
sudo yum -y install wget
sudo yum -y install gettext
sudo yum -y install vagrant
sudo yum -y install java-1.7.0-openjdk
sudo yum -y install httpd-tools
sudo yum -y install procps
sudo htpasswd -cbs  /tmp/passwd slab badger
sudo yum -y install go-server-15.2.0
sudo yum -y install https://ccs-artifactory.cisco.com/artifactory/simple/servicelab/go-agent/go-agent/15.2.0/go-agent-15.2.0-2248.noarch.rpm
sudo cp cruise-config.xml /etc/go
sudo /etc/init.d/go-server restart
sudo /etc/init.d/go-agent restart
sudo cat /etc/go/cruise-config.xml
sleep 60
echo "Accessing Go : "
curl http://localhost:8153
curl 'http://localhost:8153/go/api/pipelines.xml'   -u 'slab:badger'
wget https://www.kernel.org/pub/software/scm/git/git-2.0.0.tar.gz
tar -xzvf git-2.0.0.tar.gz
sudo yum install -y libcurl-devel zlib-devel
sudo yum install -y autoconf
sudo yum install -y perl-ExtUtils-MakeMaker
cd git-2.0.0
sudo make configure
sudo ./configure --prefix=/usr
sudo make all
sudo make install
cd ..
git --version
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
