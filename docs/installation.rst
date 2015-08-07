Installation
============

Quickstart
----------

Tested on CentOS 7::

    $ yum install python-devel

    $ git clone ssh://ccs-gerrit.cisco.com:29418/servicelab

    $ cd servicelab

    $ virtualenv venv

    $ . venv/bin/activate

    $ pip install -e .

    $ pip install -r requirements.txt

    $ git checkout develop

You should be good-to-go to begin using stack commands::

    $ stack workon service-redhouse-tenant


.. note::
   servicelab/servicelab/.stack is the working directory

   You must have all of the modules properly installed before you can run the program.

   click==4.0

   sphinx-rtd-theme==0.1.8

   requests==2.7.0

   subprocess32==3.2.6

   logger==1.4

   pyyaml==3.11

   fabric==1.10.2

   pyvbox==0.2.2

   python-vagrant==0.5.9

   cuisine==0.7.10



Finally, if you want to leave your virtualenv and go back to the real world,
use the following command::

    $ deactivate



Installing Virtualenv
---------------------


If you use Mac OS X, try::

    $ sudo pip install virtualenv

If you use CentOS 7, try::

    $ sudo yum -y install python-virtualenv

Windows
--------------------

.. note::
    If you are on Windows you must install Python 2.7, Git, and Pip.
    Python 2.7.10 automatically bundles Pip with it.


`Installing python <https://www.python.org/downloads/windows>`_

`Installing git <https://git-scm.com/book/en/v2/Getting-Started-Installing-Git>`_

`Installing pip <http://pip.readthedocs.org/en/latest/installing.html>`_


Windows user, the following command is for you::

    $ venv\scripts\activate

Either way, you should now be using your virtualenv (notice how the prompt of
your shell has changed to show the active environment).

