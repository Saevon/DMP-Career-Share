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


JOIN_RE = re.compile(r'Client (?P<name>[^ ]+?) handshook successfully')
EXIT_RE = re.compile(r'(?P<name>[^ ]+?)(( disconnected)|( sent connection end message))')
DEAD_RE = re.compile(r'Goodbye!')


def reader(profile_handler, players, line):
    match = JOIN_RE.search(line)
    if match:
        name = match.group('name')


        # load any new profiles
        print "=========="
        print "JOIN: %s" % name
        players[name] = True

        profile_handler.load_profiles()
        print "----------"

    match = EXIT_RE.search(line)
    if match:
        name = match.group('name')
        print "=========="
        print "EXIT: %s" % name

        profile_handler.load_profiles()

        players[name] = False

        for player, alive in players.iteritems():
            if not alive:
                profile_handler.merge_profile(player)

        for player, alive in players.iteritems():
            if not alive:
                profile_handler.merge_profile(player)

        print "----------"

    match = DEAD_RE.search(line)
    if match:
        print "=========="
        print "RESET"

        profile_handler.load_profiles()
        for player in players.keys():
            players[player] = False

        profile_handler.merge_all()
        print "----------"


def empty(players):
    for player, isalive in players.iteritems():
        if not isalive:
            return False
    return True

def main(profile_handler):
    counter = 0
    players = {}

    for player in profile_handler.get_players():
            players[player] = False

    if len(select.select([sys.stdin], [], [], 0)):
        line = sys.stdin.readline()
        print line,

        try:
            reader(profile_handler, players, line)
        except DMPException as err:
            trace = getattr(err, 'trace', 'NO TRACE')
            print trace

    elif counter > 30 and empty(players):
        print "=========="
        print "RESET"
        err = profile_handler.merge_all()
        print "----------"
    else:
        sleep(1)
        counter += 1


import select
from time import sleep

if __name__ == '__main__':
    options = parse_options()

    profile_handler = ProfileHandler(options['path'], options['initial_path'])

    try:
        while True:
            main(profile_handler)
    except KeyboardInterrupt:
        print "Exiting"

