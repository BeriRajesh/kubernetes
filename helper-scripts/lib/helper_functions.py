""" Module to define helper functions to use across scripts """
import csv
import collections
from pprint import pprint
import sys


verbose = 0


def debug(msg, mylevel=1, **kwargs):
    """Print msg only when verbose > level"""

    if "level" in kwargs:
        mylevel = kwargs["level"]

    if verbose >= mylevel:
        if 'flush' not in kwargs:
            kwargs['flush'] = True
        if 'level' in kwargs:
            del kwargs['level']
        print(str(msg), **kwargs)


def dd(msg, mylevel=1, **kwargs):
    """debug()'s message and stops execution only if verbose > level"""

    if "level" in kwargs:
        mylevel = kwargs["level"]

    debug(msg, mylevel, **kwargs)

    if verbose >= level:
        sys.exit()


def write_csv(write_path, lines_list):
    with open(write_path, "w") as csv_file:
        writer = csv.writer(csv_file)
        for line in lines_list:
            # pprint(line)
            writer.writerow(line)


def read_csv(path, **kwargs):
    """ naive csv reader. yields a line of the csv file
    kwargs are passed to the csv.reader() function"""

    csvfile = open(path,'r')
    lines = csv.reader(csvfile, **kwargs)
    for line in lines:
        yield line


def dict_merge(dct, merge_dct):
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None

    taken from: https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
    (adapted to Python3)
    """
        # pprint(dct)
        # pprint(merge_dct)
    for k, v in merge_dct.items():
        # print(k)
        if k in dct and isinstance(dct[k], dict) and isinstance(merge_dct[k], dict):
            # print('rec')
            # pprint(dct[k])
            # pprint(merge_dct[k])
            dict_merge(dct[k], merge_dct[k])
        else:
            # print('lin')
            dct[k] = merge_dct[k]

        # pprint(dct[k])
        # pprint(merge_dct[k])
