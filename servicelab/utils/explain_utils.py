"""
Stack explain command
"""
import os
import re
import yaml

import click
import requests
import operator

from string import maketrans

from prettytable import PrettyTable
from bs4 import BeautifulSoup

from servicelab.utils import service_utils
from servicelab.utils import ccsbuildtools_utils


def compile_man_page(path, user, password):
    """
    Grabs data from confluence pages and servicelab docs and leverages sphinx to
    convert them into a single man page that will be queried for high level info.
    """
    path_to_docs = os.path.split(path)[0]
    path_to_docs = os.path.split(path_to_docs)[0]
    path_to_docs = os.path.join(path_to_docs, 'docs')
    man_yaml = _load_slabmanyaml(path)

    # The man_contents.rst.inc file follows Sphinx syntax for enumerating the
    # files that will be included in the final man page
    with open(os.path.join(path_to_docs, "man_contents.rst.inc"), "w") as manf:
        manf.write(".. toctree::\n   :maxdepth: 2\n\n")
        manf.writelines("   " + elem + "\n" for elem in man_yaml["slab_docs"])

    # Manually download all desired sites, and leverage Sphinx's "make man" command
    # to build a single man page using pages indexed above
    for item in man_yaml['confluence_pages']:
        url = 'https://confluence.sco.cisco.com/display/' + item
        site_title = item.translate(None, '+')
        file_title = item.translate(maketrans("+", "-")).lower()[4:]
        content = requests.get(url, auth=(user, password))
        if content.status_code != 200:
            click.echo("Unable to login to {0} as user {1} "
                       " with supplied password.".format(url, user))
            return
        with open(os.path.join(path_to_docs, 'man_pages', '%s.rst' % file_title),
                  'w') as manf:
            manf.write(_parse_confluence_website(content.text, site_title))

        service_utils.run_this("echo '   man_pages/%s' >> man_contents.rst.inc"
                               % file_title, path_to_docs)

    cmd = "sed -i -e \"s/master_doc = 'index'/master_doc = 'man_index'/g\" conf.py; " \
          "make man;" \
          "sed -i -e \"s/master_doc = 'man_index'/master_doc = 'index'/g\" conf.py;"
    service_utils.run_this(cmd, path_to_docs)


def list_navigable_sections(path):
    """
    List and navigate to sections in a man page
    """
    print "\nChoose a topic to have it explained"
    path_to_man_page = _get_path_to_man_page(path)
    sections = _get_list_of_sections(path_to_man_page)
    section_name = ccsbuildtools_utils.table_selection(sections, 'Topic')
    _view_section(section_name, path_to_man_page)


def navigate_all(path):
    """
    Get all sections...show entire man page
    """
    path_to_man_page = _get_path_to_man_page(path)
    cmd_view = "man %s" % path_to_man_page
    os.system(cmd_view)


def query(path, query_str):
    """
    Lists all the sections in the man page in descending order based on the
    number of times "query" is found in that section. Also gives arbitrary recommendations
    for sections the user should visit based on the query, but ultimately lets the user
    pick which section to visit.
    """
    man_yaml = _load_slabmanyaml(path)
    topic_titles = {}
    for i in man_yaml['confluence_pages']:
        topic_name = i[4:].replace('+', ' ').upper()
        topic_titles[topic_name] = man_yaml['confluence_pages'][i]

    for i in man_yaml['slab_docs']:
        topic_titles[i.upper()] = man_yaml['slab_docs'][i]

    path_to_man_page = _get_path_to_man_page(path)

    sections = _get_list_of_sections(path_to_man_page)
    results = {}
    for item in sections:
        results[item] = _get_number_of_matches(item, path_to_man_page, query_str)

    results = sorted(results.items(), key=operator.itemgetter(1), reverse=True)

    print "Your query was " + query_str
    print "Choose a topic to have it explained."
    print "Pages relevant to your query are marked in the Recommended Column"

    table = PrettyTable(['#', 'Topic', 'Query Matches', 'Recommended'])
    table.align['#'] = 'r'
    table.align['Topic'] = 'l'

    index = 1
    for pair in results:
        recommend = ""
        if query_str.lower() in topic_titles[pair[0]]:
            recommend = "XXXXX"
        if not pair[1] == 0 or recommend:
            table.add_row([index, pair[0], pair[1], recommend])
        index = index + 1

    print table

    if table == []:
        print "Query unsuccessful. No matches found"

    valid_opts = range(1, index)
    for i in valid_opts:
        i = repr(i)

    num = ccsbuildtools_utils.get_valid_input_or_option("Enter number: ", 0, valid_opts)
    table.header = False
    table.border = False
    topic_name = table.get_string(fields=['Topic'], start=int(num)-1,
                                  end=int(num)).strip()
    _view_section(topic_name, path_to_man_page)


def _get_path_to_man_page(path):
    """
    Get path to man page
    """
    path_to_docs = os.path.split(path)[0]
    path_to_docs = os.path.split(path_to_docs)[0]
    path_to_docs = os.path.join(path_to_docs, 'docs')
    return os.path.join(path_to_docs, '_build', 'man', 'servicelab.1')


def _get_list_of_sections(path_to_man_page):
    """
    Returns a list of all man page sections
    """
    # Takes advantage of the way man pages are formatted.
    # All headings begin with .SH
    sections = []
    with open(path_to_man_page, mode='r') as manf:
        for line in manf:
            if (re.match('^.SH', line) and not line[4:].strip() == 'NAME' and
                    not line[4:].strip() == 'COPYRIGHT'):
                sections.append(line[4:].strip())
    sections.sort()
    return sections


def _view_section(section_name, path_to_man_page):
    """
    View man page section.
    """
    section_name1 = section_name.replace(' ', r'\ ')
    section_name2 = "^" + ".*".join(section_name) + "$"

    # Output the man page beginning at the appropriate section
    cmd_view = "man -P 'less -p ^%s' %s | " % (section_name1, path_to_man_page)

    # Grab everything from that man page up until and including the next line
    # that begins with nonwhitespace (i.e. the next header)
    cmd_view += "sed -n -e '/%s/,/^[^ \\t\\r\\n\\v\\f]/ p' | " % (section_name2)

    # Exclude that final header and display all the information with `more`
    cmd_view += "sed -e '$d' | more "

    # We need to use os.system here to actually let the user interact with the
    # doc the same way a man page is viewed (calling shell commands).
    # Ideally we wanted to use service_utils.run_this
    # but that wouldn't give me the appropriate behavior.
    os.system(cmd_view)


# With a bigger set of data, this runs okay. But ideally I'd want to set up a persistent
# hash which saves query results, so that the program doesn't waste time querying for the
# same keyword twice.
def _get_number_of_matches(section_name, path_to_man_page, query_str):
    """
    Return the number of times query is found in the man page section
    """
    # Equivalent to _view_section, except for the added grep command which
    # ignores case and outputs matches, which are then counted by wc
    section_name1 = section_name.replace(' ', r'\ ')
    section_name2 = "^" + ".*".join(section_name) + "$"
    cmd_view = "man -P 'less -p ^%s' %s | " % (section_name1, path_to_man_page)
    cmd_view += "sed -n -e '/%s/,/^[^ \\t\\r\\n\\v\\f]/ p' | " % (section_name2)
    cmd_view += "sed -e '$d' | grep -io %s | wc -l " % (query_str)

    # ignoring the error. just printing the output. this should be reviewed
    _, output = service_utils.run_this(cmd_view)
    return int(output.strip())


def _load_slabmanyaml(path):
    """
    Load from the yaml file
    """
    path_to_yaml = os.path.split(path)[0]
    path_to_yaml = os.path.join(path_to_yaml, "utils", "slab_man_data.yaml")
    with open(path_to_yaml, 'r') as yaml_file:
        return yaml.load(yaml_file)


# This needs improvement. Formatting is an issue for some html websites. There are too many
# manual deletes (i.e. "loading the editor" )
# Ideally, I'd want to use the URI confluence API to grab content that way, it's
# probably way more efficient than this method...where I try to manually parse the
# html file with BeautifulSoup.
def _parse_confluence_website(html_text, site_title):
    """
    Removes all html tag s and grabs relevant data from a confluence html page -
    converts the content into human-readable format.
    """
    soup = BeautifulSoup(html_text, 'html.parser')
    title = soup.title.text.split('-')[0]
    header = "\n"
    header += '-' * len(title) + '\n'
    header += title + '\n'
    header += '-' * len(title) + '\n'
    # Get EVERY TAG and then parse that list of tags
    tags_with_content = soup.find_all(True)
    content_found = False
    content = [header]
    # Parsing the list of html tags
    for tag in list(tags_with_content):
        # Any tag with hx where x is a number has relevant content
        cond_1 = re.match(re.compile("^h[0-9][0-9]?$"), tag.name)
        # Any tag prefixed with the name of the website has relevant content
        cond_2 = tag.has_attr('id') and re.match(re.compile("%s-[^/].*"
                                                            % site_title),
                                                 tag['id'])
        # If the tag has no attributes and is near relevant content it is
        # relevant
        cond_3 = content_found and tag.attrs == {}
        if cond_1 and (cond_2 or cond_3):
            content_found = True
            content.append(tag.get_text() + ": ")
        # This tries to get the output of `tree` shell command, but
        # isn't too efficient when sphinx builds final man page
        elif tag.has_attr('type') and tag['type'] == "syntaxhighlighter":
            content.append(tag.get_text()[9:])
        # These are the paragraph tags, all have relevant content
        elif tag.name == 'p' or tag.name == 'pre':
            content.append(tag.get_text())
            content_found = True
    content = ("\n\n").join(content)
    content = content.encode("utf8", 'ignore')
    parsed_website = ""
    for line in content.splitlines():
        parsed_website += line.strip() + "\n"
    parsed_website = re.sub("Loading the Editor", "", parsed_website)
    parsed_website = re.sub("Add Comment", "", parsed_website)
    parsed_website = re.sub(r"This page content was sourced from \[README.md\]",
                            "", parsed_website)
    return parsed_website
