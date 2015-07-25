#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import time
import os.path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from timer import TimerThread

from lock import with_threading_lock

import parser


class DataFile(object):

    STATUS_NOT_FOUND = "not_found"
    STATUS_LOADED = "loaded"
    STATUS_UPDATED = "updated"

    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.status = self.STATUS_NOT_FOUND
        self.data = None

    def is_ready(self):
        return self.status == self.STATUS_UPDATED

    def on_data(self, path):
        self.status = self.STATUS_UPDATED

        with open(self.path, 'r') as fp:
            self.data = parser.load(fp)


    def on_parsed(self):
        self.status == self.STATUS_LOADED

class Profile(object):

    ALL_DATA = [
        "ContractSystem.txt",
        "Funding.txt",
        "PCScenario.txt",
        "ProgressTracking.txt",
        "Reputation.txt",
        "ResearchAndDevelopment.txt",
        "ResourceScenario.txt",
        "ScenarioDestructibles.txt",
        "ScenarioNewGameIntro.txt",
        "ScenarioUpgradeableFacilities.txt",
        "StrategySystem.txt",
        "VesselRecovery.txt",
    ]

    FILE_TIMEOUT = 4

    def __init__(self, name, base_path):
        print "New Profile: ", name
        self.name = name
        self.base_path = base_path

        self.data = {}
        for name in self.ALL_DATA:
            self.data[name] = DataFile(name, os.path.join(self.base_path, name))

        self.timer = TimerThread(self.parse_files)
        self.timer.start()

    def stop(self):
        self.timer.stop()

        # TODO: should we do one last merge?
        self.parse_files()

    @with_threading_lock('data_files')
    def update_file(self, path):
        if path not in self.data:
            return

        print self.name, "updated", path

        self.data[path].on_data(os.path.join(self.base_path, self.name, path))

        # Waits for the timer to finish
        if not self.timer.is_on():
            self.timer.set(self.FILE_TIMEOUT)

    @with_threading_lock('data_files')
    def parse_files(self):
        print "Running Merger"


class ProfileHandler(FileSystemEventHandler):

    def __init__(self, base_path):
        super(ProfileHandler, self).__init__()

        self.profiles = {}
        self.base_path = base_path

        # Scan the folder on init
        self.load_profiles()

    def load_profiles(self):
        '''
        Loads the profiles and their files that currently exist in the system
        '''
        folders = [f for f in os.listdir(self.base_path) if not os.path.isfile(os.path.join(self.base_path, f))]

        for folder in folders:
            self.profiles[folder] = Profile(folder, self.base_path)

            path = os.path.join(self.base_path, folder)

            files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(self.base_path, folder, f))]
            for file in files:
                self.profiles[folder].update_file(file)


    def on_created(self, event):
        '''
        Listen for new profiles being created.
        Listen for new files being added to a profile
        '''
        path = os.path.relpath(event.src_path, self.base_path)
        parts = path.split("/")

        name = parts[0]

        if len(parts) == 1:
            self.profiles[name] = Profile(name, self.base_path)
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

    def stop(self):
        for key, profile in self.profiles.iteritems():
            profile.stop()


if __name__ == "__main__":
    path = '/Users/Saevon/Applications/Kerbal Space Program/DMPServer/Universe/Scenarios'
    observer = Observer()

    profile_handler = ProfileHandler(path)
    observer.schedule(profile_handler, path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        profile_handler.stop()
        observer.stop()
    observer.join()
