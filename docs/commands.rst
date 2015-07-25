Stack commands
______________


.. module:: stack

.. autoclass:: create
    :members:
    Repo: Standard, ansible, puppet

.. autoclass:: destroy
    VM
    Repo in Gerrit
    Destroys Artificat in Artifactory

.. autoclass::  enc
    Encrypt a value and put it in CCS Data

.. autoclass:: find
    `repo`: Searches through Gerrit’s API for a repo using your search term
    review: Searches through Gerrit’s API for a review
    build: Searches through Jenkins API for pipelines
    artifact: Searches through Artifactory’s API for artifacts using  your search term
    pipe: Searches through Go’s API for pipelines

.. autoclass:: list
    Sites: Here we list all the sites using the git submodule ccs-data
    Envs: Here we list all the environments using the git submodule ccs-data
    Hosts: Here we list all the hosts using the git submodule ccs-data
    Repo: List all the repos using Gerrit’s API
    Build: Searches through Jenkins API for pipelines using your search term
    Artifacts: List artifacts using Artifactory’s API
    Pipe: Lists pipelines using GO’s API

.. autoclass:: nuclear: Dev Purposes Only

.. autoclass:: review
    Inc: Searches through Gerrit’s API for incoming reviews for your username
    Out: Searches through Gerrit’s API for incoming reviews for your username
    Plustwo: approves and merges a gerrit change set
    Plusone: Approves, but does not merge a gerrit change set, which means change set requires approval
    Abandon: Abandon a gerrit change set

.. autoclass:: show

.. autoclass:: status

.. autoclass:: up

.. autoclass:: validate

.. autoclass:: workon
