Overview
========

ServiceLab Folder Structure
---------------------------

Current structure of servicelab with inline comments::

    servicelab
    ├── build.sh                            #
    ├── CHANGES                             #
    ├── check.sh                            #
    ├── dev                                 #
    │   ├── data.yaml                       #
    │   ├── provision.yml                   #
    │   └── templates                       #
    │       └── sdlc-mirror.repo.j2         #
    ├── docs/                               #
    ├── Gemfile                             #
    ├── Gemfile.lock                        #
    ├── install_rvm.sh                      #
    ├── Makefile                            #
    ├── README.md                           #
    ├── README.rst                          #
    ├── red-svc-ccs_vagrant_hosts           #
    ├── red-svc-default_settings.yaml       #
    ├── red-svc-Gemfile                     #
    ├── red-svc-stack.sh                    #
    ├── red-svc-Vagrantfile                 #
    ├── red-svc-vagrant.yaml                #
    ├── red-tc-ccs_vagrant_hosts            #
    ├── red-tc-default_settings.yaml        #
    ├── red-tc-stack.sh                     #
    ├── red-tc-Vagrantfile                  #
    ├── red-tc-vagrant.yaml                 #
    ├── requirements.txt                    #
    ├── servicelab                          # Main application folder
    │   ├── .stack                          # Working directory
    │   │   ├── provision                   #
    │   │   ├── services                    #
    │   ├── commands                        # Frontend commands folder
    │   │   ├── cmd_create.py               #
    │   │   ├── cmd_destroy.py              #
    │   │   ├── cmd_enc.py                  #
    │   │   ├── cmd_find.py                 #
    │   │   ├── cmd_list.py                 #
    │   │   ├── cmd_nuclear.py              #
    │   │   ├── cmd_review.py               #
    │   │   ├── cmd_show.py                 #
    │   │   ├── cmd_status.py               #
    │   │   ├── cmd_up.py                   # Spins up Vagrant file
    │   │   ├── cmd_validate.py             #
    │   │   ├── cmd_workon.py               # Creates Vagrant and sets working dir
    │   │   ├── __init__.py                 #
    │   ├── errors.py                       #
    │   ├── help_pages                      #
    │   │   └── cmd_create.md               #
    │   ├── __init__.py                     #
    │   ├── stack.py                        # Mother of all Commands
    │   └── utils                           # Main utilities / backend logic
    │       ├── ccsbuildtools_utils.py      #
    │       ├── ccsdata_dev_example_host.yaml
    │       ├── ccsdata_utils.py            # List the ccs-data sites & envs
    │       ├── encrypt_utils.py            # Encryption
    │       ├── engine.py                   #
    │       ├── helper_utils.py             #
    │       ├── __init__.py                 #
    │       ├── new_site_data               #
    │       │   ├── ip_ranges.yaml          #
    │       │   ├── service_cloud.yaml      #
    │       │   └── tenant_cloud.yaml       #
    │       ├── openstack_utils.py          # Connects to Keystone/Neutron
    │       ├── public_key.pkcs7.pem        #
    │       ├── ruby_utils.py               #
    │       ├── service_utils.py            # Main util for cmd_workon
    │       ├── vagrantfile_utils.py        # Manipulates the Vagrant file
    │       ├── vagrant_plugins.yaml        # List of plugins
    │       ├── vagrant_utils.py            # Python wrapper for executing Vagrant tasks
    │       ├── vagrant.yaml                # Vagrant Yaml (* Important)
    │       ├── yaml_utils.py               # Manipulates/Validates the Yaml
    ├── setup.py                            # Install & Setuptools
    ├── stack                               #
    ├── stack-Vagrantfile                   #
    ├── test-requirements.txt               #
    ├── tests                               #
