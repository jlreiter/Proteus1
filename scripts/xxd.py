#!/usr/bin/python

import sys
import os
import subprocess

if len(sys.argv) != 2:
    print "Usage: xxd.py <\"command to encode\">"
    sys.exit(0)

cmdencode = str(sys.argv[1])
ENCODECMD = "echo '%s' | xxd -p" % (cmdencode)
result = subprocess.check_output(ENCODECMD, shell=True)
ESCAPEDCMD = "echo '%s' | sed -e 's/../\\\\x&/g'" % (result)
DECODECHECK = "echo '%s' | xxd -r -p" % (result)
resultESCAPED = subprocess.check_output(ESCAPEDCMD, shell=True)
resultDECODE = subprocess.check_output(DECODECHECK, shell=True)

print result,
print "escaped: " + resultESCAPED,
print "decode check: " + resultDECODE,
