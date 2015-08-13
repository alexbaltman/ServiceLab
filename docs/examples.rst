Workflow
========

Input::

    $ stack

Output::

    Usage: stack [OPTIONS] COMMAND [ARGS]...

    A CLI for Cisco Cloud Services.

    Options:
    -p, --path DIRECTORY  Indicates your working servicelab folder.
    -v, --verbose         Enables verbose mode.
    -vv, --vverbose       Enables extra verbose mode.
    -vvv, --debug         Enables debug mode.
    -c, --config TEXT     You can specify a config file for               stack
                        to pull information from.
    --help                Show this message and exit.

    Commands:
    create    Creates pipeline resources to work with.
    destroy   Destroys VMs.
    enc       Encrypt a value and it will give you back an
            encrypted value for you to put into your ccs-data file.
    find      Helps you search              pipeline resources.
    list      You can list available pipeline objects
    nuclear   Cleans Everything.
    review    Helps you work with Gerrit
    show      Helps you show the details of a              pipeline resource.
    status    Shows status of your                servicelab environment.
    up        Boots VM(s).
    validate  Validate resources.
    workon    Call a service that you would like to              work on.

Input::

   $ stack find repo bdaas

Output::

    BDaaS2
    bdaas-devstackhorizon
    ccs-portal-bdaas
    ccs-portal-bdaas-backend
    service-ccs-portal-bdaas
    service-ccs-portal-bdaas-backend

Input::

 $ stack workon ccs-portal-bdaas 

Output::

    Cloning into 'ccs-portal-bdaas'...
    remote: Counting objects: 1390, done
    remote: Finding sources: 100% (1390/1390)
    remote: Total 1390 (delta 680), reused 1371 (delta 680)
    Receiving objects: 100% (1390/1390), 3.91 MiB | 324.00 KiB/s, done.
    Resolving deltas: 100% (680/680), done.

Input::

 $ cd ccs-portal-bdas 

*Make edits.*


Input::

 $ stack review 



**Other Examples**


 $ stack up --full --env <envname> --deploy-to <env to deploy to> --project <project name>


