#!/bin/python2

# plot average costs

import matplotlib.pyplot as plt
import sys

for fn in sys.argv[1:]:
    datf = open(fn, 'r')
    y = datf.read().split(',')
    x = [5 * i for i in range(0, len(y))]
    plt.plot(x,y)

plt.xlim([0, 100])
plt.show()
