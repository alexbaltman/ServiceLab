"""
gerrit functions
"""
import os
import click
import datetime

import logger_utils
import service_utils

from gerrit import filters
from gerrit import reviews

from servicelab import settings

slab_logger = logger_utils.setup_logger(settings.verbosity, 'stack.utils.gerrit')


class Format(object):
    """Format class to format input strings. It consists various utility methods.

       Attributes:
          bld   - for bold
          uline - for underline
          blue  - makes the text blue
          green - makes the text green
          warn  - makes the text red
          fail  - makes the text red
    """
    bld = 1
    uline = 1 << 1
    blue = 1 << 2
    green = 1 << 3
    warn = 1 << 4
    fail = 1 << 5
    endl = "\n"

    def __init__(self):
        """ Constructor for the Format class"""
        pass

    @staticmethod
    def time(sec):
        """ Static method returns current local  date time string for given
            input seconds.

        Args:
            sec           -- number of seconds
        """
        slab_logger.debug('Determining current date / time')
        dat = datetime.datetime.fromtimestamp(sec)
        return dat.strftime("%c")

    @staticmethod
    def message(width, pad, pflag, pstr):
        """ Static method returns a formatted pstr string of size width, left padded
            with pad spaces. The input pstr string can be formatted as per the
            various Format flags.

        Args:
            width            -- width of the  formatted string
            pad              -- defines he indent of the string
            plag             -- The flag can be  0 or any combination of
                                    Format.bld   - for bold
                                    Format.uline - for underline
                                    Format.blue  - makes the text blue
                                    Format.green - makes the text green
                                    Format.warn  - makes the text red
                                    Format.fail  - makes the text red
            pstr              -- Input text string
        """
        slab_logger.debug('Formatting message')
        prompt_format = "{}"
        if width:
            prompt_format = "{:%d}" % (width)

        if pad:
            prompt_format = " "*pad + prompt_format

        kwargs = {}
        if pflag & Format.bld:
            kwargs["bold"] = True

        if pflag & Format.uline:
            kwargs["underline"] = True

        if pflag & Format.green:
            kwargs["fg"] = "green"

        if pflag & Format.warn:
            kwargs["fg"] = "red"

        if pflag & Format.fail:
            kwargs["fg"] = "red"

        if kwargs:
            pstr = click.style(pstr, **kwargs)

        return prompt_format.format(pstr)


class GerritFnException(Exception):
    """ Gerrit function exception."""
    pass


class GerritFns(object):
    """Gerrit class for performing various gerrit functions of the gerrit server.
       The Server itself is defined in the Context class"""

    # Valid Gerrit review states.
    status = ["open", "reviewed", "submitted", "closed", "merged", "abandoned"]

    """ Flag for instrumenting code for unit testing."""
    instrument_code = False

    def __init__(self, user, project, ctx):
        """ Constructor for GerritFns Class

            Args:
                self            -- self instance
                user            -- gerrit username
                project         -- gerrit project name
                ctx             -- Context
        """
        self.user = user
        self.prjname = project
        self.hostname = ctx.get_gerrit_server()['hostname']
        self.port = ctx.get_gerrit_server()['port']

    def getkey(self):
        """ get the ssh key-credential of the user."""
        slab_logger.debug('Extracting ssh key for %s' % self.user)
        key = os.path.expanduser(os.path.join("~" + self.user,
                                              ".ssh",
                                              "id_rsa"))
        if not os.access(key, os.F_OK | os.R_OK):
            raise GerritFnException("unable to access "
                                    "user {} ssh key".format(self.user))
        return key

    def change_review(self, number, rev_number, verify_number, msg=""):
        """ Change the review and verify numbers for a gerrit review number

            Args:
                number                  -- Gerrit review
                rev_number              -- Review number can be anything
                                           from -2 to 2
                verify_number           -- Verification number can be anything from
                                           from -1 to 1
                msg                     -- Commit message

            Raises:
               GerritFnException        -- If Unable to find the gerrit review number.
         """
        slab_logger.debug('Changing review for gerrit review %i' % number)
        project = filters.OrFilter()
        project.add_items('project', [self.prjname])
        other = filters.Items()
        other.add_items('change', number)
        key = self.getkey()
        query = reviews.Query(self.hostname, self.port, self.user, key)

        for review in query.filter(project, other):
            revision = review["currentPatchSet"]["revision"]
            rev = reviews.Review(revision, self.hostname, self.port, self.user, key)
            rev.review(rev_number)
            rev.verify(verify_number)
            if not msg:
                msg = click.prompt(Format.message(0, 0, Format.bld,
                                                  "Commit Message for Review? "),
                                   default="")
            ret = rev.commit(msg)
            if not ret:
                raise GerritFnException("Unable to change the review and "
                                        "verification number on " +
                                        number)
            return
        raise GerritFnException("Unable to find the review " + number)

    def code_state(self, number, state, msg=""):
        """ Change state of the Gerrit review number to the given state and message.

            Args:
                number                  -- Review number can be anything from -2 to 2
                state                   -- The valid allowed state changes can be abondon
                                           restore or delete.
                msg                     -- Commit message

            Raises:
               GerritFnException        -- If Unable to find the gerrit review number.
         """
        slab_logger.debug('Changing the state of gerrit review to %i' % number)
        project = filters.OrFilter()
        project.add_items('project', [self.prjname])
        other = filters.Items()
        other.add_items('change', number)
        key = self.getkey()
        query = reviews.Query(self.hostname, self.port, self.user, key)
        if state not in ['abandon', 'restore', 'delete']:
            raise GerritFnException("unknown state for change " + number)

        for review in query.filter(project, other):
            revision = review["currentPatchSet"]["revision"]
            rev = reviews.Review(revision, self.hostname, self.port, self.user, key)
            rev.status(state)
            if not msg:
                msg = click.prompt(Format.message(0, 0, Format.bld, "Message? "),
                                   default="")
            ret = rev.commit(msg)
            if not ret:
                raise GerritFnException("Unable to abondon changes on " + number)
            return
        raise GerritFnException("Unable to find the review " + number)

    def code_review(self, number):
        """ Code review the given gerrit number

            Args:
                number                  -- Gerrit code review number

            Raises:
               GerritFnException        -- If Unable to find the gerrit review number.
        """
        slab_logger.debug('Pulling gerrit review %i for code review' % number)
        project = filters.OrFilter()
        project.add_items('project', [self.prjname])
        other = filters.Items()
        other.add_items('change', number)
        key = self.getkey()
        query = reviews.Query(self.hostname, self.port, self.user, key)

        for review in query.filter(project, other):
            if 'type' in review.keys() and review['type'] == 'error':
                raise GerritFnException(review['message'])

            ref = review["currentPatchSet"]["ref"]
            tdir = "/tmp/{}".format(self.prjname)
            user = self.user
            host = self.hostname + ":" + str(self.port)

            # now do a git clone without checkout
            cmd = "rm -rf {};".format(tdir)
            pkey = "GIT_SSH_COMMAND=\"ssh -i {}\"".format(key)
            cmd += "{} git clone --no-checkout ssh://{}@{}/{} {};".format(pkey,
                                                                          self.user,
                                                                          host,
                                                                          self.prjname,
                                                                          tdir)
            cmd += "cd {};".format(tdir)
            cmd += "{} git fetch ssh://{}@{}/{} {}".format(pkey,
                                                           user,
                                                           host,
                                                           self.prjname,
                                                           ref)
            cmd += " && {} git format-patch -1 --stdout FETCH_HEAD".format(pkey)
            # now run the command and get output
            ret_code, ret_str = service_utils.run_this(cmd)
            if not ret_code:
                click.echo(ret_str)
            else:
                raise GerritFnException(ret_str)

    def repo_list(self):
        """ Generate list of all repos on gerrit server."""
        slab_logger.debug('Generating list of all repos on gerrit')
        key = self.getkey()
        cmd = "ssh -i {} -p {} {}@{} gerrit ls-projects".format(key,
                                                                self.port,
                                                                self.user,
                                                                self.hostname)

        # now run the command and get output
        ret_code, ret_str = service_utils.run_this(cmd)
        if ret_code:
            raise GerritFnException(ret_str)
        return ret_str.split()

    def print_list(self):
        """ Prints the generated  list of all repos on gerrit server."""
        click.echo("\n".join(self.repo_list()))

    def print_gerrit(self, pformat="", number=None, owner="", reviewer="", status=""):
        """ Print the complete review information for a review numeber and given owner
            or reviewer with status. The print detail can be summary or detailed.

            Args:
                pformat               -- The format can be detail or summary. The default
                                         is detail.
                number                -- Review number. If no review are supplied then
                                         all the reviews of a particualr owner, reviwer
                                         or status are printed.
                owner                 -- The review owner
                reviewer              -- The reviewer.
                status                -- Any valid gerrit status.
        """
        slab_logger.debug('Extracting details of gerrit review(s)')
        other = filters.Items()
        if number:
            other.add_items('change', number)
        if owner:
            other.add_items('owner', owner)
        if reviewer:
            other.add_items('reviewer', reviewer)
        if self.prjname:
            other.add_items('project', self.prjname)

        if status:
            if status in GerritFns.status:
                other.add_items("status", status)
            else:
                raise ValueError("Invalid Status supplied")

        key = self.getkey()
        query = reviews.Query(self.hostname, self.port, self.user, key)
        for review in query.filter(other):
            if GerritFns.instrument_code:
                # if instrumenting code we only need to check the first review
                return review
            else:
                if pformat == "summary":
                    GerritFns.summary(review)
                else:
                    GerritFns.detail(review)

    @classmethod
    def summary(cls, review):
        """ Class Method to print the summary review information for a given review.
            The following information is printed.
                Review Number
                Gerrit ID
                Patch Set Revision Number
                Commit Message

            Args:
                review             -- The review number
        """
        slab_logger.debug('Displaying summary review for gerrit review')
        pstl = Format.bld
        click.echo(Format.message(32, 0, pstl, "For Number " + review["number"]))
        click.echo(Format.message(32, 0, pstl, "Id") + review['id'])
        click.echo(Format.message(32, 0, pstl, "Current Patch Set Revision") +
                   review["currentPatchSet"]["revision"])
        click.echo(Format.message(32, 0, pstl, "Commit Message"))
        click.echo(review["commitMessage"])

    @classmethod
    def detail(cls, review):
        """ Print the complete review information for a given review."""
        slab_logger.debug('Displaying full information for gerrit review')
        pstl = Format.bld
        click.echo(Format.message(24, 0, pstl, "Branch")+review['branch'])
        click.echo(Format.message(24, 0, pstl, "Created On") +
                   Format.time(review["createdOn"]))
        click.echo(Format.message(24, 0, pstl, "Subject")+review["subject"])

        stat = Format.bld
        if review["status"] == "MERGED":
            stat = Format.green | stat
        elif review["status"] == "OPEN":
            stat = Format.blue | stat
        click.echo(Format.message(24, 0, pstl, "Status") +
                   Format.message(0, 0, stat, review['status']))

        click.echo(Format.message(24, 0, pstl, "Id") + review['id'])
        click.echo(Format.message(24, 0, pstl, "Number") + review['number'])
        click.echo(Format.message(24, 0, pstl, "Open") + str(review['open']))
        click.echo(Format.message(24, 0, pstl, "Sort Key") + review["sortKey"])
        click.echo(Format.message(24, 0, pstl, "Url") + review["url"])
        click.echo(Format.message(24, 0, pstl, "Commit Message"))
        click.echo(review["commitMessage"])
        click.echo(Format.message(24, 0, pstl | Format.uline, "Current PatchSet"))

        pset = review["currentPatchSet"]
        click.echo(Format.message(24, 2, pstl, "Author") + pset["author"]["name"])
        click.echo(Format.message(24, 2, pstl, "Created On") +
                   Format.time(pset["createdOn"]))
        click.echo(Format.message(24, 2, pstl, "Is Draft") +
                   str(pset["isDraft"]))
        click.echo(Format.message(24, 2, pstl, "Number") + pset["number"])
        click.echo(Format.message(24, 2, Format.bld | Format.uline, "Parents"))
        for parent in pset["parents"]:
            click.echo("    {}".format(parent))
        click.echo(Format.message(24, 2, pstl, "Reference")+pset["ref"])
        click.echo(Format.message(24, 2, pstl, "Revision")+pset["revision"])
        click.echo(Format.message(24, 2, pstl, "Size Insertions") +
                   str(pset["sizeInsertions"]))
        click.echo(Format.message(24, 2, pstl, "Size Deleteions") +
                   str(pset["sizeDeletions"]))
        if "approvals" in pset.keys():
            click.echo(Format.message(24, 2, pstl, "Approvals"))
            for aprvl in pset["approvals"]:
                click.echo(Format.message(24, 4, pstl, "*Name") +
                           aprvl["by"]["name"])
                click.echo(Format.message(24, 4, pstl, " Type") +
                           aprvl["type"])
                click.echo(Format.message(24, 4, pstl, " Granted On") +
                           Format.time(aprvl["grantedOn"]))
                click.echo(Format.message(24, 4, pstl, " Value") + aprvl["value"])
                if 'description' in aprvl.keys():
                    click.echo(Format.message(24, 4, pstl,
                                              " Description") + aprvl["description"])
        click.echo("\n")


# driver check for this
if __name__ == '__main__':
    import sys

    GCTX = Context()
    GCTX.debug = False
    GRT = GerritFns("kunanda", "servicelab", GCTX)
    click.echo("GET SUMMARY OF ALL OUTGOING REVIEWS For Owner " + "kunanda")
    GRT.print_gerrit("summary", None, "kunanda", "", "open")
    sys.stdin.read(1)

    click.echo("\n\n\n\n")
    click.echo("GET SUMMARY OF INCOMING REVIEWS For Owner " + "kunanda")
    GRT.print_gerrit("summary", None, "", "kunanda", "open")
    sys.stdin.read(1)

    click.echo("\n\n\n\n")
    click.echo("GET " + str(23182) + " REVIEW DETAIL ")
    GRT.print_gerrit("detail", 23182, "", "", "")
    sys.stdin.read(1)

    click.echo("\n\n\n\n")
    click.echo("GET CODE REVIEW " + str(23182))
    GRT.code_review(23182)
    sys.stdin.read(1)

    click.echo("\n\n\n\n")
    click.echo("CODE REVIEW  +1 On " + str(23182))
    GRT.change_review(23182, 1, 0, "Doing 1 on this")
    sys.stdin.read(1)

    click.echo("\n\n\n\n")
    click.echo("GET CODE REVIEW " + str(23182))
    GRT.print_gerrit("detail", 23182)
#   GRT.code_state(22929, "delete")
