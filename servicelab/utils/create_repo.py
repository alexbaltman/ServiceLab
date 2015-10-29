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
import logging

from abc import ABCMeta, abstractmethod
from servicelab.utils import service_utils
from servicelab.utils import helper_utils

LOGGER = logging.getLogger('click_application')
logging.basicConfig()


class Repo(object):
    """
    ABC for creating repos of type Ansible, Puppet, Project, EmptyProject
    """
    __metaclass__ = ABCMeta

    def builder(rtype, gsrvr, path, name, interactive):
        """
        Static method Instantiates Concreate classes of type Repo.
        """
        if rtype is "Ansible":
            return Ansible(gsrvr, path, name, interactive)
        if rtype is "Puppet":
            return Puppet(gsrvr, path, name, interactive)
        if rtype is "Project":
            return Project(gsrvr, path, name, interactive)
        if rtype is "EmptyProject":
            return EmptyProject(gsrvr, path, name, interactive)
        assert 0, "unable to construct the project of type: " + rtype
    builder = staticmethod(builder)

    def __init__(self, gsrvr, path, name, interactive):
        self.gsrvr = gsrvr
        self.ctx_path = path
        self.name = name
        self.chk_script = "./check.sh"
        self.interactive = interactive

    def get_reponame(self):
        """
        Get the name of the repo

        Returns:
            str: The gerrit user name

        Raises:
            Raises Exception if type is not Ansible, Puppet, Project or
            EmptyProject.
        """
        assert type(self).__name__ != "Repo", "no repo name available "

    def create_project(self):
        """
        Create the project on the gerrit server.

        Returns:
        (
            int : return code
            str : output string if any.
        )
        """
        hostname = self.gsrvr['hostname']
        port = self.gsrvr['port']
        cmd = "ssh -p {} {} gerrit create-project {}".format(port,
                                                             hostname,
                                                             self.get_reponame())

        ret_code, ret_str = service_utils.run_this(cmd)
        return (ret_code, ret_str)

    def cleanup_properties(self, name):
        """
        Clean up any files from the template directories
        """
        pdict = {}
        fpath = os.path.join(self.get_reponame(), "serverspec", "properties.yml")
        with open(self.get_reponame() + "/serverspec/properties.yml") as ydata:
            pdict = yaml.load(ydata)
            pdict[self.name] = pdict[name]
            del pdict[name]
        os.remove(fpath)

        fpath = os.path.join(self.get_reponame(), "serverspec", "properties.yaml")
        with open(fpath, "w") as yamlf:
            yamlf.write(yaml.dump(pdict, default_flow_style=False))

    def create_repo(self, username):
        """
        create a repo on the local machine. Returns -1 if the repo creation fails.
        Returns:
        (
            int : return code
            str : output string if any.
        )
        """
        hostname = self.gsrvr['hostname']
        port = self.gsrvr['port']
        # please see https://code.google.com/p/gerrit/issues/detail?id=1013
        # for -no-checkout option.
        cmd = "git clone --no-checkout --depth=1 "
        cmd += "ssh://{}@{}:{}/{} /tmp/{}".format(username,
                                                  hostname,
                                                  port,
                                                  self.get_reponame(),
                                                  self.get_reponame())
        ret_code, ret_str = service_utils.run_this(cmd)
        assert ret_code == 0, "unable to clone the project:" + ret_str

        os.rename("/tmp/" + self.get_reponame() + "/.git", self.get_reponame() + "/.git")
        shutil.rmtree("/tmp/" + self.get_reponame())

        # now get the template repo
        return ret_code

    @abstractmethod
    def download_template(self, name):
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
    def __init__(self, gsrvr, path, name, interactive):
        super(Ansible, self).__init__(gsrvr, path, name, interactive)
        self.play_roles = []

    def get_reponame(self):
        """
        get ansible projcet of type service-<project name>-ansible
        """
        name = self.name
        if not name.startswith("service-"):
            name = "service-" + name
        if not name.endswith("-ansible"):
            name = name + "-ansible"
        return name

    def create_nimbus(self):
        """
        create the nimbus file for teh Ansible project. By default .nimbus.yaml
        is created. For downward compatability we create .nimbus.yml as a link to
        .nimbus.yaml.
        """
        if self.interactive:
            self.chk_script = click.prompt("enter the script to check",
                                           default="./check.sh", type=str)

        nimbusdict = dict(service=str(self.name + "-ansible"), version="0.0.1",
                          deploy=dict(type="ansible", playbook=str(self.name + ".yaml")),
                          verify=dict(type="serverspec"))
        if self.chk_script:
            nimbusdict['check'] = dict(script=self.chk_script)

        nimbus_name = os.path.join(".", self.get_reponame(), ".nimbus.yaml")
        with open(nimbus_name, "w") as nimbus:
            nimbus.write(yaml.dump(nimbusdict, default_flow_style=False))

        os.remove(os.path.join(".", self.get_reponame(), ".nimbus.yml"))
        os.link(nimbus_name, os.path.join(".", self.get_reponame(), ".nimbus.yml"))

    def create_ansible(self, user):
        """
        Create the ansible directory for the ansible project.
        """
        def _add_roles():
            """
            add the roles. If command is invoked with interactive flag, then user can
            enter the various roles.
            """
            if not self.interactive:
                self.play_roles.append(self.name)
                return

            if not self.play_roles:
                while True:
                    role = click.prompt("role", default=self.name, type=str)
                    if not role:
                        break
                    if role in self.play_roles:
                        lst = [astr.encode('ascii') for astr in self.play_roles]
                        click.echo(" entered roles:" + str(lst))
                        if click.confirm(' do you want to continue?'):
                            continue
                        break
                    self.play_roles.append(role)

        ansibledir = "./{}/ansible".format(self.get_reponame())
        if not os.path.isdir(ansibledir):
            os.mkdir(ansibledir)

        def _write_playfile(playdict):
            """
            write the ansible project yaml file.
            """
            playfile = "./{}/ansible/{}".format(self.get_reponame(),
                                                self.name + ".yaml")
            with open(playfile, "w") as playbook:
                playbook.write(yaml.dump(playdict, default_flow_style=False))

            os.link(playfile, "./{}/ansible/{}".format(
                self.get_reponame(), self.name + ".yml"))

        _add_roles()
        playdict = dict(hosts="{}-ansible".format(self.name),
                        remote_user=user, roles=self.play_roles)
        _write_playfile(playdict)
        return self.play_roles

    def create_roles(self, roles):
        """
        Create all the roles in the ansible directory
        """
        path = os.path.join(self.get_reponame(), "ansible", "roles")
        if not os.path.isdir(path):
            os.mkdir(path)
        for role in roles:
            os.mkdir(os.path.join(path, role))
            os.mkdir(os.path.join(path, role, "defaults"))
            os.mkdir(os.path.join(path, role, "tasks"))
            os.mkdir(os.path.join(path, role, "templates"))

    def download_template(self, username):
        """
        Download the service-helloworld-ansible template from the gerrit server
        """
        hostname = self.gsrvr['hostname']
        port = self.gsrvr['port']
        cmd = "git clone --depth=1 "
        cmd += "ssh://{}@{}:{}/service-helloworld-ansible {}".format(username,
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
        shutil.rmtree(os.path.join(self.get_reponame(), ".git"))
        self.cleanup_properties("helloworld-test")

        os.remove(os.path.join(self.get_reponame(), "doc", "README.md"))
        os.remove(os.path.join(self.get_reponame(), "data", "dev.yaml"))
        os.remove(os.path.join(self.get_reponame(), "data", "service.yaml"))

        with open(os.path.join(self.get_reponame(), "data", "dev.yaml"), "w") as devfile:
            devfile.write("# this is generated file")

        with open(os.path.join(self.get_reponame(),
                               "data",
                               "service.yaml"), "w") as sfile:
            sfile.write("# this is a generated file")

        shutil.rmtree(os.path.join(self.get_reponame(), "ansible",
                                   "roles", "helloworld-test"))

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
        try:
            user = helper_utils.get_username(self.ctx_path)
            self.create_project()
            self.download_template(user)
            self.instantiate_template()
            self.create_repo(user)
            self.create_nimbus()
            roles = self.create_ansible(user)
            self.create_roles(roles)
        except Exception:
            raise


class Puppet(Repo):
    """
    Creates a Puppet Repo of the given name on the gerrit server and local directory.
    """
    def __init__(self, gsrvr, path, name, interactive):
        super(Puppet, self).__init__(gsrvr, path, name, interactive)

    def get_reponame(self):
        """
        get a puppet service project name of type service-<project_name>-puppet
        """
        name = self.name
        if not name.startswith("service-"):
            name = "service-" + name
        if not name.endswith("-puppet"):
            name = name + "-puppet"
        return name

    def create_nimbus(self):
        """
        Create the nimbus file for the Puppet project. By default .nimbus.yaml
        is created. For downward compatability we create .nimbus.yml as a link to
        .nimbus.yaml.
        """
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

        nimbus_name = os.path.join(".", self.get_reponame(), ".nimbus.yaml")
        with open(nimbus_name, "w") as nimbus:
            nimbus.write(yaml.dump(nimbusdict, default_flow_style=False))

        os.remove(os.path.join(".", self.get_reponame(), ".nimbus.yml"))
        os.link(nimbus_name, os.path.join(".", self.get_reponame(), ".nimbus.yml"))

    def download_template(self, username):
        """
        Download the service-helloworld-ansible template from the gerrit server
        """
        hostname = self.gsrvr['hostname']
        port = self.gsrvr['port']
        cmd = "git clone --depth=1 "
        cmd += "ssh://{}@{}:{}/service-helloworld-puppet {}".format(username,
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
        # cleanup any extra artifact
        shutil.rmtree(os.path.join(self.get_reponame(), ".git"))

        os.remove(os.path.join(self.get_reponame(), "doc", "README.md"))

        os.remove(os.path.join(self.get_reponame(), "data", "dev.yaml"))
        with open(os.path.join(self.get_reponame(), "data", "dev.yaml"), "w") as devf:
            devf.write("# this is generated file\n")
            devf.write("environment_name: dev\n")
            devf.write("manage_packages: false\n")
            devf.write("{}::site_note: | \n".format(self.name))
            devf.write("  This is an example of data that you would expect to be\n")
            devf.write("  provided per site, for example, in\n")
            devf.write("  ccs-data/sites/<site>/environments/"
                       "<env_name>/data.d/environment.yaml.\n")

        os.remove(os.path.join(self.get_reponame(), "data", "service.yaml"))
        with open(os.path.join(self.get_reponame(),
                               "data",
                               "service.yaml"), "w") as servf:
            sdict = {}
            banner = "service {} - service.yaml".format(self.name)
            note = "This was populated from service.yaml"
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

        with open(os.path.join(self.get_reponame(), "Vagrantfile"), 'r+') as vagf:
            lns = [ln.replace("helloworld", self.name) for ln in vagf.readlines()]
            vagf.seek(0)
            vagf.write("".join(lns))
            vagf.truncate()

    def construct(self):
        """
        Constructing the puppet project involves
            1. Creating the project on the gerrit server.
            2. downloading the template
            3. Instantiating the template to the correct value.
            4. Creating the git repo files.
            5. Creating the nimbus
        """
        try:
            user = helper_utils.get_username(self.ctx_path)
            self.create_project()
            self.download_template(user)
            self.instantiate_template()
            self.create_repo(user)
            self.create_nimbus()
        except Exception:
            raise


class Project(Repo):
    """
    Create a Project of the given name on the gerrit server and local directory.
    """
    def __init__(self, gsrvr, path, name, interactive):
        super(Project, self).__init__(gsrvr, path, name, interactive)

    def get_reponame(self):
        """
        get project repo name of type project-<project name>.
        """
        name = self.name
        if not name.startswith("project-"):
            name = "project-" + name
        return name

    def download_template(self, username):
        """
        Download the created project from the gerrit server
        """
        hostname = self.gsrvr['hostname']
        port = self.gsrvr['port']
        cmd = "git clone --depth=1 "
        cmd += "ssh://{}@{}:{}/{}".format(username,
                                          hostname,
                                          port,
                                          self.get_reponame())
        ret_code, ret_str = service_utils.run_this(cmd)
        assert ret_code == 0, "unable to get project template project:" + ret_str

    def instantiate_template(self):
        """
        Instantiating the project involves creating the project spec file.
        """
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
        Create the nimbus file for the project. By default .nimbus.yaml
        is created. For downward compatability we create .nimbus.yml as a link to
        .nimbus.yaml.
        """
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

        nimbus_name = os.path.join(".", self.get_reponame(), ".nimbus.yaml")
        with open(nimbus_name, "w") as nimbus:
            nimbus.write(yaml.dump(nimbusdict, default_flow_style=False))

        ymlfile = os.path.join(".", self.get_reponame(), ".nimbus.yml")
        if os.path.exists(ymlfile):
            os.unlink(ymlfile)
        os.link(nimbus_name, os.path.join(".", self.get_reponame(), ".nimbus.yml"))

    def construct(self):
        """
        Constructing the project involves
            1. Creating the project on the gerrit server.
            2. Downloading the template.
            3. Instantiating the template to the correct value.
            4. Creating the nimbus
        """
        try:
            user = helper_utils.get_username(self.ctx_path)
            self.create_project()
            self.download_template(user)
            self.instantiate_template()
            self.create_nimbus()
        except Exception:
            raise


class EmptyProject(Repo):
    """
    Create an Empty project of the given name on the gerrit server and local directory.
    """
    def __init__(self, gsrvr, path, name, interactive):
        super(EmptyProject, self).__init__(gsrvr, path, name, interactive)

    def get_reponame(self):
        """
        get an project name of type <project name>
        """
        return self.name

    def download_template(self, username):
        """
        Download the created project from the gerrit server
        """
        hostname = self.gsrvr['hostname']
        port = self.gsrvr['port']
        cmd = "git clone --depth=1 ssh://{}@{}:{}/{}".format(username,
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
        try:
            user = helper_utils.get_username(self.ctx_path)
            self.create_project()
            self.download_template(user)
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
