#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os.path


from timer import TimerThread

from lib.lock import with_threading_lock, get_threading_lock
from lib.cascade import cascade

import parser
import merger

import subprocess


class DataFile(object):

    STATUS_NOT_FOUND = "not_found"
    STATUS_LOADED = "loaded"
    STATUS_UPDATED = "updated"

    def __init__(self, name, path):
        self.name = name
        self.path = os.path.join(path, name)

        self.reset()

    def reset(self):
        self.status = self.STATUS_NOT_FOUND
        self.data = None

    def is_ready(self):
        return self.status == self.STATUS_UPDATED

    @cascade
    def refresh(self):
        self.status = self.STATUS_UPDATED

        with open(self.path, 'r') as fp:
            self.data = parser.load(fp)

    @cascade
    def save(self, path=None):
        '''
        Dumps the data to the given path using kerbal format
        '''
        if path is None:
            path = self.path

        with open(path, 'w') as fp:
            fp.write(parser.dump(self.data))

    def on_parsed(self):
        self.status == self.STATUS_LOADED

class FakeDataFile(DataFile):
    '''
    Wrapper around a real datafile, so that we can pretend the data is made up
    of multiple files
    '''

    def __init__(self, real_data_file, name):
        self.name = name
        self.real_name = name[:-len(".txt")]
        self.real_data_file = real_data_file

    @property
    def data(self):
        for scenario in self.real_data_file.data["GAME"][0]["SCENARIO"]:
            if scenario["name"] == self.real_name:
                return scenario
        raise LookupError(self.name)

    @property
    def status(self):
        return self.real_data_file.status

    @property
    def path(self):
        return self.real_data_file.path

    @cascade
    def refresh(self):
        self.real_data_file.refresh()

    @cascade
    def save(self, path=None):
        if path is not None:
            raise NotImplementedError("Can't save FakeDataFile to a location")
        self.real_data_file.save()

    @cascade
    def export(self, path):
        df = DataFile(name=self.name, path=path)
        df.data = self.data
        df.save()
        df.refresh()

        return df


class Profile(object):

    ALL_DATA = [
        # "ContractSystem.txt",
        "Funding.txt",
        # "PCScenario.txt",
        # "ProgressTracking.txt",
        "Reputation.txt",
        "ResearchAndDevelopment.txt",
        # "ResourceScenario.txt",
        "ScenarioDestructibles.txt",
        # "ScenarioNewGameIntro.txt",
        "ScenarioUpgradeableFacilities.txt",
        # "StrategySystem.txt",
        # "VesselRecovery.txt",
    ]

    FILE_TIMEOUT = 4

    def __init__(self, name, base_path, enable_timer=False):
        print "%s New Profile" % (name)
        self.name = name
        self.base_path = base_path

        self.all_files = set()

        self.data = {}
        for name in self.ALL_DATA:
            self.data[name] = DataFile(
                name,
                path=os.path.join(self.base_path, self.name),
            )
            self.all_files.add(self.data[name])

        self.enable_timer = enable_timer
        if enable_timer:
            self.timer = TimerThread(self.on_timer_end)
            self.timer.start()

    @cascade
    def stop(self):
        try:
            self.timer.stop()
        except:
            pass

    @cascade
    @with_threading_lock('data_files')
    def update_file(self, path):
        if path not in self.data:
            return

        print "%s: updated %s" % (self.name, path)

        self._update_file(path)

        # # Waits for the timer to finish
        if self.enable_timer and not self.timer.is_on():
            self.timer.set(self.FILE_TIMEOUT)

    def _update_file(self, path):
        self.data[path].refresh()

    def on_timer_end(self):
        print "%s: Running Merger" % self.name

        self.merge()

    @cascade
    @with_threading_lock('data_files')
    def merge(self):
        '''
        Merges all the files
        '''
        self._merge()

        for name in self.ALL_DATA:
            self.data[name].on_parsed()

    def _merge(self):
        pass

    @cascade
    @with_threading_lock('data_files')
    def refresh(self):
        '''
        Reloads all the data files for the profile
        '''
        for data_file in self.all_files:
            data_file.refresh()




class DualProfile(Profile):

    @cascade
    def set_server(self, server_profile):
        self.server_profile = server_profile

    def __init__(self, name, base_path, initial_path, enable_timer=False):
        super(DualProfile, self).__init__(name, base_path, enable_timer)

        self.initial_path = initial_path

        # Create the Initial folder if needed
        subprocess.call(['mkdir', '-p', os.path.join(self.initial_path, self.name)])

        self.initial = {}
        for key in self.ALL_DATA:
            self.initial[key] = DataFile(
                key,
                path=os.path.join(self.initial_path, self.name),
            )
            self.all_files.add(self.initial[key])

    def _merge(self):
        with get_threading_lock(self.server_profile, 'data_files'):
            errors = merger.merge(self.initial, self.data, self.server_profile.data)

            for error in errors:
                print error

            # Finish the parse
            for name in self.ALL_DATA:
                self.server_profile.data.save()
                self.data[name].save()
                self.initial[name].save()

                self.server_profile.data.on_parsed()
                self.data[name].on_parsed()
                self.initial[name].on_parsed()

    def _update_file(self, path):
        if not os.path.exists(self.initial[path].path):
            subprocess.call(['cp', self.data[path].path, self.initial[path].path])

        self.initial[path].refresh()
        self.data[path].refresh()


class FullSaveProfile(Profile):

    def __init__(self, name, base_path):
        self.name = name
        self.base_path = base_path

        self.data_file = DataFile(
            name,
            path=self.base_path,
        ).refresh()

        self.data = {}
        for scenario in self.data_file.data["GAME"][0]["SCENARIO"]:
            name = scenario["name"] + ".txt"
            self.data[name] = FakeDataFile(self.data_file, name)

    @cascade
    def refresh(self):
        self.data_file.refresh()

    @cascade
    def save(self):
        self.data_file.save()

    @cascade
    def merge(self):
        raise NotImplementedError


class ProfileHandler(object):

    SERVER_PROFILE = 'Initial'

    def __init__(self, base_path, initial_path, enable_timer=False):
        super(ProfileHandler, self).__init__()

        self.profiles = {}
        self.base_path = base_path
        self.initial_path = initial_path

        self.enable_timer = enable_timer

        self.server_profile = None

        # Scan the folder on init
        try:
            self.load_profiles()
        except:
            self.stop()
            raise


    @cascade
    def load_profiles(self):
        '''
        Loads the profiles and their files that currently exist in the system
        '''
        if self.server_profile is None:
            self.server_profile = self.load_profile(self.SERVER_PROFILE)

        folders = [f for f in os.listdir(self.base_path) if not os.path.isfile(os.path.join(self.base_path, f))]

        for folder in folders:
            if folder == self.SERVER_PROFILE:
                continue

            if folder in self.profiles.keys():
                continue

            self.load_profile(folder)

    def load_profile(self, folder):
        '''
        Loads the profile at the given folder

        Note: the server profile must be loaded first
        '''
        # Create the profile, server is special
        if folder == self.SERVER_PROFILE:
            profile = Profile(folder, self.base_path, enable_timer=self.enable_timer)
        else:
            profile = DualProfile(folder, self.base_path, self.initial_path, enable_timer=self.enable_timer)
            profile.set_server(self.server_profile)

        self.profiles[folder] = profile
        path = os.path.join(self.base_path, folder)

        # Update each file in the profile
        for filename in os.listdir(path):
            fp = os.path.join(path, filename)
            if not os.path.isfile(fp):
                continue

            profile.update_file(filename)

        return profile

    @cascade
    def refresh_profile(self, name):
        '''
        Reloads all the files for the given profile
        '''
        profile = self.profiles[name]
        profile.refresh()

    def stop(self):
        for key, profile in self.profiles.iteritems():
            print "Killing: %s" % key
            profile.stop()
            print "Killed: %s" % key

    @cascade
    def merge_profile(self, name):
        '''
        Runs a profile merge right away
        '''
        profile = self.profiles[name]

        self.refresh_profile(name)
        self.refresh_profile("Initial")

        profile.merge()

    @cascade
    def merge_all(self):
        '''
        Runs a full merge of the system
        '''
        # Note: Do this twice, to ensure all profiles are up to date
        # Since each merge updates the current player only to the ones already merged

        for key, profile in self.profiles.iteritems():
            self.merge_profile(profile)

        for key, profile in self.profiles.iteritems():
            self.merge_profile(profile)

