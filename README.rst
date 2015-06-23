
$ stack_

  stack is a CLI that loads subcommands dynamically from the 'commands' plugin folder.

  All the commands are implemented as plugins in the
  `complex.commands` package.  If a python module is
  placed named "cmd_foo" it will show up as "foo"
  command. The `cli` object within it will be
  loaded as nested Click command.

Usage:
  $ virtualenv venv
  $ . venv/bin/activate
  $ pip install --editable .
  $ complex --help


Afterwards, your command should be available:

  $ stack
