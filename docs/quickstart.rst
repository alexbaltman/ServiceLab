Installation
============

virtualenv
----------

Virtualenv is what you want to use for developing Stack applications.

What problem does virtualenv solve?  Chances are that you will be working with different
versions of Python itself, or at least different versions of Python
libraries.  Let's face it: quite often libraries break backwards
compatibility, and it's unlikely that any serious application will have
zero dependencies.  So what do you do if two or more of your projects have
conflicting dependencies?

Virtualenv to the rescue!  Virtualenv enables multiple side-by-side
installations of Python, one for each project.  It doesn't actually
install separate copies of Python, but it does provide a clever way to
keep different project environments isolated.  Let's see how virtualenv
works.
.. note:: If you are on Windows you must install Python 2.7, Git, and Pip.
   Python 2.7.10 automatically bundles Pip with it.

   - .. _installing python: https://www.python.org/downloads/windows/

   - .. _installing git: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git

   - .. _installing pip: http://pip.readthedocs.org/en/latest/installing.html

If you are on Mac OS X, try::

    $ sudo pip install virtualenv

If you use CentOS, you can also try::

    $ sudo yum -y install python-virtualenv

Once you have virtualenv installed, just fire up a shell and create
your own environment.  I usually create a project folder and a `venv`
folder within::

    $ mkdir myproject
    $ cd myproject
    $ virtualenv venv

Now, whenever you want to work on a project, you only have to activate the
corresponding environment.  On OS X and Linux, do the following::

    $ . venv/bin/activate

If you are a Windows user, the following command is for you::

    $ venv\scripts\activate

Either way, you should now be using your virtualenv (notice how the prompt of
your shell has changed to show the active environment).


After doing this, the prompt of your shell should be as familar as before.

Now, let's move on. Enter the following command to get Stack activated in your
virtualenv::

    $ pip install -e .

A few seconds later and you are good to go to begin using stack commands.

Finally, if you want to leave your virtualenv and go back to the real world,
use the following command::

    $ deactivate

Basic Concepts
--------------


:func:`stack.command`.

.. stack:example::

    stack list envs
