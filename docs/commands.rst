Stack commands
______________

. module:: stack

.. autoclass:: create
    :members: repo
    .. method:: standard
    .. method:: ansible
    .. method:: puppet

.. autoclass:: destroy
    :members: vm, repo, artifact

.. autoclass::  enc
    Encrypt a value and put it in CCS Data

.. autoclass:: find
    :members: repo, review, build, artifact, pipe
    repo: Searches through Gerrit’s API for a repo using your search term
    review: Searches through Gerrit’s API for a review
    build: Searches through Jenkins API for pipelines
    artifact: Searches through Artifactory’s API for artifacts using  your search term
    pipe: Searches through Go’s API for pipelines

.. autoclass:: list
    :members: sites, envs, hosts, repo, build, artifacts, pipe
    sites: Here we list all the sites using the git submodule ccs-data
    snvs: Here we list all the environments using the git submodule ccs-data
    hosts: Here we list all the hosts using the git submodule ccs-data
    repo: List all the repos using Gerrit’s API
    build: Searches through Jenkins API for pipelines using your search term
    artifacts: List artifacts using Artifactory’s API
    pipe: Lists pipelines using GO’s API

.. autoclass:: nuclear: Dev Purposes Only

.. autoclass:: review
    :members: inc, out, plustwo, plusone, abandon
    inc: Searches through Gerrit’s API for incoming reviews for your username
    out: Searches through Gerrit’s API for incoming reviews for your username
    plustwo: approves and merges a gerrit change set
    plusone: Approves, but does not merge a gerrit change set, which means change set requires approval
    abandon: Abandon a gerrit change set

.. autoclass:: show
    :members: artifact, build, pipe, repo, review

.. autoclass:: status
    :members:

.. autoclass:: up
    :members:

.. autoclass:: validate
    :members:

.. autoclass:: workon
    :members:
