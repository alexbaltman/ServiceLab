.. _templating:

Templating
==========

Overview
---------

At runtime, the BOM takes templates defined in the ``./templates/`` directory and coverts them into files using the data from various lookups. Templates follow ERB syntax and can access global variables and functions defined in the BOM generation script ``lightfuse.rb``.

Compilation
-----------

Templates are read in by the BOM and are generated into files located by default at ``out/<site_name>/<environment_name>/etc/ccs/data/<template_name>``. The ``.erb`` extension is removed from the file name. If you wish to supply additional paths for the generated file, you can do so by setting the ``@paths`` variable in the template.

Environments are looped over, each reading from the ``templates/environment/*.erb`` directory and outputting the resultant file.

Variables
---------


A number of variables are made available to templates by the BOM generation script. These variables can be used and manipulated as seen fit by the template author.


**@globals**

Type: ``hash``

Description: Values about the current operating environment and site.

Example::

    {
      "site_name": "alln01-svc-2",
      "environments": [
        "alln01-svc-2",
        "us-texas-3"
      ],
      "environment_name": "us-texas-3",
      "hosts": [
        "csx-a-keystonectl-001",
        "csx-a-glancectl-001",
        ...
      ],
      "services": [
        "build-server",
        "glance-images",
        "secgroups"
      ]
    }



**@facts**


Type: ``hash``

Description: Facts currently set and used in key lookups.

Example::

    {
      "site": "alln01-svc-2",
      "environment": "us-texas-3"
    }


**@paths**


Type: ``array``

Description: Variable set in template files used to supply additional destination paths for the compiled result.

Default: ``[]``

Example::

    # mytemplate.erb
    @paths = [
      '/etc/mytemplate/result.conf',
      '/usr/local/etc/mytemplate/result.conf'
    ]



Functions
---------

The BOM offers a number of functions that can be used by the template during compilation time. Many of these functions reference the global variables such as ``@globals`` and ``@facts``.



**get_fact**

Description: Retrieves the value of a given fact.

Required Arguments:
  ``fact`` (_string_)

Returns: ``string``

Example::

    fact_environment = <%= get_fact('environment') %>



**set_fact**

Description: Sets a fact with the supplied value.

Required Arguments:

  ``fact`` (_string_)
  ``value`` (_string_)

Returns: ``nil``

Example::

    <% set_fact('host', 'csx-a-keystonectl-001') %>



**in_hierarchy**

Description: Checks to see if a key exists in the hierarchy (given the facts currently set).

Required Arguments:

  ``key`` (_string_)

Returns: ``nil``

Example::

    <% if in_hierarchy('mykey') %>
    mykey = <%= hiera('mykey') %>
    <% end %>



**hiera**

Description: Performs a key lookup against the hierarchy given the facts currently set and returns the value.

Required Arguments:

  ``key`` (_string_)

Optional Arguments:

  ``default`` (_string_, _bool_, _hash_, _array_, _int_) default value if no key is found [default: ``nil``]
  ``to_yaml`` (_bool_) return the value as yaml instead of Ruby type [default: ``false``]

Returns: (_string_, _bool_, _hash_, _array_, _int_)

Example:

    mykey = <%= hiera('mykey') %>
    mykey_default = <%= hiera('mykey', 'defaultvalue') %>
    mykey_nodefault_yaml = <%= hiera('mykey', nil, true) %>



**hiera_array**

Description: Performs a key lookup against the hierarchy given the facts currently set and returns an array value.

Required Arguments:

  ``key`` (_string_)

Optional Arguments:

  ``default`` (_string_, _bool_, _hash_, _array_, _int_) default value if no key is found [default: ``nil``]

  ``to_yaml`` (_bool_) return the value as yaml instead of Ruby type [default: ``false``]

Returns: (_array_)

Example::

    mykey = <%= hiera_array('mykey') %>



**hiera_hash**

Description: Performs a key lookup against the hierarchy given the facts currently set and returns a merged hash of the results.

Required Arguments:

  ``key`` (_string_)

Optional Arguments:

  ``default`` (_string_, _bool_, _hash_, _array_, _int_) default value if no key is found [default: ``nil``]

  ``to_yaml`` (_bool_) return the value as yaml instead of Ruby type [default: ``false``]

Returns: (_hash_)

Example::

    mykey = <%= hiera_hash('mykey') %>



**get_environ_keys**

Description: Returns keys from the current environment's ```environment.yaml`` file given the facts currently set.

Returns: (_array_)

Example::

    <% get_environ_keys().each do |key| %>
    <%= key %>: <%= hiera(key) %>
    <% end %>



**get_service_keys**

Description: Returns all keys for all services in the current environment given the facts currently set.

Returns: (_array_)

Example::

    <% get_service_keys().each do |key| %>
    <%= key %>: <%= hiera(key) %>
    <% end %>
