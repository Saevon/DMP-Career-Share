# !/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import sys

from error import DMPException
from profile import ProfileHandler
import re


def merge(name):
    try:
        profile_handler.merge_profile(name)
    except DMPException as err:
        trace = getattr(err, 'trace', 'NO TRACE')
        print trace


from optparse import OptionParser
app_parser = OptionParser(usage="usage: %prog profile_path initial_path [options]")
app_parser.add_option(
    "-v", "--debug", "--verbose",
    dest="debug",
    action="store_true",
)

def parse_options():
    '''
    Reads any commandline options, returning a final dict of options
    '''
    (options, args) = app_parser.parse_args()

    if len(args) != 2:
        app_parser.error("Both profile_path and initial_path are required")

    # Remove any unset options, using the defaults defined earlier instead
    options = vars(options)
    options = dict((key, options[key]) for key in options if options[key] is not None)

    options['path'] = os.path.abspath(args[0])
    options['initial_path'] = os.path.abspath(args[1])

    return options


JOIN_RE = re.compile(r'Client ([^ ]+?) handshook successfully')
EXIT_RE = re.compile(r'Client ([^ ]+?) disconnected')

def reader(profile_handler, line):
    match = JOIN_RE.match(line)
    if match:
        name = match.group(1)

        # load any new profiles
        print "JOIN: %s" % name
        profile_handler.load_profiles()

    match = EXIT_RE.match(line)
    if match:
        name = match.group(1)

        print "EXIT: %s" % name
        profile_handler.merge_profile(name)


import select

if __name__ == '__main__':
    options = parse_options()

    profile_handler = ProfileHandler(options['path'], options['initial_path'])

    try:
        while True:
            if len(select.select([sys.stdin], [], [], 1)):
                line = sys.stdin.readline()
                reader(profile_handler, line)
                print line,
    except KeyboardInterrupt:
        print "Exiting"

