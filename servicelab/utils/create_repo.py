import os
import shutil

import string
import yaml
import click
import logging

from abc import ABCMeta, abstractmethod
from servicelab.utils import service_utils
from servicelab.utils import ccsdata_utils
from servicelab.utils import yaml_utils
from servicelab.stack import Context

logger = logging.getLogger('click_application')
logging.basicConfig()


class Repo(object):
    __metaclass__ = ABCMeta

    def construct(type, ctx, name):
        if type is "Ansible":
            return Ansible(ctx, name)
        if type is "Puppet":
            return Puppet(ctx, name)
        if type is "Project":
            return Project(ctx, name)
        if type is "EmptyProject":
            return EmptyProject(ctx, name)
        assert 0, "unable to construct the project of type: " + type
    construct = staticmethod(construct)

    def __init__(self, ctx, name):
        self.ctx = ctx
        self.name = name

    def get_usr(self):
        cmd = "git config user.name"
        retCode, username = service_utils.run_this(cmd)
        if retCode == 1:
            click.echo("Unable to fetch user name from git. Please provide")
            username = click.prompt("username", type=str, default="")
        username = string.strip(username)
        assert username, "unable to proceed as username is not available"
        return username

    def get_reponame(self):
        repo_type = type(self).__name__
        if repo_type is "Ansible":
            return "service-" + self.name + "-ansible"
        if repo_type is "Puppet":
            return "service-" + self.name + "-puppet"
        if repo_type is "Project":
            return "project-" + self.name
        if repo_type is "EmptyProject":
            return self.name
        assert type(self).__name__ != "Repo", "no repo name available for i" + repo_type

    def create_project(self):
        hostname = self.ctx.get_gerrit_server()['hostname']
        port = self.ctx.get_gerrit_server()['port']
        cmd = "ssh -p {} {} gerrit create-project {}".format(
                                port, hostname, self.get_reponame())

        retCode, retStr = service_utils.run_this(cmd)
        return (retCode, retStr)

    def cleanup_properties(self, name):
        pdict = {}
        fpath = os.path.join(self.get_reponame(), "serverspec", "properties.yml")
        with open(self.get_reponame() + "/serverspec/properties.yml") as f:
            pdict = yaml.load(f)
            pdict[self.name] = pdict[name]
            del pdict[name]
        os.remove(fpath)

        fpath = os.path.join(self.get_reponame(), "serverspec", "properties.yaml")
        with open(fpath, "w") as f:
            f.write(yaml.dump(pdict, default_flow_style=False))

    def create_repo(self, username):
        # please see https://code.google.com/p/gerrit/issues/detail?id=1013
        # for -no-checkout option.
        hostname = ctx.get_gerrit_server()['hostname']
        port = ctx.get_gerrit_server()['port']
        cmd = "git clone --no-checkout --depth=1 ssh://{}@{}:{}/{} /tmp/{}".format(
                      username, hostname, port,
                      self.get_reponame(), self.get_reponame())
        retCode, retStr = service_utils.run_this(cmd)
        assert retCode == 0, "unable to clone the project:" + retStr

        os.rename("/tmp/" + self.get_reponame() + "/.git", self.get_reponame() + "/.git")
        shutil.rmtree("/tmp/" + self.get_reponame())

        # now get the template repo
        return retCode

    @abstractmethod
    def download_template(self):
        return

    @abstractmethod
    def create_nimbus():
        return


class Ansible(Repo):
    def __init__(self, ctx, name):
        super(Ansible, self).__init__(ctx, name)

    def create_nimbus(self):
        chk_script = click.prompt(
            "enter the script to check", default="", type=str)
        nimbusdict = dict(service=self.name + "-ansible", version="0.0.1",
                          deploy=dict(type="ansible", playbook=self.name + ".yaml"),
                          verify=dict(type="serverspec"))
        if chk_script:
            nimbusdict['check'] = dict(script=chk_script)

        n = os.path.join(".", self.get_reponame(), ".nimbus.yaml")
        with open(n, "w") as nimbus:
            nimbus.write(yaml.dump(nimbusdict, default_flow_style=False))

        os.remove(os.path.join(".", self.get_reponame(), ".nimbus.yml"))
        os.link(n, os.path.join(".", self.get_reponame(), ".nimbus.yml"))

    def create_ansible(self, user):
        ansibledir = "./{}/ansible".format(self.get_reponame())
        if not os.path.isdir(ansibledir):
            os.mydir(ansibledir)

        play_roles = []
        while True:
            role = click.prompt("role", default="", type=str)
            if not role:
                break
            play_roles.append(role)

        playdict = dict(hosts="{}-ansible".format(self.name),
                        remote_user=user, roles=play_roles)

        playfile = "./{}/ansible/{}".format(self.get_reponame(),
                                            self.name + ".yaml")
        with open(playfile, "w") as playbook:
            playbook.write(yaml.dump(playdict, default_flow_style=False))

        os.link(playfile, "./{}/ansible/{}".format(
            self.get_reponame(), self.name + ".yml"))

        return play_roles

    def create_roles(self, roles):
        path = os.path.join(self.get_reponame(), "ansible", "roles")
        if not os.path.isdir(path):
            os.mkdir(path)
        for role in roles:
            os.mkdir(os.path.join(path, role))
            os.mkdir(os.path.join(path, role, "defaults"))
            os.mkdir(os.path.join(path, role, "tasks"))
            os.mkdir(os.path.join(path, role, "templates"))

    def download_template(self, username):
        hostname = self.ctx.get_gerrit_server()['hostname']
        port = self.ctx.get_gerrit_server()['port']
        cmd = "git clone --depth=1 ssh://{}@{}:{}/service-helloworld-ansible {}".format(
                     username, hostname, port, self.get_reponame())
        retCode, retStr = service_utils.run_this(cmd)
        assert retCode == 0, "unable to get ansible template project:" + retStr

    def instantiate_template(self):
        shutil.rmtree(os.path.join(self.get_reponame(), ".git"))
        self.cleanup_properties("helloworld-test")

        os.remove(os.path.join(self.get_reponame(), "doc", "README.md"))
        os.remove(os.path.join(self.get_reponame(), "data", "dev.yaml"))
        os.remove(os.path.join(self.get_reponame(), "data", "service.yaml"))

        with open(os.path.join(self.get_reponame(), "data", "dev.yaml"), "w") as f:
            f.write("# this is generated file")

        with open(os.path.join(self.get_reponame(), "data", "service.yaml"), "w") as f:
            f.write("# this is a generated file")

        shutil.rmtree(os.path.join(self.get_reponame(), "ansible",
                                   "roles", "helloworld-test"))

    def construct(self):
        try:
            user = self.get_usr()
            self.create_project()
            self.download_template(user)
            self.instantiate_template()
            self.create_repo(user)
            self.create_nimbus()
            roles = self.create_ansible(user)
            self.create_roles(roles)
        except Exception as e:
            raise


class Puppet(Repo):
    def __init__(self, ctx, name):
        super(Puppet, self).__init__(ctx, name)

    def create_nimbus(self):
        chk_script = click.prompt(
            "enter the script to check", default="./check.sh", type=str)
        nimbusdict = dict(service=self.name + "-puppet",
                          version="0.0.1",
                          deploy=dict(type="puppet", manifest="manifests/site.pp"),
                          verify=dict(type="serverspec"))
        if chk_script:
            nimbusdict['check'] = dict(script=chk_script)
        if chk_script is not "./check.sh":
            os.remove(os.path.join(self.get_reponame(), "check.sh"))

        n = os.path.join(".", self.get_reponame(), ".nimbus.yaml")
        with open(n, "w") as nimbus:
            nimbus.write(yaml.dump(nimbusdict, default_flow_style=False))

        os.remove(os.path.join(".", self.get_reponame(), ".nimbus.yml"))
        os.link(n, os.path.join(".", self.get_reponame(), ".nimbus.yml"))

    def download_template(self, username):
        hostname = self.ctx.get_gerrit_server()['hostname']
        port = self.ctx.get_gerrit_server()['port']
        cmd = "git clone --depth=1 ssh://{}@{}:{}/service-helloworld-puppet {}".format(
                     username, hostname, port, self.get_reponame())
        retCode, retStr = service_utils.run_this(cmd)
        assert retCode == 0, "unable to get puppet template project:" + retStr

    def instantiate_template(self):
        # cleanup any extra artifact
        shutil.rmtree(os.path.join(self.get_reponame(), ".git"))

        os.remove(os.path.join(self.get_reponame(), "doc", "README.md"))

        os.remove(os.path.join(self.get_reponame(), "data", "dev.yaml"))
        with open(os.path.join(self.get_reponame(), "data", "dev.yaml"), "w") as f:
            f.write("# this is generated file\n")
            f.write("environment_name: dev\n")
            f.write("manage_packages: false\n")
            f.write("{}::site_note: | \n".format(self.name))
            f.write("  This is an example of data that you would expect to be\n")
            f.write("  provided per site, for example, in\n")
            f.write("  ccs-data/sites/<site>/environments/"
                    "<env_name>/data.d/environment.yaml.\n")

        os.remove(os.path.join(self.get_reponame(), "data", "service.yaml"))
        with open(os.path.join(self.get_reponame(), "data", "service.yaml"), "w") as f:
            sdict = {}
            banner = "service {} - service.yaml".format(self.name)
            note = "This was populated from service.yaml"
            sdict["{}::banner".format(self.name)] = banner
            sdict["{}::service-note".format(self.name)] = note
            f.write(yaml.dump(yaml.dump(sdict, default_flow_style=False)))

        with open(os.path.join(self.get_reponame(), "puppet",
                  "manifests", "site.pp"), "w") as f:
            f.write("node default {\n  include ::" + self.name + "\n}")

        shutil.rmtree(os.path.join(self.get_reponame(), "puppet", "modules",
                                   "helloworld"))
        os.mkdir(os.path.join(self.get_reponame(), "puppet", "modules", self.name))
        os.mkdir(os.path.join(self.get_reponame(), "puppet", "modules", self.name,
                              "manifests"))
        with open(os.path.join(self.get_reponame(), "puppet", "modules",
                  self.name, "manifests", "init.pp"), "w") as f:
            f.write("#generated init.pp\n"
                    "  $banner       = 'Default banner!',\n"
                    "  $service_note = 'Default service note',\n"
                    "  $site_note    = 'Default site note',\n"
                    ") {\n"
                    "\n"
                    "}\n")

        os.mkdir(os.path.join(self.get_reponame(), "puppet", "modules", self.name,
                              "templates"))
        with open(os.path.join(self.get_reponame(), "puppet", "modules", self.name,
                               "templates", "index.html.erb"), "w") as f:
            f.write("<html>\n"
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

        with open(os.path.join(self.get_reponame(), "Vagrantfile"), 'r+') as f:
            l = [l.replace("helloworld", self.name) for l in f.readlines()]
            f.seek(0)
            f.write("".join(l))
            f.truncate()

    def construct(self):
        try:
            user = self.get_usr()
            self.create_project()
            self.download_template(user)
            self.instantiate_template()
            self.create_repo(user)
            self.create_nimbus()
        except Exception as e:
            raise


class Project(Repo):
    def __init__(self, ctx, name):
        super(Project, self).__init__(ctx, name)

    def download_template(self, username):
        hostname = self.ctx.get_gerrit_server()['hostname']
        port = self.ctx.get_gerrit_server()['port']
        cmd = "git clone --depth=1 ssh://{}@{}:{}/{}".format(
                     username, hostname, port, self.get_reponame())
        retCode, retStr = service_utils.run_this(cmd)
        assert retCode == 0, "unable to get puppet template project:" + retStr

    def instantiate_template(self):
        with open(self.name + ".spec", "w") as f:
            f.write(
                    "Name:" + self.name + "\n"
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
        chk_script = click.prompt(
            "enter the script to check", default="/bin/true", type=str)
        nimbusdict = dict(project=self.name,
                          version="0.0.1",
                          package=dict(name=self.name,
                                       specfile=os.path.join(".", self.name+".spec"),
                                       src=os.path.join(".", "src")))
        if chk_script:
            nimbusdict['check'] = dict(script=chk_script)

        n = os.path.join(".", self.get_reponame(), ".nimbus.yaml")
        with open(n, "w") as nimbus:
            nimbus.write(yaml.dump(nimbusdict, default_flow_style=False))
        os.link(n, os.path.join(".", self.get_reponame(), ".nimbus.yml"))

    def construct(self):
        try:
            user = self.get_usr()
            self.create_project()
            self.download_template(user)
            self.instantiate_template()
            self.create_nimbus()
        except Exception as e:
            print "exception"
            raise


class EmptyProject(Repo):
    def __init__(self, ctx, name):
        super(EmptyProject, self).__init__(ctx, name)

    def download_template(self, username):
        import pdb
        pdb.set_trace()
        hostname = self.ctx.get_gerrit_server()['hostname']
        port = self.ctx.get_gerrit_server()['port']
        cmd = "git clone --depth=1 ssh://{}@{}:{}/{}".format(
                     username, hostname, port, self.get_reponame())
        retCode, retStr = service_utils.run_this(cmd)
        assert retCode == 0, "unable to get puppet template project:" + retStr

    def instantiate_template(self):
        pass

    def create_nimbus(self):
        pass

    def construct(self):
        try:
            user = self.get_usr()
            self.create_project()
            self.download_template(user)
            self.instantiate_template()
            self.create_nimbus()
        except Exception as e:
            print "exception"
            raise

#
# This is the driver stub
#
if __name__ == '__main__':
    ctx = Context()
    ctx.debug = True
#   a = Repo.construct("Puppet", ctx, "gamma")
#   a = Repo.construct("Ansible", ctx, "gamma")
    a = Repo.construct("EmptyProject", ctx, "gamma")
    a.construct()
    print "completed"
