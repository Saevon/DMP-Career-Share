#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import traceback


class DMPException(Exception):

    @classmethod
    def wrap(Class, err):
        new_err = Class(repr(err))
        new_err.trace = traceback.format_exc()
        return new_err
