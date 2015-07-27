# !/usr/bin/env python
# -*- coding: UTF-8 -*-
import os

from profile import Profile
from error import DMPException
import merger

import termcolor


TEST_PATH = './test/'
DEBUG = False

class TestError(Exception):
    pass

def debug(*vals):
    if not DEBUG:
        return

    for val in vals:
        print vals


def compare(input, output, index):
    if input is None or output is None:
        # lists with no values don't get output, so act as None
        if len(input) == 0 or len(output) == 0:
            return

    if type(input) != type(output):
        raise TestError("Type mismatch: %s (%s != %s)" % (
            index,
            type(input), type(output),
        ))

    if isinstance(input, list):
        compare_list(input, output, index)
    elif isinstance(input, dict):
        compare_dict(input, output, index)
    else:
        debug('compare %s' % input)
        if input != output:
            raise TestError("Mismatch: %s (%s != %s)" % (index, input, output))

def compare_id(input, output, index):
    input_id = input.get('id', None)
    output_id = output.get('id', None)

    if input_id != output_id:
        raise TestError("Mismatch (id): %s (%s != %s)" % (index, input_id, output_id))

def compare_list(input, output, index):
    length = max(len(input), len(output))

    for i in range(length):
        subindex = "%s.%i" % (index, i)
        if isinstance(output[i], dict) and output[i].get('id', False):
            compare_id(input[i], output[i], subindex)
            subindex = "%s(%s)" % (subindex, output[i]['id'])


        debug("List: %s" % subindex)
        compare(input[i], output[i], subindex)

def compare_dict(input, output, index):
    keys = set()

    for key in input.keys():
        keys.add(key)
    for key in output.keys():
        keys.add(key)

    for key in keys:
        subindex = "%s['%s']" % (index, key)
        debug("Dict: %s" % subindex)

        compare(input.get(key, None), output.get(key, None), subindex)

def compare_data_profile(input, output):
    for key, val in input.data.iteritems():
        debug("File: %s" % key)
        compare_dict(input.data[key].data, output.data[key].data, key[:-len(".txt")])

def test(name):
    path = os.path.join(TEST_PATH, name)

    initial = Profile('initial', path).refresh()
    current = Profile('current', path).refresh()
    server = Profile('server', path).refresh()
    out = Profile('out', path).refresh()

    errors = merger.merge(initial.data, current.data, server.data)
    if errors:
        print termcolor.colored(errors, 'yellow')

    compare_data_profile(initial, out)

if __name__ == '__main__':
    for folder in os.listdir(TEST_PATH):
        path = os.path.join(TEST_PATH, folder)

        if os.path.isfile(path):
            continue
        if not os.path.exists(os.path.join(path, 'explain.txt')):
            continue

        print "====================="
        print "Testing: %s" % folder
        print "---------------------"
        try:
            test(folder)
        except DMPException as err:
            print termcolor.colored(err.trace, 'red')
        except TestError as err:
            print termcolor.colored(err, 'red')
