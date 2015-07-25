#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from collections import OrderedDict
import json

from parser_data import InlineList, DuplicationList
from state import State, StateMachine
from type_check import is_int, is_float



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

            # Check if the data exists, in which case its actually a list so we have to change its type
            old_data = self.data.get(key, None)
            if old_data is None:
                self.data[key] = self.read_data(val)
            elif not isinstance(old_data, DuplicationList):
                val = self.data[key]
                self.data[key] = DuplicationList()
                self.data[key].append(val)
            else:
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
            val = float(val)

        return val

class DictState(DataState):

    def __init__(self, data):
        super(DictState, self).__init__(data)

        self.val = OrderedDict()

        self.run = self.state_name

    def state_name(self, val):
        # print 'name'
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
                self.data[self.name] = []
            self.data.get(self.name).append(self.val)

            self.depth -= 1
            return self.finish_state()
        else:
            self.debug('= DATA = ')
            return self.rerun_with_state(
                NeutralState(self.val).set_parent(self)
            )


def load(fp):
    machine = ParserStateMachine({
        # 'verbose': True,
    })
    machine.runAll(fp)

    return machine.get_data()


if __name__ == "__main__":
    with open('../Universe/Scenarios/Saevon/ProgressTracking.txt', 'r') as fp:
        data = load(fp)
        print json.dumps(data, indent=4)
        print

    # with open('../Universe/Scenarios/Saevon/ResearchAndDevelopment.txt', 'r') as fp:
    #     data = load(fp)
    #     print json.dumps(data, indent=4)
