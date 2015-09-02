
--------------------------------
Ansible site variable framework
--------------------------------


For a full explanation of ansible variable mechanics, refer to the ansible documentation.

Site-specific variables are provided in a group_vars/all file, defined in the ansible.cfg.  These variables are pulled from the environment.yaml file found at ccs-data/src/sites/[site]/environments/[environment]/environment.yaml.  No special configuration is required within a playbook to leverage these keys.  Documentation of all keys available for an environment is still being developed.  For now, a developer can reference the relevant environment.yaml file in ccs-data.

Ansible allows for any play to reference variables from a common scope.  For a `domain_name` key provided within a site; any play can use this variable by using the jinja2 tag `{{ domain_name }}`.

No special configuraton is required.

Within a role, developers are encourage to use the `defaults/main.yml` to supply sane defaults for required parameters.  Due to ansible variable precedence, these variables will be automatically overridden by values provided in host_vars, group_vars, or in an include statement when calling the role.







