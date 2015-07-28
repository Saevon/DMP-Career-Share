#!/bin/bash
tail -f ../dmp.log | python scanner.py ../Universe/Scenarios/ ../Universe/Initial/
