#!/bin/bash

UNAME=$USER
PIP_TYPE=''
WD=$(pwd)
ENABLE_HA=0
PROFILE='dev'

_usage() {
  echo "Usage: $0 [options] <command>"
  echo "Commands:"
  echo -e "\tprep               Download required resources"
  echo -e "\tupdate             Update all repos"
  echo -e "\tgit-status         Perform a git status of downloaded repos"
  echo -e "\tup [target]        Start all nodes required for [target]"
  echo -e "\tdown [target]      Destroy all nodes required for [target]"
  echo -e "\tstatus             Status of current environment"
  echo -e "\thelp               This help screen"
  echo "Options"
  echo -e "\t--ha               Boot all nodes in cluster (default: false)"
  echo -e "\t--user [username]  Username to clone as"
  echo "Targets"
  echo -e "\tall"
  echo -e "\taio                All-in-one nodes"
  echo -e "\tcompute"
}

_print_title() {
  msg=$1
  echo
  echo "#####################################"
  echo "# ${msg}"
  echo "#####################################"
}

_link_children() {
  echo
}

_get_branch() {
  local repo_key=$1
  local branch='master'
  if [ -f settings.yaml ] && grep -q 'ccs-data: ' settings.yaml; then
    branch=$(grep 'ccs-data: ' settings.yaml | cut -d ' ' -f2)
  elif grep -q 'ccs-data: ' .default_settings.yaml; then
    branch=$(grep 'ccs-data: ' .default_settings.yaml | cut -d ' ' -f2)
  fi
  echo $branch
}

_prep() {
  local ccs_data_branch=$(_get_branch ccs-data)
  gem list | grep -q 'librarian-puppet-simple' || { echo "Please 'bundle install' before prepping"; exit 1; }
  if [ ! -d "dev/ccs-data/.git" ]; then
    git clone -b $ccs_data_branch ssh://$UNAME@cis-gerrit.cisco.com:29418/ccs-data dev/ccs-data
  else
    cd dev/ccs-data; git pull --ff-only origin $ccs_data_branch; cd $WD
  fi
  echo "Generating BOM for ccs-dev-1/dev"
  cd dev/ccs-data && bundle install && ./lightfuse.rb -d msg -s ccs-dev-1 -c hiera-bom-unenc.yaml || { echo "Error with installing and running ccs-data BOM"; exit 1; }
  cd $WD

  cd puppet
  librarian-puppet install --verbose
  cd modules && ls | while read line; do
    cd $line
    if ! git branch | grep '*' | grep -q '('; then
      git pull origin $(git branch | grep '*' | awk '{ print $2 }')
    fi
    cd ..
  done
  cd $WD
}

_update() {
  local ccs_data_branch=$(_get_branch ccs-data)
  cd dev/ccs-data; git pull --ff-only origin $ccs_data_branch
  bundle install && ./lightfuse.rb -d msg -s ccs-dev-1 -c hiera-bom-unenc.yaml || { echo "Error with installing and running ccs-data BOM"; exit 1; }
  cd $WD/puppet
  librarian-puppet update --verbose
  cd $WD
}

_git_status() {
  if ! git status | grep -q 'nothing to commit'; then
    _print_title "Git Status: ccs-dev"
    git status
  fi
  if [ -d './dev/ccs-data/.git' ]; then
    cd dev/ccs-data
    if ! git status | grep -q 'nothing to commit'; then
      _print_title "Git Status: ccs-data"
      git status
    fi
    cd $WD
  fi
  if [ -d './puppet/modules' ]; then
    cd puppet/modules
    for repo in $(ls); do
      cd $repo
      if ! git status | grep -q 'nothing to commit'; then
        _print_title "Git Status: icehouse module ${repo}"
        git status
      fi
      cd ..
    done
    cd $WD
  fi
}

_vagrant_up() {
  if [[ $1 == '' ]]; then
    echo "Must pass host args to _vagrant_up"
    exit 1
  fi
  vagrant up $1
  [ $ENABLE_HA == 0 ] || vagrant up $(echo "${*:2}")
}

_vagrant_down() {
  if [[ $1 == '' ]]; then
    echo "Must pass host args to _vagrant_down"
    exit 1
  fi
  vagrant destroy -f $(echo "${*:1}")
}

_status() {
  vagrant status
}

_vagrant_action() {
  local action=$1
  local target=${2:-all}
  if [[ $action == '' ]] || ! echo $action | egrep -q '(up|down)'; then
    echo "Invalid action '${action}'; must be 'up' or 'down'"
    exit 1
  fi
  if ! echo $target | egrep -q '(all|aio|compute)'; then
    echo "Invalid target specified '${target}'"
    exit 1
  fi
  _vagrant_${action} aio-001 aio-002 aio-003
  [[ $target != 'aio' ]] || return
  _vagrant_${action} nova-001 nova-002
}

if [ $# == 0 ]; then
  _usage
  exit 1
fi

while [[ $1 != '' ]]; do
  case $1 in
    --ha)        ENABLE_HA=1;;
    --user)      shift; UNAME=$1; USER=$1;;
    help)        _usage; exit 0;;
    prep)        ACTION='prep';;
    update)      ACTION='update';;
    git-status)  ACTION='git-status';;
    up)          ACTION='up'; shift; TARGET=$1;;
    down)        ACTION='down'; shift; TARGET=$1;;
    status)      ACTION='status';;
    *)           _usage; exit 0;;
  esac
  shift
done

case $ACTION in
  prep)        _prep;;
  update)      _update;;
  git-status)  _git_status | less;;
  up)          _vagrant_action 'up' $TARGET;;
  down)        _vagrant_action 'down' $TARGET;;
  status)      _status;;
esac
