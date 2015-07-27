# !/usr/bin/env python
# -*- coding: UTF-8 -*-
import os

from profile import FullSaveProfile
from error import DMPException


PATH = "/Users/Saevon/Applications/Kerbal Space Program/saves/Saevon/"
OUT_PATH = "/Users/Saevon/Applications/Kerbal Space Program/saves/Saevon2/"
NAME = "persistent.sfs"

if __name__ == '__main__':
    save = FullSaveProfile(NAME, PATH).refresh()

    for key, scenario in save.data.iteritems():
        print "Exporting: %s" % key
        scenario.export(OUT_PATH)
