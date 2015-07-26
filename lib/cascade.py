#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from functools import wraps


def cascade(func):
    '''
    A method wrapper that ensures that self is always returned
    '''
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        func(self, *args, **kwargs)
        return self
    return wrapper
