#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import re


INT_RE = re.compile('^-?[0-9]+$')
FLOAT_RE = re.compile('^-?[0-9]+(\.[0-9]+)?$')
SCI_RE = re.compile('^[0-9]+E-?[0-9]+$')

def is_float(val):
    return FLOAT_RE.match(val) is not None

def is_int(val):
    return INT_RE.match(val) is not None

def is_sci_notation(val):
    return SCI_RE.match(val) is not None
