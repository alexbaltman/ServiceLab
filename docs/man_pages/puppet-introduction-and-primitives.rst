
-----------------------------------
Puppet introduction and primitives
-----------------------------------


Puppet is a declarative language for expressing system configuration, a client and server for distributing it, and a library for realizing the configuration.  As system administrators acquire more and more systems to manage, automation of mundane tasks is increasingly important. Rather than develop in-house scripts, it is desirable to share a system that everyone can use, and invest in tools that can be used regardless of one’s employer. Certainly doing things manually doesn’t scale.  Puppet has been developed to help the sysadmin community move to building and sharing mature tools that avoid the duplication of everyone solving the same problem. It does so in two ways:

It provides a powerful framework to simplify the majority of the technical tasks that sysadmins need to perform
The sysadmin work is written as code in Puppet’s custom language which is shareable just like any other code.
This means that your work as a sysadmin can get done much faster, because you can have Puppet handle most or all of the details, and you can download code from other sysadmins to help you get done even faster. The majority of Puppet implementations use at least one or two modules developed by someone else, and there are already hundreds of modules developed and shared by the community.

 

Core Puppet Features:

Idempotency:

One big difference between Puppet and most other tools is that Puppet configurations are idempotent, meaning they can safely be run multiple times.  Puppet will only make any changes to the system if the system state does not match the configured state.

Cross Platform:

Puppet’s Resource Abstraction Layer (RAL) allows you to focus on the parts of the system you care about, ignoring implementation details like command names, arguments, and file formats — your tools should treat all users the same, whether the user is stored in NetInfo or /etc/passwd. Puppets calls these system entities resources.

Resource Types:

The concept of each resource (like service, file, user, group, etc) is modeled as a “type”. Puppet decouples the definition from how that implementation is fulfilled on a particular operating system, for instance, a Linux user versus an OS X user can be talked about in the same way but are implemented differently inside of Puppet.

Providers:

Providers are the fulfillment of a resource. For instance, for the package type, both ‘yum’ and ‘apt’ are valid ways to manage packages. Sometimes more than one provider will be available on a particular platform, though each platform always has a default provider. There are currently 17 providers for the package type.

Modifying the System:

Puppet resource providers are what are responsible for directly managing the bits on disk. You do not directly modify a system from Puppet language — you use the language to specify a resource, which then modifies the system. This way puppet language behaves exactly the same way in a centrally managed server setup as it does locally without a server. Resources have attributes called ‘properties’ which change the way a resource is managed. For instance, users have an attribute that specifies whether the home directory should be created.  ‘Metaparams’ are another special kind of attribute, those exist on all resources. This include things like the log level for the resource, whether the resource should be in noop mode so it never modifies the system, and the relationships between resources.

Resource Relationships:

Puppet has a system of modeling relationships between resources — what resources should be evaluated before or after one another. They also are used to determine whether a resource needs to respond to changes in another resource (such as if a service needs to restart if the configuration file for the service has changed). This ordering reduces unnecessary commands, such as avoiding restarting a service if the configuration has not changed.

 

Core Puppet Concepts:

Resources, Classes, and Nodes:

The core of the Puppet language is declaring resources. Every other part of the language exists to add flexibility and convenience to the way resources are declared.

Groups of resources can be organized into classes, which are larger units of configuration. While a resource may describe a single file or package, a class may describe everything needed to configure an entire service or application (including any number of packages, config files, service daemons, and maintenance tasks). Smaller classes can then be combined into larger classes which describe entire custom system roles, such as “database server” or “web application worker.”

Nodes that serve different roles will generally get different sets of classes. The task of configuring which classes will be applied to a given node is called node classification. Nodes can be classified in the Puppet language using node definitions; they can also be classified using node-specific data from outside your manifests, such as that from an ENC or Hiera.

Ordering:

Puppet’s language is mostly declarative: Rather than listing a series of steps to carry out, a Puppet manifest describes a desired final state.  The resources in a manifest can be freely ordered — they will not necessarily be applied to the system in the order they are written. This is because Puppet assumes most resources aren’t related to each other. If one resource depends on another, you must say so explicitly.   Although resources can be freely ordered, several parts of the language do depend on parse order. The most notable of these are variables, which must be set before they are referenced.

Configurable Ordering:

The ordering setting allows you to configure how resources are ordered when relationships are not present.  By default, the order of unrelated resources is effectively random. If you set ordering = manifest in puppet.conf, Puppet will apply unrelated resources in the order in which they appear in the manifest.  This setting only affects resources whose relative order is not otherwise determined, e.g., by metaparameters like before or require. See the language page on relationships for more information.

Files:

Puppet language files are called manifests, and are named with the .pp file extension. Manifest files should use UTF8 encoding and may use Unix (LF) or Windows (CRLF) line breaks.  Puppet always begins compiling with a single manifest (which may be broken up into several pieces), called the “site manifest” or “main manifest.” See the reference page on the main manifest for details about this special file/directory.  Any classes declared in the main manifest can be auto loaded from manifest files in modules. Puppet will also autoload any classes declared by an optional external node classifier. See the reference page on catalog compilation for details.  The simplest Puppet deployment is a lone main manifest file with a few resources. Complexity can grow progressively, by grouping resources into modules and classifying your nodes more granularly.

 
