#!/bin/python2

# parse average costs from server.dat and
# save to file specified

import sys, re

ret = []

datf = open('server.dat', 'r')
for line in datf:
    dat = re.search(r'Avg cost: (.*?),', line)
    if dat:
        ret.append(dat.group(1))
datf.close()

out = open(sys.argv[1], 'w')
out.write(','.join(ret))
out.close()
