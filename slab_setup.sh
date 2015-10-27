#!/bin/sh
OS=`cat /etc/redhat-release | awk {'print $1'}`
echo "OS value is ..... $OS"
if [ "$OS" == "Red" ]
then
sudo yum -y install python-devel
curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
sudo python get-pip.py
sudo pip install virtualenv
sudo yum -y install gcc  ruby-devel rubygems
fi
if [[ "$OSTYPE" == "darwin"* ]]
then
sudo pip install virtualenv
fi
virtualenv venv
source venv/bin/activate
sudo pip install -r requirements.txt
gpg2 --keyserver hkp://keys.gnupg.net --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3
curl -L get.rvm.io | bash -s stable
curl -sSL https://get.rvm.io | bash -s stable --ruby
gem install bundler
bundle install