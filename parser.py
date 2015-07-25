#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from collections import OrderedDict
from decimal import Decimal
import json

from parser_data import InlineList, DuplicationList
from state import State, StateMachine
from type_check import is_int, is_float
from format import format



class ParserStateMachine(StateMachine):
    def __init__(self, options):
        self.data = OrderedDict()

        initial = NeutralState(self.data)
        initial.parent = initial

        super(ParserStateMachine, self).__init__(initial, options)

    def get_data(self):
        return self.data

    def preprocess(self, val):
        return val.strip()

class DataState(State):
    def __init__(self, data):
        super(DataState, self).__init__()
        self.data = data


class NeutralState(DataState):
    def run(self, line):
        if '=' in line:
            key, val = [val.strip() for val in line.split('=')]

            old_data = self.data.get(key, None)
            if old_data is None:
                # First time we got said data, just add it in
                self.data[key] = self.read_data(val)
            elif isinstance(old_data, DuplicationList):
                # The stored data is a list, append to it
                self.data[key].append(val)
            else:
                # We got the same key? Turn the stored data into a list
                old_val = self.data[key]
                self.data[key] = DuplicationList()
                self.data[key].append(old_val)
                self.data[key].append(val)

            return self.finish_state()
        else:
            self.debug('= DICT =')
            return self.rerun_with_state(
                DictState(self.data).set_parent(self.parent)
            )

    def read_data(self, val):
        if ',' in val:
            val = [subval.strip() for subval in val.split(',')]
            val = [self.read_data(subval) for subval in val]
            val = InlineList(val)
        elif val == 'True':
            val = True
        elif val == 'False':
            val = False
        elif is_int(val):
            val = int(val)
        elif is_float(val):
            old_val = val
            val = Decimal(val)

        return val

class DictState(DataState):

    def __init__(self, data):
        super(DictState, self).__init__(data)

        self.val = OrderedDict()

        self.run = self.state_name

    def state_name(self, val):
        self.debug('= NAME = ')

        self.name = val

        self.run = self.state_open

    def state_open(self, val):
        self.debug('= OPEN = ')

        if val != '{':
            raise State.Error("Expected dict open brace")

        self.depth += 1
        self.run = self.state_data

    def state_data(self, val):

        if val == '}':
            self.debug('= CLOSED = ')
            if not self.data.get(self.name, False):
                self.data[self.name] = DuplicationList()
            self.data.get(self.name).append(self.val)

            self.depth -= 1
            return self.finish_state()
        else:
            self.debug('= DATA = ')
            return self.rerun_with_state(
                NeutralState(self.val).set_parent(self)
            )


def load(fp, options=None):
    config = {
        # 'verbose': True,
    }
    if options is not None:
        config.update(options)

    machine = ParserStateMachine(config)
    machine.runAll(fp)

    return machine.get_data()

def dump(data, options=None):
    config = {
        # 'verbose': True,
    }
    if options is not None:
        config.update(options)

    lines = []
    for key, val in data.iteritems():
        lines += format(key, val)

    # Adds Trailing newline
    lines.append('')

    return '\n'.join(lines)


def _test(infile, outfile):
    with open(infile, 'r') as fp:
        data = load(fp)

    with open(infile, 'r') as fp:
        raw = fp.read()

    # print json.dumps(data, indent=4)

    out = dump(data)

    with open(outfile, 'w') as fp:
        fp.write(out)

    import subprocess
    subprocess.call(['diff', infile, outfile])
    subprocess.call(['rm', outfile])


if __name__ == "__main__":
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

    outfile = './tmp.txt'

    import os.path
    for filename in ALL_DATA:
        infile = os.path.join('../Universe/Scenarios/Saevon/', filename)
        _test(infile, outfile)
