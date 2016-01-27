#!/bin/sh
OS=`cat /etc/redhat-release | awk {'print $1'}`
echo "OS value is ..... $OS"
if [ "$OS" == "Red" ] ||  [ "$OS" == "CentOS" ]
then
export http_proxy='proxy-wsa.esl.cisco.com:80'
gpg2 --keyserver hkp://keys.gnupg.net:80 --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3
sudo yum -y install python-devel
curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
sudo python get-pip.py
sudo yum -y install gcc
sudo yum -y install clang
fi
if [[ "$OSTYPE" == "darwin"* ]]
then
brew install wget
fi
sudo pip install virtualenv
virtualenv venv
source venv/bin/activate
sudo pip install -r requirements.txt
sudo pip install -e .
curl -L get.rvm.io | bash -s stable
curl -sSL https://get.rvm.io | bash -s stable --ruby
source ~/.profile
rvm install 1.9.3 --with-gcc=clang
sudo yum -y install rubygems
gem install bundler
bundle install
ruby -v
