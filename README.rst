
$ stack
-------

  stack is a CLI that loads subcommands dynamically from the 'commands' plugin folder.

  All the commands are implemented as plugins in the `servicelab.commands` package.
  If a python module is placed named "cmd_foo" it will show up as "foo" command.
  The `cli` object within it will be loaded as nested Click command.

Quick start
-----------

::
        $ yum install python-devel

        $ git clone ssh://ccs-gerrit.cisco.com:29418/servicelab

        $ cd servicelab

        $ virtualenv venv

        $ . venv/bin/activate

        $ pip install -e .

        $ pip install -r requirements.txt


Afterwards, your CLI should be available:

::
        $ stack

Making the Documentation
------------------------

The Servicelab docs use Sphinx to generate documentation. All of the docs are located in the docs/ directory. To generate the html documentation, cd into the docs directory and run make html::


        $ cd docs
        $ make html


The generated documentation will be in the docs/_build/html directory. The source for the documentation is located in docs/source directory, and uses restructured text for the markup language.::

        $ firefox _build/html/index.html
