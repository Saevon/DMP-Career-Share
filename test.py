# !/usr/bin/env python
# -*- coding: UTF-8 -*-
import os

from profile import Profile
from error import DMPException
import merger


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

def compare_list(input, output, index):
    length = max(len(input), len(output))

    for i in range(length):
        if isinstance(output[i], dict) and output[i].get('id', False):
            subindex = "%s.%i(%s)" % (index, i, output[i]['id'])
        else:
            subindex = "%s.%i" % (index, i)


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
        compare(input[key], output[key], subindex)

def compare_data_profile(input, output):
    for key, val in input.data.iteritems():
        debug("File: %s" % key)
        compare_dict(input.data[key].data, output.data[key].data, key.strip(".txt"))

def test(name):
    path = os.path.join(TEST_PATH, name)

    initial = Profile('initial', path).refresh()
    current = Profile('current', path).refresh()
    server = Profile('server', path).refresh()
    out = Profile('out', path).refresh()

    merger.merge(initial.data, current.data, server.data)

    err = compare_data_profile(out, initial)
    if err:
        print err

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
            print err.trace
