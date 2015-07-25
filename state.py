#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from cascade import cascade


class VerboseMixin(object):
    def __init__(self):
        self.__verbose = False

        self.depth = 0

    def debug(self, *lines):
        '''
        Prints all the given text if the verbose option is set
        '''
        if not self.__verbose:
            return

        self.__print(*lines)

    def error(self, *lines):
        '''
        Prints all the given text as an error
        '''
        self.__print(*lines)

    def __print(self, *lines):
        for line in lines:
            print '    ' * self.depth + str(line)

    @property
    def logging_enabled(self):
        return self.__verbose

    @logging_enabled.setter
    def logging_enabled(self, val):
        self.__verbose = val

    @property
    def depth(self):
        return self.__depth

    @depth.setter
    def depth(self, val):
        self.__depth = val

        if self.__depth < 0:
            self.__depth = 0



class StateMachine(VerboseMixin):

    DEFAULT_OPTIONS = {
        'verbose': False,
    }

    def __init__(self, initial_state, options=None):
        super(StateMachine, self).__init__()

        self.options = {}
        self.options.update(self.DEFAULT_OPTIONS)
        if options is not None:
            self.options.update(options)

        self.__state = State()
        self.state = initial_state
        self.line = 0

        self.logging_enabled = options.get('verbose', False)

    def run(self, line):
        # Note: Trampolined function for tail recursion
        rerun = True
        while rerun:
            self.state, rerun = self.state(line)

    ###########################
    # Public Use

    def runAll(self, inputs):
        '''
        Runs the StateMachine on an iterator
        '''
        for val in inputs:
            val = self.preprocess(val)

            self.debug("'%s'" % val)
            self.line += 1
            try:
                self.run(val)
            except State.Error as err:
                self.error("StateError: line %i" % self.line, err)
                return

    @property
    def state(self):
        return self.__state

    @state.setter
    def state(self, state):
        # Store the old depth
        self.depth = self.__state.depth

        self.__state = state
        self.__state.logging_enabled = self.logging_enabled

        self.__state.depth = self.depth

    #############################
    # Subclass methods

    def preprocess(self, val):
        '''
        Pre-processes the given value before passing it to the current State
        '''
        return val


class State(VerboseMixin):

    class Error(Exception):
        pass


    def __init__(self):
        super(State, self).__init__()

        self.parent = None

        self.__next = None
        self.__rerun = False

    #########################
    # Public Use

    def __call__(self, val):
        '''
        Use the State as a function
        '''
        self.reuse_state()

        self.run(val)

        return self.__next, self.__rerun

    @cascade
    def set_parent(self, parent):
        self.parent = parent

    ############################
    # Setting the next state

    @cascade
    def reuse_state(self):
        self.__next = self
        self.__rerun = False

    @cascade
    def finish_state(self):
        self.__next = self.parent
        self.__rerun = False

    @cascade
    def new_state(self, state):
        self.__next = state
        self.__rerun = False

    @cascade
    def rerun_with_state(self, state):
        self.__next = state
        self.__rerun = True

    #########################
    # Subclass Methods

    def run(self, val):
        '''
        Runs the state parser
            Overwrite this method in subclasses
        '''
        raise NotImplemented

