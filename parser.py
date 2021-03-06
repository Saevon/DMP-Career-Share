#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from collections import OrderedDict
from decimal import Decimal

from parser_data import InlineList, DuplicationList
from state import State, StateMachine
from type_check import is_int, is_float, is_sci_notation
from format import format
from error import DMPException



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
            space_formatted = ', ' in val

            val = [subval.strip() for subval in val.split(',')]
            val = [self.read_data(subval) for subval in val]
            val = InlineList(val)

            val.space_formatted = space_formatted
        elif val == 'True':
            val = True
        elif val == 'False':
            val = False
        elif is_sci_notation(val):
            val = Decimal(val)
        elif is_int(val):
            val = Decimal(val)
        elif is_float(val):
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


class PostProcessor(object):
    '''
    Module for post processing
    '''

    PROCESSORS = {}

    def register_processor(mapping, name):
        def wrapper(func):
            mapping[name] = func

            return func
        return wrapper

    @classmethod
    def run(Class, data):
        return Class().process(data)

    def process(self, data):
        '''
        Does special post-processing based on a file schema
        '''
        # This
        if "GAME" in data.keys():
            scenarios = data["GAME"][0]["SCENARIO"]
            for scenario in scenarios:
                if "name" in data.keys():
                    self.process_scenario(scenario)
        elif "name" in data.keys():
            self.process_scenario(data)

        return data

    def process_scenario(self, scenario):
        processor = self.PROCESSORS.get(scenario["name"], False)
        if processor:
            processor(self, scenario)

    @register_processor(PROCESSORS, "ResearchAndDevelopment")
    def process_rnd(self, scenario):
        # We know for sure that each tech has a list of parts
        # but the list is a duplication list (therefore sometimes parses as a single item)
        for tech in scenario.get("Tech", {}):
            if "part" in tech.keys() and not isinstance(tech["part"], list):
                tech["part"] = DuplicationList([tech["part"]])


def load(fp, options=None):
    config = {
        # 'verbose': True,
    }
    if options is not None:
        config.update(options)

    machine = ParserStateMachine(config)
    try:
        machine.runAll(fp)
    except State.Error as err:
        raise DMPException.wraps(err)

    return PostProcessor.run(machine.get_data())

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
