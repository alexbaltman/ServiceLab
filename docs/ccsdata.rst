CCS Data
========

This is the holy grail. The collection of key/value pairs that describes all the sites and environments in CCS. One could look at it as a giant Python hash piped through Jinja templates. Everything begins and ends here. If you have an issue, most of the time, your answer lies here.

Clone it::

    >>> git clone ssh://ccs-gerrit.cisco.com:29418/ccs-data

Overview
--------

This repository holds all data used in orchestration and automation for sites pertaining to Icehouse and beyond.

Data presented in this repository does not represent it's final form as would be displayed on an end system. Overlap in keys/data can be strategically used for overriding values at compile time. The script ``lightfuse.rb`` will convert templates found in the repository, using data found from lookups, for each environment resulting in a compiled artifact that will be packaged and shipped to the end system.


Terminology
-----------

**Site** [*sīt*]: a compilation of multiple regions of environments; typically a site will be referred to by the service cloud associated with it, or the `building code <http://wikicentral.cisco.com/display/nimbus/Naming+Standards>`_ for the location.

**Environment** [*inˈvīrənmənt*]: typically, an individual region that exists in a site; an environment could reference a service or tenant cloud.

**BOM** [*bäm*]: *bill of materials*, or *software bill of materials*, used to specify the data required and supplied for a site, environment, and any/all orchestration or automation components; essentially represents the compiled data sources required for successful operation.

Folder Structure
----------------

Below is a representation of the current structure of ccs-data. Comments are made inline.::

    ├── build                           # contains scripts for building data artifacts
    ├── data.d                          # global
    ├── doc                             # documentation for ccs-data
    ├── hiera-bom.yaml                  # global hiera config file used for all puppet installations
    ├── lightfuse.rb                    # BOM generation script
    ├── Gemfile                         # Gems required to run the BOM and other tools in this repo
    ├── schemas                         # Schemas used for data validation
    ├── settings.yaml                   # Settings used by the BOM script and other tools in this repo
    ├── sites                           # contains all sites and subsequent site specific information
    │   ├── [site_name]                 #
    │   │   ├── data.d                  # global site data entries
    │   │   └── environments            #
    │   │       └── [env_name]          #
    │   │           ├── data.d          # env specific data entries used by orchestration and automation
    │   │           └── hosts.d         # host specific variables used by orchestration and automation
    ├──templates                        # templates used for generating BOM components
    │   └── environment                 # env specific BOM templates
    └── test                            # contains unit, schema, and other tests for the repo

Hierarchy of Lookups
--------------------

When the BOM is compiled, data is populated by performing a series of lookups for keys set in different YAML files, starting from the first entry (top) of the hierarchy and working downward. By default, a key's value is returned when the first occurance is found in one of the locations below. If the key is not found, an exception is raised causing the BOM complication to fail.::

    sites/%{site}/environments/%{environment}/hosts.d/%{host}.yaml
    sites/%{site}/environments/%{environment}/data.d/%{service}.yaml
    sites/%{site}/environments/%{environment}/data.d/%{role}.yaml
    sites/%{site}/environments/%{environment}/data.d/environment.yaml
    sites/%{site}/data.d/%{service}.yaml
    sites/%{site}/data.d/%{role}.yaml
    sites/%{site}/data.d/site.yaml
    data.d/%{service}.yaml
    data.d/%{role}.yaml
    data.d/common.yaml

Facts Used in Lookups
---------------------

Facts, or variables, are used when looking up keys and affect the files/paths included in the lookup. For example, if the ``site`` fact was set to ``alln01-svc-1``, the ``%{site}`` variable in the lookup hierarchy would be interpolated with ``alln01-svc-1``.

We currently employ five facts that can be set to manipulate the lookup hierarchy:

* ``site`` _a name of a site (ex. alln01-svc-2)_
* ``environment`` _a name of an environment (ex. us-texas-3)_
* ``host`` _a hostname of a targetted host (ex. csx-a-nova1-001)_
* ``service`` _a name of a heighliner service (ex. build-server)_
* ``role`` _a role for a given host found in it's hosts.d file (ex. compute\_local)_

When no facts are set, the paths interpolating these facts are ignored since they cannot be found. Following that example, given the hierarchy above, only ``data.d/common.yaml`` would be searched for a the key in question. Not all facts need to be set in order to perform a valid search.

Consider the following facts::

    site=alln01-svc-2
    environment=us-texas-3
    host=csx-a-nova1-001

Assuming no other facts were set, the hierarchy referenced above would effectively result in the following when a lookup is performed::

    sites/alln01-svc-2/environments/us-texas-3/hosts.d/csx-a-nova1-001.yaml
    sites/alln01-svc-2/environments/us-texas-3/data.d/environment.yaml
    sites/alln01-svc-2/data.d/site.yaml
    data.d/common.yaml

If the file ``sites/alln01-svc-2/environments/us-texas-3/hosts.d/csx-a-nova1-001.yaml`` does not exist, then it will be skipped and the next item in the hierarchy will be consulted.

Merging Data in Hash/Dictionary Lookups
---------------------------------------

The backend exposes a function to templates that will not return on first match for a hash/dict value, and instead continue looking for values in other hierarchy paths, performing a hash/dict merge when a new value is found.

For example, if you had the following files with the same key::

    # sites/alln01-svc-2/data.d/site.yaml
    mydict:
      value1: one

    # data.d/common.yaml
    mydict:
      value1: notone
      value2: two

The result of a hash lookup (when the ``site`` fact is set to ``alln01-svc-2``` would be the following::

    {
      "mydict": {
        "value1": "one",
        "value2": "two"
      }
    }

It should be noted, however, that the hash lookup is not the default behavior. By default, the lookup is returned when the first match is found in the hierarchy.

Encrypting Data
---------------

All passwords are required to be encrypted before committing to Git/Gerrit. We offer a public located in this repository to use when encrypting values and have added functionality to ``dutil.rb`` to assist with encryption actions.

Use the following YAML file for example::

    # sites/alln01-svc-1/data.d/site.yaml
    ---
    site_password: supersecure
    nameservers:
      - secret2

Encrypting the site_password key could be done two different ways: using ``dutil.rb`` to encrypt inline or simply outputting the encrypted string for you to update the file with.

**Method 1:** ``dutil.rb`` inline encryption::

    dutil.rb key encrypt site_password sites/alln01-svc-1/data.d/site.yaml

This would result in the file being updated to the following::

    # sites/alln01-svc-1/data.d/site.yaml
    ---
    site_password: ENC[PKCS7,SDf09dsflk345ljdsf09dflkkjl4690235...]
    nameservers:
      - secret2

**Method 2:** ``dutil.rb`` outputting an encrypted string::

    dutil.rb key encrypt site_password supersecure

This would return an encrypted string in YAML format for you to copy/paste into the file of your choice.

Schemas
-------

Schemas are validated using ``dutil.rb schema`` and reference the layout defined by the key 'schema' in settings.yaml. There are currently three categories of schemas: host, site, and environment. Each category must be a YAML dictionary with at least a 'default' key with it's value being an array. Other keys in the category dictionary are intrepretted to be case statements, meaning when the key is found in the YAML file being validated (target), the key's values (value of the key in the target YAML file) are specified as arrays including the schemas to run against the target file. For example::

    # settings.yaml
    schema:
      default: []
      my_key:
        value1:
          - value1_schema
          - another_schema
        value2:
          - value2_schema

    # environment.yaml
    my_key: value1
    key2: another string value

Taking the above as an example, when we run the schema validation via ``dutil.rb`` against environment.yaml, no default schemas will be tested, and since my_key was found in envrionment.yaml with the value 'value1', we will validate environment.yaml against value1_schema.yaml and another_schema.yaml.

For syntax on hosts.d or environment YAML files, please reference :doc:`schema`.

Templating
----------

For documentation on working with templates, please reference :doc:`templating`.

Known Workarounds
-----------------

There are a few workarounds that are required when adding certain types of keys/values.

Interpolating hiera lookups
---------------------------

Since we use hiera during BOM compilation time, there is a need to escape a value that is performing a recursive hiera call meant for deploy time (in an actual environment). For example, if you wanted to retrieve the IP address of the eth0 interface at run time, you would typically add the following line::

    ip: "%{ip_address}"

Would need to be added into the BOM as::

    ip: "%%{}{ip_address}"

This tricks hiera to interpolating the ``%{}`` into a an empty value, and returning the value as a literal ``%{ip_address}``, still preserving the interpolation until actual run time.



Common Tricks for Compute
-------------------------

Is my data actually in the build server? Is it correct?

    Check /etc/ccs/data/environments/<SVC>/TC>/hosts.yaml

Do I get a DHCP request coming to the build server?

    Run TCPDUMP on the build server

What do I see on the KVM console?

    Do I see it trying to PXE boot? Is there a media link failure?

Are my UCS configs correct?

    Check the interface configuration. Check the BIOS configuration for PXE boot option.

Are my networking config correct?

    Ping the networking team.

IP Helpers enabled?

    Network team needs to check the physical switches.

Is this server on the correct VLAN?

    Check /etc/dnsmasq.conf | Does it have the right range & vlan? What about UCS VLAN?