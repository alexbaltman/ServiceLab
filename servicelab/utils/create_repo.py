"""
The create_repo module has a set of classes to create an Empty project, Project, Ansible
project or a Puppet project. Each of the above project type derives and delegates it
creation and construction to the common abstact base class Repo. One can get instance of
Project, Empty project, Ansible, or Puppet by invoking static Repo::builder method.
One can invoke construct method to the instance to
   1. Create the gerrit project.
   2. Download a template project.
   3. Instantiate the template project with the project name.

For
    1. Ansible project - create_repo uses service-helloworld-ansible as a template
    2. Puppet project  - create_repo uses service-helloworld-puppet as a template

"""
import os
import shutil

import yaml
import click

from abc import ABCMeta, abstractmethod
from servicelab.utils import service_utils

from servicelab.stack import SLAB_Logger

ctx = SLAB_Logger()


class Repo(object):
    """
    ABC for creating repos of type Ansible, Puppet, Project, EmptyProject
    """
    __metaclass__ = ABCMeta

    def builder(rtype, gsrvr, path, name, username, interactive):
        """
        Static method Instantiates Concreate classes of type Repo.
        """
        ctx.logger.log(15, 'Setting up repo method')
        if rtype is "Ansible":
            repo = Ansible(gsrvr, path, name, username, interactive)
            ctx.logger.debug('Repo configured for Anisble')
        elif rtype is "Puppet":
            repo = Puppet(gsrvr, path, name, username, interactive)
            ctx.logger.debug('Repo configured for Puppet')
        elif rtype is "Project":
            repo = Project(gsrvr, path, name, interactive)
            ctx.logger.debug('Repo configured for Project')
        elif rtype is "EmptyProject":
            repo = EmptyProject(gsrvr, path, name, username, interactive)
            ctx.logger.debug('Repo configured for EmptyProject')
        else:
            assert 0, "unable to construct the project of type: " + rtype
        repo.set_reponame()
        return repo

    builder = staticmethod(builder)

    def __init__(self, gsrvr, path, name, username, interactive):
        self.gsrvr = gsrvr
        self.ctx_path = path
        self.name = name
        self.reponame = name
        self.chk_script = "./check.sh"
        self.interactive = interactive
        self.username = username

    def get_reponame(self):
        """
        Get the name of the repo

        Returns:
            str: The type of the repo

        Raises:
            Raises Exception if type is not Ansible, Puppet, Project or
            EmptyProject.
        """
        assert type(self).__name__ != "Repo", "no repo name available "

    def set_reponame(self):
        """
        get ansible projcet of type service-<project name>-ansible
        """
        if self.interactive:
            self.reponame = click.prompt("enter the reponame",
                                         default=self.reponame, type=str)

    def check(self):
        """
        if the repo exist, print message and return true.
        """
        ctx.logger.log(15, 'Checking for repo %s' % self.get_reponame())
        if os.path.exists("./{}".format(self.get_reponame())):
            click.echo("repo for {0} exist as {1}".format(self.name, self.get_reponame()))
            return True
        return False

    def create_project(self):
        """
        Create the project on the gerrit server.

        Returns:
        (
            int : return code
            str : output string if any.
        )
        """
        ctx.logger.log(15, 'Creating project %s on gerrit' % self.get_reponame())
        hostname = self.gsrvr['hostname']
        port = self.gsrvr['port']
        cmd = "ssh -p {} {}@{} gerrit create-project {}".format(port,
                                                                self.username,
                                                                hostname,
                                                                self.get_reponame())

        ret_code, ret_str = service_utils.run_this(cmd)
        return (ret_code, ret_str)

    def cleanup_properties(self, name):
        """
        Clean up any files from the template directories
        """
        ctx.logger.log(15, 'Cleaning up files from template directories')
        pdict = {}
        fpath = os.path.join(self.get_reponame(), "serverspec", "properties.yml")
        with open(self.get_reponame() + "/serverspec/properties.yml") as ydata:
            pdict = yaml.load(ydata)
            pdict[str(self.name)] = pdict[name]
            del pdict[name]
        os.remove(fpath)

    def create_repo(self):
        """
        create a repo on the local machine. Returns -1 if the repo creation fails.
        Returns:
        (
            int : return code
            str : output string if any.
        )
        """
        ctx.logger.log(15, 'Creating local repo %s' % self.get_reponame())
        hostname = self.gsrvr['hostname']
        port = self.gsrvr['port']
        # please see https://code.google.com/p/gerrit/issues/detail?id=1013
        # for -no-checkout option.
        cmd = "git clone --no-checkout --depth=1 "
        cmd += "ssh://{}@{}:{}/{} {}/.tmp".format(self.username,
                                                  hostname,
                                                  port,
                                                  self.get_reponame(),
                                                  self.get_reponame())
        ret_code, ret_str = service_utils.run_this(cmd)
        assert ret_code == 0, "unable to clone the project:" + ret_str

        os.rename(os.path.join(self.get_reponame(), ".tmp", ".git"),
                  os.path.join(self.get_reponame(), ".git"))
        shutil.rmtree(os.path.join(self.get_reponame(), ".tmp"))

        return ret_code

    def releasenote(self, rtype):
        """
        creates the correct rlease nootes file.
        """
        ctx.logger.log(15, 'Creating release notes file')
        # correcting the release note
        release_note = """#
# Release Notes for component service-{0}-{1}
#

Current version: 0.1.1

## 0.1.1
 * Baseline Component Version to support SDLC Pipeline Tooling
 * SDLC Docs: https://confluence.sco.cisco.com/display/CCS/SDLC+Group+Onboarding
        """.format(self.name, rtype)
        with open("{}/release-notes.md".format(self.get_reponame()), "w") as relfile:
            relfile.write(release_note)

    def remove(self, name):
        """
        if the repo exist, then remove
        """
        ctx.logger.log(15, 'Removing repo %s' % name)
        if os.path.exists(name):
            os.remove(name)

    @abstractmethod
    def download_template(self):
        """
        download template is an abstarct method redefined in the subclass.
        """
        return

    @abstractmethod
    def create_nimbus(self):
        """
        create nimbus is an abstarct method redefined in the subclass.
        """
        return


class Ansible(Repo):
    """
    Creates the Ansible Repo.
    """
    def __init__(self, gsrvr, path, name, username, interactive):
        super(Ansible, self).__init__(gsrvr, path, name, username, interactive)
        self.play_roles = []
        self.chk_script = "python test.py"
        if not self.reponame.startswith("service-"):
            self.reponame = "service-" + self.reponame
        if not self.reponame.endswith("-ansible"):
            self.reponame = self.reponame + "-ansible"

    def get_reponame(self):
        """
        get ansible projcet of type service-<project name>-ansible
        """
        ctx.logger.debug('Repo name is %s' % self.reponame)
        return self.reponame

    def create_nimbus(self):
        """
        create the nimbus file .nimbus.yml for Ansible project.
        """
        ctx.logger.log(15, 'Creating .nimbus.yml for %s' % self.get_reponame())
        if self.interactive:
            self.chk_script = click.prompt("enter the script to check",
                                           default="./check.sh", type=str)

        nimbusdict = dict(service=str(self.name + "-ansible"), version="0.0.1",
                          deploy=dict(type="ansible", playbook=str(self.name + ".yml")),
                          verify=dict(type="serverspec"))
        if self.chk_script:
            nimbusdict['check'] = dict(script=self.chk_script)

        nimbus_name = os.path.join(".", self.get_reponame(), ".nimbus.yml")
        with open(nimbus_name, "w") as nimbus:
            nimbus.write(yaml.dump(nimbusdict, default_flow_style=False))

    def create_ansible(self):
        """
        Create the ansible directory for the ansible project.
        """
        def _add_roles():
            """
            add the roles. If command is invoked with interactive flag, then user can
            enter the various roles.
            """
            ctx.logger.log(15, 'Determining Anisble roles')
            if not self.interactive:
                self.play_roles.append(str(self.name))
                return

            if not self.play_roles:
                while True:
                    role = click.prompt("role", default=str(self.name), type=str)
                    if not role:
                        break
                    if role in self.play_roles:
                        lst = [str(play_role) for play_role in self.play_roles]
                        click.echo(" entered roles:" + str(lst))
                        if click.confirm(' do you want to continue?'):
                            continue
                        break
                    self.play_roles.append(role)

        def _write_playfile(playdict):
            """
            write the ansible project yml file.
            """
            ctx.logger.log(15, 'Creating Ansible project file for %s' % self.get_reponame())
            playfile = "./{}/ansible/{}".format(self.get_reponame(),
                                                self.name + ".yml")
            with open(playfile, "w") as playbook:
                playbook.write(yaml.dump(playdict, default_flow_style=False))

        # make the necessary directory
        ansibledir = "./{}/ansible".format(self.get_reponame())
        if not os.path.isdir(ansibledir):
            os.mkdir(ansibledir)

        _add_roles()
        playdict = dict(hosts="{}-ansible".format(self.name),
                        remote_user=self.username, roles=self.play_roles)
        _write_playfile(playdict)
        return self.play_roles

    def create_roles(self, roles):
        """
        Create all the roles in the ansible directory
        """
        path = os.path.join(self.get_reponame(), "ansible", "roles")
        ctx.logger.log(15, 'Creating roles within %s' % path)
        if not os.path.isdir(path):
            os.mkdir(path)
        for role in roles:
            os.mkdir(os.path.join(path, role))
            os.mkdir(os.path.join(path, role, "defaults"))
            os.mkdir(os.path.join(path, role, "tasks"))
            os.mkdir(os.path.join(path, role, "templates"))

    def download_template(self):
        """
        Download the service-helloworld-ansible template from the gerrit server
        """
        ctx.logger.log(15, 'Downloading service-helloworld-ansible template from gerrit')
        hostname = self.gsrvr['hostname']
        port = self.gsrvr['port']
        cmd = "git clone --depth=1 "
        cmd += "ssh://{}@{}:{}/service-helloworld-ansible {}".format(self.username,
                                                                     hostname,
                                                                     port,
                                                                     self.get_reponame())
        ret_code, ret_str = service_utils.run_this(cmd)
        assert ret_code == 0, "unable to get ansible template project:" + ret_str

    def instantiate_template(self):
        """
        Instantiate the service-helloworld-ansible to the project. This involves
        removing some files as well updating others with the correct input project
        name.
        """
        ctx.logger.log(15, 'Instantiating service-helloworld-ansible to %s'
                       % self.get_reponame)
        shutil.rmtree(os.path.join(self.get_reponame(), ".git"))
        self.cleanup_properties("helloworld-test")

        self.remove(os.path.join(self.get_reponame(), "doc", "README.md"))

        with open(os.path.join(self.get_reponame(), "data", "dev.yaml"), "w") as devfile:
            devfile.write("# This generated file is the local replacement of ccs-data for\n"
                          "# local development, otherwise your playbook will error out.\n"
                          "# If using servicelab to deploy for real site please update \n"
                          "#  ccs-dev/environments/dev-tenant in ccs-data appropriately.")

        with open(os.path.join(self.get_reponame(),
                               "data",
                               "service.yaml"), "w") as sfile:
            sfile.write("# This generated file contains service specific parameters.")

        shutil.rmtree(os.path.join(self.get_reponame(), "ansible",
                                   "roles", "helloworld-test"))

        # correcting the test.py
        testdata = "#!/usr/bin/env python\n"\
                   "# A syntax check for an ansible yaml file\n"\
                   "import yaml\n"\
                   "import sys\n"\
                   "\n"\
                   "try:\n"\
                   "    playbook = yaml.load(open('ansible/{0}.yml','r'))\n"\
                   "except:\n"\
                   "    print 'Error loading the playbook, must be a yaml syntax problem'\n"\
                   "    sys.exit(1)\n"\
                   "else:\n"\
                   "    print 'YAML syntax looks good.'".format(self.name)
        with open("{}/test.py".format(self.get_reponame()), "w") as tfile:
            tfile.write(testdata)\

        # removing not required ansible/helloworld.yml file
        red_file = "./{}/ansible/helloworld.yml".format(self.get_reponame())
        if os.path.exists(red_file):
            os.remove(red_file)

        # changing contents of the Vagrant file
        content = ""
        with open('{}/Vagrantfile'.format(self.get_reponame()), 'r') as content_file:
            content = ''.join(content_file.readlines())
            content = content.replace("service_name = 'helloworld-ansible'",
                                      "service_name = '{0}-ansible'".format(self.name))
        content_file = open('{}/Vagrantfile'.format(self.get_reponame()), 'w')
        content_file.write(content)
        content_file.close()

        self.releasenote("ansible")

    def construct(self):
        """
        Constructing the ansible project involves
            1. Creating the project on the gerrit server.
            2. downloading the template
            3. Instantiating the template to the correct value.
            4. Creating the git repo files.
            5. Creating the nimbus
            6. Creating the roles directory.
        """
        ctx.logger.log(15, 'Constructing the ansible project')
        try:
            if self.check():
                return
            self.create_project()
            self.download_template()
            self.instantiate_template()
            self.create_repo()
            self.create_nimbus()
            roles = self.create_ansible()
            self.create_roles(roles)
        except Exception:
            raise


class Puppet(Repo):
    """
    Creates a Puppet Repo of the given name on the gerrit server and local directory.
    """
    def __init__(self, gsrvr, path, name, username, interactive):
        super(Puppet, self).__init__(gsrvr, path, name, username, interactive)
        if not self.reponame.startswith("service-"):
            self.reponame = "service-" + self.reponame
        if not self.reponame.endswith("-puppet"):
            self.reponame = self.reponame + "-puppet"

    def get_reponame(self):
        """
        get a puppet service project name of type service-<project_name>-puppet
        """
        ctx.logger.debug('Service project name is %s' % self.reponame)
        return self.reponame

    def create_nimbus(self):
        """
        Create the nimbus file .nimbus.yml for the Puppet project.
        """
        ctx.logger.log(15, 'Creating .nimbus.yml for project %s' % self.get_reponame())
        if self.interactive:
            self.chk_script = click.prompt("enter the script to check",
                                           default="./check.sh", type=str)
        nimbusdict = dict(service=str(self.name + "-puppet"),
                          version="0.0.1",
                          deploy=dict(type="puppet", manifest="manifests/site.pp"),
                          verify=dict(type="serverspec"))
        if self.chk_script:
            nimbusdict['check'] = dict(script=self.chk_script)
        if self.chk_script is not "./check.sh":
            os.remove(os.path.join(self.get_reponame(), "check.sh"))

        nimbus_name = os.path.join(".", self.get_reponame(), ".nimbus.yml")
        with open(nimbus_name, "w") as nimbus:
            nimbus.write(yaml.dump(nimbusdict, default_flow_style=False))

    def download_template(self):
        """
        Download the service-helloworld-ansible template from the gerrit server
        """
        ctx.logger.log(15, 'Downloading the service-helloworld-ansible template')
        hostname = self.gsrvr['hostname']
        port = self.gsrvr['port']
        cmd = "git clone --depth=1 "
        cmd += "ssh://{}@{}:{}/service-helloworld-puppet {}".format(self.username,
                                                                    hostname,
                                                                    port,
                                                                    self.get_reponame())
        ret_code, ret_str = service_utils.run_this(cmd)
        assert ret_code == 0, "unable to get puppet template project:" + ret_str

    def instantiate_template(self):
        """
        Instantiate the service-helloworld-project to the project. This involves
        removing some files as well updating others with the correct input project
        name.
        """
        ctx.logger.log(15, 'Instantiating service-helloworld-project to project %s'
                       % self.get_reponame())
        # cleanup any extra artifact
        shutil.rmtree(os.path.join(self.get_reponame(), ".git"))

        os.remove(os.path.join(self.get_reponame(), "doc", "README.md"))

        with open(os.path.join(self.get_reponame(), "data", "dev.yaml"), "w") as devf:
            devf.write("# this is generated file\n")
            devf.write("environment_name: dev\n")
            devf.write("manage_packages: false\n")
            devf.write("{}::site_note: | \n".format(self.name))
            devf.write("  This is an example of data that you would expect to be\n")
            devf.write("  provided per site, for example, in\n")
            devf.write("  ccs-data/sites/<site>/environments/"
                       "<env_name>/data.d/environment.yml.\n")

        with open(os.path.join(self.get_reponame(),
                               "data",
                               "service.yaml"), "w") as servf:
            sdict = {}
            banner = "service {} - service.yml".format(self.name)
            note = "This was populated from service.yml"
            sdict["{}::banner".format(self.name)] = banner
            sdict["{}::service-note".format(self.name)] = note
            servf.write(yaml.dump(yaml.dump(sdict, default_flow_style=False)))

        with open(os.path.join(self.get_reponame(), "puppet",
                               "manifests", "site.pp"), "w") as sitef:
            sitef.write("node default {\n  include ::" + self.name + "\n}")

        shutil.rmtree(os.path.join(self.get_reponame(), "puppet", "modules",
                                   "helloworld"))
        os.mkdir(os.path.join(self.get_reponame(), "puppet", "modules", self.name))
        os.mkdir(os.path.join(self.get_reponame(), "puppet", "modules", self.name,
                              "manifests"))
        with open(os.path.join(self.get_reponame(), "puppet", "modules",
                               self.name, "manifests", "init.pp"), "w") as initf:
            initf.write("#generated init.pp\n"
                        "  $banner       = 'Default banner!',\n"
                        "  $service_note = 'Default service note',\n"
                        "  $site_note    = 'Default site note',\n"
                        ") {\n"
                        "\n"
                        "}\n")

        os.mkdir(os.path.join(self.get_reponame(), "puppet", "modules", self.name,
                              "templates"))
        with open(os.path.join(self.get_reponame(), "puppet", "modules", self.name,
                               "templates", "index.html.erb"), "w") as indexf:
            indexf.write("<html>\n"
                         "<head>\n"
                         "  <title> service" + self.name + "</title>\n"
                         "</head>\n"
                         "<body>\n"
                         "  <h1><%= @banner %></h1>\n"
                         "  <p><%= @service_note %></p>"
                         "  <p><%= @site_note %></p>"
                         "</body>\n"
                         "</html>\n")

        self.cleanup_properties("helloworld-puppet")

        with open(os.path.join(self.get_reponame(), "Vagrantfile"), 'r+') as vfile:
            lns = [ln.replace("helloworld", self.name) for ln in vfile.readlines()]
            vfile.seek(0)
            vfile.write("".join(lns))
            vfile.truncate()

        self.releasenote("puppet")

    def construct(self):
        """
        Constructing the puppet project involves
            1. Creating the project on the gerrit server.
            2. downloading the template
            3. Instantiating the template to the correct value.
            4. Creating the git repo files.
            5. Creating the nimbus
        """
        ctx.logger.log(15, 'Constructing the puppet project')
        try:
            if self.check():
                return
            self.create_project()
            self.download_template()
            self.instantiate_template()
            self.create_repo()
            self.create_nimbus()
        except Exception:
            raise


class Project(Repo):
    """
    Create a Project of the given name on the gerrit server and local directory.
    """
    def __init__(self, gsrvr, path, name, username, interactive):
        super(Project, self).__init__(gsrvr, path, name, username, interactive)
        if not self.reponame.startswith("project-"):
            self.reponame = "project-" + self.reponame

    def get_reponame(self):
        """
        get project repo name of type project-<project name>.
        """
        ctx.logger.debug('Repo project name is %s' % self.reponame)
        return self.reponame

    def download_template(self):
        """
        Download the created project from the gerrit server
        """
        hostname = self.gsrvr['hostname']
        port = self.gsrvr['port']
        cmd = "git clone --depth=1 "
        cmd += "ssh://{}@{}:{}/{}".format(self.username,
                                          hostname,
                                          port,
                                          self.get_reponame())
        ret_code, ret_str = service_utils.run_this(cmd)
        assert ret_code == 0, "unable to get project template project:" + ret_str

    def instantiate_template(self):
        """
        Instantiating the project involves creating the project spec file.
        """
        ctx.logger.log(15, 'Instantiating the repo %s' % self.get_reponame())
        with open(os.path.join(".", self.get_reponame(), self.name + ".spec"),
                  "w") as specf:
            specf.write("Name:" + self.name + "\n"
                        "Version:        1.0\n"
                        "Release:        1%{?build_number}%{?branch_name}%{?dist}\n"
                        "Summary:        "+self.name + " Project\n"
                        "Group:          'Development/Tools'\n"
                        "License:        Cisco Systems\n"
                        "Source:         %{name}.tar.gz\n"
                        "%description\n\n\n"
                        "%prep\n"
                        "%setup -n src\n"
                        "%files\n\n"
                        "%install\n\n"
                        "%changelog\n\n")
        os.mkdir(os.path.join(self.get_reponame(), "src"))

    def create_nimbus(self):
        """
        Create the nimbus file .nimbus.yml for the project.
        """
        ctx.logger.log(15, 'Creating .nimbus.yml for project %s' % self.get_reponame())
        if self.interactive:
            self.chk_script = click.prompt("enter the script to check",
                                           default="/bin/true",
                                           type=str)
        nimbusdict = dict(project=str(self.name),
                          version="0.0.1",
                          package=dict(name=str(self.name),
                                       specfile=str(os.path.join(".", self.name+".spec")),
                                       src=str(os.path.join(".", "src"))))
        if self.chk_script:
            nimbusdict['check'] = dict(script=self.chk_script)

        nimbus_name = os.path.join(".", self.get_reponame(), ".nimbus.yml")
        with open(nimbus_name, "w") as nimbus:
            nimbus.write(yaml.dump(nimbusdict, default_flow_style=False))

    def construct(self):
        """
        Constructing the project involves
            1. Creating the project on the gerrit server.
            2. Downloading the template.
            3. Instantiating the template to the correct value.
            4. Creating the nimbus
        """
        ctx.logger.log(15, 'Constructing the repo project')
        try:
            if self.check():
                return
            self.create_project()
            self.download_template()
            self.instantiate_template()
            self.create_nimbus()
        except Exception:
            raise


class EmptyProject(Repo):
    """
    Create an Empty project of the given name on the gerrit server and local directory.
    """
    def __init__(self, gsrvr, path, name, username, interactive):
        super(EmptyProject, self).__init__(gsrvr, path, name, username, interactive)

    def get_reponame(self):
        """
        get an project name of type <project name>
        """
        return self.reponame

    def download_template(self):
        """
        Download the created project from the gerrit server
        """
        ctx.logger.log(15, 'Downloading project %s from gerrit' % self.get_reponame())
        hostname = self.gsrvr['hostname']
        port = self.gsrvr['port']
        cmd = "git clone --depth=1 ssh://{}@{}:{}/{}".format(self.username,
                                                             hostname,
                                                             port,
                                                             self.get_reponame())
        ret_code, ret_str = service_utils.run_this(cmd)
        assert ret_code == 0, "unable to get puppet template project:" + ret_str

    def instantiate_template(self):
        """
        This is a stubbed  function
        """
        pass

    def create_nimbus(self):
        """
        This is a stubbed  function
        """
        pass

    def construct(self):
        """
        Constructing an empty  project involves
            1. Creating the project on the gerrit server.
            2. Downloading the template.
            3. Instantiating the template to the correct value.
            4. Creating the nimbus
        """
        ctx.logger.log(15, 'Constructing the empty project')
        try:
            if self.check():
                return
            self.create_project()
            self.download_template()
            self.instantiate_template()
            self.create_nimbus()
        except Exception:
            raise

#
# This is the driver stub
#
if __name__ == '__main__':
    from servicelab.stack import Context
    Repo.builder("Puppet", Context().get_gerrit_staging_server(), "gamma").construct()
    Repo.builder("Ansible", Context().get_gerrit_staging_server(), "gamma").construct()
    Repo.builder("Project", Context().get_gerrit_staging_server(), "gamma").construct()
    Repo.builder("EmptyProject", Context().get_gerrit_staging_server(),
                 "gamma").construct()
