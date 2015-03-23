#!/usr/bin/python2

# Create Mininet topology and run tests

from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import time

def setup():
    net = Mininet(controller = RemoteController)

    net.addController( 'c0' )

    h1 = net.addHost('h1', ip='10.0.0.1')
    h2 = net.addHost('h2', ip='10.0.0.2')

    s1 = net.addSwitch('s1')

    net.addLink(h1, s1)
    net.addLink(h2, s1)

    return net, h1, h2

def test():
    for r in [float(i) / 100.0 for i in range(0, 100, 5)]:
        info('Setting up Mininet...\n')
        net, h1, h2 = setup()

        net.start()
        h2.setMAC("7a:4e:18:bf:a3:24")
        net.pingAll()

        info('Delay 5 sec for network setup')
        time.sleep(5)

        info('Testing on rate %.2f...\n' % r)
        h2.cmd("python2 server.py &")
        h1.cmdPrint("sleep 1 && python2 client.py %.2f 50000" % r)
        h2.cmd("sleep 5 && cat server.pid | xargs kill -s sigint")
        net.stop()

        time.sleep(1)

if __name__ == '__main__':
    setLogLevel( 'info' )
    test()
