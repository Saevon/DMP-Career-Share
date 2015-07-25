#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from threading import Thread
from time import sleep


class TimerThread(Thread):
    '''
    Timer thread that
    '''

    SLEEP_INCREMENTS = 1

    def __init__(self, event):
        '''
        Creates a timer thread

            event: the function to run when the timer runs out
        '''
        super(TimerThread, self).__init__()
        self.event = event

        self.wait_time = 0
        self.total_time = 0

        self.should_die = False

    def run(self):
        while not self.should_die:
            if self.wait_time and self.total_time > self.wait_time:
                self.reset()
                self.event()
            else:
                sleep(self.SLEEP_INCREMENTS)
                self.total_time += self.SLEEP_INCREMENTS

    def stop(self):
        '''
        Stops the thread
        '''
        self.should_die = True

    def reset(self):
        '''
        Turns the timer off
        '''
        self.wait_time = 0
        self.total_time = 0

    def set(self, time):
        '''
        Starts the timer with the given time, if there is a timer already running, turns it off
        '''
        self.reset()
        self.wait_time = time

    def is_on(self):
        '''
        Returns whether the timer is running or not
        '''
        return self.wait_time != 0

