import yaml
from collections import OrderedDict

"""
based on the stack overflow discussin
http://stackoverflow.com/questions/5121931/in-python-how-can-you-load-yaml-mappings-as-ordereddicts


Observations:
Tried with ruamel.yaml implementation but found that it was converting the double quote
hierra strings to a pair of single quote strings.

Not sure if this was a good approach even though in addition to the order it preserved
the comments also. I do not like formatting to be changed as double quotes and single
quotes have distinct meaning in yaml.

Till the complete ruamel.yaml solution is found discarding the below implementation:
import ruamel.yaml as yaml
def ordered_load(stream):
    data = yaml.load(stream, Loader=yaml.RoundTripLoader)
    return  data


def ordered_dump(stream, data):
    stream.write(yaml.dump(data, Dumper=yaml.RoundTripDumper))

"""


def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)


def ordered_dump(data, stream=None, Dumper=yaml.Dumper, **kwds):
    class OrderedDumper(Dumper):
        pass

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            data.items())

    OrderedDumper.add_representer(OrderedDict, _dict_representer)
    return yaml.dump(data, stream, OrderedDumper, **kwds)


# test driver
if __name__ == '__main__':
    fnm = "./example.yaml"
    dict = {}
    with open(fnm) as f:
        dict = ordered_load(f)
    with open(fnm + ".new", "w") as f:
        ordered_dump(dict, f)
