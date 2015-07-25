Quickstart
==========

.. currentmodule:: stack

You can get the library directly from PyPI::

    pip install stack

The installation into a :ref:`virtualenv` is heavily recommended.

.. _virtualenv:

virtualenv
----------

Virtualenv is probably what you want to use for developing Stack
applications.

What problem does virtualenv solve?  Chances are that you want to use it
for other projects besides your Click script.  But the more projects you
have, the more likely it is that you will be working with different
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

If you are on Mac OS X or Linux, chances are that one of the following two
commands will work for you::

    $ sudo easy_install virtualenv

or even better::

    $ sudo pip install virtualenv

One of these will probably install virtualenv on your system.  Maybe it's even
in your package manager.  If you use Ubuntu, try::

    $ sudo apt-get install python-virtualenv

If you are on Windows (or none of the above methods worked) you must install
``pip`` first.  For more information about this, see `installing pip`_.
Once you have it installed, run the ``pip`` command from above, but without
the `sudo` prefix.

.. _installing pip: http://pip.readthedocs.org/en/latest/installing.html

Once you have virtualenv installed, just fire up a shell and create
your own environment.  I usually create a project folder and a `venv`
folder within::

    $ mkdir myproject
    $ cd myproject
    $ virtualenv venv
    New python executable in venv/bin/python
    Installing setuptools, pip............done.

Now, whenever you want to work on a project, you only have to activate the
corresponding environment.  On OS X and Linux, do the following::

    $ . venv/bin/activate

If you are a Windows user, the following command is for you::

    $ venv\scripts\activate

Either way, you should now be using your virtualenv (notice how the prompt of
your shell has changed to show the active environment).

And if you want to go back to the real world, use the following command::

    $ deactivate

After doing this, the prompt of your shell should be as familar as before.

Now, let's move on. Enter the following command to get Stack activated in your
virtualenv::

    $ pip install -e .

A few seconds later and you are good to go.



Basic Concepts
--------------


:func:`stack.command`.

.. stack:example::

    stack list envs



.. _switching-to-setuptools:

Switching to Setuptools
-----------------------

In the code you wrote so far there is a block at the end of the file which
looks like this: ``if __name__ == '__main__':``.  This is traditionally
how a standalone Python file looks like.  With Click you can continue
doing that, but there are better ways through setuptools.

There are two main (and many more) reasons for this:

The first one is that setuptools automatically generates executable
wrappers for Windows so your command line utilities work on Windows too.

The second reason is that setuptools scripts work with virtualenv on Unix
without the virtualenv having to be activated.  This is a very useful
concept which allows you to bundle your scripts with all requirements into
a virtualenv.

Click is perfectly equipped to work with that and in fact the rest of the
documentation will assume that you are writing applications through
setuptools.

I strongly recommend to have a look at the :ref:`setuptools-integration`
chapter before reading the rest as the examples assume that you will
be using setuptools.