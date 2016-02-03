import re
import yaml
from collections import OrderedDict
from servicelab.stack import Logger

ctx = Logger()

"""
based on the stack overflow discussin
http://stackoverflow.com/questions/5121931/in-python-how-can-you-load-yaml-mappings-as-ordereddicts

"""


def load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    ctx.logger.log(15, 'Loading yaml file into ordered dictionary')

    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)


def dump(data, fname, Dumper=yaml.Dumper):
    # this dumps the data as it was read in by load
    ctx.logger.log(15, 'Writing data as it was read in by load')

    class OrderedDumper(Dumper):
        pass

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            data.items())

    with open(fname, "w") as stream:
        OrderedDumper.add_representer(OrderedDict, _dict_representer)
        yaml.dump(data, stream, OrderedDumper, default_flow_style=False)

    # massaging the data with correct anchor names rather than m/c names
    # assumption is the key name is the anchor name
    data = ""
    with open(fname) as rstream:
        data = rstream.read()

    p = re.compile("([A-Za-z0-9_]+):[ \t]*&(id[0-9]{3})")
    for m in p.finditer(data):
        repl = m.group(1)
        srch = m.group(2)
        data = re.sub(srch, repl, data)

    with open(fname, "w") as stream:
        stream.write(data)


"""
def load(stream):
    return yaml.load(stream)


def dump(data, stream):
    yaml.dump(data, stream, default_flow_style=False)

"""

# test driver
if __name__ == '__main__':
    fnm = "./example.yaml"
    dict = {}
    with open(fnm) as f:
        dict = load(f)
    dump(dict, fnm+".new")
