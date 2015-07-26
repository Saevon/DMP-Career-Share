#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import time
import os

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from profile import ProfileHandler


class ProfileWatchHandler(FileSystemEventHandler):

    def on_created(self, event):
        '''
        Listen for new profiles being created.
        Listen for new files being added to a profile
        '''
        path = os.path.relpath(event.src_path, self.base_path)
        parts = path.split("/")

        name = parts[0]

        if len(parts) == 1:
            self.load_profile(name)
        elif len(parts) == 2:
            self.profiles[name].update_file(parts[1])
        else:
            print "Warning: Subdirectories have been created"

    def on_modified(self, event):
        '''
        Listen for file modifications under a profile
        '''
        path = os.path.relpath(event.src_path, self.base_path)
        parts = path.split("/")

        name = parts[0]

        if len(parts) == 1:
            # This might mean a data file has been created
            # This might mean a data file has been removed
            # Therefore ignore it
            pass
        elif len(parts) == 2:
            self.profiles[name].update_file(parts[1])
        else:
            print "Warning: Subdirectories have been edited"



from optparse import OptionParser
app_parser = OptionParser(usage="usage: %prog profile_path server_profile_path")

def parse_options():
    '''
    Reads any commandline options, returning a final dict of options
    '''
    (options, args) = app_parser.parse_args()

    if len(args) != 2:
        app_parser.error("Too many arguments")

    # Remove any unset options, using the defaults defined earlier instead
    options = vars(options)
    options = dict((key, options[key]) for key in options if options[key] is not None)

    options['path'] = args[0]
    options['initial_path'] = args[1]

    return options

def run(options):
    parse_options

    try:
        profile_handler = ProfileWatchHandler(options['path'], options['initial_path'])

        observer = Observer()
        observer.schedule(profile_handler, options['path'], recursive=True)
        observer.start()

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print "Exiting"
        profile_handler.stop()
        observer.stop()

    print "Waiting for threads to die"
    observer.join()

if __name__ == '__main__':
    options = parse_options()
    run(options)
