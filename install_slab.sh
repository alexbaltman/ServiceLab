#!/bin/bash

export PATH=$PATH:/usr/local/bin
set -e

##################
# Helper functions
##################
rhel_prep(){
    # Make sure we have an epel repo
    #
    # Special hack for Cisco RHEL7 Vagrant Box
    if [ -f /etc/yum.repos.d/ccs-mirror.repo ];then
        fix_epel_config
    fi
    export http_proxy='proxy-wsa.esl.cisco.com:80'
    sudo yum makecache fast
    EPEL_REPO="$(yum repolist all | grep 'epel')"
    if [ -z "$EPEL_REPO" ];then
        echo "Installing EPEL repo"
        MAJ_VER=$(echo $VERSION_ID | cut -d. -f1)
        sudo yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-${MAJ_VER}.noarch.rpm
    fi
    # Ensure some stuff is installed for later commands to succeed
    echo "Installing a few prereqs"
    sudo yum -y --enablerepo=epel install python-devel python-pip gcc gnupg2
}

ubuntu_prep() {
    # Ensure some stuff is installed for later commands to succeed
    echo "Installing a few prereqs"
    sudo apt-get -y install python-dev python-pip build-essential
}

mac_prep(){
    type python || brew_install python
    type pip || brew_install pip
    type wget || brew_install wget
    type gpg || brew install gpg
}

install_homebrew(){
    # Attempt to install brew per http://brew.sh/
    echo "Installing homebrew"
    /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
}

brew_install(){
    # Make sure brew is installed, attempt to install it if not
    type brew || install_homebrew

    # brew it up
    echo "Installing $1"
    brew install $1
}

setup_venv(){
    sudo pip install virtualenv
    if [ ! -d ./venv ]; then
        echo "Setting up virtualenv venv"
        virtualenv venv
    fi
    source venv/bin/activate
    pip install -r requirements.txt
    pip install -e .
}

setup_rvm(){
    gpg --keyserver hkp://keys.gnupg.net --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3
    \curl -sSL https://get.rvm.io | bash -s stable
    if [ -f /etc/profile.d/rvm.sh ];then
        source /etc/profile.d/rvm.sh
    else
        source ~/.rvm/scripts/rvm
    fi
    rvm install 2.0
    gem install bundler
    bundle install
}

# Hopefully we'll be able to remove this soon ...
fix_epel_config(){
    sudo sed -i '/^\[epel\]/,$d' /etc/yum.repos.d/ccs-mirror.repo
    sudo su -c 'cat << EPEL >> /etc/yum.repos.d/ccs-mirror.repo
[epel]
name=epel
failovermethod=priority
#baseurl=http://download-i2.fedoraproject.org/pub/epel/7/x86_64/
mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=epel-7&arch=\$basearch
enabled=0
metadata_expire=7d
gpgcheck=0
EPEL'
}

###############
# Main Action
###############

# We attempt to support RHEL/CentOS, Ubuntu, and OS X
OS="$(uname)"

if [ "$OS" == "Linux" ]; then
    # Get more OS details
    if [ -f /etc/os-release ];then
        # Load the file and get relevant value
        . /etc/os-release
        OS=$ID
    else
        echo "Your Linux distribution is not RHEL/CentOS, or Ubuntu."
        exit 1
    fi
fi

echo "Detected OS is: $OS"

# Get to the point where we can 'pip install' in supported environments
case "$OS" in
    rhel)
        rhel_prep
        ;;
    centos)
        rhel_prep
        ;;
    ubuntu)
        ubuntu_prep
        ;;
    Darwin)
        mac_prep
        ;;
    *)
        echo "$OS is not supported by this setup script."
        exit 1
esac

# Install servicelab into a virtualenv sandbox
setup_venv

# Install supporting gems into an RVM sandbox
setup_rvm

# Probably good to go if we made it here
echo "You can now use servicelab by activating your venv with: source ./venv/bin/activate"
