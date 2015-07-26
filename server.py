# !/usr/bin/env python
# -*- coding: UTF-8 -*-
from functools import wraps
import bottle
import datetime
import json
import os

from error import DMPException
from profile import ProfileHandler


app = bottle.Bottle()


def json_return(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        data = json.dumps(func(*args, **kwargs), **app.config['json'])
        data = data.replace(' ', '&nbsp;').replace('\n', '<br/>')
        return data

    return wrapper


@app.route('/favicon.ico')
def favicon():
    bottle.response.status = 404

@app.route('/')
@json_return
def root():
    return {
        'status': 200,
        'data': "Welcome, go to '/profile_name' to sync your profile>"
    }

@app.route('/<name>')
@json_return
def sync(name):
    '''
    Shows the data in the root folder
    '''
    try:
        print name
        profile_handler.merge_profile(name)
    except KeyError as err:
        return {
            'status': 404,
            'error': 'Profile not Found',
        }
    except DMPException as err:
        trace = getattr(err, 'trace', 'NO TRACE')
        print trace

        return {
            'status': 500,
            'error': 'Server Error',
        }

    return {
        'status': 200,
        'data': "Profile %s updated" % name,
        'time_server': datetime.datetime.now().strftime('%b %d %Y at %H:%M'),
        'time_utc': datetime.datetime.utcnow().strftime('%b %d %Y at %H:%M UTC'),
    }


##################################################
# Settings & Startup
##################################################
app.config.update({
    'debug': False,

    'host': '0.0.0.0',
    'port': 7070,

    'quiet': True,

    'json': {
        'sort_keys': True,
        'indent': 4,
    },
})


from optparse import OptionParser
app_parser = OptionParser(usage="usage: %prog profile_path initial_path [options]")
app_parser.add_option(
    "-p", "--port",
    dest="port",
)
app_parser.add_option(
    "-v", "--debug", "--verbose",
    dest="debug",
    action="store_true",
)
app_parser.add_option(
    "-r", "--root",
    dest="static_root",
    action="store",
)
app_parser.add_option(
    "-q", "--quiet",
    dest="debug",
    action="store_false",
)
app_parser.add_option(
    "--host",
    dest="host",
    action="store",
)
app_parser.add_option(
    "--open",
    dest="host",
    action="store_const",
    const="0.0.0.0",
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


if __name__ == '__main__':
    options = parse_options()
    app.config.update(options)

    profile_handler = ProfileHandler(options['path'], options['initial_path'], enable_timer=False)

    # Debug only settings go here
    if app.config["debug"]:
        bottle.debug(True)
        app.config.update({
            'reloader': True,
            'quiet': False,
        })

    print 'starting Server'
    app.run(**app.config)
