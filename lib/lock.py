#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from functools import wraps


LOCK_PREFIX = "__is_locked"

def _lock_key(name):
    if name is None:
        return LOCK_PREFIX
    return "%s_%s" % (LOCK_PREFIX, name)


def when_locked(name, lock=True):
    '''
    Method decorator, only runs when the named lock is locked
    '''
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if self.is_locked(name) != lock:
                return

            return func(self, *args, **kwargs)
        return wrapper
    return decorator

def when_unlocked(name):
    '''
    Method decorator, only runs when the named lock is unlocked
    '''
    return when_locked(name, False)


class LockMixin(object):
    '''
    A mixin for a cleaner locking API
        Locks work on a per-object basis
    '''
    def lock(self, name=None, lock=True):
        '''
        Updates the lock status
        '''
        setattr(self, _lock_key(name), lock)

    def unlock(self, name=None):
        return self.lock(name, False)

    def is_locked(self, name=None):
        '''
        Checks on the lock status
        '''
        return getattr(self, _lock_key(name), False)



import threading


def get_threading_lock(self, name):
    '''
    Gets this instance's threading lock for the given name
    '''
    lock = getattr(self, _lock_key(name), None)

    if lock is None:
        lock = threading.Lock()
        setattr(self, _lock_key(name), lock)
    return lock

def with_threading_lock(name):
    '''
    Ensures the method only runs with the named lock
    '''
    def wrapper(function):
        @wraps(function)
        def decorator(self, *args, **kwargs):
            with get_threading_lock(self, name):
                function(self, *args, **kwargs)
        return decorator
    return wrapper


