
--------------------------------------
Puppet examples and Cisco usage links
--------------------------------------


Take a look below at an example that represents key functionality that puppet provides:

package { 'openssh-server':
ensure => installed,
}
file { '/etc/ssh/sshd_config':
source  => 'puppet:///modules/sshd/
sshd_config',
owner   => 'root',
group   => 'root',
mode    => '640',
notify  => Service['sshd'], # sshd
will restart whenever you
edit this file.
require => Package['openssh-server'],
}
service { 'sshd':
ensure => running,
enable => true,
hasstatus => true,
hasrestart => true,
}


Now lets look at the key Puppet resource types to support the above example  Most of the work you will need to do for the SDLC Pipeline deployment will be contained within these resource types below:

file:

Manages local files.

ATTRIBUTES

ensure — Whether the file should exist, and what it should be.

Variables: present, absent, file, directory, and link

path — The fully qualified path to the file; defaults to title.

source — Where to download the file. A puppet:/// URL to a file on the master, or a path to a local file on the agent.

content — A string with the file’s desired contents. Most useful when paired with templates, but you can also use the output of the file function.

target — The symlink target. (When ensure => link.)

recurse — Whether to recursively manage the directory. (When ensure => directory.)

Variables: true or false

purge — Whether to keep unmanaged files out of the directory. (When recurse => true.)

Variables: true or false

owner — By name or UID.

group — By name or GID.

mode — Must be specified exactly. Does the right thing for directories.

See also: backup, checksum, force, ignore, links, provider, recurselimit, replace, selrange, selrole, seltype, seluser, sourceselect, type.

package:

Manages software packages. Some platforms have better package tools than others, so you’ll have to do some research on yours; check the type reference for more info.

ATTRIBUTES

ensure — The state for this package. • present

Variables: latest, {any version string}, absent, purged

name — The name of the package, as known to your packaging system; defaults to title.

source — Where to obtain the package, if your system’s packaging tools don’t use a repository.

See also: adminfile, allowcdrom, category, configfiles, description, flavor, instance, platform, provider, responsefile, root, status, type, vendor.

service:

Manages services running on the node. Like with packages, some platforms have better tools than others, so read up. To restart a service whenever a file changes, subscribe to the file or have the file notify the service. (subscribe => File['sshd _ config'] or notify => Service['sshd'])

ATTRIBUTES

ensure — The desired status of the service. • running (or true)

Variables:  stopped (or false)

enable — Whether the service should start on boot. Doesn’t work everywhere.

Variables:  true or false

name — The name of the service to run; defaults to title.

Variables:  status, start, stop, and restart

hasrestart — Whether to use the init script’s restart command instead of stop+start. Defaults to false.

Variables:  true or false

hasstatus — Whether to use the init script’s status command instead of grepping the process table.

Variables:  true or false   Defaults to false.

pattern — A regular expression to use when grepping the process table. Defaults to the name of the service.
See also: binary, control, manifest, path, provider.

 

Example 2: Using Notifications:

notify:

Sends an arbitrary message to the agent run-time log.

notify { "This message is getting logged
on the agent node.": }
notify { "Mac warning":
message => $operatingsystem ? {
'Darwin' => "This seems to be a
Mac.",
default => "And I’m a PC.",
},
}


ATTRIBUTES

message — Defaults to title.

See also: withpath

 

Example 3: Executing commands:

exec:

Executes an arbitrary command on the agent node. When using execs, make sure the command can be safely run multiple times or specify that it should only run under certain conditions.

Exec {
path => [
'/usr/local/bin',
'/opt/local/bin',
'/usr/bin',
'/usr/sbin',
'/bin',
'/sbin'],
logoutput => true,
}
exec {'pwd':}
exec {'whoami':}


ATTRIBUTES

command — The command to run; defaults to title. If this isn’t a fully-qualified path, use the path attribute.

path — A search path for executables; colon- separated list or an array. This is most useful as a resource default, e.g.:

creates — A file created by this command; if the file exists, the command won’t run.

refreshonly — If true, the exec will only run if a resource it subscribes to (or a resource which notifies it) has changed.

Variables:  true or false

onlyif — A command or array of commands; if any have a non-zero return value, the command won’t run.

unless — The opposite of onlyif.

environment — An array of environment

Variables to set (e.g. ['MYVAR=somevalue', 'OTHERVAR=othervalue']).

See also: cwd, group, logoutput, returns, timeout, tries, try _ sleep, user.

 

Example 4: Adding cron jobs:

cron:

Manages cron jobs. Largely self-explanatory.

cron { logrotate:
command => "/usr/sbin/logrotate",
user => root,
hour => 2,
minute => 0
}


ATTRIBUTES

command — The command to execute.

ensure — Whether the job should exist.

Variables: present, absent

hour, minute, month, monthday, and weekday — The timing of the cron job.

See also: environment, name, provider, special, target, user.

 

Example 5: Administering user functionality:

user:

Manages user accounts; mostly used for system users.

user { "dave":
ensure     => present,
uid        => '507',
gid        => 'admin',
shell      => '/bin/zsh',
home       => '/home/dave',
managehome => true,
}


ATTRIBUTES
name (defaults to title)

uid — The user ID. Must be specified numerically; chosen automatically if omitted.

ensure — Whether the user should exist.

Variables: present • absent • role

gid — The user’s primary group. Can be specified numerically or by name.

groups — An array of secondary groups to which the user belongs. (Don’t include the group specified as the GID.)

home — The user’s home directory.

managehome — Whether to manage the home
directory when managing the user; if you don’t set this to true, you’ll need to create the user’s home directory manually.

Variables: true or false

shell — The user’s login shell.

See also: allowdupe, auths, comment, expiry, key _ membership, keys, membership, password, password _ max _ age, password _ min _ age, profile _ membership, profiles, project, provider, role _ membership, roles.

group:

Manages groups.

ATTRIBUTES

name (defaults to title)

gid — The group ID; must be specified numerically, and will be chosen automatically if omitted.

ensure — Whether the group should exist.

Variables: present • absent

See also: allowdupe, auth _ membership, members, provider.

 

Cisco related examples:

Please click the link below to see more complex example of how puppet is implemented withn the existing Cisco ecosystem..  Click on the gitweb link to the right side, then the tree link to see the file structure, then the blob link to view the code.

Note, you must be signed into cis-gerrit.cisco.com to view this information.

http://cis-gerrit.cisco.com/#/admin/projects/?filter=puppet

 
