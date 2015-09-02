
------------------------
Puppet runtime commands
------------------------


To run puppet assuming in home puppet folder exists a manifests folder where your manifests reside, for this main.pp:

puppet apply manifests/main.pp


To run puppet assuming same configuration as above, as well as adding a modules folder in home puppet folder:

puppet apply manifests/main.pp --modulepath=/modules


To run puppet assuming same configuration as above, but adding more output and debugging:

puppet apply manifests/main.pp --modulepath=/modules --verbose --debug


To run puppet assuming same configuration as above, but doing a test run instead of actual machine configuration:

puppet apply manifests/main.pp --modulepath=/modules --verbose --debug --noop


 
