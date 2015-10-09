
--------------------
Heighliner Workflow
--------------------


Heighliner is a tool for parsing and executing actions specified in .nimbus.yml file. It is written in Python by SDLC team for on-boarding of CCS projects into the CI/CD pipeline. 

You will need to setup at least one project repo and service repo for each project. 

The project repo (i.e. helloworld) contains the source code (such as Java, Python, Ruby or any scripts) and automated unit tests (if applicable). 

The service repo (i.e. service-helloworld) contains the deployment scripts (written in Ansible or Puppet) to deploy the packages into target hosts. The service repo must be setup with same name as project repo but prefixed with service- (i.e. service-helloworld). The heighliner identifies project repo and service repo using this distinction and thus it is a must to follow this naming convention.

This is a special file that is required for heighliner. The .nimbus.yml file exists in the root folder of both project and service repo. Refer .nimbus.yml file section of Heighliner API docs for syntax. Typically, the project repo will have check and build actions defined in .nimbus.yml file with the corresponding scripts (i.e. unit_test.sh for check action and build.sh for build action in helloworld repo). On the other hand, the service repo can have check, deploy and verify actions in its .nimbus.yml (i.e. python check.py for check action, no build action but it is automatic, deploy.yml for deploy action, and serverspec/ for verify action in service-helloworld repo). The deploy and verify (Ansible and Puppet version) actions are only applicable to service repo - refer Base Plugins section of Heighliner API docs for all supported actions.

This is a shared global repo contains key/value pair applicable to per-service, per-environment, per-site or at global level. It creates isolation between the service package and data. At a minimum, you will have to add the service name under groups section in the host file to deploy this service into this host. This data repo goes through its own Jenkins build process and generates ccs-data rpm which is pushed into sdlc-mirror. A separate Go pipeline will deploy the ccs-data rpm into the corresponding build server. For example, ccs-data structure for rtp10-svc-2 looks like,

├── rtp10-svc-2
│   ├── data.d
│   │   └── site.yaml
│   └── environments
│       ├── rtp10-svc-2
│       │   ├── data.d
│       │   │   ├── build-server.yaml
│       │   │   └──
│       │   └── hosts.d
│       │       ├── csm-a-aio-001.yaml
│       │       └──
│       └── us-stage-1
│           ├── data.d
│           │   └── environment.yaml
│           └── hosts.d
│               ├── csl-a-net-001.yaml
│               └── ]]>

Click here for higher resolution pic.



Jenkins jobs are used to run automated unit tests and perform build tasks using heighliner check and build. The jobs are auto-created by Jenkins Job Builder (JJB) tool. The first git review after creating new repos will auto-create two jobs in Jenkins (check and build) - the repo must contain .nimbus.yml file in the root folder otherwise these Jenkins jobs will not be created.

The check job (i.e. check_helloworld) will be triggered whenever changes are pushed into gerrit using 'git review' command. The check job will execute the corresponding check action script defined in .nimbus.yml file (i.e. unit_test.sh for helloworld repo).

The build job (i.e. build_helloworld) will be triggered whenever the changes are merged in gerrit. The build job will execute the corresponding build action script in .nimbus.yml file (i.e. build.sh for helloworld repo). At the end of build job, the resulting artifacts that are created (such as .rpm, .iso, .qcow, qcow2 and .img) will be uploaded to ccs-secure-repo in sdlc-mirror.cisco.com server. Correspondingly, the service repo (i.e. build_service-helloworld) will generate a service rpm.

Jenkins launches a docker container for executing the check and build jobs. At the end of each run, the docker container is destroyed. By executing Jenkins jobs inside the docker container, project team will have an isolated environment to install/uninstall of any tools necessary for the check and build actions. 

Go pipelines are used to deploy build artifacts created from service repo into target hosts using heighliner deploy. Pipelines for services are automatically created when your services is associated with a host via a hosts.d file (ex. service-helloworld is present in the groups: key within the hosts.d file). The Go pipeline follows a standard naming convention, deploy-project-repo-name-environment-name (i.e. deploy-helloworld-rtp10-svc-1). It is important to follow this naming convention so that managing hundreds of Go pipelines is sustainable.

Go pipeline is executed in the build server. The build server (aka infra host) is a node (i.e. csm-a-infra-001) that has Go agent installed to orchestrate the deployment to all the hosts under the given site or environment. The Go pipeline is created using a standard template for service deployment which has two major stages - 1) prepare_materials and 2) deploy_service.

Go polls for new package materials (i.e. service rpm) from ccs-secure-repo and triggers this stage automatically. This is a gating in Go and user must click '>|>' button to proceed the deployment to next stage.

This stage syncs up packages from ccs-secure-repo into build server using cobbler sync.

This final stage installs the service rpm (i.e. deployment scripts) into the build server and executes heighliner deploy action which in turn executes (Ansible or Puppet) deployment scripts in the target hosts. Heighliner uses Ansible dynamic host inventory to fetch target hosts from the ccs-data residing in build server. Once execution is done, the service rpm is then removed from the build-server (rpm -e).







