#!/usr/bin/env python
# -*- coding: UTF-8 -*-


class InlineList(list):
    '''
    Simple list wrapper that IDS lists that need to be printed inline when outputting
    '''
    def __init__(self, iterable=None):
        args = []
        if iterable:
            args.append(iterable)
            self.__space_formatted = getattr(iterable, 'space_formatted', True)
        else:
            self.__space_formatted = True



        super(InlineList, self).__init__(*args)

    @property
    def space_formatted(self):
        return self.__space_formatted

    @space_formatted.setter
    def space_formatted(self, val):
        self.__space_formatted = val

class DuplicationList(list):
    '''
    Simple list wrapper that IDS lists that need to be printed as duplicate entries
    '''
    pass
