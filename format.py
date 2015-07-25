#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from collections import OrderedDict
from functools import wraps
from decimal import Decimal

from parser_data import InlineList, DuplicationList



def deepen(val, depth=0):
    return '%s%s' % (
        chr(0x9) * depth,
        val,
    )

def deepen_return(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        out = func(*args, **kwargs)

        depth = kwargs.get('depth', 0)

        for i, line in enumerate(out):
            out[i] = deepen(line, depth)
        return out
    return decorator


@deepen_return
def format(key, val, depth=0):
    # Convert normal lists to their default output type

    # Now choose a formatter to use
    if isinstance(val, DuplicationList):
        return format_dups(key, val, depth)
    elif isinstance(val, dict):
        return format_dict(key, val, depth)
    elif isinstance(val, OrderedDict):
        return format_dict(key, val, depth)
    elif isinstance(val, list):
        val = InlineList(val)
        return format_simple(key, val, depth)
    else:
        return format_simple(key, val, depth)

def format_dups(key, val, depth=0):
    lines = []

    for line in val:
        lines += format(key, line)

    return lines


def format_dict(key, val, depth=0):
    '''
    Formats a dictionary
    '''
    lines = []

    lines.append(key)
    lines.append('{')

    for subkey, subval in val.iteritems():
        lines += format(subkey, subval, depth=1)

    lines.append('}')

    return lines


def format_simple(key, val, depth=0):
    '''
    Formats simple data that is listed with a name
    '''
    string = format_unnamed(val)
    return [
        '%s = %s' % (key, string),
    ]

def format_unnamed(val):
    '''
    Formats simple data that is listed without a name and a depth
    '''

    # Format the data
    if isinstance(val, str):
        out = val
    elif isinstance(val, bool):
        out = str(val)
    elif isinstance(val, InlineList):
        join_str = ', ' if val.space_formatted else ','

        out = join_str.join([format_unnamed(subval) for subval in val])
    elif isinstance(val, float):
        # Floats get to have at most 12 digit precision
        # However if it needs to strip any trailing zeros (and the decimal point if its basically an int)
        out = ('%.12f' % val).rstrip('0').rstrip('.')
    elif isinstance(val, Decimal):
        out = str(val)
    elif isinstance(val, int):
        out = str(val)
    else:
        raise NotImplementedError("Can't convert val: %s" % type(val))

    return out



