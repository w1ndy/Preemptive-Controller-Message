import numpy as np
import matplotlib.pyplot as plt
import sys

for fn in sys.argv[1:]:
    datf = open(fn, 'r')
    y = np.array(map(float, datf.read().split(',')))
    datf.close()
    x = np.array([5.0 * i for i in range(0, len(y))])
    func = np.poly1d(np.polyfit(x, y, 1))
    func_x = np.linspace(0, 100, 200)
    plt.plot(x, y, '.', label='%s points' % fn)
    plt.plot(func_x, func(func_x), '-', label='%s linear fit' % fn)

plt.legend(loc='best')
plt.xlim([0,100])
plt.show()


